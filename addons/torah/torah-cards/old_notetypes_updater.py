import pathlib

from anki.consts import MODEL_CLOZE
from anki.models import ChangeNotetypeRequest
from aqt import gui_hooks, mw
from aqt.operations.notetype import update_notetype_legacy
from aqt.qt import *
from aqt.utils import askUser, tooltip

from .main_templates import getOrCreateModels

# change notetypes og old cards to new notetypes
old_to_new_notetypes = {
    "00 - תורני כללי": "01 געווענליכע שאלה (איין קארטל)",
    "01 - תורני - נושאים": "05 בחינה אויף נושאים און מקורות (צוויי קארטלעך: וואו שטייט עס און וואס שטייט אין א מקור)",
    "02 - תורני - מקור מוסתר (משמש לבחינה גם על המקורות)": "03 געווענליכע שאלה מיט א באהאלטענעם מקור אלס רמז (איין קארטל)",
    "03 - חמשה חומשי תורה": "01 געווענליכע שאלה (איין קארטל)",
    "03 - גמרא": "01 געווענליכע שאלה (איין קארטל)",
    "04 - גמרא - מקור בשורה חדשה": "01 געווענליכע שאלה (איין קארטל)",
    "05 - גמרא - מקור באותה שורה": "01 געווענליכע שאלה (איין קארטל)",
    "07 - טור ושו''ע": "01 געווענליכע שאלה (איין קארטל)",
    "08 - שאלות בגמרא עם רמז וקישורים": "02 שאלות מיט א בילד פונעם בלאט און אן אויספירליכע תשובה (איין קארטל)",
    "09 - בסיסי (הקלד את התשובה)": "04 שרייבט אריין די תשובה (איין קארטל)",
    "10 - בסיסי (וכרטיס הופכי)": "05 בחינה אויף נושאים און מקורות (צוויי קארטלעך: וואו שטייט עס און וואס שטייט אין א מקור)",
    "12 - השלם את החסר": "08 פילט אויס דאס אויסגעלאזטע - א טייל אינהאלט איז באהאלטן (דער צאל קארטלעך ווענדט זיך אין די באהאלטונגען; איין אדער מער אין א שאלה אדער באזונדערע קארטלעך)",
    "13 - בסיסי": "01 געווענליכע שאלה (איין קארטל)",
    "14 - שאלות אמריקאיות ": "10 שאלות מיט אן אויסוואל פון תשובות (איין קארטל)",
    "15 - שאלות ותשובות מרובות": "06 עטליכע שאלות און תשובות - נאך דער תשובה קומט נאך א פארבינדענע שאלה (איין קארטל)",
    # "16 - גמרא - מקור במבחן נפרד": "03 שאלה רגילה עם מקור מוסתר כמו רמז (כרטיס אחד)",
    "17 - שאלות ותשובות מרובות- כל שלב מוצג גם בתור שאלה נפרדת": "07 ווי 06: יעדע שאלה אלס המשך און אויך אלס באזונדער קארטל (ביז 10 קארטלעך)"
}
not_new_equal = (
    "06 - גמרא - נושאים",
    "11 - בסיסי (כרטיס הופכי אופציונלי)",
    "16 - גמרא - מקור במבחן נפרד"
)


def update_old_to_new_notetypes():
    mw.col.set_schema_modified()
    for old_nt, new_nt in old_to_new_notetypes.items():
        input = ChangeNotetypeRequest()
        res = mw.col.find_notes(f'"note:{old_nt}"')
        old_id = mw.col.models.id_for_name(old_nt)
        new_id = mw.col.models.id_for_name(new_nt)
        old_nt_dict = mw.col.models.get(old_id)
        new_nt_dict = mw.col.models.get(new_id)
        if old_nt_dict is not None and new_nt_dict is not None:
            is_cloze = old_nt_dict["type"] == MODEL_CLOZE or new_nt_dict["type"] == MODEL_CLOZE
            old_tmpls = len(old_nt_dict['tmpls'])
            new_tmpls = len(new_nt_dict['tmpls'])
            old_flds = len(old_nt_dict['flds'])
            new_flds = len(new_nt_dict['flds'])
            for cid in res:
                input.note_ids.append(cid)
            for field in range(0, new_flds):
                if field <= old_flds:
                    input.new_fields.append(field)
                else:
                    input.new_fields.append(-1)
            for template in range(0, new_tmpls):
                if template <= old_tmpls:
                    input.new_templates.append(template)
                else:
                    input.new_templates.append(-1)
            input.old_notetype_id = int(old_id)
            input.new_notetype_id = int(new_id)
            input.current_schema = mw.col.db.first("select scm from col")[0]
            input.old_notetype_name = old_nt
            input.is_cloze = is_cloze
            # showText(str(input))
            mw.col.models.change_notetype_of_notes(input)
            #             מחיקת סוג רשומה ישן
            res = mw.col.find_notes(f'"note:{old_nt}"')
            if len(res) == 0:
                mw.col.models.remove(old_id)


# ישמש לעדכון סוגי רשומות שאין להם תחליף חדש
def onRename() -> None:
    for nt_old_name in not_new_equal:
        nid = mw.col.models.id_for_name(nt_old_name)
        if nid is not None:
            res = len(mw.col.find_notes(f'"note:{nt_old_name}"'))
            if res != 0:
                nt = mw.col.models.get(nid)
                nt["name"] = "ישן" + nt_old_name
                update_notetype_legacy(parent=mw, notetype=nt).success(
                    lambda a: tooltip("הצליח")
                ).run_in_background()
            else:
                mw.col.models.remove(nid)


def ask_before_update_old_notetypes(from_menu = False):
    conf_key = "updated_ha_notetypes"
    if mw.col.db.first("select count(*) from cards;")[0] == 0: # משתמש חדש שרק יתווספו לו כרטיסים
        getOrCreateModels(new_user=True)
        mw.col.conf[conf_key] = True
        return

    ask_text = ("שים לב! בגירסא החדשה שונו סוגי הרשומות ושופרו. האם ברצונך לעדכן את סוגי הרשומות ולשנות את סוג הרשומה לשאלות שכבר כתבת לסוגי "
                "הרשומה המקבילים החדשים?\nאם תלחץ על 'כן' תוכל לבטל פעולה זאת אחר כך על ידי שחזור "
                "מגיבוי.\nאם תבחר ב'לא' תוכל לעדכן על ידי האפשרות שבתפריט>כלי מאגר>עדכון לרשומות "
                "חדשות.\nאם אתה משתמש בסינכרון, לאחר פעולה זו תזדקק לסנכרון מלא במהלך הסנכרון הבא.\nלהמשיך?")

    if mw.col.conf.get(conf_key) is None or from_menu:
    # if True:
        if askUser(ask_text):
            getOrCreateModels(new_user=True)
            update_old_to_new_notetypes()
            onRename()
        mw.col.conf[conf_key] = True

def add_menu_action():
    if not hasattr(mw, "addon_col_menu"):
        return
    action = QAction("עדכון לרשומות חדשות", mw)
    qconnect(action.triggered, lambda: ask_before_update_old_notetypes(from_menu=True))
    filename = str(pathlib.Path(__file__).parent.resolve())
    icon = QIcon(filename + "/upgrade.png")
    action.setIcon(icon)
    mw.addon_col_menu.addAction(action)

gui_hooks.main_window_did_init.append(add_menu_action)


