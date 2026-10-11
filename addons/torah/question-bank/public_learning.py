"""Public calendar lookup and conservative, row-level import planning (no Qt)."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from html import unescape
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import tarfile

from .learning_catalog import DIRSHU_TRACKS, EXTRA_TRACKS, PENDING_TRACKS


TRACKS = {"amud": "העמוד היומי — דרשו", "halacha": "דף היומי בהלכה — דרשו",
          "weekly": "דף השבוע", "chofetz": "חפץ חיים העולמי — מסלול שנתי"}
TRACKS.update({key: spec[0] for key, spec in EXTRA_TRACKS.items()})
TRACKS.update(DIRSHU_TRACKS)
ACTIVE_TRACKS = {key: title for key, title in TRACKS.items() if key not in PENDING_TRACKS}
CHOFETZ_SECTIONS = {"Hakdamah": "הקדמה", "Psichah": "פתיחה", "Lavin": "לאוין",
                   "Asin": "עשין", "Arurin": "ארורין", "Hilchos LH": "לשון הרע",
                   "Hilchos Rechilus": "רכילות", "Tziyurim": "ציורים"}
TRACTATES = dict(zip(
    ("Berachot|Shabbat|Eruvin|Pesachim|Shekalim|Yoma|Sukkah|Beitzah|Rosh Hashana|"
     "Taanit|Megillah|Moed Katan|Chagigah|Yevamot|Ketubot|Nedarim|Nazir|Sotah|Gitin|"
     "Kiddushin|Baba Kamma|Baba Metzia|Baba Batra|Sanhedrin|Makkot|Shevuot|Avodah Zarah|"
     "Horayot|Zevachim|Menachot|Chullin|Bechorot|Arachin|Temurah|Keritot|Meilah|Kinnim|"
     "Tamid|Midot|Niddah").split("|"),
    ("ברכות|שבת|עירובין|פסחים|שקלים|יומא|סוכה|ביצה|ראש השנה|תענית|מגילה|מועד קטן|"
     "חגיגה|יבמות|כתובות|נדרים|נזיר|סוטה|גיטין|קידושין|בבא קמא|בבא מציעא|בבא בתרא|"
     "סנהדרין|מכות|שבועות|עבודה זרה|הוריות|זבחים|מנחות|חולין|בכורות|ערכין|תמורה|"
     "כריתות|מעילה|קינים|תמיד|מידות|נדה").split("|")))
NUMBER = r"[א-ת\d][א-ת\d'׳\"״]*"
VALUES = dict(zip("אבגדהוזחטיכלמנסעפצקרשת", [1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100,200,300,400]))
KNOWN_TYPES = {"AnkiDaf": 3, "Anki-Daf-cloze": 2,
               "תת - שאלה רגילה - (לשימוש המאגר)": 3,
               "תת_לשימוש_המאגר_המוכן_משנב": 3,
               "תת_לשימוש_המאגר_המוכן_חפץ_חיים": 3}
HALACHA_SOURCES = {
    "@halacha:kadung": ("כדונג נמסו", "שאלות מפורטות על ו' חלקים- כדונג נמסו"),
    "@halacha:zichron": ("זכרון חנה", "זכרון חנה"),
    "@halacha:yha": ("הרב י.ח.א", "הרב י.ח.א"),
}


@lru_cache(maxsize=1)
def halacha_mapping():
    path = Path(__file__).with_name("halacha_daily_mapping.json")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def chofetz_mapping():
    path = Path(__file__).with_name("chofetz_daily_mapping.json")
    return json.loads(path.read_text(encoding="utf-8"))


def halacha_forecast_warning():
    return halacha_mapping()["scope"]["forecast_warning"]


def halacha_source_id(path):
    for source_id, (_, marker) in HALACHA_SOURCES.items():
        if marker in path:
            return source_id
    return None


def plain(text):
    return " ".join(unescape(re.sub(r"<[^>]*>", " ", text)).split())


def number(text):
    text = re.sub(r"['׳\"״]", "", text)
    if text.isdigit():
        return int(text)
    if not text or any(c not in VALUES for c in text):
        raise ValueError(f"Invalid number: {text}")
    if any(VALUES[a] < VALUES[b] for a, b in zip(text, text[1:])):
        raise ValueError(f"Non-numeral word: {text}")
    return sum(VALUES[c] for c in text)


# #461 — מספרי הספק מוצגים באותיות עבריות; ערכי begin/end נשארים מספריים למיפוי.
def _hebrew_numeral(value):
    if value == 0:
        return "0"
    if value >= 1000:
        thousands, remainder = divmod(value, 1000)
        prefix = _hebrew_numeral(thousands) + "׳"
        return prefix + (_hebrew_numeral(remainder) if remainder else "")
    letters = ""
    for amount, letter in ((400, "ת"), (300, "ש"), (200, "ר"), (100, "ק"),
                           (90, "צ"), (80, "פ"), (70, "ע"), (60, "ס"),
                           (50, "נ"), (40, "מ"), (30, "ל"), (20, "כ")):
        count, value = divmod(value, amount)
        letters += letter * count
    if value in (15, 16):
        return letters + ("טו" if value == 15 else "טז")
    if value >= 10:
        letters += "י"
        value -= 10
    return letters + "אבגדהוזחט"[value - 1] if value else letters


def _display_numerals(label):
    return re.sub(r"[0-9]+", lambda match: _hebrew_numeral(int(match.group())), label)


@dataclass(frozen=True)
class Lesson:
    track: str
    day: str
    label: str
    book: str
    begin: tuple[int, int]
    end: tuple[int, int]
    review: bool = False
    year: int = 0
    mapped: bool = True
    forecast: bool = False

    def __post_init__(self):
        # #461 — נקודת התצוגה המשותפת לכל המסלולים, גם בחלון וגם בהודעות הייבוא.
        object.__setattr__(self, "label", _display_numerals(self.label))


def calendar_data():
    data = json.loads(Path(__file__).with_name("public_calendars.json").read_text(encoding="utf-8"))
    local = json.loads(Path(__file__).with_name("dirshu_5787_calendars.json").read_text(encoding="utf-8"))
    data["calendars"].update(local["calendars"])
    halacha = halacha_mapping()
    days = halacha["days"]
    data["calendars"]["halacha"] = {
        "start": min(days),
        "end": max(days),
        "readings": days,
        "url": "https://www.dirshu.co.il/category/הדף-היומי-בהלכה/",
        "forecast_start": halacha["scope"]["forecast_start_day"],
        "last_official_day": halacha["scope"]["last_official_day"],
    }
    return data


def annual_year_for(day, data=None):
    years = (data or calendar_data())["calendars"]["chofetz"]["years"]
    for year, info in years.items():
        if info["start"] <= str(day) <= info["end"]:
            return int(year), info
    raise ValueError("נישטא קיין חפץ חיים קאלענדאר פארן געזוכטן יאר; מען דארף דערהיינטיגן די קאלענדארן.")


def lesson_for(track, day, data=None):
    """Finite published calendars: never extrapolate beyond their coverage."""
    if track not in TRACKS:
        raise ValueError("דער לערנען סדר איז נישט אקטיוו")
    if data is None:
        data = calendar_data()
    calendar = data["calendars"][track]
    day = date.fromisoformat(str(day))
    lookup = day - timedelta(days=(day.weekday() + 1) % 7) if track == "weekly" else day
    text = calendar["readings"].get(lookup.isoformat())
    if text is None:
        if track == "halacha" and calendar["start"] <= lookup.isoformat() <= calendar["end"]:
            return Lesson(track, day.isoformat(), "א טאג אן א נייעם הספק", "משנה ברורה",
                          (0, 0), (0, 0), review=True, mapped=False)
        if track in EXTRA_TRACKS and calendar["start"] <= lookup.isoformat() <= calendar["end"]:
            return Lesson(track, day.isoformat(), "עס איז נישט פארעפנטליכט קיין הספק פאר דעם טאג אינעם קאלענדאר פונעם לערנען סדר", "", (0, 0), (0, 0), review=True, mapped=False)
        raise ValueError(f"נישטא קיין קאלענדאר פארן דאטום {day}. קאלענדאר פארנעם: {calendar['start']} — {calendar['end']}. דערהיינטיגט די קאלענדארן פונעם צוגאב.")
    if track == "halacha" and isinstance(text, dict):
        return Lesson(
            track,
            day.isoformat(),
            text["label"],
            "משנה ברורה",
            tuple(text["begin"]),
            tuple(text["end"]),
            mapped=text.get("mapped", True),
            forecast=text["basis"] == "forecast_previous_cycle",
        )
    if track in DIRSHU_TRACKS:
        return Lesson(track, day.isoformat(), text["label"], text.get("book", ""),
                      tuple(text.get("begin", (0, 0))), tuple(text.get("end", (0, 0))),
                      review=text["review"], year=5787)
    if track in EXTRA_TRACKS:
        label = text["hebrew"].replace("Book I,", "חלק א׳,").replace("Book II,", "חלק ב׳,")
        if track == "mitzvot":
            label = re.sub(r"Day (\d+):", r"יום \1:", label)
            label = re.sub(r"\bP(\d+)", r"עשה \1", label)
            label = re.sub(r"\bN(\d+)", r"לא תעשה \1", label)
        if track == "mishna":
            match = re.fullmatch(r"(.+?) (\d+):(\d+)(?:-(?:(\d+):)?(\d+))?", label)
            if match:
                chapter, mishnah = int(match[2]), int(match[3])
                return Lesson(track, day.isoformat(), label, match[1], (chapter, mishnah),
                              (int(match[4] or chapter), int(match[5] or mishnah)))
        elif track == "perek":
            match = re.fullmatch(rf"(.+?) ({NUMBER})", label)
            if match:
                chapter = number(match[2])
                return Lesson(track, day.isoformat(), label, match[1], (chapter, 1), (chapter, 999))
        return Lesson(track, day.isoformat(), label, "", (0, 0), (0, 0), mapped=False)
    if track == "chofetz":
        year, info = annual_year_for(day, data)
        match = re.fullmatch(r"(Hakdamah|Psichah|Lavin|Asin|Arurin|Hilchos LH|Hilchos Rechilus|Tziyurim)(?: ([\d., -]+))?", text)
        if not match:
            raise ValueError(f"אומבאקאנטער חפץ חיים הספק מבנה: {text}")
        section = CHOFETZ_SECTIONS[match[1]]
        refs = re.findall(r"\d+(?:\.\d+)?", match[2] or "")
        def ref(value):
            pieces = value.split(".")
            return (int(pieces[0]), int(pieces[1]) if len(pieces) == 2 else 0)
        begin, end = (ref(refs[0]), ref(refs[-1])) if refs else ((0, 0), (999, 999))
        kind = "מעוברת" if info["leap"] else "רגילה"
        label = f"חפץ חיים {year} ({kind}) — {section} {match[2] or ''}".strip()
        return Lesson(track, day.isoformat(), label, section, begin, end, year=year)
    if track == "halacha":
        match = re.fullmatch(r"(Chazarah )?Mishnah Berurah (\d+)(?::(\d+))?(?:-(\d+)(?::(\d+))?)?", text)
        if not match:
            raise ValueError(f"אומבאקאנטער הלכה הספק מבנה: {text}")
        review, siman, seif, last, last_seif = match.groups()
        begin = (int(siman), int(seif or 1))
        if last is None:
            end = (int(siman), int(seif or 999))
        elif last_seif is None and seif is not None:
            end = (int(siman), int(last))
        else:
            end = (int(last), int(last_seif or 999))
        return Lesson(track, day.isoformat(), text.replace("Chazarah ", "חזרה: ").replace("Mishnah Berurah", "משנה ברורה"),
                      "משנה ברורה", begin, end, bool(review))
    match = re.fullmatch(r"(.+) (\d+)([ab])?", text)
    if not match or match[1] not in TRACTATES or (track == "amud" and not match[3]):
        raise ValueError(f"אומבאקאנטער הספק מבנה: {text}")
    book, page = TRACTATES[match[1]], int(match[2])
    side = {"a": 1, "b": 2}.get(match[3], 0)
    label = f"{book} {page}" + (f" ע״{'א' if side == 1 else 'ב'}" if side else "")
    return Lesson(track, lookup.isoformat(), label, book, (page, side or 1), (page, side or 2))


def source_roots(tree, track):
    if track == "halacha":
        return [(source_id, title) for source_id, (title, _) in HALACHA_SOURCES.items()]
    category = EXTRA_TRACKS[track][5] if track in EXTRA_TRACKS else {"halacha": "משנה ברורה", "chofetz": "עניינים"}.get(track, "שס")
    if not category:
        return []
    node = next((c for c in tree["children"] if c["name"] == category), {"children": []})
    return [(f"{tree['name']}/{category}/{c['name']}", c["name"].rstrip("$").replace("_", " "))
            for c in node["children"] if track != "chofetz" or c["name"] == "01חפץ_חיים_אור_מנחם"]


def candidate_files(tree, lesson, sources):
    """Find page/siman files, preserving the index's author and file order."""
    if lesson.track == "halacha":
        selected = set(sources)
        files = [
            path for path in halacha_mapping()["files_by_day"].get(lesson.day, [])
            if halacha_source_id(path) in selected
        ]
        return files, 0
    if lesson.track == "chofetz":
        if not lesson.mapped:
            return [], 0
        paths = {
            row["file"] for row in chofetz_mapping()["rows"].values()
            if row["book"] == lesson.book
            and lesson.begin <= tuple(row["ref"]) <= lesson.end
            and any(row["file"].startswith(source + "/") for source in sources)
        }
        return sorted(paths), 0
    found = []
    unmapped = 0
    if not lesson.mapped:
        return found, unmapped
    def walk(node, path):
        nonlocal unmapped
        path = f"{path}/{node['name']}" if path else node["name"]
        if node.get("type") == "directory":
            for child in node.get("children", []):
                walk(child, path)
            return
        if not path.endswith(".txt") or not any(path.startswith(s + "/") for s in sources):
            return
        if lesson.track in ("mishna", "perek"):
            match = re.fullmatch(rf"(.+)_פרק_({NUMBER})\.txt", node["name"])
            if match and normalize_book(match[1]) == normalize_book(lesson.book):
                if lesson.begin[0] <= number(match[2]) <= lesson.end[0]:
                    found.append(path)
            elif not match:
                unmapped += 1
            return
        if lesson.track != "halacha":
            folders = [re.sub(r"^\d+", "", p.split("%")[0]).replace("_", " ") for p in path.split("/")[3:-1]]
            if lesson.book not in folders:
                return
        stem = node["name"][:-4].replace("_", " ")
        prefix = "סימן" if lesson.track == "halacha" else re.escape(lesson.book)
        match = re.fullmatch(rf"(?:{prefix}\s+)?({NUMBER})(?:\s*[-–]\s*({NUMBER}))?", stem)
        if match is None:
            unmapped += 1
            return
        try:
            start, end = number(match[1]), number(match[2] or match[1])
        except ValueError:
            unmapped += 1
            return
        if start <= lesson.end[0] and end >= lesson.begin[0]:
            found.append(path)
    walk(tree, "")
    return found, unmapped


