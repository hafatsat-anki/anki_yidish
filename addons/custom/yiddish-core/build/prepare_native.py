"""Prepare official Anki 25.09.2 source for a native, complete yi locale.

Run with Python 3, then cargo build --release --locked -p rsbridge
--features native-tls on Windows with Python 3.13, Rust 1.89, and protoc.
This script modifies only the supplied independent upstream checkout.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

ANKI_COMMIT = "3890e12c9e48c028c3f12aa58cb64bd9f8895e30"
BUILDHASH = "3890e12c"
KEY = re.compile(r"^(-?[a-zA-Z][\w-]*)\s*=", re.MULTILINE)
VAR = re.compile(r"\$([a-zA-Z][\w-]*)")


def messages(text: str) -> dict[str, str]:
    matches = list(KEY.finditer(text))
    return {
        match.group(1): text[match.end(): matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        for i, match in enumerate(matches)
    }


def prepare(upstream: Path, locale: Path, allow_incomplete: bool = False) -> int:
    revision = subprocess.check_output(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != ANKI_COMMIT:
        raise ValueError(f"Unsupported Anki source revision: {revision}")
    total = 0
    missing = []
    for category, output in (
        ("core", upstream / "ftl/core-repo/core/yi"),
        ("qt", upstream / "ftl/qt-repo/desktop/yi"),
    ):
        output.mkdir(parents=True, exist_ok=True)
        for original in sorted((upstream / "ftl" / category).glob("*.ftl")):
            translated = locale / category / original.name
            if not translated.is_file():
                missing.append(f"{category}/{original.name}")
                continue
            originals = messages(original.read_text(encoding="utf-8"))
            text = translated.read_text(encoding="utf-8")
            translations = messages(text)
            if set(originals) != set(translations):
                raise ValueError(f"Message ID coverage differs in {category}/{original.name}")
            for key, val in originals.items():
                # Ignore upstream translator comments when finding variables.
                val = "\n".join(line for line in val.splitlines() if not line.lstrip().startswith("#"))
                if set(VAR.findall(val)) != set(VAR.findall(translations[key])):
                    raise ValueError(f"Fluent variable mismatch in {key}")
            if not text.endswith("\n"):
                raise ValueError(f"Missing final newline in {translated}")
            shutil.copyfile(translated, output / translated.name)
            total += len(translations)
    if missing and not allow_incomplete:
        raise ValueError(f"Incomplete localization: {', '.join(missing)}")
    (upstream / "out").mkdir(exist_ok=True)
    (upstream / "out/buildhash").write_text(BUILDHASH, encoding="ascii")
    # Upstream's Windows build assumes its own out/pyenv exists. A standalone
    # GitHub rsbridge build instead uses setup-python via PYO3_PYTHON.
    build_script = upstream / "pylib/rsbridge/build.rs"
    rust = build_script.read_text(encoding="utf-8")
    old = '        let output = Command::new("../../out/pyenv/scripts/python")'
    new = '''        let python = std::env::var("PYO3_PYTHON")
            .unwrap_or_else(|_| "../../out/pyenv/scripts/python".to_string());
        let output = Command::new(python)'''
    if old in rust:
        build_script.write_bytes(rust.replace(old, new).encode("utf-8"))
    elif new not in rust:
        raise ValueError("Unsupported rsbridge Windows Python bootstrap")
    print(f"Prepared {total} native Yiddish messages; incomplete files: {len(missing)}")
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--locale", type=Path, default=Path(__file__).resolve().parents[1] / "locale")
    parser.add_argument("--allow-incomplete", action="store_true", help="Development build only; never use for a release")
    args = parser.parse_args()
    prepare(args.upstream.resolve(), args.locale.resolve(), args.allow_incomplete)
