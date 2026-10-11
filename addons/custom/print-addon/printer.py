import html
import pathlib
import re
import shutil
import zipfile
from collections.abc import Iterable
from datetime import datetime
from html.parser import HTMLParser
from typing import NamedTuple
from urllib.parse import unquote

from anki.cards import Card
from anki.notes import Note
from anki.utils import join_fields, tmpfile
from aqt.utils import openLink, showInfo, showWarning
from PyQt6.QtGui import QDesktopServices

from _shared_libs.haf_logging import get_logger

from .lib.pyluach.dates import GregorianDate
from .printUI import *

logger = get_logger("print_addon")

config = mw.addonManager.getConfig(__name__)
more_q_in_a_notetypes = ('06 שאלות ותשובות מרובות- לאחר הצגת התשובה מופיעה שאלה נוספת המקושרת לאותה שאלה (כרטיס אחד)', '07 כמו 06 רק שכל שאלה מוצגת גם בתור המשך לשאלות הקודמות וגם בתור כרטיס נפרד (עד 9 כרטיסים)', '07 כמו 06 רק שכל שאלה מוצגת גם בתור המשך לשאלות הקודמות וגם בתור כרטיס נפרד (עד 10 כרטיסים)', '15 - שאלות ותשובות מרובות', '17 - שאלות ותשובות מרובות- כל שלב מוצג גם בתור שאלה נפרדת', '06 עטליכע שאלות און תשובות - נאך דער תשובה קומט נאך א פארבינדענע שאלה (איין קארטל)', '07 ווי 06: יעדע שאלה אלס המשך און אויך אלס באזונדער קארטל (ביז 10 קארטלעך)')

files_to_copy = []




class FileInfo(NamedTuple):
    name: str
    path: str


def files_in_note(note: Note) -> Iterable[FileInfo]:
    """
    Returns FileInfo for every file referenced by the note.
    Skips missing files.
    """
    for file_ref in note.col.media.files_in_str(note.mid, join_fields(note.fields)):
        if os.path.exists(file_path := os.path.join(note.col.media.dir(), file_ref)):
            yield FileInfo(file_ref, file_path)


def copy_media_files(note: Note) -> None:
    for file in files_in_note(note):
        files_to_copy.append(file)


def files_in_html(note: Note, html_text: str) -> Iterable[FileInfo]:
    """
    #252 — מעדיע טעקעס וואס ווערן דערמאנט אין-HTML דעם באארבעטען (אויך פעסטע בילדער וואס קומען פונעם מוסטער
    אליין און נישט פונעם רשומה פעלד). א פעלנדיגער בילד אין דער ליסטע ברענגט א צעבראכענעם בילד ביים עקספארטירן Word.
    Skips missing files.
    """
    for file_ref in note.col.media.files_in_str(note.mid, html_text):
        if os.path.exists(file_path := os.path.join(note.col.media.dir(), file_ref)):
            yield FileInfo(file_ref, file_path)


def copy_media_files_in_html(note: Note, html_text: str) -> None:
    for file in files_in_html(note, html_text):
        files_to_copy.append(file)


def copy_file(src_path, dest_path):
    shutil.copy(src_path, dest_path)
    logger.info(f"File copied from {src_path} to {dest_path} successfully.")


# #252 — יצוא Word נבנה כקובץ docx עצמאי בלי COM ובלי התקנת Word.
def _unique_media_files(media_files: Iterable[FileInfo]) -> list[FileInfo]:
    seen: set[tuple[str, str]] = set()
    unique: list[FileInfo] = []
    for file in media_files:
        key = (file.name, file.path)
        if key not in seen:
            seen.add(key)
            unique.append(file)
    return unique


def _copy_media_files_to_folder(media_files: Iterable[FileInfo], media_dir: pathlib.Path) -> None:
    media_dir.mkdir(parents=True, exist_ok=True)
    for file in _unique_media_files(media_files):
        copy_file(file.path, str(media_dir / pathlib.Path(file.name).name))