def classify_source(source, lesson):
    """Return exact/manual/outside. Uncertain boundaries are never auto-selected."""
    if lesson.track in DIRSHU_TRACKS:
        # Only the printed day/page schedule is imported at this stage.
        # Detailed question mapping was explicitly deferred by the user.
        return "manual"
    source = plain(source)
    if lesson.track in ("mishna", "perek"):
        location = re.fullmatch(rf"(?:[^/]+/)*([^/]+)/פרק\s+({NUMBER})/משנה\s+({NUMBER})", source)
        if location:
            if normalize_book(location[1]) != normalize_book(lesson.book):
                return "outside"
            ref = (number(location[2]), number(location[3]))
            return "exact" if lesson.begin <= ref <= lesson.end else "outside"
        match = re.fullmatch(rf"(.+?)\s+(?:פרק\s+)?({NUMBER})\s*[, :]\s*(?:משנה\s+)?({NUMBER})", source)
        if match and normalize_book(match[1]) == normalize_book(lesson.book):
            ref = (number(match[2]), number(match[3]))
            return "exact" if lesson.begin <= ref <= lesson.end else "outside"
        return "manual"
    if lesson.track == "chofetz":
        match = re.fullmatch(rf"(?:הלכות\s+)?(לשון הרע|רכילות)\s+כלל\s+({NUMBER})\s+סעיף\s+({NUMBER})", source)
        if match:
            ref = (number(match[2]), number(match[3]))
            return "exact" if match[1] == lesson.book and lesson.begin <= ref <= lesson.end else "outside"
        # Archive source fields describe question groups, not unique se'ifim.
        # plan_rows uses the separately reviewed row map for these files.
        return "manual"
    if lesson.track == "halacha":
        # A se'if may span several daily printed pages: both boundary se'ifim
        # require selection, even when the source names that se'if exactly.
        match = re.fullmatch(rf"סימן\s+({NUMBER})\s+סעיף\s+({NUMBER})", source)
        if match:
            ref = (number(match[1]), number(match[2]))
            if not lesson.begin <= ref <= lesson.end:
                return "outside"
            return "exact" if lesson.begin < ref < lesson.end else "manual"
        return "manual"
    # Accept the archive's three unambiguous page conventions: ב,א / ב. / ב ע״א.
    matches = re.findall(rf"(?<![א-ת\d])({NUMBER})\s*(?:,\s*([אב])(?=$|\s)|([.:])|ע[\"״']([אב])(?=$|\s))", source)
    refs = set()
    for n, side, punct, explicit in matches:
        try:
            refs.add((number(n), 1 if (side or explicit) == "א" or punct == "." else 2))
        except ValueError:
            return "manual"
    # A second side without a repeated page ("ע״א וע״ב") is not a single-side question.
    if len(set(re.findall(r"ע[\"״']([אב])", source))) > 1 or re.search(r"\s[-–]\s|\bעד\b", source):
        return "manual"
    if len(refs) == 1:
        ref = next(iter(refs))
        return "exact" if lesson.begin <= ref <= lesson.end else "outside"
    return "manual"


