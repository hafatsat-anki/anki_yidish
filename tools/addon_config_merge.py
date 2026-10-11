"""Complete upgraded settings without replacing explicit user preferences."""
from copy import deepcopy
import json
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parents[1] / "installer-src/installer_files/addon_settings_policy.json"
POLICY = json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _lookup(data, path):
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return False, None
        data = data[key]
    return True, data


def _set_path(data, path, value):
    for key in path[:-1]:
        data = data.setdefault(key, {})
    data[path[-1]] = deepcopy(value)


def upgraded_metadata(defaults: dict, saved: dict | None, addon_name: str) -> dict:
    """Preserve enablement/unknown user metadata, but never old package identity."""
    saved = saved if saved is not None else {}
    if not isinstance(defaults, dict) or not isinstance(saved, dict):
        raise ValueError("Metadata must be a JSON object")
    for metadata in (defaults, saved):
        if "disabled" in metadata and not isinstance(metadata["disabled"], bool):
            raise ValueError("meta.disabled must be a boolean")
    result = {key: deepcopy(value) for key, value in defaults.items() if key != "config"}
    for key, value in saved.items():
        if key not in POLICY["package_meta_fields"] and key != "config":
            result[key] = deepcopy(value)
    if addon_name in POLICY["forced_disabled"]:
        result["disabled"] = True
    return result


def merge_settings(defaults: dict, saved: dict, location: str = "config") -> dict:
    if not isinstance(defaults, dict) or not isinstance(saved, dict):
        raise ValueError(f"{location} must be a JSON object")
    result = deepcopy(defaults)
    for key, value in saved.items():
        if key in result and value is None and result[key] is not None:
            print(f"Restored null setting: {location}.{key}")
            continue
        if isinstance(result.get(key), dict):
            if not isinstance(value, dict):
                raise ValueError(f"Expected a settings object at {location}.{key}")
            result[key] = merge_settings(result[key], value, f"{location}.{key}")
        else:
            result[key] = deepcopy(value)
    return result


def upgraded_configs(defaults: dict, saved: dict, overrides: dict | None,
                     addon_name: str, *, is_upgrade: bool | None = None) -> tuple[dict, dict | None]:
    merged = merge_settings(defaults, saved)
    effective = merge_settings(merged, overrides, "meta.config") if overrides is not None else None
    if addon_name == "modern-theme" and defaults:
        release = defaults.get("distribution_version")
        if not isinstance(release, str) or not release.strip():
            raise ValueError("The new package is missing distribution_version")
    for path in POLICY["package_config"].get(addon_name, []):
        present, value = _lookup(defaults, path)
        if present:
            _set_path(merged, path, value)
            if effective is not None:
                _set_path(effective, path, value)
    if is_upgrade is None:
        is_upgrade = bool(saved or overrides)
    if is_upgrade:
        for marker in POLICY["migration_markers"].get(addon_name, []):
            present, value = _lookup(saved, marker["path"])
            override_present, override_value = _lookup(overrides, marker["path"])
            _set_path(merged, marker["path"], value if present else marker["initial"])
            if effective is not None:
                _set_path(effective, marker["path"], override_value if override_present else
                          value if present else marker["initial"])
    return merged, effective