def _image_size_px(path: str) -> tuple[int, int] | None:
    try:
        with open(path, "rb") as image_file:
            header = image_file.read(32)
            if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
                return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
            if header[:6] in (b"GIF87a", b"GIF89a") and len(header) >= 10:
                return int.from_bytes(header[6:8], "little"), int.from_bytes(header[8:10], "little")
            if header.startswith(b"\xff\xd8"):
                image_file.seek(2)
                while True:
                    marker_start = image_file.read(1)
                    if not marker_start:
                        return None
                    if marker_start != b"\xff":
                        continue
                    marker = image_file.read(1)
                    while marker == b"\xff":
                        marker = image_file.read(1)
                    if marker in (b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"):
                        image_file.read(3)
                        height = int.from_bytes(image_file.read(2), "big")
                        width = int.from_bytes(image_file.read(2), "big")
                        return width, height
                    segment_size_bytes = image_file.read(2)
                    if len(segment_size_bytes) != 2:
                        return None
                    segment_size = int.from_bytes(segment_size_bytes, "big")
                    image_file.seek(max(segment_size - 2, 0), os.SEEK_CUR)
    except Exception as e:
        logger.warning(f"Failed reading image size for Word export: {path}: {e}")
    return None


def _image_ext_and_content_type(path: str) -> tuple[str, str] | None:
    ext = pathlib.Path(path).suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    content_types = {
        "png": "image/png",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tif": "image/tiff",
        "tiff": "image/tiff",
    }
    content_type = content_types.get(ext)
    if not content_type:
        return None
    return ext, content_type
















def _resolve_docx_image_path(src: str, html_path: pathlib.Path, media_by_name: dict[str, str]) -> str | None:
    if src.startswith("data:"):
        return None
    cleaned_src = unquote(src.split("?", 1)[0].split("#", 1)[0])
    qurl = QUrl(cleaned_src)
    if qurl.isLocalFile():
        candidate = pathlib.Path(qurl.toLocalFile())
    else:
        candidate = pathlib.Path(cleaned_src)
        if not candidate.is_absolute():
            candidate = html_path.parent / candidate
    file_name = pathlib.Path(cleaned_src).name
    if file_name in media_by_name:
        return media_by_name[file_name]
    if candidate.exists():
        return str(candidate)
    return None




def _embed_images_as_base64(html_text: str, html_path: pathlib.Path, media_files: Iterable[FileInfo], *, remove_base_tag: bool = True) -> str:
    """#259 — לייגט אריין בילדער אלס-base64 data URI אינעם-HTML, כדי זיי זאלן זיין צוטריטלעך אין-altChunk פון Word."""
    import base64
    media_by_name = {pathlib.Path(file.name).name: file.path for file in _unique_media_files(media_files)}

    def replace_src(match: re.Match) -> str:
        prefix, quote, src = match.group(1), match.group(2), html.unescape(match.group(3))
        image_path = _resolve_docx_image_path(src, html_path, media_by_name)
        if not image_path:
            return match.group(0)
        ext_info = _image_ext_and_content_type(image_path)
        if not ext_info:
            return match.group(0)
        _ext, content_type = ext_info
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            return f'{prefix}{quote}data:{content_type};base64,{b64}{quote}'
        except Exception:
            return match.group(0)

    if remove_base_tag:
        html_text = re.sub(r"<base\b[^>]*>", "", html_text, flags=re.I)
    return re.sub(r"(\bsrc\s*=\s*)(['\"])([^'\"]+)(['\"])", lambda m: replace_src(m), html_text, flags=re.I)


def _write_docx_html_chunk(html_path: str, docx_path: str, media_files: Iterable[FileInfo]) -> None:
    html_file = pathlib.Path(html_path)
    html_text = html_file.read_text(encoding="utf8")
    # #259 — altChunk לא תומך בנתיבים יחסיים לתמונות; מטמיעים כ-base64 בתוך ה-HTML.
    html_text = _embed_images_as_base64(html_text, html_file, list(media_files))
    if "<meta charset=" not in html_text.lower():
        html_text = re.sub(r"<head(\s[^>]*)?>", '<head\\1><meta charset="utf-8">', html_text, count=1, flags=re.I)
    # #337: כיוון RTL מפורש לכל המסמך — בלעדיו Word נותן לטבלאות ולפסקאות במצב "עיצוב מלא"
    # כיוון LTR, מה שהופך את מראה הסוגריים בטקסט עברי. dir על תגית html + כלל CSS גורף.
    html_text = re.sub(r"<html(?![^>]*\bdir=)", '<html dir="rtl" lang="he"', html_text, count=1, flags=re.I)
    html_text = re.sub(
        r"<head(\s[^>]*)?>",
        '<head\\1><style>body, table, td, th, div, p { direction: rtl; }</style>',
        html_text, count=1, flags=re.I)

    pathlib.Path(docx_path).parent.mkdir(parents=True, exist_ok=True)
    document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body><w:altChunk r:id="rIdHtml"/><w:sectPr><w:bidi/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>'''

    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="html" ContentType="text/html"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')
        docx.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')
        docx.writestr("word/_rels/document.xml.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdHtml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/aFChunk" Target="afchunk.html"/>
</Relationships>''')
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/afchunk.html", html_text)


def _write_docx_from_html(html_path: str, docx_path: str, media_files: Iterable[FileInfo]) -> None:
    # #252 — יצוא Word במצב עיצוב מלא שומר את ה-HTML שהופק מאנקי בתוך docx כ-altChunk, במקום לתרגם רק קומץ מאפייני CSS ידנית.
    return _write_docx_html_chunk(html_path, docx_path, media_files)



