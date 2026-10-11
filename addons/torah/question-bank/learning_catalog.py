"""Verified calendar choices and the question-bank support available for each."""
from functools import lru_cache
import json
from pathlib import Path


# key: (title, group, Hebcal option, event category, subcategory, bank category, note)
DIRSHU_TRACKS = {
    "dirshu_kolel": "דף הכולל — דרשו",
    "dirshu_chabura": "חבורת ש״ס — דרשו",
}

# Kept for calendar/mapping development, excluded from settings and automatic imports.
PENDING_TRACKS = {
    "dirshu_kolel": ("דף הכולל — דרשו", "א תשפ״ז קאלענדאר איז פארהאן; די צוטיילונג פון שאלות צו די הספקים איז נאך נישט פארענדיגט."),
    "dirshu_chabura": ("חבורת ש״ס — דרשו", "א תשפ״ז קאלענדאר איז פארהאן; די צוטיילונג פון שאלות צו די הספקים איז נאך נישט פארענדיגט."),
}
# ממתינים לחומר/מיפוי מתאים; אינם מסלולים פעילים ואינם מופיעים בממשק:
# dirshu_kinyan_yerushalmi — קנין ירושלמי: לאמת מהדורה ומספור מול השאלות.
# dirshu_kinyan_mishnayot — קנין משניות: יש טווחי מבחנים; אין להסיק מהם חלוקה יומית.
# dirshu_kinyan_chochma — קנין חכמה: יסוד ושורש העבודה ואבות עם רבנו יונה;
# נדרשות שאלות מתאימות וחלוקה מאומתת, שאינה זהה למשנה יומית.
# dirshu_mussar — שמירת הלשון ואהבת חסד: נדרש מיפוי למילות הפתיחה בלוח.
# קנין תורה הוא הדף היומי הקיים, ולכן לא נוצרת עבורו אפשרות כפולה.

EXTRA_TRACKS = {
    # המסלולים שבהערות בהמשך מושבתים ואינם מופיעים כלל בממשק או בהצעות.
    # הם נשמרים כאן בהמתנה להגעת שאלות מתאימות למאגר ולמיפוין להספק היומי.
    # רק לאחר הוספת החומר, אימות המיפוי ורענון הלוח ניתן להסיר את סימני ההערה.
    "mishna": ("משנה יומית — שתי משניות", "משנה ותלמוד", "myomi", "mishnayomi", "", "משניות", "צוויי משניות א טאג; דער מאגר דעקט עס בלויז טיילווייז."),
    "perek": ("פרק יומי במשנה", "משנה ותלמוד", "dpy", "perekYomi", "", "משניות", "א פרק משניות א טאג; אויסגעקליבענע שאלות פון די פרקים אינעם מאגר."),
    # "yerushalmi_vilna": ("ירושלמי יומי — וילנא", "משנה ותלמוד", "yyomi", "yerushalmi", "vilna", "", "לוח וילנא; אין עדיין מיפוי מאומת של שאלות המאגר לדפי מהדורה זו."),
    # "yerushalmi_schottenstein": ("ירושלמי יומי — שוטנשטיין", "משנה ותלמוד", "yys", "yerushalmi", "schottenstein", "", "לוח שוטנשטיין; אין להשתמש במספור וילנא לייבוא השאלות."),
    # "rambam1": ("רמב״ם יומי — פרק אחד", "הלכה ורמב״ם", "dr1", "dailyRambam1", "", "", "מסלול פרק אחד ביום; אין במאגר הנוכחי מאגר שאלות מתאים לרמב״ם."),
    # "rambam3": ("רמב״ם יומי — שלושה פרקים", "הלכה ורמב״ם", "dr3", "dailyRambam3", "", "", "מסלול שלושה פרקים ביום; אין במאגר הנוכחי מאגר שאלות מתאים לרמב״ם."),
    # "mitzvot": ("ספר המצוות לרמב״ם", "הלכה ורמב״ם", "dsm", "seferHaMitzvot", "", "", "לפי תקנת הלימוד היומי ברמב״ם; כרגע לוח לימוד ללא שאלות לייבוא."),
    # "kitzur": ("קיצור שולחן ערוך יומי", "הלכה ורמב״ם", "dksa", "kitzurShulchanAruch", "", "", "לפי קיצור שולחן ערוך של רבי שלמה גאנצפריד; שאלות משנ״ב אינן תחליף למקור זה."),
    # "arukh": ("ערוך השולחן יומי", "הלכה ורמב״ם", "ahsy", "arukhHaShulchanYomi", "", "", "לימוד ערוך השולחן; שאלות שולחן ערוך ומשנ״ב אינן משויכות אליו אוטומטית."),
    # "shemirat": ("שמירת הלשון היומי", "מוסר", "dshl", "shemiratHaLashon", "", "", "לוח שנתי. שאלות אור מנחם שבמאגר מקובצות בטווחים רחבים שטרם מופו להספק היומי."),
    # "nach": ("נ״ך יומי", "תנ״ך", "nyomi", "nachyomi", "", "", "פרק נ״ך ביום; כרגע לוח לימוד ללא שאלות לייבוא."),
    # "psalms": ("תהילים יומי — חלוקה חודשית", "תנ״ך", "dps", "dailyPsalms", "", "", "לפי היום בחודש העברי; כרגע לוח לימוד ללא שאלות לייבוא."),
}


def group_for(key):
    if key in DIRSHU_TRACKS:
        return "משנה ותלמוד"
    if key in EXTRA_TRACKS:
        return EXTRA_TRACKS[key][1]
    return {"amud": "משנה ותלמוד", "weekly": "משנה ותלמוד",
            "halacha": "הלכה ורמב״ם", "chofetz": "מוסר"}[key]


@lru_cache(maxsize=1)
def source_catalog():
    path = Path(__file__).with_name("source_catalog.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["sources"]


def source_description(path, title=""):
    info = source_catalog().get(path, {})
    label = title or path.rsplit("/", 1)[-1].rstrip("$").replace("_", " ")
    if not info:
        return label, "דער פארנעם פונעם מקור איז נאך נישט געמאסטן; קאנטראלירט די געוויזענע שאלות איידער איר אימפארטירט."
    summary = f"{label}  ·  {info['kind']}  ·  {info['questions']:,} שאלות / {info['files']:,} טעקעס"
    detail = info["note"]
    if info.get("simanim"):
        detail += f"\nגעפונען: {len(info['simanim'])} פארשידענע סימנים אינעם מקור; דאס באווייזט נישט אז יעדער סעיף איז אינגאנצן געדעקט."
    return summary, detail
