"""Patch only the independent packaged Anki runtime for its dedicated yi UI."""

from __future__ import annotations

import argparse
import hashlib
import json
import importlib.util
import marshal
import shutil
import struct
import sys
import zlib
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def runtime_source(name: str) -> str:
    sources = ADDON / "build/runtime_sources"
    manifest = json.loads((sources / "manifest.json").read_text(encoding="utf-8"))
    path = sources / name
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest["files"][name]:
        raise ValueError(f"Bundled runtime source differs from its recorded SHA256: {name}")
    return content.decode("utf-8").replace("\r\n", "\n")


def patch_frozen_archive(app: Path, modules: dict[str, Path], backup_dir: Path) -> dict:
    """Replace the actual frozen modules; external .py files cannot override PYZ."""
    from PyInstaller.archive.readers import CArchiveReader
    from PyInstaller.archive.writers import CArchiveWriter

    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("The packaged Anki runtime uses Python 3.13; run with py -3.13")
    executable = app / "anki.exe"
    archive = CArchiveReader(str(executable))
    pyz = archive.open_embedded_archive("PYZ.pyz")
    original = executable.read_bytes()
    original_pyz = archive.extract("PYZ.pyz")
    if original_pyz[4:8] != importlib.util.MAGIC_NUMBER:
        raise ValueError("Frozen Python bytecode version differs from this interpreter")
    backup = backup_dir / "anki.exe"
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        backup.write_bytes(original)

    # Preserve every unrelated compressed bytecode entry byte for byte. Only
    # the three owned modules are recompiled from the distribution's sources.
    toc = []
    rebuilt = bytearray(original_pyz[:17])
    for name, (kind, offset, length) in pyz.toc.items():
        if name in modules:
            source = modules[name].read_text(encoding="utf-8")
            filename = name.replace(".", "/") + ("/__init__.py" if kind == 1 else ".py")
            blob = zlib.compress(marshal.dumps(compile(source, filename, "exec")), level=6)
        else:
            blob = original_pyz[offset:offset + length]
        toc.append((name, (kind, len(rebuilt), len(blob))))
        rebuilt.extend(blob)
    for name in modules.keys() - pyz.toc.keys():
        source = modules[name].read_text(encoding="utf-8")
        blob = zlib.compress(marshal.dumps(compile(source, name.replace(".", "/") + ".py", "exec")), level=6)
        toc.append((name, (0, len(rebuilt), len(blob))))
        rebuilt.extend(blob)
    struct.pack_into("!i", rebuilt, 8, len(rebuilt))
    rebuilt.extend(marshal.dumps(toc))

    pkg = bytearray()
    pkg_toc = []
    for name, (offset, length, unpacked, compressed, kind) in archive.toc.items():
        if name == "allinanki" and "anki_yiddish_smoke_diagnostics" not in archive.toc:
            diagnostic_code = '''import os, sys
if os.environ.get("ANKI_YIDISH_SMOKE_REPORT"):
    import faulthandler
    _yi_diag_path = os.environ["ANKI_YIDISH_SMOKE_REPORT"] + ".startup.txt"
    _yi_diag_file = open(_yi_diag_path, "w", encoding="utf-8", buffering=1)
    _yi_diag_file.write("Frozen bootloader reached Python runtime\\n")
    faulthandler.dump_traceback_later(35, repeat=True, file=_yi_diag_file)
'''
            blob = marshal.dumps(compile(diagnostic_code, "anki_yiddish_smoke_diagnostics.py", "exec"))
            pkg_toc.append((len(pkg), len(blob), len(blob), 0, "s", "anki_yiddish_smoke_diagnostics"))
            pkg.extend(blob)
        if name == "allinanki":
            entry_source = '''import sys, tempfile, os
from os import path

def main():
    log_path = path.join(tempfile.gettempdir(), "anki-yidish.log")
    with open(log_path, "w", encoding="utf-8", buffering=1) as sys.stdout:
        sys.stderr = sys.stdout
        print("Anki Yidish 25.09.2")
        if os.name == "nt":
            os.environ["ANKI_LAUNCHER"] = path.abspath(path.join(sys._MEIPASS, "../Anki.exe"))
        import aqt
        if os.environ.get("ANKI_YIDISH_SMOKE_REPORT"):
            import aqt.utils, aqt.main, json
            def capture_startup_error(message, *args, **kwargs):
                with open(os.environ["ANKI_YIDISH_SMOKE_REPORT"], "w", encoding="utf-8") as file:
                    json.dump({"startup_error": str(message)}, file, ensure_ascii=False, indent=2)
            aqt.utils.showInfo = capture_startup_error
            aqt.main.showInfo = capture_startup_error
        aqt.run()

if __name__ == "__main__":
    main()
'''
            entry = marshal.dumps(compile(entry_source, "allinanki.py", "exec"))
            blob = zlib.compress(entry, 9) if compressed else entry
            unpacked = len(entry)
        elif name == "PYZ.pyz":
            blob = zlib.compress(rebuilt, 9) if compressed else bytes(rebuilt)
            unpacked = len(rebuilt)
        else:
            start = archive._start_offset + offset
            blob = original[start:start + length]
        pkg_toc.append((len(pkg), len(blob), unpacked, compressed, kind, name))
        pkg.extend(blob)
    for name in archive.options:
        pkg_toc.append((len(pkg), 0, 0, 0, "o", name))
    toc_offset = len(pkg)
    serialized = CArchiveWriter._serialize_toc(pkg_toc)
    pkg.extend(serialized)
    cookie = struct.unpack(CArchiveReader._COOKIE_FORMAT,
                           original[archive._end_offset - archive._COOKIE_LENGTH:archive._end_offset])
    if cookie[4] != 313:
        raise ValueError("Only the packaged Python 3.13 executable is supported")
    pkg.extend(struct.pack(CArchiveReader._COOKIE_FORMAT, cookie[0],
                           len(pkg) + archive._COOKIE_LENGTH, toc_offset,
                           len(serialized), cookie[4], cookie[5]))
    prefix = bytearray(original[:archive._start_offset])
    pe_offset = struct.unpack_from("<I", prefix, 0x3C)[0]
    optional_offset = pe_offset + 24
    if struct.unpack_from("<H", prefix, optional_offset)[0] != 0x20B:
        raise ValueError("Only the x64 PE32+ runtime is supported")
    # A modified executable cannot retain an Authenticode signature/checksum.
    struct.pack_into("<I", prefix, optional_offset + 64, 0)
    struct.pack_into("<II", prefix, optional_offset + 112 + 4 * 8, 0, 0)
    replacement = executable.with_suffix(".yi-new.exe")
    replacement.write_bytes(prefix + pkg)
    verified = CArchiveReader(str(replacement))
    new_pyz = verified.open_embedded_archive("PYZ.pyz")
    changed = []
    for name in pyz.toc:
        if name in modules:
            changed.append(name)
        elif pyz.extract(name, raw=True) != new_pyz.extract(name, raw=True):
            raise ValueError(f"Unrelated frozen module was altered: {name}")
    for name in modules:
        if new_pyz.extract(name) is None:
            raise ValueError(f"Patched frozen module is empty: {name}")
    replacement.replace(executable)
    return {
        "original_executable_sha256": hashlib.sha256(original).hexdigest(),
        "patched_executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "frozen_modules_replaced": changed,
        "frozen_modules_added": sorted(modules.keys() - pyz.toc.keys()),
        "unrelated_frozen_modules_preserved": len(pyz.toc) - len(changed),
    }