def _open_exported_file(savepath: str, ptintorfile: str) -> None:
    # #258 — קבצי Word נפתחים באפליקציית ברירת המחדל של Windows ולא במציג הפנימי של Anki.
    if ptintorfile == "doc":
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(savepath)):
            showWarning("די טעקע איז אפגעזיכערט, אבער מען האט נישט געפונען א פראגראם צו עפענען א טעקע Word.")
        return
    # #189 — guides-framework עוטף openLink ומצפה למחרוזת; QUrl גרם לקריסה בהדפסה ל-HTML.
    openLink(QUrl.fromLocalFile(savepath).toString())


import os

from PyQt6.QtCore import QUrl


def create_filtered_deck(_filter_string):
    today_heb = GregorianDate.today().to_heb().hebrew_date_string()
    now = datetime.now().strftime('%H:%M:%S')
    f_deck_name = mw.col.decks.new_filtered("פראגעס געדרוקט אום: " + today_heb + " " + now)
    f_deck = mw.col.decks.current()
    f_deck['resched'] = True
    f_deck['delays'] = None
    f_deck['terms'] = [[_filter_string, 10000, 6]]
    mw.col.decks.save(f_deck)
    mw.col.sched.rebuild_filtered_deck(f_deck_name)
    mw.reset()


def create_tmp_file(file_type):
    if file_type != "file":
        return tmpfile(suffix=".html")
    return None


def templates_for_card(card: Card, cardside):
    template = card.template()
    q, a = None, None
    if cardside == "q":
        return q or template.get("qfmt")
    elif cardside == "a":
        return a or template.get("afmt")


def get_styled_cards(c, show_hint, state):
    # Fix 126: Type Answer card printing bug
    if c.note_type()["name"] in ("04 הקלד את התשובה (כרטיס אחד)", "04 שרייבט אריין די תשובה (איין קארטל)") and state in ("a", "qa"):
        return get_fields_txt_for_cards(c, "a")

    # Fix 125 + #360: כל סוגי הרשומה מרובות-השאלות (06/07/17) חייבים לעבור דרך שדות
    # הטקסט הגולמיים ולא דרך render_output — ל-06 יש card_back שמתחיל ב-{{FrontSide}},
    # כך שה-HTML המרונדר של answer_html מכיל את שאלה 1 (מהחזית) בשנית, מה שהופיע
    # כשאלה ראשונה כפולה בהדפסה/PDF/HTML וגם בייצוא לוורד (merge_multi_q עובר דרך
    # get_fields_txt_for_cards ולא כאן, אבל get_styled_cards עדיין נקרא במסלולים אחרים).
    if c.note_type()["name"] in more_q_in_a_notetypes:
        # #360 — מצב qa אינו ממופה לתבנית יחידה; force_merge אוסף במפורש את כל
        # שדות שאלה/תשובה. בלעדיו העקיפה של render_output הסירה את הכפילות אך
        # הייתה עלולה להחזיר רק את שדה המקור.
        return get_fields_txt_for_cards(c, state, force_merge=True)

    rendered = c.render_output(True, False)
    question_html = rendered.question_text or ""
    answer_html = rendered.answer_text or ""
    copy_media_files_in_html(c.note(), question_html + answer_html)
    c_str = ""
    if state == "q":
        c_str += mw.prepare_card_text_for_display(question_html)
    elif state == "a":
        answer_only = answer_html[len(question_html):] if question_html and answer_html.startswith(question_html) else answer_html
        c_str += mw.prepare_card_text_for_display(answer_only)
    elif state == "qa":
        c_str += mw.prepare_card_text_for_display(answer_html)
    # הצגת הרמזים והמקורות המוסתרים ומחיקת שם השדה
    if show_hint:
        pattern = re.compile(
            r'''<a\s+class=hint\s+href="#"\s+onclick="this\.style\.display=\'none\';\s*document\.getElementById\(\'(?:[^\']+|\\')*\'\)\.style\.display=\'block\';\s*return false;">.*?</a>''',
            re.DOTALL)
        c_str = pattern.sub('', c_str)
        c_str = c_str.replace('class=hint style="display: none"', "")

    if c.note_type()["name"] in more_q_in_a_notetypes:
        elements_to_replace = ['''
<button onclick=showall()>
    ווייז אלעס
</button>
<button onclick=hideall()>
    באהאלט אלעס
</button>

''',
'''
<button onclick=showall()>
    ווייז אלעס
</button>
<button onclick=hideall()>
    באהאלט אלעס
</button>
</tbody>
''',"hidden>","    hideall()"]

        for num in range(0, 11):
            elements_to_replace.append(f'''<button id="bq{num}" onclick=show("q{num}")>
    ווייז די פראגע {num}
</button>''')
            elements_to_replace.append(f'''<<button id="ba{num}" onclick=show("a{num}")>
    ווייז די ענטפער {num}
</button>''')
            elements_to_replace.append(f'''
<button id="ba{num}" onclick=show("a{num}")>
    ווייז די ענטפער {num}
</button>''')
        for element in elements_to_replace:
            c_str = c_str.replace(element, "")

    return c_str



