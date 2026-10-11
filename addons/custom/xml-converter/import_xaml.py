import html
import contextlib
import traceback
import xml.etree.ElementTree as ET

from aqt import mw
from aqt.utils import showInfo, showWarning, tooltip
from _shared_libs.haf_notifications import show_failure

from .xaml_to_html_converter import convert_kalizcor_xaml_to_html

open_importdialog = 0


# #154 — חיפוש לפי שם מקומי של תג מאפשר לייבא גם כשמרחב השמות של קלזכור משתנה.
def _find_child_text(parent, local_name: str) -> str:
    for elem in parent.iter():
        if elem.tag.split("}", 1)[-1] == local_name:
            return elem.text or ""
    return ""


def _has_child(parent, local_name: str) -> bool:
    for elem in parent.iter():
        if elem.tag.split("}", 1)[-1] == local_name:
            return True
    return False


def import_xaml(xml, deck_dest, model, import_style):
    global open_importdialog
    import_ = False
    fields = 0
    warning = 0
    error_text = None
    mw.progress.start(immediate=True)
    try:
        notetype = mw.col.models.get(int(model))
        if notetype is None:
            raise ValueError(f"דער סארט קארטל איז נישט געפונען געווארן: {model}")
        for x in xml:
            tree = ET.parse(str(x))
            root = tree.getroot()
            for child in root:
                # #154 — קובץ קלזכור תקין יכול להכיל שאלה כמחרוזת או XAML; לא מסמנים אותו כשגוי בגלל קיום השדה.
                has_plain = _has_child(child, "שאלה_כמחרוזת") and _has_child(child, "תשובה_כמחרוזת")
                xaml_q = _find_child_text(child, "זאמל_שאלה")
                xaml_a = _find_child_text(child, "זאמל_תשובה")
                has_xaml = bool(xaml_q.strip() or xaml_a.strip())
                if not has_plain and not has_xaml:
                    showWarning(f"די טעקע {xml} איז נישט איבערגעטוישט געווארן.\nאין דעם פענסטער קען מען איבערבייטן טעקעס XML וואס זענען עקספארטירט נאר פונעם קלזכור פראגראם.\nצו אימפארטירן טעקסט, נוצט די געווענליכע אימפארט אפציע.")
                    continue

                style = bool((import_style and has_xaml) or (has_xaml and not has_plain))
                if style:
                    q = convert_kalizcor_xaml_to_html(xaml_q)
                    a = convert_kalizcor_xaml_to_html(xaml_a)
                else:
                    q = html.escape(_find_child_text(child, "שאלה_כמחרוזת"), quote=False).strip().replace("\n", "<br>")
                    a = html.escape(_find_child_text(child, "תשובה_כמחרוזת"), quote=False).strip().replace("\n", "<br>")

                s = html.escape(_find_child_text(child, "נתיב"), quote=False).strip().replace("\n", "<br>")
                h = html.escape(_find_child_text(child, "רמז"), quote=False).strip().replace("\n", "<br>")
                n = html.escape(_find_child_text(child, "הערות"), quote=False).strip().replace("\n", "<br>")

                duplicated_note = mw.col.new_note(notetype)
                duplicated_note.tags = ""
                new_note_len = len(duplicated_note.fields)
                values = [q, a, s, h, n]
                import_ = True
                fields = min(new_note_len, len(values))
                if new_note_len < 2:
                    if warning == 0:
                        showWarning("מען דארף אויסקלייבן א סארט קארטל מיט כאטש צוויי פעלדער.")
                    warning = 1
                    import_ = False
                    continue
                # #155 — לא פותחים מחדש את חלון הייבוא מתוך שגיאת סוג כרטיס; מציגים אזהרה וממשיכים בבטחה.
                field_values = values[:new_note_len]
                if new_note_len > len(field_values):
                    field_values.extend([""] * (new_note_len - len(field_values)))
                duplicated_note.fields = field_values
                mw.col.add_note(note=duplicated_note, deck_id=int(deck_dest))
    except Exception:
        error_text = traceback.format_exc()
    finally:
        with contextlib.suppress(Exception):
            mw.progress.finish()

    if error_text:
        show_failure("דער אימפארט פון קלזכור איז נישט פארענדיגט. קוקט צי די טעקע איז עקספארטירט געווארן פון קלזכור און דער פאסיגער סארט קארטל איז אויסגעקליבן. טייל רשומות קענען שוין זיין אימפארטירט; קוקט דעם פעקל פארן ווידער פרובירן.", error_text)
        return

    mw.reset()
    if fields == 3:
        showInfo("ווייל מען האט אויסגעקליבן א סארט קארטל מיט בלויז דריי פעלדער, זענען די פעלדער 'רמז', 'הערות'.")
    elif fields == 2:
        showInfo("ווייל מען האט אויסגעקליבן א סארט קארטל מיט בלויז צוויי פעלדער, זענען די פעלדער 'מקור', 'רמז', 'הערות'.")
    if import_:
        tooltip("דאס איבערבייטן איז מיט הצלחה פארענדיגט")
    # except:
    #     showWarning("שגיאה: קובץ XML לא תקין.")