def normalize_book(text):
    text = re.sub(r"[\u0591-\u05c7]", "", text.replace("_", " ")).strip()
    return {"אוהלות": "אהלות", "נידה": "נדה", "עוקצין": "עוקצים", "טבול יום": "טבול יום"}.get(text, text)


def normalize_question_source(source):
    """Return the canonical question-source form without guessing missing refs."""
    source = plain(source).replace("\\", "/")
    source = re.sub(r"\bסי(?:מן)?[׳']\s*", "סימן ", source)
    source = re.sub(r"\bסע(?:יף)?[׳']\s*", "סעיף ", source)
    source = re.sub(r"\bס[\"״׳']?ק\b", "ס״ק", source)
    source = re.sub(r"\s*/\s*", "/", source)
    source = " ".join(source.split())
    # Only discard library hierarchy when it explicitly identifies this book.
    # Keep commentary names, compound references and named appendices intact.
    if "/" in source and "משנה ברורה" in source.split("/"):
        parts = source.split("/")
        start = next((i for i, part in enumerate(parts) if part.startswith("סימן ")), None)
        if start is not None:
            source = " ".join(parts[start:])
        else:
            # A missing siman cannot be recovered from a se'if alone.
            source = " ".join(parts[parts.index("משנה ברורה"):])
    source = re.sub(
        rf"(סימן\s+)({NUMBER})(?=\s|$)",
        lambda m: m[1] + re.sub(r"[׳'״\"]", "", m[2]), source,
    )
    # In siman 36, מ״ס is the named appendix "Mishnat Sofrim", not the
    # gematria 100. Keep that semantic label instead of inventing se'if 100.
    if re.fullmatch(r"סימן\s+לו\s+סעיף\s+מ[\"״]?ס", source):
        return "סימן לו משנת סופרים"
    # Otsaria-style paths carry useful hierarchy, but the source field used by
    # Anki and the daily-import UI has one stable, compact representation.
    path_match = re.search(
        rf"(?:^|/)סימן\s+({NUMBER})/סעיף\s+({NUMBER})(?:/ס״ק\s+({NUMBER}))?/?$",
        source,
    )
    simple_match = re.fullmatch(
        rf"סימן\s+({NUMBER})\s+סעיף\s+({NUMBER})(?:\s+ס״ק\s+({NUMBER}))?",
        source,
    )
    match = path_match or simple_match
    if not match:
        return source
    values = [re.sub(r"[׳'״\"]", "", value or "") for value in match.groups()]
    canonical = f"סימן {values[0]} סעיף {values[1]}"
    if values[2]:
        canonical += f" ס״ק {values[2]}"
    return canonical