def _field_label(label: str) -> str:
    # Field names are data contracts; only their printed headings are localized.
    first, separator, rest = str(label).partition(" ")
    if first in ("שאלה", "תשובה") and separator and rest.isdigit():
        first = "פראגע" if first == "שאלה" else "ענטפער"
        return first + separator + rest
    return {
        "שאלה": "פראגע", "תשובה": "ענטפער", "כותרת": "קעפל",
        "מקור": "מקור", "רמז": "רמז", "מיקום": "פלאץ",
        "מסכת ודף": "מסכתא און בלאט",
    }.get(str(label), str(label))

def get_fields_txt_for_cards(c, state, force_merge=False, styled=False):
    c_str = ""
    # Fix 125 & 124: Logic for split types
    is_split_type = ("07" in c.note_type()["name"] or "17" in c.note_type()["name"])
    # #336: גם סוג רשומה 06 (כל השאלות בכרטיס אחד) נכלל באיחוד השדות בעת force_merge,
    # כדי שייצוא לוורד יציג את כל השאלות ולא רק את המקור.
    is_multi_q = c.note_type()["name"] in more_q_in_a_notetypes

    # #336 סבב 2: במצב עיצוב מלא כל שאלה/תשובה נעטפת ב-div.colors — אותו class מה-CSS של
    # סוג הרשומה (שכבר נכתב לקובץ ב-_write_note_type_css) — כדי לשחזר את מראה התבנית בוורד.
    def _wrap(label: str, val: str) -> str:
        row = "<b>" + _field_label(label) + "</b>: " + val
        if styled:
            return ('<div class="colors" style="border-radius: 5px; padding: 6px 10px;'
                    ' margin-bottom: 4px;">' + row + "</div>")
        return row + "<br>"

    # --- תיקון לבעיה 124: איחוד כל השאלות ברשומה ---
    if force_merge and (is_split_type or is_multi_q):
        # הדפסת שדות מטא (כותרת, מקור וכו') פעם אחת בהתחלה
        for fld in ["כותרת", "מקור", "רמז", "מיקום", "מסכת ודף"]:
            if fld in c.note() and c.note()[fld]:
                c_str += _wrap(str(fld), str(c.note()[fld]))

        if not styled:
            c_str += "<br>"  # רווח מפריד בין כותרות לתוכן

        # לולאה על כל השאלות והתשובות האפשריות (עד 21 כרטיסים אפשריים)
        for i in range(1, 22):
            q_key = f"שאלה {i}"
            a_key = f"תשובה {i}"

            # אם יש תוכן בשאלה
            if q_key in c.note() and c.note()[q_key] and state in ("q", "qa"):
                c_str += _wrap(q_key, str(c.note()[q_key]))

            # אם יש תוכן בתשובה והמצב דורש תשובה
            if a_key in c.note() and c.note()[a_key] and state in ("a", "qa"):
                c_str += _wrap(a_key, str(c.note()[a_key]))

        if not styled:
            c_str += "<br>"
        return c_str
    # -----------------------------------------------

    current_idx = c.ord + 1 if is_split_type else -1
    target_q_fld = f"שאלה {current_idx}"
    target_a_fld = f"תשובה {current_idx}"

    # Fix 127: Force Source inclusion
    force_source = c.note_type()["name"] in more_q_in_a_notetypes

    for fld, val in c.note().items():
        if val == "":
            continue

        if is_split_type:
            # Logic for split types (Single card view): specific Q/A + Meta fields only
            is_meta = fld in ["מקור", "רמז", "מיקום", "מסכת ודף", "כותרת"]
            is_target_q = (fld == target_q_fld)
            is_target_a = (fld == target_a_fld)

            if state == "q":
                if is_meta or is_target_q:
                    c_str += "<b>" + _field_label(str(fld)) + "</b>" + ": " + str(val) + "<br>"
            elif state == "a":
                if is_target_a:
                    c_str += " " + "<b>" + _field_label(str(fld)) + "</b>" + ": " + str(val)
            elif state == "qa" and (is_meta or is_target_q or is_target_a):
                c_str += "<b>" + _field_label(str(fld)) + "</b>" + ": " + str(val) + "<br>"
        else:
            # Standard logic
            c_t = str(templates_for_card(c, state))
            if fld in c_t or (force_source and fld == "מקור"):
                if state in ("q", "qa"):
                    c_str += "<b>" + _field_label(str(fld)) + "</b>" + ": " + str(val) + "<br>"
                elif state == "a":
                    c_str += " " + "<b>" + _field_label(str(fld)) + "</b>" + ": " + str(val)

    if c.note_type()["name"] in more_q_in_a_notetypes:
        c_str += "<br>"
    return c_str