def patch(app: Path, *, backup_dir: Path, report_path: Path | None = None) -> dict:
    app = app.resolve()
    backup_dir = backup_dir.resolve()
    if backup_dir.is_relative_to(app):
        raise ValueError("Keep original runtime backups outside the app being packaged")
    internal = app / "_internal"
    lang = internal / "anki/lang.py"
    qt = internal / "aqt/__init__.py"
    originals = {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None for p in (lang, qt)}
    text = runtime_source("anki_lang.py")
    start = text.index("langs = ")
    end = text.index("# compatibility with old versions")
    text = text[:start] + 'langs = [("יידיש", "yi")]\n\n' + text[end:]
    text = text.replace('current_lang = "en"', 'current_lang = "yi"')
    text = text.replace('lang = "en_US"\n        idx', 'lang = "yi"\n        idx')
    text = text.replace('("he", "ar", "fa", "ug")', '("yi", "he", "ar", "fa", "ug")')
    write(lang, text)
    text = runtime_source("aqt_init.py")
    text = text.replace(
        '    KEY = f"anki{checksum(getpass.getuser())}"',
        '    KEY = os.environ.get("ANKI_YIDISH_INSTANCE", f"anki-yidish{checksum(getpass.getuser())}")',
    )
    text = text.replace('    lang = anki.lang.lang_to_disk_lang(lang)', '    lang = "yi"')
    text = text.replace('            "Startup Error",', '            "תקלה ביים עפענען",')
    text = text.replace('f"Please notify support of this error:', 'f"ביטע באריכט דעם תקלה צו שטיצע:')
    text = text.replace('"Startup Failed", "Unable to create data folder"', '"תקלה ביים עפענען", "מען האט נישט געקענט שאפן דעם דאטן־תיקיה"')
    marker = "    backend = anki.lang.current_i18n\n"
    injection = '    if lang == "yi":\n        from aqt.yiddish import install_qt\n\n        install_qt(app)\n\n'
    if injection not in text:
        if text.count(marker) != 1:
            raise ValueError("Unsupported Anki Qt initialization layout")
        text = text.replace(marker, injection + marker)
    text = text.replace(
        '    if pmLoadResult.firstTime:\n        pm.setDefaultLang(lang[0])',
        '    if pmLoadResult.firstTime:\n        pm.setLang("yi")',
    )
    early_marker = "    app = AnkiApp(argv)\n"
    previous_early = '    from aqt.yiddish import install_qt\n\n    install_qt(app)\n'
    early_injection = '    from aqt.yiddish import install_qt, verify_native\n\n    install_qt(app)\n    verify_native(anki.lang.current_i18n)\n'
    text = text.replace(previous_early, early_injection)
    if early_injection not in text:
        if text.count(early_marker) != 1:
            raise ValueError("Unsupported Anki QApplication initialization layout")
        text = text.replace(early_marker, early_marker + early_injection)
    write(qt, text)
    shutil.copyfile(ADDON / "runtime.py", internal / "aqt/yiddish.py")
    shutil.copyfile(ADDON / "yiddish_qt.json", internal / "aqt/yiddish_qt.json")
    frozen = patch_frozen_archive(app, {
        "anki.lang": lang,
        "aqt": qt,
        "aqt.yiddish": internal / "aqt/yiddish.py",
    }, backup_dir)
    report = {
        "runtime": str(app),
        "original_sha256": originals,
        "patched_sha256": {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (lang, qt)},
        "language": "yi",
        "rtl": True,
        "native_dialogs": False,
        "frozen_archive": frozen,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Registered dedicated yi locale, RTL and Yiddish Qt widgets in isolated packaged runtime")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    patch(args.app, backup_dir=args.backup_dir, report_path=args.audit)