def normalize_row_source(row):
    """Normalize a known note type while preserving its field count/order."""
    result = list(row)
    if not result:
        return result
    source_index = KNOWN_TYPES.get(result[0])
    if source_index is not None and len(result) > source_index:
        result[source_index] = normalize_question_source(result[source_index])
    return result


def csv_parts(text):
    """Keep Anki directives separate from CSV (quoted fields may span lines)."""
    lines = text.lstrip("\ufeff").splitlines(keepends=True)
    headers = []
    while lines and (lines[0].startswith("#") or not lines[0].strip()):
        headers.append(lines.pop(0))
    if "#separator:tab" not in "".join(headers) or "#notetype column:1" not in "".join(headers):
        raise ValueError("די מאגר טעקע איז נישט אינעם געשטיצטן TSV פארמאט מיט א סארט רשומה אינעם ערשטן זייל")
    return "".join(headers), list(csv.reader(io.StringIO("".join(lines)), delimiter="\t"))


def select_csv_rows(path, indices):
    """Rewrite only the temporary extracted copy, preserving note fields/IDs/tags."""
    path = Path(path)
    header, rows = csv_parts(path.read_text(encoding="utf-8-sig"))
    wanted = set(indices)
    if not wanted or any(i < 0 or i >= len(rows) for i in wanted):
        raise ValueError("די אויסוואל פון שאלות שטימט נישט מיט דער מקור טעקע")
    # The archive may have been updated while the preview was open.
    for index, expected in indices.items():
        if row_digest(rows[index]) != expected:
            raise ValueError("די מקור טעקע האט זיך געענדערט זינט מען האט זי געוויזן. ווייזט דעם הספק נאכאמאל איידער איר אימפארטירט.")
    with path.open("w", encoding="utf-8", newline="") as output:
        output.write(header)
        csv.writer(output, delimiter="\t", lineterminator="\n").writerows(
            normalize_row_source(row) for i, row in enumerate(rows) if i in wanted
        )