def _write_note_type_css(buf, note_type: dict, written_note_type_css: set) -> None:
    note_type_id = note_type.get("id") or note_type.get("name")
    if note_type_id in written_note_type_css:
        return
    css = note_type.get("css") or ""
    if css:
        buf.write(f'\n<style data-anki-print-notetype="{html.escape(str(note_type_id), quote=True)}">\n{css}\n</style>\n')
    written_note_type_css.add(note_type_id)


def for_all_cards(ids, buf, numer, show_hint, add_deck, styled, state, written_note_type_css=None,
                  merge_multi_q=False):
    if written_note_type_css is None:
        written_note_type_css = set()
    processed_nids = set()
    num = 0
    for j, cid in enumerate(ids):
        c = mw.col.get_card(cid)
        deck = mw.col.decks.name(c.did)
        note = c.note()

        is_split_type = note and ("07" in note.note_type()["name"] or "17" in note.note_type()["name"])
        # #336 + #338: בייצוא לוורד (merge_multi_q) גם סוג רשומה 06 עובר למסלול איחוד השדות —
        # ה-HTML המרונדר של התבנית (טבלאות + כפתורי הצג/הסתר) לא מוצג תקין ב-Word ומשאיר
        # שורות ריקות עבור שדות שלא מולאו. איחוד השדות מדלג אוטומטית על שדות ריקים.
        if merge_multi_q and note and note.note_type()["name"] in more_q_in_a_notetypes:
            is_split_type = True

        if is_split_type:
            if note.id in processed_nids:
                continue
            processed_nids.add(note.id)

        num += 1
        if styled and note:
            _write_note_type_css(buf, c.note_type(), written_note_type_css)

        if numer and styled:
            buf.write(str(num))
        elif numer:
            buf.write("<br>" + str(num) + ": ")
        else:
            buf.write("<br>")

        if is_split_type:
            # #336 סבב 2: העברת styled כדי שהאיחוד ישמר את עיצוב סוג הרשומה (div.colors)
            c_str = get_fields_txt_for_cards(c, state, force_merge=True, styled=styled)
        elif styled and state == "qa":
            c_str = get_styled_cards(c, show_hint, "qa")
        elif styled:
            c_str = get_styled_cards(c, show_hint, state)
        elif not styled and state == "qa":
            c_str = ""
            if c.note_type()["name"] not in more_q_in_a_notetypes:
                c_str += get_fields_txt_for_cards(c, "q")
                c_str += get_fields_txt_for_cards(c, "a")
            else:
                c_str = get_fields_txt_for_cards(c, state)
        else:
            c_str = get_fields_txt_for_cards(c, state)

        if c_str == "":
            buf.write("(ליידיג)")
        elif styled:
            buf.write('<div class="card" dir="rtl">')
            buf.write(c_str)
            buf.write("</div>")
        else:
            buf.write(c_str)

        if add_deck:
            buf.write(f"""<br><b>פעקל:</b>{deck}<br>""")

        # media
        if note:
            copy_media_files(note)

        if state in ("a", "qa") and j % 50 == 0:
            mw.progress.update(f"דרוקט {j + 1} קארטלעך.")


