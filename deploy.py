"""Deployment script for Anki Torah addon distribution.

Maps source directories to Anki's expected addon folder names
and copies/symlinks them into the active addons21 directory.
"""

# #375 — שוחזר לאחר שנמחק בלי מנגנון חלופי, כדי שרישום/פריסה של יכולות תוסף
# חדשות ייבדקו שוב ב-dry-run ובבדיקות הרגרסיה של הפרויקט.

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import uuid
from pathlib import Path

from tools.addon_config_merge import POLICY, upgraded_configs, upgraded_metadata

REGISTRY_PATH = Path("config/addon_registry.json")
COMPAT_PATH = Path("config/anki_compatibility.json")


def load_json(filepath: Path) -> dict:
    if not filepath.exists():
        print(f"ERROR: File not found at {filepath}")
        sys.exit(1)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def load_registry(repo_root: Path) -> list[dict]:
    data = load_json(repo_root / REGISTRY_PATH)
    return data["addons"]


def load_compat_config(repo_root: Path) -> dict:
    filepath = repo_root / COMPAT_PATH
    if not filepath.exists():
        return {}
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def print_compat_summary(compat: dict) -> None:
    if not compat:
        return
    target = compat.get("target_anki_version", "?")
    min_ver = compat.get("min_anki_version", "?")
    print(f"Target Anki: {target} (min: {min_ver})")

    overrides = compat.get("addon_overrides", {})
    disabled_by_compat = [
        (k, v.get("reason", ""))
        for k, v in overrides.items()
        if not v.get("enabled", True)
    ]
    if disabled_by_compat:
        print(f"Disabled by compatibility: {len(disabled_by_compat)} addons")
        for deploy_dir, reason in disabled_by_compat:
            print(f"  - {deploy_dir}: {reason}")


def resolve_addons21_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", ""))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    return base / "Anki2" / "addons21"


def read_user_config(addon_dir: Path) -> tuple[dict | None, dict | None]:
    # Preserve legacy edits too, but merge them into NEW defaults, never copy wholesale.
    config_path = addon_dir / "config.json"
    config_json = None
    if config_path.exists():
        config_json = json.loads(config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(config_json, dict):
            raise ValueError(f"Configuration must be a JSON object: {config_path}")
    meta_config: dict | None = None

    meta_path = addon_dir / "meta.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8-sig") as f:
            meta = json.load(f)
            if not isinstance(meta, dict):
                raise ValueError(f"Metadata must be a JSON object: {meta_path}")
            meta_config = meta.get("config")
            if "config" in meta and meta_config is None:
                print(f"Restored null user configuration: {meta_path}")
                meta_config = {}
            elif meta_config is not None and not isinstance(meta_config, dict):
                raise ValueError(f"meta.config must be a JSON object: {meta_path}")

    return config_json, meta_config


def write_user_config(
    target: Path,
    config_json: dict | None,
    meta_config: dict | None,
    saved_metadata: dict | None = None,
    is_upgrade: bool | None = None,
) -> None:
    config_path = target / "config.json"
    meta_path = target / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8-sig")) if meta_path.exists() else None
    defaults = json.loads(config_path.read_text(encoding="utf-8-sig")) if config_path.exists() else {}
    merged, meta_config = upgraded_configs(defaults, config_json or {}, meta_config, target.name,
                                          is_upgrade=is_upgrade)
    if config_path.exists() or config_json is not None:
        config_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    if meta is not None:
        meta = upgraded_metadata(meta, saved_metadata, target.name)
        if meta_config is not None:
            meta["config"] = meta_config
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)


def deploy_addon(
    source: Path,
    target: Path,
    *,
    use_symlink: bool,
    preserve_config: bool,
    legacy_target: Path | None = None,
) -> str:
    if not source.exists():
        return f"SKIP (source missing): {source}"

    config_json: dict | None = None
    meta_config: dict | None = None
    migrated_from: str | None = None
    saved_metadata = None
    backup = None
    user_files = []
    saved_user_files = {}
    previous = target if target.exists() else legacy_target

    if preserve_config:
        if target.exists():
            config_json, meta_config = read_user_config(target)
        elif legacy_target and legacy_target.exists():
            config_json, meta_config = read_user_config(legacy_target)
            migrated_from = legacy_target.name
        if previous and (previous / "meta.json").exists():
            saved_metadata = json.loads((previous / "meta.json").read_text(encoding="utf-8-sig"))

    if not use_symlink:
        # Validate BEFORE deleting the installed addon; keep exact original bytes for recovery.
        source_defaults, _ = read_user_config(source)
        defaults = source_defaults if source_defaults is not None else {}
        upgraded_configs(defaults, config_json or {}, meta_config, target.name,
                         is_upgrade=preserve_config and previous is not None and previous.exists())
        package_meta = json.loads((source / "meta.json").read_text(encoding="utf-8-sig")) if (source / "meta.json").exists() else {}
        upgraded_metadata(package_meta, saved_metadata, target.name)
        if preserve_config and previous and previous.exists():
            backup = target.parent.parent / "haf-addon-settings-backup" / target.name / uuid.uuid4().hex
            user_files = list(POLICY["user_data_files"].get(target.name, []))
            for name in ("config.json", "meta.json", *user_files):
                original = previous / name
                # Never follow a user-data link out of the addon or into a live profile.
                if name in user_files:
                    if not original.resolve().is_relative_to(previous.resolve()):
                        raise ValueError(f"User-data path escapes addon: {original}")
                    for part in (original, *original.parents):
                        if part == previous.parent:
                            break
                        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
                            raise ValueError(f"Linked user-data path is not supported: {part}")
                if original.exists():
                    destination = backup / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original, destination)
                    if original.read_bytes() != destination.read_bytes():
                        raise OSError(f"Settings backup verification failed: {destination}")
                    if name in user_files:
                        saved_user_files[name] = destination

            # If both generations exist, current settings win, but keep the old
            # copy for recovery and recover files missing from the current one.
            if legacy_target and legacy_target != previous and legacy_target.exists():
                for name in ("config.json", "meta.json", *user_files):
                    original = legacy_target / name
                    if not original.resolve().is_relative_to(legacy_target.resolve()):
                        raise ValueError(f"Legacy settings path escapes addon: {original}")
                    if original.exists():
                        destination = backup / "legacy" / legacy_target.name / name
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(original, destination)
                        if original.read_bytes() != destination.read_bytes():
                            raise OSError(f"Settings backup verification failed: {destination}")
                        if name in user_files:
                            saved_user_files.setdefault(name, destination)

    if target.exists() or target.is_symlink():
        if target.is_symlink():
            target.unlink()
        else:
            shutil.rmtree(target)

    if legacy_target and legacy_target.exists() and legacy_target != target:
        if not preserve_config:
            config_json, meta_config = None, None
        shutil.rmtree(legacy_target)

    if use_symlink:
        target.symlink_to(source.resolve())
        action = "SYMLINK"
    else:
        shutil.copytree(source, target)
        action = "COPY"

    if not use_symlink:
        write_user_config(target, config_json, meta_config, saved_metadata,
                          is_upgrade=preserve_config and previous is not None and backup is not None)
        if backup:
            for name, saved_path in saved_user_files.items():
                destination = target / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(saved_path, destination)

    suffix = f" (migrated from {migrated_from})" if migrated_from else ""
    return f"{action}: {source.name} -> {target.name}{suffix}"


