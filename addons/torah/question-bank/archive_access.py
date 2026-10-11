"""
#346 — גישה לארכיון מאגר השאלות ללא תלות בספריות חיצוניות.

עד כה המאגר נשמר כ-`מאגר השאלות.7z` ונקרא עם `py7zr`, שדרשה 48 בינאריים
מקומפלים (`.pyd` של `cp313-win_amd64`) בתיקיית `vendor/`. הבינאריים האלה
חסמו את התוסף לחלוטין במק ובלינוקס — הייבוא נכשל ולכן התוסף כולו לא נטען.

המאגר הומר ל-`מאגר השאלות.tar.xz`, שנקרא עם `tarfile` + `lzma` שבספרייה
הסטנדרטית של פייתון. שני המודולים מגיעים עם אנקי בכל פלטפורמה, ולכן אין
יותר צורך ב-vendor/ כלל.

אלגוריתם הדחיסה (LZMA) זהה לזה של 7z, ודחיסת tar היא "סוליד" — כלומר כל
הקבצים נדחסים כזרם אחד — בדיוק כמו הארכיון הקודם. לכן גם גודל הקובץ וגם
זמן החילוץ נשארים דומים: גם py7zr נאלצה לפרוס את כל הזרם כדי לשלוף קבצים
בודדים מארכיון סוליד.
"""
from __future__ import annotations

import os
import tarfile

ARCHIVE_NAME = "מאגר השאלות.tar.xz"

_ADDON_PATH = os.path.dirname(os.path.realpath(__file__))


def archive_path() -> str:
    """הנתיב המלא לארכיון המאגר."""
    return os.path.join(_ADDON_PATH, ARCHIVE_NAME)


def _normalize(name: str) -> str:
    """שמות בתוך הארכיון תמיד עם קו נטוי קדימה, גם כשהקורא שלח נתיב ווינדוס."""
    return name.replace("\\", "/")


def extract_targets(targets: list[str], path: str) -> None:
    """
    מחלץ אך ורק את הערכים המבוקשים אל תוך `path`, תוך שמירת מבנה התיקיות
    שבתוך הארכיון — בדיוק כמו `py7zr.SevenZipFile.extract(targets=..., path=...)`
    שהיה כאן קודם.

    ערך שאינו קיים בארכיון מדולג בשקט, כפי שהתנהגה py7zr.
    """
    wanted = {_normalize(t) for t in targets}
    if not wanted:
        return

    os.makedirs(path, exist_ok=True)
    # "r|xz" הוא מצב זרימה — מעבר סדרתי יחיד על הארכיון. הצורה הרגילה "r:xz"
    # מחייבת קריאה אחת לבניית רשימת הערכים ועוד אחת לחילוץ, כלומר פריסה כפולה
    # של 121MB. במדידה כאן זה היה ההבדל בין ~10 שניות ל-~5.
    remaining = set(wanted)
    with tarfile.open(archive_path(), "r|xz") as tar:
        for member in tar:
            name = _normalize(member.name)
            if name not in remaining:
                continue
            # filter="data" חוסם נתיבים מוחלטים ויציאה מחוץ ליעד (CVE-2007-4559).
            # ברירת המחדל משתנה ל-"data" בפייתון 3.14; ציון מפורש שומר על
            # התנהגות זהה בכל הגרסאות שאנקי נתמכת בהן.
            tar.extract(member, path=path, filter="data")
            remaining.discard(name)
            if not remaining:
                break  # נמצאו כל היעדים — אין טעם להמשיך לפרוס את שאר הארכיון


def list_names(suffix: str | None = None) -> list[str]:
    """
    שמות כל הערכים בארכיון, לסינון אופציונלי לפי סיומת.
    משמש את כלי הפיתוח `create_json_tree.py`.
    """
    with tarfile.open(archive_path(), "r|xz") as tar:
        names = [_normalize(m.name) for m in tar if m.isfile()]
    if suffix:
        names = [n for n in names if n.lower().endswith(suffix.lower())]
    return names