class _HtmlToXamlParser(HTMLParser):
    """טוישט HTML צו פאראגראפן XAML וואס פאסן צו קל לזכור."""

    _NS = "http://schemas.microsoft.com/winfx/2006/xaml/presentation"

    def __init__(self, media_folder_name: str = "") -> None:
        super().__init__(convert_charrefs=False)
        self._media = media_folder_name
        self._inline: list[str] = []
        self._paras: list[str] = []
        self._run_depth = 0

    # --- helpers ---
    def _open_run(self, attrs_str: str = "") -> None:
        self._inline.append(f'<Run {attrs_str}>' if attrs_str else "<Run>")
        self._run_depth += 1

    def _close_run(self) -> None:
        if self._run_depth > 0:
            self._inline.append("</Run>")
            self._run_depth -= 1

    def _flush_para(self) -> None:
        while self._run_depth > 0:
            self._close_run()
        content = "".join(self._inline).strip()
        ns = self._NS
        if content:
            self._paras.append(f'<Paragraph xmlns="{ns}">{content}</Paragraph>')
        else:
            self._paras.append(f'<Paragraph xmlns="{ns}" xml:space="preserve"/>')
        self._inline = []

    # --- HTMLParser callbacks ---
    def handle_starttag(self, tag: str, attrs: list) -> None:
        d = dict(attrs)
        t = tag.lower()
        if t in ("b", "strong"):
            self._open_run('FontWeight="Bold"')
        elif t in ("i", "em"):
            self._open_run('FontStyle="Italic"')
        elif t == "u":
            self._inline.append(
                "<Run>"
                "<Run.TextDecorations>"
                '<TextDecoration Location="Underline"/>'
                "</Run.TextDecorations>"
            )
            self._run_depth += 1
        elif t == "span":
            style = d.get("style", "")
            run_attrs: list[str] = []
            if re.search(r"font-weight\s*:\s*bold", style, re.I):
                run_attrs.append('FontWeight="Bold"')
            if re.search(r"font-style\s*:\s*italic", style, re.I):
                run_attrs.append('FontStyle="Italic"')
            cm = re.search(r"(?:^|;)\s*color\s*:\s*([^;]+)", style)
            if cm:
                run_attrs.append(f'Foreground="{html.escape(cm.group(1).strip())}"')
            bg = re.search(r"background-color\s*:\s*([^;]+)", style)
            if bg:
                run_attrs.append(f'Background="{html.escape(bg.group(1).strip())}"')
            fz = re.search(r"font-size\s*:\s*([\d.]+)\s*pt", style)
            if fz:
                run_attrs.append(f'FontSize="{fz.group(1)}"')
            self._open_run(" ".join(run_attrs))
        elif t == "br" or t in ("div", "p", "li"):
            self._flush_para()
        elif t == "img":
            src = d.get("src", "")
            fname = pathlib.Path(src).name
            ref = f"{self._media}/{fname}" if self._media else fname
            ns = self._NS
            self._flush_para()
            self._paras.append(
                f'<BlockUIContainer xmlns="{ns}">'
                f'<Image Source="{html.escape(ref)}"/>'
                f"</BlockUIContainer>"
            )

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in ("b", "strong", "i", "em", "u", "span"):
            self._close_run()
        elif t in ("div", "p", "li"):
            self._flush_para()

    def handle_data(self, data: str) -> None:
        if data:
            self._inline.append(html.escape(data))

    def handle_entityref(self, name: str) -> None:
        import html.entities
        cp = html.entities.name2codepoint.get(name)
        if cp:
            self._inline.append(html.escape(chr(cp)))

    def handle_charref(self, name: str) -> None:
        cp = int(name[1:], 16) if name.startswith("x") else int(name)
        self._inline.append(html.escape(chr(cp)))

    def finalize(self) -> list[str]:
        while self._run_depth > 0:
            self._close_run()
        remaining = "".join(self._inline).strip()
        if remaining:
            ns = self._NS
            self._paras.append(f'<Paragraph xmlns="{ns}">{remaining}</Paragraph>')
        self._inline = []
        return self._paras


def convert_html_to_kalizcor_xaml(html_content: str, media_folder_name: str = "") -> str:
    """טוישט דעם אינהאלט HTML צו א טעקסט שטריקל XAML וואס פאסט צו קל לזכור (Section פון WPF)."""
    NS = "http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    parser = _HtmlToXamlParser(media_folder_name)
    parser.feed(html_content)
    paras = parser.finalize()
    inner = "\n".join(paras)
    return f'<Section xmlns="{NS}" xml:space="preserve">\n{inner}\n</Section>'


def clean_content_for_xml(text):
    # Fix 163: Convert HTML to XAML friendly tags
    text = text.replace("<br>", "&#xD;\n").replace("<br/>", "&#xD;\n").replace("<br />", "&#xD;\n")
    text = text.replace("<div>", "&#xD;\n").replace("</div>", "")
    text = text.replace("&nbsp;", " ")

    # Map basic HTML formatting to XAML tags
    text = re.sub(r'<b>(.*?)</b>', r'<Bold>\1</Bold>', text, flags=re.IGNORECASE)
    text = re.sub(r'<strong>(.*?)</strong>', r'<Bold>\1</Bold>', text, flags=re.IGNORECASE)
    text = re.sub(r'<i>(.*?)</i>', r'<Italic>\1</Italic>', text, flags=re.IGNORECASE)
    text = re.sub(r'<em>(.*?)</em>', r'<Italic>\1</Italic>', text, flags=re.IGNORECASE)
    text = re.sub(r'<u>(.*?)</u>', r'<Underline>\1</Underline>', text, flags=re.IGNORECASE)

    # Strip other tags
    text = re.sub(r'<(?!\/?(Bold|Italic|Underline))[^>]*>', '', text)
    text = re.sub(r'&(?!quot;|amp;|apos;|gt;|lt;|#xD;)\w+;', '', text)
    return text