def deploy_shared_libs(
    repo_root: Path,
    addons21: Path,
    *,
    use_symlink: bool,
) -> str:
    source = repo_root / "shared_libs"
    target = addons21 / "_shared_libs"
    if not source.exists():
        return "SKIP (shared_libs not found)"
    return deploy_addon(
        source, target, use_symlink=use_symlink, preserve_config=False
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy Anki Torah addons to addons21 directory"
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Target addons21 directory (auto-detected if omitted)",
    )
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="Create symlinks instead of copying files (dev mode)",
    )
    parser.add_argument(
        "--no-preserve-config",
        action="store_true",
        help="Do not preserve user settings from meta.json",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Deploy only specific addons (by deploy_dir name)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--target-name",
        choices=["deploy", "source"],
        default="deploy",
        help="Name target folders by deploy_dir (default) or by source folder name",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.resolve()
    addons21 = args.target or resolve_addons21_path()
    preserve_config = not args.no_preserve_config

    print(f"Repository root: {repo_root}")
    print(f"Target addons21: {addons21}")
    print(f"Mode: {'symlink' if args.symlink else 'copy'}")
    print(f"Target naming: {args.target_name}")
    print(f"Preserve user configs: {preserve_config}")

    compat = load_compat_config(repo_root)
    print_compat_summary(compat)
    print("-" * 60)

    if not args.dry_run and not addons21.exists():
        addons21.mkdir(parents=True, exist_ok=True)
        print(f"Created target directory: {addons21}")

    compat_overrides = compat.get("addon_overrides", {})
    addons = load_registry(repo_root)
    results: list[str] = []

    for addon in addons:
        deploy_dir = addon["deploy_dir"]
        source_name = Path(addon["source_dir"]).name
        target_name = deploy_dir if args.target_name == "deploy" else source_name

        if addon.get("status") == "disabled":
            results.append(f"DISABLED: {addon['name']}")
            continue

        override = compat_overrides.get(deploy_dir, {})
        if not override.get("enabled", True):
            results.append(f"DISABLED (compat): {addon['name']} - {override.get('reason', '')}")
            continue

        if args.only and deploy_dir not in args.only and source_name not in args.only:
            continue

        source = repo_root / addon["source_dir"]
        target = addons21 / target_name
        legacy_deploy_dir = addon.get("legacy_deploy_dir")
        legacy_target = addons21 / legacy_deploy_dir if legacy_deploy_dir else None

        if args.dry_run:
            migrate_note = ""
            if legacy_target and legacy_target.exists():
                migrate_note = f" (will migrate from {legacy_deploy_dir})"
            results.append(f"DRY-RUN: {source} -> {target}{migrate_note}")
            continue

        result = deploy_addon(
            source,
            target,
            use_symlink=args.symlink,
            preserve_config=preserve_config,
            legacy_target=legacy_target,
        )
        results.append(result)

    if not args.dry_run:
        results.append(deploy_shared_libs(repo_root, addons21, use_symlink=args.symlink))
    else:
        results.append("DRY-RUN: shared_libs -> _shared_libs")

    print("\nDeployment Report:")
    print("=" * 60)
    deployed = 0
    skipped = 0
    disabled = 0
    migrated = 0
    for result in results:
        print(f"  {result}")
        if result.startswith(("COPY", "SYMLINK")):
            deployed += 1
            if "migrated from" in result:
                migrated += 1
        elif result.startswith("SKIP"):
            skipped += 1
        elif result.startswith("DISABLED"):
            disabled += 1
        elif result.startswith("DRY-RUN"):
            deployed += 1

    print("=" * 60)
    summary = f"Total: {deployed} deployed, {skipped} skipped, {disabled} disabled"
    if migrated:
        summary += f", {migrated} migrated"
    print(summary)


if __name__ == "__main__":
    main()