def row_digest(row):
    return sha256(json.dumps(row, ensure_ascii=False).encode("utf-8")).hexdigest()


def plan_rows(archive, files, lesson):
    """Read selected archive members without extracting or accessing Anki."""
    wanted = set(files)
    result = []
    with tarfile.open(archive, "r|xz") as bundle:
        for member in bundle:
            if member.name not in wanted or not member.isfile():
                continue
            wanted.remove(member.name)
            _, rows = csv_parts(bundle.extractfile(member).read().decode("utf-8-sig"))
            for index, row in enumerate(rows):
                if not row or not any(row):
                    continue
                source_index = KNOWN_TYPES.get(row[0])
                if source_index is None or len(row) <= source_index:
                    # One malformed/foreign row must not take down the whole
                    # daily-import board. It remains available in regular import.
                    continue
                source = normalize_question_source(row[source_index])
                digest = row_digest(row)
                if lesson.track == "halacha":
                    mapped = halacha_mapping()["rows"].get(digest)
                    if mapped is None:
                        status = "outside"
                    elif mapped.get("day") == lesson.day:
                        status = "exact"
                    elif lesson.day in mapped.get("candidate_days", []):
                        status = "manual"
                    else:
                        status = "outside"
                elif lesson.track == "chofetz":
                    mapped = chofetz_mapping()["rows"].get(digest)
                    status = (
                        "exact" if mapped is not None
                        and mapped["file"] == member.name and mapped["index"] == index
                        and mapped["book"] == lesson.book
                        and lesson.begin <= tuple(mapped["ref"]) <= lesson.end
                        else "outside"
                    )
                else:
                    status = classify_source(source, lesson)
                if status != "outside":
                    source_id = halacha_source_id(member.name) if lesson.track == "halacha" else None
                    result.append({"file": member.name, "index": index, "question": plain(row[1]),
                                   "source": plain(source), "status": status, "digest": digest,
                                   "source_name": HALACHA_SOURCES[source_id][0] if source_id else ""})
            if not wanted:
                break
    if wanted:
        raise ValueError("טעקעס פונעם אינדעקס פעלן אינעם ארכיוו: " + ", ".join(sorted(wanted)))
    order = {path: i for i, path in enumerate(files)}
    return sorted(result, key=lambda r: (order[r["file"]], r["index"]))
