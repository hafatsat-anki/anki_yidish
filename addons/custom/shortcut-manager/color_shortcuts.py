import ast
import json
import re


# #238/#212 - accept old string/list formats and skip malformed color rows instead of unpacking them directly.
_LEGACY_PAIR_RE = re.compile(r"\[\s*([^,\[\]]*?)\s*,\s*([^\[\]]*?)\s*\]")
_EMPTY_SHORTCUTS = {"", "none", "<nop>", "null"}


def _clean_legacy_token(value):
    if value is None:
        return ""
    return str(value).strip().strip("'\"")


def _parse_string_keys(raw_keys):
    text = raw_keys.strip()
    if not text:
        return []

    for loader in (json.loads, ast.literal_eval):
        try:
            parsed = loader(text)
        except Exception:
            continue
        if isinstance(parsed, (list, tuple)):
            return parsed

    rows = []
    for color, shortcut in _LEGACY_PAIR_RE.findall(text):
        rows.append([_clean_legacy_token(color), _clean_legacy_token(shortcut)])
    return rows


def normalize_color_shortcut_rows(raw_keys, expected_rows=None):
    if isinstance(raw_keys, str):
        raw_keys = _parse_string_keys(raw_keys)

    rows = []
    if isinstance(raw_keys, (list, tuple)):
        for row in raw_keys:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            color = _clean_legacy_token(row[0])
            shortcut = _clean_legacy_token(row[1])
            rows.append([color, shortcut])

    if expected_rows is not None:
        rows = rows[:expected_rows]
        while len(rows) < expected_rows:
            rows.append(["", ""])
    return rows


def iter_active_color_shortcuts(raw_keys):
    for color, shortcut in normalize_color_shortcut_rows(raw_keys):
        if not color:
            continue
        if shortcut.strip().lower() in _EMPTY_SHORTCUTS:
            continue
        yield color, shortcut