def onPrint(self, savepath, did, formating, ptintorfile, sortqbefore, numer, show_hint, add_deck, deckname, order,
            ascending, filtered_deck):
    ids = []
    for card_id in mw.col.find_cards(did, order=mw.col.get_browser_column(order), reverse=ascending):
        ids.append(card_id)
    if filtered_deck:
        _filter_string = ""
        for cid in ids:
            _filter_string += f"cid:{str(cid)} OR "
        create_filtered_deck(_filter_string[:-4])

    tsavepath = create_tmp_file(ptintorfile) or savepath

    if ptintorfile == "xml":
        # formating = False # Removed to allow XAML formatting
        sortqbefore = False
        buf = open(savepath, "w", encoding="utf8", newline='\n')  # noqa: SIM115
        buf.write(
            '''<ArrayOfשאלה_ותשובה xmlns="http://schemas.datacontract.org/2004/07/%D7%9C%D7%90_%D7%90%D7%A9%D7%9B%D7%97" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">\n
''')
    else:
        buf = open(tsavepath, "w", encoding="utf8")  # noqa: SIM115
        buf.write(
            "<html><head>" + '<meta charset="utf-8">' + mw.baseHTML() +
            '</head><body dir="rtl">'
        )

        buf.write(
            """<style>
    img { max-width: 100%; }
    .playImage { display: none; }
    /* #337: ריכטונג RTL קלאר אויך פאר טאבעלעס און פאראגראפן — די זעלבע ווארד פאררעכטונג גייט אויך אן אויף
       PDF/HTML/דרוקן, כדי קלאמערן אין העברעאישן טעקסט זאלן זיך נישט איבערקערן אינעם מצב "פולער אויסשטעל". */
    body, table, td, th, div, p { direction: rtl; }
    </style>"""
        )

    mw.progress.start(immediate=True)
    written_note_type_css = set()
    # #336 + #338: סוגי רשומה מרובי-שאלות מיוצאים באיחוד שדות (ראו for_all_cards).
    # #336 סבב 3: לא רק בוורד — גם ב-PDF, ב-HTML ובהדפסה התבנית המרונדרת של 06 מסתירה את
    # השאלות הנוספות (סקריפט hideall של התבנית מריץ הסתרה גם שם) והוצג רק המקור.
    # מאחדים שדות בכל סוגי הייצוא מלבד XML, שיש לו מסלול משלו.
    merge_multi_q = ptintorfile != "xml"
    if formating and ptintorfile != "xml":
        if sortqbefore:
            for_all_cards(ids, buf, numer, show_hint, add_deck, True, "qa", written_note_type_css, merge_multi_q)
        else:
            for_all_cards(ids, buf, numer, show_hint, add_deck, True, "q", written_note_type_css, merge_multi_q)
            for_all_cards(ids, buf, numer, show_hint, add_deck, True, "a", written_note_type_css, merge_multi_q)
        buf.write("</body></html>")

    elif ptintorfile != "xml":
        if sortqbefore:
            for_all_cards(ids, buf, numer, show_hint, add_deck, False, "qa", merge_multi_q=merge_multi_q)
        else:
            for_all_cards(ids, buf, numer, show_hint, add_deck, False, "q", merge_multi_q=merge_multi_q)
            for_all_cards(ids, buf, numer, show_hint, add_deck, False, "a", merge_multi_q=merge_multi_q)
            buf.write("<br>")
        buf.write("</body></html>")
    else:
        #     print to xml
        num = 0
        for j, cid in enumerate(ids):
            c = mw.col.get_card(cid)
            num += 1

            # Fix 163: Copy media for XML
            note = c.note()
            if note:
                copy_media_files(note)

            buf.write('''<שאלה_ותשובה>''')
            buf.write('''<הערות i:nil="true"/>\n''')

            deckname = deckname.replace("::", "/")
            deckname = clean_content_for_xml(deckname)

            buf.write(f'''<נתיב>{"פראגעס פון אנקי/" + deckname}</נתיב>\n''')

            buf.write('''<רמז i:nil="true"/>\n''')

            qfields = ""
            afields = ""

            # Fix 125: Handle filtering for 07/17 in XML export loop
            is_split_type = ("07" in c.note_type()["name"] or "17" in c.note_type()["name"])
            current_idx = c.ord + 1 if is_split_type else -1
            target_q_fld = f"שאלה {current_idx}"
            target_a_fld = f"תשובה {current_idx}"

            for fld, val in c.note().items():
                if val == "":
                    continue

                should_add_q = False
                should_add_a = False

                if is_split_type:
                    if fld in ["מקור", "רמז", "מיקום", "מסכת ודף", "כותרת"] or fld == target_q_fld:
                        should_add_q = True
                    if fld == target_a_fld:
                        should_add_a = True
                else:
                    q = str(templates_for_card(c, "q"))
                    a = str(templates_for_card(c, "a"))
                    if fld in q:
                        should_add_q = True
                    if fld in a:
                        should_add_a = True

                if should_add_q:
                    qfields += str(val) + "<br>"
                if should_add_a:
                    afields += str(val) + "<br>"

            # Save raw HTML before cleaning (needed for XAML conversion)
            q_raw = qfields
            a_raw = afields

            if qfields != "":
                buf.write('<שאלה_כמחרוזת>\n')
                if numer:
                    buf.write(str(num) + ": ")
                qfields = clean_content_for_xml(qfields)
                buf.write(qfields)
                buf.write('</שאלה_כמחרוזת>\n')
            else:
                buf.write('''\n<שאלה_כמחרוזת i:nil="true"/>''')

            if afields != "":
                buf.write('<תשובה_כמחרוזת>')
                afields = clean_content_for_xml(afields)
                buf.write(afields)
                buf.write('</תשובה_כמחרוזת>\n')
            else:
                buf.write('''\n<תשובה_כמחרוזת i:nil="true"/>''')

            # Fix 51: Write XAML fields when formatting is enabled
            if formating:
                media_folder_name = pathlib.Path(savepath).name + "_קבצים"
                if q_raw:
                    xaml_q = convert_html_to_kalizcor_xaml(q_raw, media_folder_name)
                    buf.write(f'<זאמל_שאלה>{html.escape(xaml_q, quote=False)}</זאמל_שאלה>\n')
                else:
                    buf.write('<זאמל_שאלה i:nil="true"/>\n')
                if a_raw:
                    xaml_a = convert_html_to_kalizcor_xaml(a_raw, media_folder_name)
                    buf.write(f'<זאמל_תשובה>{html.escape(xaml_a, quote=False)}</זאמל_תשובה>\n')
                else:
                    buf.write('<זאמל_תשובה i:nil="true"/>\n')

            buf.write('''</שאלה_ותשובה>\n''')

            if j % 50 == 0:
                mw.progress.update(f"דרוקט {j + 1} קארטלעך.")

        buf.write('''\n</ArrayOfשאלה_ותשובה>''')

    buf.close()
    global files_to_copy
    media_files = _unique_media_files(files_to_copy)
    files_to_copy = []

    # #325 — הטמעת תמונות כ-base64 בייצוא HTML/PDF/הדפסה לקובץ עצמאי (כמו Word).
    # PDF/printonly שומרים את ה-<base> tag כי QWebEngineView צריך אותו לטעינת משאבי אנקי.
    if media_files and ptintorfile in ("file", "pdf", "printonly"):
        html_path = pathlib.Path(tsavepath)
        html_text = html_path.read_text(encoding="utf8")
        html_text = _embed_images_as_base64(html_text, html_path, media_files, remove_base_tag=(ptintorfile == "file"))
        html_path.write_text(html_text, encoding="utf8")
    elif media_files and ptintorfile == "xml":
        showInfo("די טעקעס וואס באלאנגען צו די עקספארטירטע פראגעס זענען קאפירט געווארן אין א פאלדער מיטן זעלבן נאמען ווי די געשאפענע טעקע. מען דארף זיי אליין צושטעלן אינעם קל לזכור פראגראם.")
        xml_base = pathlib.Path(savepath).with_suffix("")
        media_dir = xml_base.parent / (xml_base.name + "_קבצים")
        _copy_media_files_to_folder(media_files, media_dir)

    if ptintorfile == "doc":
        try:
            mw.progress.finish()
            savepath = savepath.replace(".html", ".docx")
            _write_docx_from_html(tsavepath, savepath, media_files)
        except Exception as exc:
            mw.progress.finish()
            from _shared_libs.haf_notifications import show_failure
            show_failure("שאפן א טעקע Word איז נישט פארענדיגט געווארן. קלייבט אויס אן אנדערן אפזיכער פאלדער און פרובירט נאכאמאל; אויב דער פראבלעם קומט צוריק, שיקט א באריכט דורכן הילף מעניו.", exc)

    elif ptintorfile == "pdf":
        mw.progress.finish()
        savepath = savepath.replace(".html", ".pdf")
        DlgWebPrinter(mw, tsavepath, savepath, "pdf")

    elif ptintorfile == "printonly":
        mw.progress.finish()
        DlgWebPrinter(mw, tsavepath, savepath, "printonly")

    else:
        mw.progress.finish()

    if ptintorfile not in ("printonly", "pdf"):
        _open_exported_file(savepath, ptintorfile)
