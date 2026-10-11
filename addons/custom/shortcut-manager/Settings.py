# // by m.s. some parts of this file from another addon by auth_ Mohamad Janati
# Refactored and Fixed Version 4.0 (Browser Ctrl+Num Warning Added)

import contextlib
import copy
import ctypes
import json
import os
import sys
from datetime import datetime
from os.path import dirname, join

from aqt import dialogs as aqt_dialogs
from aqt import mw
from aqt.qt import *
from aqt.utils import askUser, getSaveFile, showInfo
from _shared_libs.haf_notifications import show_failure

from .color_shortcuts import normalize_color_shortcut_rows
from .config_defaults import DEFAULT_CONFIGS
from . import custom_shortcuts
from .lib.pyluach.dates import GregorianDate

# רשימת המקשים הגלובליים (הקבוצה הראשונה בטאב 0)
GLOBAL_MAIN_KEYS = {
    'create_deck', 'main deckbrowser', 'main study', 'main add',
    'main browse', 'main stats', 'main sync'
}

# #195 — קבוצת מפתחות של פעולות עיצוב כתב בעורך/עריכה במבחן. עבור מפתחות אלו אסור לקבוע
# קיצור שהוא אות/ספרה בודדת ללא Ctrl/Alt, כי הקלדה רגילה של אות צריכה לכתוב אותה לשדה.
FORMATTING_SHORTCUT_KEYS = {
    # עריכה במבחן (edit-field-review)
    'Qbold', 'Qitalic', 'Qunderline', 'QstrikeThrough',
    'QjustifyCenter', 'QjustifyFull', 'QjustifyLeft', 'QjustifyRight',
    'QinsertOrderedList', 'QinsertUnorderedList', 'Qindent', 'Qoutdent',
    'QremoveFormat', 'Qsubscript', 'Qsuperscript',
    'qforec1', 'qforec2', 'qforec3', 'qforec4', 'qforec5', 'qforec6',
    # עורך (editor)
    'editor bold', 'editor italic', 'editor underline',
    'editor subscript', 'editor superscript', 'editor remove format',
    'editor foreground',
    'color1_shortcut', 'color2_shortcut', 'color3_shortcut',
    'color4_shortcut', 'color5_shortcut', 'color6_shortcut',
    # סגנונות מהירים של font-size
    'style_preset_1_shortcut', 'style_preset_2_shortcut',
    'style_preset_3_shortcut', 'style_preset_4_shortcut',
    'style_preset_5_shortcut',
    # #269 — קיצורי סגנון במבחן שייכים ל-edit-field-review ולא לקיצורי font-size של העורך הרגיל.
    'review_style_preset_1_shortcut', 'review_style_preset_2_shortcut',
    'review_style_preset_3_shortcut', 'review_style_preset_4_shortcut',
    'review_style_preset_5_shortcut',
}


# #138 — בכל שדה טקסט בעורך או בעריכה במבחן, אות ללא Ctrl/Alt היא הקלדה ולא
# פקודה. הבדיקה משמשת גם את חלון הקליטה וגם את Apply, כדי שגיבוי ישן לא יעקוף אותה.
def _navigation_shortcut_has_shift(key, shortcut):
    return key in {"window_browser first card", "window_browser last card"} and (
        "shift" in str(shortcut).lower().split("+")
    )


def _unsafe_editing_letter_shortcut(shortcut):
    if not isinstance(shortcut, str):
        return False
    parts = [part.strip() for part in shortcut.split("+") if part.strip()]
    if not parts or shortcut.strip().lower() in {"none", "<nop>", "<default>"}:
        return False
    lowered = {part.lower() for part in parts}
    if "ctrl" in lowered or "control" in lowered or "alt" in lowered:
        return False
    non_modifiers = [
        part for part in parts
        if part.lower() not in {"shift", "meta", "cmd", "command"}
    ]
    return len(non_modifiers) == 1 and len(non_modifiers[0]) == 1 and non_modifiers[0].isalpha()

# אישיו #400: שומרים את האות העברית שהמשתמש לחץ עליה במקום להמיר אותה למקש הלטיני
# הפיזי, כדי שאפשר יהיה להגדיר ולהפעיל קיצור עברי בלי להחליף את שפת המקלדת.
HEBREW_TO_LATIN_KEY = {
    'א': 'א', 'ב': 'ב', 'ג': 'ג', 'ד': 'ד', 'ה': 'ה', 'ו': 'ו', 'ז': 'ז',
    'ח': 'ח', 'ט': 'ט', 'י': 'י', 'כ': 'כ', 'ך': 'ך', 'ל': 'ל', 'מ': 'מ',
    'ם': 'ם', 'נ': 'נ', 'ן': 'ן', 'ס': 'ס', 'ע': 'ע', 'פ': 'פ', 'ף': 'ף',
    'צ': 'צ', 'ץ': 'ץ', 'ק': 'ק', 'ר': 'ר', 'ש': 'ש', 'ת': 'ת',
}

# #359 — HEBREW_TO_LATIN_KEY (#354) מכסה רק 22 אותיות, וגם עבורן וגם עבור ספרות/פיסוק
# מקלדת עברית עלולה להפיק תו לגמרי שונה (ניקוד, סימן אחר) שאינו מופיע באף טבלה — למשל
# Ctrl+Shift+[ (סוגר מרובע שמאלי) נקלט בתור '}' ונשמר קיצור שכלל לא ניתן לפרסור ב-Qt.
# ה-virtual key הפיזי של Windows (evt.nativeVirtualKey()) מייצג את מיקום המקש בפועל
# בלי תלות בשפת הקלט הפעילה, ולכן מספק זיהוי אמין הרבה יותר מהתו שהמקלדת בפועל הפיקה.
# הטבלה הזו ממפה ספרות/אותיות/פיסוק תקניים (מיקום לפי פריסת US) לפי קוד ה-VK שלהם.
WINDOWS_VK_KEY_MAP = {
    **{0x30 + i: str(i) for i in range(10)},   # ספרות 0-9
    **{0x41 + i: chr(0x41 + i) for i in range(26)},  # אותיות A-Z
    0xBA: ';', 0xBB: '=', 0xBC: ',', 0xBD: '-', 0xBE: '.',
    0xBF: '/', 0xC0: '`', 0xDB: '[', 0xDC: '\\', 0xDD: ']', 0xDE: "'",
}
# #354 — סמלי הפיסוק המודפסים עם Shift נשמרים כסמל עצמו (ולא כאילו נלחץ
# המקש הלא-מוזז). כך Ctrl+Shift+<, Ctrl+Shift+> וכדומה נרשמים ועובדים ב-Qt.
WINDOWS_SHIFTED_VK_KEY_MAP = {
    0xBA: ':', 0xBB: '+', 0xBC: '<', 0xBD: '_', 0xBE: '>',
    0xBF: '?', 0xC0: '~', 0xDB: '{', 0xDC: '|', 0xDD: '}', 0xDE: '"',
}

UI_STRUCTURE = {
    'main': {
        'title': "הויפט עקראן",
        'index': 0,
        'groups': {
            'main_shortcuts': ('קיצור קנעפלעך פארן הויפט עקראן און חזרה', {
                'create_deck': "שאף א פעקל",
                'main deckbrowser': "הויפט עקראן",
                'main study': "לערן דעם יעצטיגן פעקל",
                'main add': "שרייבט א פראגע",
                'main browse': "דורכבלעטערן",
                'main stats': "סטאטיסטיק",
                'main sync': "סינכראניזירן"
            }),
            'deck_options': ('קיצור קנעפלעך פאר פעקל אפציעס (פארן אויסגעקליבענעם פעקל)', {
                'deck_rename': "טויש נאמען", 'deck_options': "אפציעס", 'deck_export': "עקספארטירן", 'deck_delete': "מעק אויס",
                'deck_create_sub_deck': "שאף אן אונטערפעקל", 'deck_move': "פיר אריבער אין א פעקל...", 'deck_overview': "סיכום",
                'deck_unbury': "ברענג צוריק פון באזייטיגן", 'deck_filter': "פילטערט פראגעס", 'deck_custom': "צוגעפאסט לערנען",
                'deck_rebuild_f_deck': "בוי פון פריש", 'deck_empty': "ליידיג אויס"
            }),
            'menu_options': ('קיצור קנעפלעך פאר אפציעס אינעם מעניו', {
                'm_toolbox study': "קלייבט אויס א פעקל צו לערנען", 'm_toolbox undo': "מאך צוריק די לעצטע פעולה", 'm_toolbox _duplicates': "געפין דאפלטע", 'print_open': "דרוקן און עקספארטירן צו ווארד",
                'm_toolbox create filtered deck': "שאף א געפילטערטן פעקל", 'm_toolbox import': "אימפארטירן", 'm_toolbox export': "עקספארטירן",
                'm_toolbox preferences': "פרעפערענצן", 'm_toolbox switch profile': "בייט פראפיל", 'm_toolbox addons': "צוגאבן", 'm_toolbox quit': "פארמאכט דעם פראגראם"
            })
        }
    },
    'reviewer': {
        'title': "חזרה",
        'index': 1,
        'groups': {
            'reviewer_shortcuts': ('קיצור קנעפלעך פארן חזרה עקראן', {
                'reviewer flip card 1': "ווייז די ענטפער 1", 'reviewer flip card 2': "ווייז די ענטפער 2", 'reviewer flip card 3': "ווייז די ענטפער 3",
                'reviewer choice 1': "ענטפער קנעפל 1", 'reviewer choice 2': "ענטפער קנעפל 2", 'reviewer choice 3': "ענטפער קנעפל 3", 'reviewer choice 4': "ענטפער קנעפל 4",
                'Button_Skip_Button': "איבערהיפן", 'Button_Info_Button': "אינפארמאציע", 'Button_Undo_Button': "מאך צוריק די לעצטע פעולה", 'Button_Defer_Button': "פיר אריבער צום שפעטער באהאנדלען",
                'reviewer set due date': "שטעל אן אייגענעם דאטום", 'reviewer mark card': "צייכן אן א פראגע", 'reviewer edit current': "רעדאקטיר א פראגע",
                'reviewer bury card': "לייג דעם קארטל באזייטיג ביז מארגן", 'reviewer bury note': "לייג די רשומה באזייטיג ביז מארגן", 'reviewer suspend card': "שטעל אפ דעם קארטל", 'reviewer suspend note': "שטעל אפ די רשומה",
                'reviewer card info': "קארטל אינפארמאציע", 'hide_ans': "באהאלט די ענטפער", 'resched_addon': "פארבעסערטער מאנועלער צייטפלאן", 'show_skipped': "ווייז איבערגעהיפטע קארטלעך",
                # #138 — Anki 25 כולל שבעה דגלים; 0 הוא פעולת ניקוי ולא דגל נוסף.
                'reviewer set flag 0': "נעם אוועק דעם פאן", 'reviewer set flag 1': "שטעל א פאן 1", 'reviewer set flag 2': "שטעל א פאן 2", 'reviewer set flag 3': "שטעל א פאן 3", 'reviewer set flag 4': "שטעל א פאן 4",
                'reviewer set flag 5': "שטעל א פאן 5", 'reviewer set flag 6': "שטעל א פאן 6", 'reviewer set flag 7': "שטעל א פאן 7",
                'reviewer delete note': "מעק אויס די רשומה", 'reviewer more options': "מעניו פון נאך אפציעס", 'reviewer options menu': "פעקל איינשטעלונגען", 'reviewer pause audio': "שטעל אפ דעם קלאנג",
                'reviewer replay audio 1': "שפיל נאכאמאל 1", 'reviewer replay audio 2': "שפיל נאכאמאל 2",
                'reviewer seek backward': "גיי צוריק 5 סעקונדעס אינעם קלאנג", 'reviewer seek forward': "גיי פאראויס 5 סעקונדעס אינעם קלאנג", 'reviewer previous card info': "אינפארמאציע פונעם פריערדיגן קארטל",
                'reviewer play recorded voice': "שפיל די רעקארדירונג", 'reviewer record voice': "רעקארדיר",
                'reviewer toggle auto advance': "שאלט אן/אויס אויטאמאטיש ווייטערגיין"
            })
        }
    },
    'quick_edit': {
        'title': "רעדאקטירן ביים חזרן",
        'index': 2,
        'groups': {
            'quick_edit_shortcuts': ('קיצור קנעפלעך צום רעדאקטירן ביים חזרן', {
                # #138 — edit-field-review כולל גם italic; מציגים אותו ב-shortcut-manager כדי שיהיה לו קיצור וברירת מחדל.
                'review_fontfamily': "סארט שריפט", 'review_fontsize': "גרייס", 'Qbold': "מאך דעם טעקסט דיק", 'Qitalic': "שיף", 'Qunderline': "אונטערשטרייכן", 'QstrikeThrough': "דורכשטרייכן אותיות",
                'QjustifyCenter': "אויסריכטן אין מיטן", 'QjustifyFull': "אויסריכטן צו ביידע זייטן", 'QjustifyLeft': "אויסריכטן לינקס", 'QjustifyRight': "אויסריכטן רעכטס",
                # #138 — כותרות הרשימות תואמות לפעולה בפועל: ordered=list מספרים, unordered=נקודות.
                'QinsertOrderedList': "נומערירטע ליסטע", 'QinsertUnorderedList': "ליסטע מיט פינטלעך", 'Qindent': "רוק מער אריין", 'Qoutdent': "רוק ווייניגער אריין",
                'QremoveFormat': "נעם אוועק דעם אויסשטעל", 'Qsubscript': "אונטערשריפט", 'Qsuperscript': "אויבערשריפט"
            }),
            'review_style_presets': ('סטיל קנעפלעך אינעם חזרה רעדאקטירער סרגל', {
                # #269 — קיצורי הכפתורים שמפעילים את הסגנונות מוצגים כקבוצה נפרדת וברורה בטאב עריכה במבחן.
                'review_style_preset_1_shortcut': "נוץ דעם סטיל קנעפל 1",
                'review_style_preset_2_shortcut': "נוץ דעם סטיל קנעפל 2",
                'review_style_preset_3_shortcut': "נוץ דעם סטיל קנעפל 3",
                'review_style_preset_4_shortcut': "נוץ דעם סטיל קנעפל 4",
                'review_style_preset_5_shortcut': "נוץ דעם סטיל קנעפל 5",
            }),
            'quick_edit_colors': ('קאלירן צום רעדאקטירן ביים חזרן', [
                {'key_color': 'Qccolor1', 'key_shortcut': 'qforec1', 'label': "טעקסט קאליר 1"}, {'key_color': 'Qccolor2', 'key_shortcut': 'qforec2', 'label': "טעקסט קאליר 2"},
                {'key_color': 'Qccolor3', 'key_shortcut': 'qforec3', 'label': "טעקסט קאליר 3"}, {'key_color': 'Qccolor4', 'key_shortcut': 'qforec4', 'label': "טעקסט קאליר 4"},
                {'key_color': 'Qccolor5', 'key_shortcut': 'qforec5', 'label': "טעקסט קאליר 5"}, {'key_color': 'Qccolor6', 'key_shortcut': 'qforec6', 'label': "טעקסט קאליר 6"},
            ])
        }
    },
    'editor': {
        'title': "רעדאקטירער",
        'index': 3,
        'groups': {
            'editor_shortcuts': ('קיצור קנעפלעך פארן פראגע צולייג עקראן', {
                'editor_fontfamily': "סארט שריפט", 'editor_fontsize': "גרייס", 'editor focus tags': "גיי צום צעטלעך פעלד", 'editor toggle sticky current': "געדענק דעם יעצטיגן פעלד פאר דער קומענדיגער פראגע",
                'editor toggle sticky all': "געדענק אלע פעלדער פאר דער קומענדיגער פראגע", 'editor foreground': "טעקסט קאליר", 'editor bold': "דיקער טעקסט",
                'editor italic': "שיפער טעקסט", 'editor underline': "אונטערשטרייכן", 'editor subscript': "אונטערשריפט", 'editor superscript': "אויבערשריפט",
                'editor remove format': "נעם אוועק דעם אויסשטעל", 'editor cloze': "פיל אויס דאס פעלנדיגע", 'remove_cloze': "נעם אוועק די אויסלאזונג צייכנס", 'editor card layout': "קארטל אויסשטעל", 'editor change deck': "טויש פעקל",
                'editor change col': "טויש דעם אויסגעקליבענעם טעקסט קאליר", 'editor add media': "שטעל צו מעדיע", 'editor record sound': "רעקארדיר א קלאנג",
                'editor change note type': "טויש דעם סארט רשומה", 'editor confirm add card': "באשטעטיג דאס צולייגן דעם קארטל", 'editor add card close window': "פארמאך דעם קארטל צולייג פענסטער",
                # #187 — תוסף pdf-viewer מקבל שורת קיצור בעורך לצד פעולות המדיה האחרות.
                'pdf_viewer_insert': "אריינלייגן PDF",
                'style_preset_1_shortcut': "שנעלער סטיל 1", 'style_preset_2_shortcut': "שנעלער סטיל 2", 'style_preset_3_shortcut': "שנעלער סטיל 3",
                'style_preset_4_shortcut': "שנעלער סטיל 4", 'style_preset_5_shortcut': "שנעלער סטיל 5",
                # #359 — external-editor פועל על חלון העריכה הרגיל (הוספת שאלה/עורך בדפדוף),
                # לא על העריכה בתוך מסך המבחן — לכן הקיצור שייך לכאן ולא לטאב "עריכה במבחן".
                'external_editor_open_advanced': "עפנט דעם פארגעשריטענעם רעדאקטירער"
            }),
            'editor_colors': ('קיצור קנעפלעך צו טוישן קאלירן', [
                {'key_color': 'fore_color1', 'key_shortcut': 'color1_shortcut', 'label': "קיצור פארן טעקסט קאליר 1"}, {'key_color': 'fore_color2', 'key_shortcut': 'color2_shortcut', 'label': "קיצור פארן טעקסט קאליר 2"},
                {'key_color': 'fore_color3', 'key_shortcut': 'color3_shortcut', 'label': "קיצור פארן טעקסט קאליר 3"}, {'key_color': 'fore_color4', 'key_shortcut': 'color4_shortcut', 'label': "קיצור פארן טעקסט קאליר 4"},
                {'key_color': 'fore_color5', 'key_shortcut': 'color5_shortcut', 'label': "קיצור פארן טעקסט קאליר 5"}, {'key_color': 'fore_color6', 'key_shortcut': 'color6_shortcut', 'label': "קיצור פארן טעקסט קאליר 6"},
            ])
        }
    },
    'browser': {
        'title': "דורכבלעטערן",
        'index': 4,
        'groups': {
            'browser_shortcuts': ('קיצור קנעפלעך פארן דורכבלעטערער עקראן', {
                'window_browser add note': "לייג צו א רשומה", 'window_browser change deck': "טויש פעקל", 'window_browser change note type': "טויש דעם סארט רשומה",
                'window_browser add tag': "לייג צו א צעטל", 'window_browser remove tag': "נעם אוועק א צעטל", 'window_browser clear unused tags': "ריין אויס נישט גענוצטע צעטלעך",
                'window_browser preview': "ווייז די פראגע אינעם פארויסקוק", 'window_browser info': "קארטל אינפארמאציע", 'window_browser reposition': "שטעל ווידער א פלאץ אינעם חזרה סדר",
                'window_browser reschedule': "מאך א נייעם צייטפלאן", 'window_browser suspend': "שטעל אפ", 'window_browser toggle mark': "צייכן אן/נעם אוועק דעם סימון",
                'window_browser flag_red': "צייכן אן מיט א רויטן פאן", 'window_browser flag_orange': "צייכן אן מיט אן אראנזשן פאן", 'window_browser flag_green': "צייכן אן מיט א גרינעם פאן", 'window_browser flag_blue': "צייכן אן מיט א בלויעם פאן",
                'window_browser flag_pink': "צייכן אן מיט א ראזען פאן", 'window_browser flag_turquoise': "צייכן אן מיט א טורקיזן פאן", 'window_browser flag_purple': "צייכן אן מיט א לילא פאן",
                'window_browser undo': "מאך צוריק די לעצטע פעולה", 'window_browser delete': "מעק אויס", 'window_browser find': "זוך", 'window_browser filter': "גיי צום זוכן אינעם זייט סרגל", 'window_browser find and replace': "זוכן און איבערבייטן",
                'window_browser find duplicates': "געפין דאפלטע", 'window_browser goto card list': "גיי צו דער קארטל ליסטע", 'window_browser goto next note': "גיי צום קומענדיגן קארטל",
                'window_browser goto previous note': "גיי צום פריערדיגן קארטל", 'window_browser goto sidebar': "גיי צום זייט סרגל", 'window_browser sidebar search': "זוכעניש אינעם זייט סרגל",
                'window_browser sidebar select': "קלייב אויס אינעם זייט סרגל", 'window_browser select notes': "קלייב אויס די אנגעצייכנטע רשומה", 'window_browser first card': "גיי צום ערשטן קארטל (מיט Shift: צייכן אן ביז אים)",
                'window_browser last card': "גיי צום לעצטן קארטל (מיט Shift: צייכן אן ביז אים)", 'window_browser select all': "קלייב אלעס אויס", 'window_browser invert selection': "קער איבער די אויסוואל",
                'window_browser goto note': "גיי צום רעדאקטירן די רשומה", 'window_browser manage note types': "פיר סארטן רשומה", 'browser_refresh': "פריש אויף דעם דורכבלעטערער פענסטער",
                'window_browser close': "פארמאך דעם דורכבלעטערער פענסטער"
            })
        }
    },
    'global_settings': {
        'title': "אלגעמיינע איינשטעלונגען",
        'index': 5,
        'groups': {
            'toggles': ('אן און אויסשאלט איינשטעלונגען (מען דארף אנהייבן פון פריש)', [
                {'key': 'Ω enable conflict warning', 'label': "ווארענונג אויב נאך א קנעפל ניצט דעם זעלבן קיצור", 'type': 'checkbox'},
                {'key': 'Ω enable editor', 'label': "שאלט אן אייגענע קיצורים אינעם רעדאקטירער", 'type': 'checkbox'},
                {'key': 'Ω enable m_toolbox', 'label': "ערלויב אייגענע קיצורים אינעם כלים מעניו", 'type': 'checkbox'},
                {'key': 'Ω enable main', 'label': "ערלויב אייגענע קיצורים אויפן הויפט עקראן", 'type': 'checkbox'},
                {'key': 'Ω enable reviewer', 'label': "ערלויב אייגענע קיצורים ביים חזרן", 'type': 'checkbox'},
                {'key': 'Ω enable window_browser', 'label': "ערלויב אייגענע קיצורים אינעם דורכבלעטערער", 'type': 'checkbox'},
            ])
        }
    }
}

ADDON_CONFIG_MAP = {
    'print-addon': {'print_shortcut': 'print_open'},
    'bottom-bar': {'Button_ Shortcut_ Skip Button': 'Button_Skip_Button', 'Button_ Shortcut_ Info Button': 'Button_Info_Button', 'Button_ Shortcut_ Undo Button': 'Button_Undo_Button', 'Button_ Shortcut_ Show Skipped Button': 'show_skipped'},
    # #138 v2 — תוספי AnkiWeb נפרסים תחת שם תיקייה מספרי (deploy_dir). אנקי מזהה אותם לפי המזהה המספרי בלבד,
    # ולכן כתיבת config דרך mw.addonManager.writeConfig חייבת להשתמש במזהה המספרי ולא בשם תיקיית המקור.
    '149564514': {'hotkey': 'Button_Defer_Button'},
    'edit-field-review': {
        'reviewer_font_shortcut': 'review_fontfamily', 'reviewer_size_shortcut': 'review_fontsize',
        # #138 — edit-field-review משתמש במפתחות אנגליים בקובץ config.json; כתיבה למפתחות עבריים יצרה הגדרות שלא נטענו ב-JS.
        'special_formatting.bold.shortcut': 'Qbold', 'special_formatting.italic.shortcut': 'Qitalic',
        # #138 v2 — מפתח נפרד Qunderline למקש קיצור underline ב-edit-field-review (לא לערבב עם 'editor underline' של אנקי המקורי).
        'special_formatting.underline.shortcut': 'Qunderline',
        'special_formatting.strikethrough.shortcut': 'QstrikeThrough', 'special_formatting.justifyCenter.shortcut': 'QjustifyCenter',
        'special_formatting.justifyFull.shortcut': 'QjustifyFull', 'special_formatting.justifyLeft.shortcut': 'QjustifyLeft', 'special_formatting.justifyRight.shortcut': 'QjustifyRight',
        'special_formatting.orderedlist.shortcut': 'QinsertOrderedList', 'special_formatting.unorderedlist.shortcut': 'QinsertUnorderedList', 'special_formatting.indent.shortcut': 'Qindent',
        'special_formatting.outdent.shortcut': 'Qoutdent', 'special_formatting.removeformat.shortcut': 'QremoveFormat', 'special_formatting.subscript.shortcut': 'Qsubscript',
        'special_formatting.superscript.shortcut': 'Qsuperscript',
        # #269 — קיצורי פריסטים במהלך מבחן נכתבים לקונפיג הפעיל של edit-field-review.
        'review_preset_shortcuts.preset_1': 'review_style_preset_1_shortcut',
        'review_preset_shortcuts.preset_2': 'review_style_preset_2_shortcut',
        'review_preset_shortcuts.preset_3': 'review_style_preset_3_shortcut',
        'review_preset_shortcuts.preset_4': 'review_style_preset_4_shortcut',
        'review_preset_shortcuts.preset_5': 'review_style_preset_5_shortcut',
        # #138 — ששת צבעי הטקסט הם שש פעולות foreColor עצמאיות. edit-field-review
        # רושם דינמית כל רשומת special_formatting, ולכן לכל שורה במנהל יש יעד runtime אמיתי.
        'special_formatting.טעקסט קאליר 1.shortcut': 'qforec1', 'special_formatting.טעקסט קאליר 2.shortcut': 'qforec2',
        'special_formatting.טעקסט קאליר 3.shortcut': 'qforec3', 'special_formatting.טעקסט קאליר 4.shortcut': 'qforec4',
        'special_formatting.טעקסט קאליר 5.shortcut': 'qforec5', 'special_formatting.טעקסט קאליר 6.shortcut': 'qforec6',
        'special_formatting.טעקסט קאליר 1.arg.value': 'Qccolor1', 'special_formatting.טעקסט קאליר 2.arg.value': 'Qccolor2',
        'special_formatting.טעקסט קאליר 3.arg.value': 'Qccolor3', 'special_formatting.טעקסט קאליר 4.arg.value': 'Qccolor4',
        'special_formatting.טעקסט קאליר 5.arg.value': 'Qccolor5', 'special_formatting.טעקסט קאליר 6.arg.value': 'Qccolor6'
    },
    'rescheduler': {'access_dialog_from_reviewer': 'resched_addon'},
    # #138 v2 — empty-addon פרוס תחת המזהה המספרי 1566569834.
    '1566569834': {'shortcut': 'hide_ans'},
    # #138 v2 — remove-clozes פרוס תחת המזהה המספרי 1966460736. שימוש בשם תיקיית המקור גרם לכך
    # ש-writeConfig/getConfig של אנקי כשלו בשקט ולכן הקיצור במנהל לא היה מסונכרן עם התוסף.
    '1966460736': {'hotkey': 'remove_cloze'},
    'refresh-browser': {'ShortCut': 'browser_refresh'},
    # #187 — shortcut-manager כותב את קיצור כפתור PDF לקונפיג של pdf-viewer.
    'pdf-viewer': {'editor_shortcut': 'pdf_viewer_insert'},
    'font-size': {
        'font_Shortcut': 'editor_fontfamily', 'size_Shortcut': 'editor_fontsize',
        'style_preset_1_shortcut': 'style_preset_1_shortcut', 'style_preset_2_shortcut': 'style_preset_2_shortcut',
        'style_preset_3_shortcut': 'style_preset_3_shortcut', 'style_preset_4_shortcut': 'style_preset_4_shortcut',
        'style_preset_5_shortcut': 'style_preset_5_shortcut'
    }
}

def _load_addon_default_config(addon_id):
    # #264 — שחזור ברירות מחדל חייב לטעון גם defaults של תוספים חיצוניים כמו bottom-bar.
    try:
        defaults = mw.addonManager.addonConfigDefaults(addon_id)
        if defaults is not None:
            return copy.deepcopy(defaults)
    except Exception:
        pass

    try:
        config_path = join(mw.addonManager.addonsFolder(), addon_id, "config.json")
        with open(config_path, encoding="utf-8") as config_file:
            return json.load(config_file)
    except Exception:
        return {}

# #138 — גרסאות קודמות שמרו קיצורי edit-field-review עם underscore בסוף; נטען אותם כדי שההגדרות הקיימות של המשתמש לא ייעלמו.
LEGACY_MAIN_KEY_ALIASES = {
    'Qbold': 'Qbold_',
    # #138 — תאימות לגיבויים/קונפיג ישנים אם נוסף בהם קיצור italic עם underscore.
    'Qitalic': 'Qitalic_',
    'QstrikeThrough': 'QstrikeThrough_',
    'QjustifyCenter': 'QjustifyCenter_',
    'QjustifyFull': 'QjustifyFull_',
    'QjustifyLeft': 'QjustifyLeft_',
    'QjustifyRight': 'QjustifyRight_',
    'QinsertOrderedList': 'QinsertOrderedList_',
    'QinsertUnorderedList': 'QinsertUnorderedList_',
    'Qindent': 'Qindent_',
    'Qoutdent': 'Qoutdent_',
    'QremoveFormat': 'QremoveFormat_',
    'Qsubscript': 'Qsubscript_',
    'Qsuperscript': 'Qsuperscript_',
}

# #138 — גרסאות ישנות של edit-field-review שמרו חלק מקיצורי העיצוב תחת שמות עבריים בתוך special_formatting.
EDIT_FIELD_REVIEW_LEGACY_PATHS = {'Qbold': ['special_formatting.מאך דעם טעקסט דיק.shortcut', 'special_formatting.הדגש טקסט.shortcut'], 'Qitalic': ['special_formatting.שיף.shortcut', 'special_formatting.שיפער טעקסט.shortcut', 'special_formatting.נטוי.shortcut', 'special_formatting.טקסט נטוי.shortcut'], 'QstrikeThrough': ['special_formatting.דורכשטרייכן.shortcut', 'special_formatting.דורכשטרייכן אותיות.shortcut', 'special_formatting.קו באמצע אות.shortcut', 'special_formatting.קו באמצע אותיות.shortcut'], 'QjustifyCenter': ['special_formatting.אויסריכטן אין מיטן.shortcut', 'special_formatting.יישור למרכז.shortcut'], 'QjustifyFull': ['special_formatting.אויסריכטן צו ביידע זייטן.shortcut', 'special_formatting.יישור לשני הצדדים.shortcut'], 'QjustifyLeft': ['special_formatting.אויסריכטן לינקס.shortcut', 'special_formatting.יישור לשמאל.shortcut'], 'QjustifyRight': ['special_formatting.אויסריכטן רעכטס.shortcut', 'special_formatting.יישור לימין.shortcut'], 'QinsertOrderedList': ['special_formatting.מאך א ליסטע.shortcut', 'special_formatting.הפוך לרשימה.shortcut'], 'QinsertUnorderedList': ['special_formatting.נעם אוועק די ליסטע.shortcut', 'special_formatting.בטל רשימה.shortcut'], 'Qindent': ['special_formatting.רוק מער אריין.shortcut', 'special_formatting.הגדל הזחה.shortcut'], 'Qoutdent': ['special_formatting.רוק ווייניגער אריין.shortcut', 'special_formatting.הקטן הזחה.shortcut'], 'QremoveFormat': ['special_formatting.נעם אוועק דעם אויסשטעל.shortcut', 'special_formatting.הסר עיצוב.shortcut'], 'Qsubscript': ['special_formatting.אונטערשריפט.shortcut', 'special_formatting.טקסט תחתון.shortcut'], 'Qsuperscript': ['special_formatting.אויבערשריפט.shortcut', 'special_formatting.טקסט עליון.shortcut'], 'qforec1': ['special_formatting.טעקסט קאליר 1.shortcut', 'special_formatting.צבע טקסט 1.shortcut'], 'qforec2': ['special_formatting.טעקסט קאליר 2.shortcut', 'special_formatting.צבע טקסט 2.shortcut'], 'qforec3': ['special_formatting.טעקסט קאליר 3.shortcut', 'special_formatting.צבע טקסט 3.shortcut'], 'qforec4': ['special_formatting.טעקסט קאליר 4.shortcut', 'special_formatting.צבע טקסט 4.shortcut'], 'qforec5': ['special_formatting.טעקסט קאליר 5.shortcut', 'special_formatting.צבע טקסט 5.shortcut'], 'qforec6': ['special_formatting.טעקסט קאליר 6.shortcut', 'special_formatting.צבע טקסט 6.shortcut'], 'Qccolor1': ['special_formatting.טעקסט קאליר 1.arg.value', 'special_formatting.צבע טקסט 1.arg.value'], 'Qccolor2': ['special_formatting.טעקסט קאליר 2.arg.value', 'special_formatting.צבע טקסט 2.arg.value'], 'Qccolor3': ['special_formatting.טעקסט קאליר 3.arg.value', 'special_formatting.צבע טקסט 3.arg.value'], 'Qccolor4': ['special_formatting.טעקסט קאליר 4.arg.value', 'special_formatting.צבע טקסט 4.arg.value'], 'Qccolor5': ['special_formatting.טעקסט קאליר 5.arg.value', 'special_formatting.צבע טקסט 5.arg.value'], 'Qccolor6': ['special_formatting.טעקסט קאליר 6.arg.value', 'special_formatting.צבע טקסט 6.arg.value']}


def _is_hebrew_character(value: str) -> bool:
    # A Hebrew combining mark from AltGr+digit is not a shortcut letter.
    return len(value) == 1 and "\u05d0" <= value <= "\u05ea"


def _hebrew_character_from_event(event) -> str:
    # אישיו #400: משתמשים קודם בטקסט הסמנטי של Qt, כי הוא משקף את שפת המקלדת הפעילה.
    text = str(event.text() or "")
    if _is_hebrew_character(text):
        return text

    # אישיו #400: בצירוף Ctrl/Alt Windows עלול לרוקן את event.text; ממירים לפי פריסת הקלט הפעילה.
    if sys.platform != "win32":
        return ""
    try:
        virtual_key = int(event.nativeVirtualKey())
        scan_code = int(event.nativeScanCode())
        if not virtual_key:
            return ""
        keyboard_state = (ctypes.c_ubyte * 256)()
        # Hebrew Shift emits Latin capitals on Windows. Resolve the base letter
        # in the active layout; Shift is retained separately in the shortcut.
        user32 = ctypes.windll.user32
        layout = user32.GetKeyboardLayout(0)
        buffer = ctypes.create_unicode_buffer(8)
        count = user32.ToUnicodeEx(
            virtual_key,
            scan_code,
            keyboard_state,
            buffer,
            len(buffer),
            0,
            layout,
        )
        if count > 0 and _is_hebrew_character(buffer.value[:count][0]):
            return buffer.value[:count][0]
    except Exception:
        return ""
    return ""

def _get_nested_config(config, key_path, default=None):
    keys = key_path.split('.')
    val = config
    try:
        for key in keys:
            val = val[key]
        return val
    except (KeyError, TypeError):
        return default

def _set_nested_config(config, key_path, value):
    keys = key_path.split('.')
    d = config
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value

def get_keys_from_tab(tab_index):
    """ברענגט צוריק אלע קיצורים אין א באזונדערן טאב."""
    keys = set()
    for _tab_name, tab_data in UI_STRUCTURE.items():
        if tab_data['index'] == tab_index:
            for _group_name, group_content in tab_data['groups'].items():
                if isinstance(group_content[1], dict):
                    keys.update(group_content[1].keys())
                elif isinstance(group_content[1], list):
                    for item in group_content[1]:
                        if item.get('type') == 'shortcut':
                            keys.add(item['key'])
                        elif 'key_shortcut' in item:
                            keys.add(item['key_shortcut'])
    return keys

def get_all_addon_keys():
    keys = set()
    for tab in UI_STRUCTURE.values():
        for _group_name, group_content in tab['groups'].items():
            if isinstance(group_content[1], dict):
                keys.update(group_content[1].keys())
            elif isinstance(group_content[1], list):
                for item in group_content[1]:
                    if 'key_color' in item:
                        keys.add(item['key_color'])
                    if 'key_shortcut' in item:
                        keys.add(item['key_shortcut'])
                    if 'key' in item:
                        keys.add(item['key'])
    return keys

def load_all_configs(use_temp=False, temp_configs=None):
    config = {}

    main_conf = temp_configs.get('main', {}) if use_temp and temp_configs else mw.addonManager.getConfig(__name__) or {}

    all_keys = get_all_addon_keys()

    for key in all_keys:
        if key in main_conf:
            config[key] = main_conf[key]
        elif key in DEFAULT_CONFIGS:
            config[key] = DEFAULT_CONFIGS[key]
        else:
            config[key] = ""

    color_keys = normalize_color_shortcut_rows(main_conf.get('keys', []), expected_rows=6)
    config['keys'] = color_keys

    for addon_id, key_map in ADDON_CONFIG_MAP.items():
        try:
            if use_temp and temp_configs:
                addon_conf = temp_configs.get(addon_id, {})
            else:
                addon_conf = mw.addonManager.getConfig(addon_id)
            if not addon_conf:
                continue

            if addon_id == 'edit-field-review' and not use_temp:
                raw = mw.addonManager.addonMeta(addon_id).get('config', {}) or {}
                if isinstance(raw, dict):
                    addon_conf = copy.deepcopy(addon_conf)
                    for active_path, target_key in key_map.items():
                        if _get_nested_config(raw, active_path) is not None:
                            continue
                        for old_path in EDIT_FIELD_REVIEW_LEGACY_PATHS.get(target_key, []):
                            old_value = _get_nested_config(raw, old_path)
                            if old_value is not None:
                                _set_nested_config(addon_conf, active_path, old_value)
                                break

            for source_path, target_key in key_map.items():
                val = _get_nested_config(addon_conf, source_path)
                if val is not None:
                    config[target_key] = val
            # #138 — אם קונפיג קיים עדיין מחזיק שמות עבריים ישנים, מציגים אותם ב-shortcut-manager ואז השמירה הבאה תמיר למפתחות האנגליים הפעילים.
            if addon_id == 'edit-field-review':
                for target_key, legacy_paths in EDIT_FIELD_REVIEW_LEGACY_PATHS.items():
                    if config.get(target_key):
                        continue
                    for legacy_path in legacy_paths:
                        legacy_val = _get_nested_config(addon_conf, legacy_path)
                        if legacy_val:
                            config[target_key] = legacy_val
                            break
        except Exception:
            pass

    # #138 — ערכי legacy עם underscore משמשים רק fallback; הם לא דורסים את קונפיג edit-field-review הפעיל שנקרא מהמפתחות האנגליים.
    for target_key, legacy_key in LEGACY_MAIN_KEY_ALIASES.items():
        legacy_value = main_conf.get(legacy_key)
        if target_key not in main_conf and legacy_value and not config.get(target_key):
            config[target_key] = legacy_value

    if len(color_keys) == 6:
        for i in range(6):
            config[f'fore_color{i+1}'] = color_keys[i][0]
            config[f'color{i+1}_shortcut'] = color_keys[i][1]

    return config

class GetShortcut(QDialog):
    def __init__(self, parent, button_variable, conflict_list, tab_index):
        QDialog.__init__(self, parent=parent)
        self.parent = parent
        self.button_variable = button_variable
        self.conflict_list = conflict_list
        self.tab_index = tab_index # שומר את האינדקס של הטאב הנוכחי
        self.active, self.ctrl, self.alt, self.shift, self.extra = 0, False, False, False, None
        self.f_keys = {f"f{i}": False for i in range(1, 13)}

        text = QLabel('<div style="font-size: 15px">דריקט די געוואונטשענע צוזאמשטעל פון קנעפלעך...</div>')
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(text)
        # אישיו #400: מאפשרים לבטל את הקיצור הנוכחי ישירות מחלונית קליטת הקיצור.
        clear_button = QPushButton("נעם אוועק דעם ביז יעצטיגן קיצור", self)
        clear_button.clicked.connect(self._clear_current_shortcut)
        mainLayout.addWidget(clear_button)
        self.setLayout(mainLayout)
        self.setWindowTitle('אויפנעמען קיצור קנעפלעך')

    def _clear_current_shortcut(self):
        # אישיו #400: מחיקת קיצור מעדכנת את הגדרות המסך וסוגרת את החלונית מיד.
        self.parent.update_shortcut(self.button_variable, "")
        self.accept()

    # #463 — ניסיון שנדחה חייב להתחיל מחדש ללא Shift/מקשים שנשמרו מהניסיון הקודם.
    def _reset_capture(self):
        self.active, self.ctrl, self.alt, self.shift, self.extra = 0, False, False, False, None
        self.f_keys = {f"f{i}": False for i in range(1, 13)}

    def keyPressEvent(self, evt):
        # #463 — גם אחרי שחרור רגיל של כל המקשים מתחיל צירוף חדש ונקי.
        if self.active <= 0:
            self._reset_capture()
        self.active += 1
        key = evt.key()
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            self.f_keys[f"f{key - Qt.Key.Key_F1 + 1}"] = True
        elif key == Qt.Key.Key_Control:
            self.ctrl = True
        elif key == Qt.Key.Key_Alt:
            self.alt = True
        elif key == Qt.Key.Key_Shift:
            self.shift = True
        elif key in (Qt.Key.Key_Less, Qt.Key.Key_Greater):
            # #391 — בפריסת עברית Windows עשוי למפות את המקשים הפיזיים של
            # פסיק/נקודה בכיוון הפוך. Qt כבר מספק כאן את הסמל הסמנטי שנלחץ,
            # ולכן הוא גובר על טבלת ה-VK הפיזית ומונע החלפה בין < לבין >.
            self.extra = "<" if key == Qt.Key.Key_Less else ">"
        elif evt.nativeVirtualKey() in WINDOWS_VK_KEY_MAP:
            # #359 — נבדק לפני chr(key)/הענף האחר: מקלדת עברית עלולה להפיק תו לגמרי
            # שונה מהמקש הפיזי שנלחץ (למשל Ctrl+Shift+[ נקלט בתור '}'), בין אם evt.key()
            # נופל בטווח ה-ASCII הרגיל (כמו במקרה הזה) ובין אם לא (ספרות עם ניקוד).
            # ה-virtual key הפיזי של Windows מזהה את מיקום המקש בלי תלות בשפת הקלט.
            key_map = WINDOWS_SHIFTED_VK_KEY_MAP if self.shift else WINDOWS_VK_KEY_MAP
            self.extra = key_map.get(
                evt.nativeVirtualKey(), WINDOWS_VK_KEY_MAP[evt.nativeVirtualKey()]
            )
        elif key > 30 and key < 127:
            self.extra = chr(key)
        else:
            if key not in [Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backspace, Qt.Key.Key_Enter, Qt.Key.Key_Return,
                           Qt.Key.Key_Insert, Qt.Key.Key_Delete, Qt.Key.Key_Pause, Qt.Key.Key_Home, Qt.Key.Key_Left,
                           Qt.Key.Key_Up, Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
                           Qt.Key.Key_CapsLock, Qt.Key.Key_NumLock]:
                self.extra = QKeySequence(key).toString()

        # אישיו #400: האות שהמקלדת הפיקה גוברת על מיפוי המקש הפיזי באנגלית.
        hebrew_character = _hebrew_character_from_event(evt)
        if hebrew_character:
            self.extra = hebrew_character

    def keyReleaseEvent(self, evt):
        # #463 — שחרור מאוחר אחרי הודעת שגיאה אינו ניסיון קיצור חדש.
        if self.active <= 0:
            return
        self.active -= 1
        if self.active > 0:
            return

        # אישיו #400: אות עברית נשמרת כאות עברית, ולכן אין צורך להחליף שפת מקלדת להפעלת הקיצור.
        if self.extra and self.extra in HEBREW_TO_LATIN_KEY:
            self.extra = HEBREW_TO_LATIN_KEY[self.extra]

        # #359 — רשת ביטחון: אם בכל זאת נקלט תו לא-ASCII שלא זוהה (למשל ניקוד ממקלדת
        # עברית בצירוף שלא כוסה למעלה), מסרבים לשמור קיצור משובש במקום להניח לו לעבור
        # בשקט ולהתנגש/לא לעבוד בכלל מבלי שהמשתמש יבין למה.
        if self.extra and not (self.extra.isascii() or self.extra in HEBREW_TO_LATIN_KEY):
            showInfo(
                "די העברעאישע קלאוויאטור האט ארויסגעגעבן א צייכן וואס מען קען נישט אפזיכערן אלס א גילטיגן קיצור. "
                "בייט צו אן ענגלישער קלאוויאטור און פרובירט נאכאמאל.",
                title="אומגילטיגער קיצור",
                parent=self,
            )
            self._reset_capture()
            return

        combination_parts = []
        if self.ctrl:
            combination_parts.append("Ctrl")
        if self.shift:
            combination_parts.append("Shift")
        if self.alt:
            combination_parts.append("Alt")
        for i in range(1, 13):
            if self.f_keys[f"f{i}"]:
                combination_parts.append(f"F{i}")
        if self.extra:
            combination_parts.append(self.extra)

        combination = "+".join(combination_parts)
        if _navigation_shortcut_has_shift(self.button_variable, combination):
            showInfo("ביים איבערגיין צום ערשטן אדער לעצטן קארטל Shift איז פארהאלטן צום פארברייטערן די אויסוואל. קלייבט אויס א קיצור אן Shift.", parent=self)
            self._reset_capture()
            return

        if not combination or (not any(self.f_keys.values()) and not self.extra):
            showInfo("דער קנעפל קען נישט ווערן גענוצט אלס קיצור. פרובירט אן אנדערע אפציע.", title="קיצור קנעפל", parent=self)
            self._reset_capture()
            return

        # #359 — רשת ביטחון אחרונה: בדיקה שהרצף בפועל ניתן לפרסור ע"י Qt לפני השמירה.
        # ללא זה, קיצור שנכשל בפרסור (למשל תו לא חוקי) נשמר "בהצלחה" אבל אף פעם לא
        # נרשם בפועל כ-QShortcut (keys="" מדולג בשקט ב-editor.addButton) — המשתמש
        # רואה שהקיצור "נשמר" אך הוא פשוט לא עובד, בלי שום הודעת שגיאה.
        if QKeySequence(combination).toString() == "" and not any(self.f_keys.values()):
            showInfo(
                f"די צוזאמשטעל '{combination}' איז נישט קיין גילטיגער קיצור און מען קען זי נישט אפזיכערן. פרובירט אן אנדערע צוזאמשטעל.",
                title="אומגילטיגער קיצור",
                parent=self,
            )
            self._reset_capture()
            return

        # #364 — Ctrl+Shift+: opens Anki's debug console.  The physical semicolon key
        # is reported as ';' while Shift turns it into ':', so block both
        # textual representations instead of allowing the reserved shortcut.
        if self.ctrl and self.shift and not self.alt and self.extra in {";", ":"}:
            showInfo(
                "די צוזאמשטעל Ctrl+Shift+: קען נישט ווערן גענוצט אלס קיצור.",
                title="פארהאלטענער קיצור",
                parent=self,
            )
            self._reset_capture()
            return

        # #138 — ההגנה חלה על כל קיצור בשתי לשוניות העריכה, ולא רק על רשימת
        # פעולות עיצוב חלקית. Shift+אות עדיין נחשב הקלדת אות גדולה ולכן נחסם.
        if self.tab_index in (2, 3) and _unsafe_editing_letter_shortcut(combination):
            showInfo(
                "מען קען נישט איינשטעלן אינעם רעדאקטירער א קיצור מיט בלויז אן אות אדער Shift+אן אות, "
                "ווייל דער אות דארף זיך שרייבן אינעם פעלד. לייגט צו Ctrl אדער Alt צום קיצור.",
                title="אומגילטיגער קיצור",
                parent=self,
            )
            self._reset_capture()
            return

        # #364 — בחירה מחדש של הקיצור שכבר שייך לפעולה הנוכחית אינה
        # התנגשות. ה-QShortcut החי עדיין מחזיק את הערך הישן עד לחיצה על
        # "אישור", ולכן סריקת החלונות הייתה מזהה בטעות את הפעולה מול עצמה.
        current_combination = str(
            self.parent.config_data.get(self.button_variable, "") or ""
        )
        if (
            QKeySequence(current_combination).toString().upper()
            == QKeySequence(combination).toString().upper()
        ):
            self.close()
            return

        # #364 — אוספים את כל סוגי ההתנגשות ושואלים פעם אחת אם להגדיר בכל זאת.
        conflict_reasons = []
        current_conflicts = set(self.conflict_list)
        if hasattr(self.parent, "_conflict_values_for_tab"):
            # #364 — הקונפיגורציה נקראת מחדש בכל ניסיון, כך ששינוי קיצור של
            # AnkiQt/תוסף אחר בזמן שהדיאלוג פתוח נלקח בחשבון לפני OK.
            current_conflicts.update(
                self.parent._conflict_values_for_tab(self.tab_index, self.button_variable)
            )
        warned_about_conflict = combination.upper() in current_conflicts
        if warned_about_conflict:
            conflict_reasons.append("דער קיצור ווערט שוין גענוצט אויף דעם עקראן אדער אויפן הויפט עקראן וואס האט אן השפעה דערויף")

        # 1ב. #359 — בדיקת התנגשות בפועל: הרשימה הסטטית למעלה לא תפסה את ההתנגשות
        # המקורית (Ctrl+0 בין "הגדר דגל 0" לפתיחת העורך המתקדם) כי הם משתייכים לשני
        # תוספים שונים ולא מופיעים יחד באותה רשימה. במקום זאת סורקים בפועל אילו
        # QShortcut רשומים כרגע בחלונות הרלוונטיים לקטגוריה הזו (ראו _TAB_RELEVANT_WINDOWS)
        # ומתריעים אם הצירוף כבר תפוס — אוטומטית, בכל הגדרת קיצור, בלי כפתור נפרד.
        if hasattr(self.parent, "_live_shortcuts_for_tab"):
            combo_upper = combination.upper()
            for live_shortcut in self.parent._live_shortcuts_for_tab(self.tab_index):
                key_str = live_shortcut.key().toString()
                if key_str and key_str.upper() == combo_upper and not warned_about_conflict:
                    owner = live_shortcut.parent()
                    owner_name = type(owner).__name__ if owner else "?"
                    conflict_reasons.append(
                        f"דער קיצור איז שוין טאקע איינגעשריבן אויף {owner_name}"
                    )
                    break

        # 2. Ctrl+מספר שמור לבחירת שדה בעורך Anki. הדבר נכון גם בעורך הרגיל
        # וגם בעורך שבתוך הדפדפן, ולכן אין להציג את הצירוף כאילו הוא פנוי.
        if self.tab_index in (3, 4):
            is_ctrl_num = (self.ctrl and self.extra and self.extra in "0123456789"
                           and not self.alt and not self.shift)
            if is_ctrl_num:
                conflict_reasons.append(
                    "Ctrl+מיט א נומער ווערט גענוצט דורך Anki אויסצוקלייבן א פעלד אינעם רעדאקטירער און איז נישט פריי פאר א קיצור"
                )

        # #364 — תשובת "כן" מאפשרת לשמור במכוון; "לא" מחזירה לחלון הקליטה בלי שינוי.
        if conflict_reasons:
            details = "\n• ".join(conflict_reasons)
            if not askUser(
                f"מען האט געפונען א קאנפליקט פאר '{combination}':\n• {details}\n\n"
                "איינשטעלן דעם קיצור דאך?",
                parent=self,
                # #364 — אותה תיבת אישור משמשת גם להתנגשות שנמצאה בזמן אמת.
                title="א קאנפליקט אין דער אמתן",
            ):
                self._reset_capture()
                return

        self.parent.update_shortcut(self.button_variable, combination)
        self.close()

class SettingsMenu(QDialog):
    def __init__(self, parent=None, use_temp=False, temp_data=None):
        super().__init__(parent)
        self.addon_path = dirname(__file__)
        self.config_data = load_all_configs(use_temp, temp_data)
        # #364 — קיצורי QShortcut החיים עדיין מכילים את הערך הישן עד לחיצה על
        # אישור. עוקבים אחר הערכים שהוחלפו כדי שלא ידווחו כהתנגשות מיושנת.
        self._stale_live_shortcut_values = set()
        self.ui_widgets = {}
        self._init_ui()

    def _create_widget_for_setting(self, group_layout, setting_data):
        if isinstance(setting_data, dict):
            if setting_data.get('type') == 'checkbox':
                self._create_checkbox_widget(group_layout, setting_data['key'], setting_data['label'])
            else:
                self._create_shortcut_widget(group_layout, setting_data['key'], setting_data['label'])
        elif isinstance(setting_data, list):
            for item in setting_data:
                if item.get('type') == 'checkbox':
                    self._create_checkbox_widget(group_layout, item['key'], item['label'])
                elif 'key_color' in item:
                    self._create_color_widget(group_layout, item['key_color'], item['key_shortcut'], item['label'])

    def _create_shortcut_widget(self, parent_layout, key, label):
        layout = QHBoxLayout()
        qlabel = QLabel(label)
        # #138 — reserve label space while keeping shortcut buttons compact.
        qlabel.setMinimumWidth(220)
        button = QPushButton()
        # #138 — Qt includes font metrics, DPI and style padding in sizeHint().
        button.setText("Ctrl+Shift+Alt+W")
        # #138 — add one third to the font-aware width, as requested.
        button.setFixedWidth((button.sizeHint().width() * 4 + 2) // 3)
        button.clicked.connect(lambda _, k=key: self.show_get_shortcut_dialog(k))
        layout.addWidget(qlabel)
        layout.addStretch()
        layout.addWidget(button)
        parent_layout.addLayout(layout)
        self.ui_widgets[key] = {'widget': button, 'type': 'shortcut'}

    def _create_checkbox_widget(self, parent_layout, key, label):
        layout = QHBoxLayout()
        qlabel = QLabel(label)
        checkbox = QCheckBox()
        # תמיכה ב-State Changed שממיר ל-Y/N
        checkbox.stateChanged.connect(lambda state, k=key: self.update_config_bool(k, state))
        layout.addWidget(qlabel)
        layout.addStretch()
        layout.addWidget(checkbox)
        parent_layout.addLayout(layout)
        self.ui_widgets[key] = {'widget': checkbox, 'type': 'checkbox'}

    def _create_color_widget(self, parent_layout, key_color, key_shortcut, label):
        layout = QHBoxLayout()
        qlabel = QLabel(label)
        qlabel.setFixedWidth(125)
        color_button = QPushButton()
        color_button.setFixedWidth(150)
        color_button.clicked.connect(lambda _, k=key_color, btn=color_button: self.show_get_color_dialog(k, btn))
        shortcut_button = QPushButton()
        # #138 — same compact, font-aware width for color shortcuts.
        shortcut_button.setText("Ctrl+Shift+Alt+W")
        # #138 — color shortcut buttons use the same one-third extra width.
        shortcut_button.setFixedWidth((shortcut_button.sizeHint().width() * 4 + 2) // 3)
        shortcut_button.clicked.connect(lambda _, k=key_shortcut: self.show_get_shortcut_dialog(k))
        layout.addWidget(qlabel)
        layout.addStretch()
        layout.addWidget(color_button)
        layout.addWidget(shortcut_button)
        parent_layout.addLayout(layout)
        self.ui_widgets[key_color] = {'widget': color_button, 'type': 'color_display'}
        self.ui_widgets[key_shortcut] = {'widget': shortcut_button, 'type': 'shortcut'}

    def _init_ui(self):
        self.setWindowTitle("קיצור קנעפל איינשטעלונגען")
        self.setWindowIcon(QIcon(join(self.addon_path, 'images', 'icon.png')))
        # #138 — compact buttons no longer require the previous wide dialog.
        self.resize(660, 620)
        vbox = QVBoxLayout(self)
        vbox.addWidget(QLabel("● פארן איינשטעלן דעם קיצור, קוקט צי די קלאוויאטור איז אויף העברעאיש אדער ענגליש."))

        self.tabs = QTabWidget()
        sorted_tabs = sorted(UI_STRUCTURE.items(), key=lambda item: item[1]['index'])

        for _tab_key, tab_data in sorted_tabs:
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setMinimumWidth(600)
            scroll_area.setFixedHeight(500)

            tab_content_widget = QWidget()
            tab_layout = QVBoxLayout(tab_content_widget)

            for group_title, settings_map in tab_data['groups'].values():
                group_box = QGroupBox(group_title)
                group_layout = QVBoxLayout(group_box)
                if isinstance(settings_map, dict):
                    for key, label in settings_map.items():
                        self._create_widget_for_setting(group_layout, {'key': key, 'label': label})
                elif isinstance(settings_map, list):
                     self._create_widget_for_setting(group_layout, settings_map)

                tab_layout.addWidget(group_box)

            tab_layout.addStretch()
            scroll_area.setWidget(tab_content_widget)
            self.tabs.addTab(scroll_area, tab_data['title'])

        vbox.addWidget(self.tabs)
        self._add_action_buttons(vbox)
        self._update_all_ui_elements()

    def _add_action_buttons(self, layout):
        button_box = QHBoxLayout()
        restore_btn = QPushButton("&ברענג צוריק ברירת מחדל איינשטעלונגען")
        restore_btn.clicked.connect(self.on_restore_defaults)
        save_btn = QPushButton("&מאך א גיבוי פון די איינשטעלונגען")
        save_btn.clicked.connect(self.on_save_settings)
        load_btn = QPushButton("&ברענג צוריק פון א גיבוי")
        load_btn.clicked.connect(self.on_load_settings)
        accept_btn = QPushButton("&באשטעטיגן")
        accept_btn.clicked.connect(self.on_apply)
        reject_btn = QPushButton("&אפזאגן")
        reject_btn.clicked.connect(self.reject)

        button_box.addWidget(restore_btn)
        button_box.addWidget(save_btn)
        button_box.addWidget(load_btn)
        button_box.addStretch()
        button_box.addWidget(accept_btn)
        button_box.addWidget(reject_btn)
        layout.addLayout(button_box)

    # #359 — לכל טאב/קטגוריה, אילו חלונות פתוחים כרגע רלוונטיים לבדיקת התנגשות בפועל.
    # מסך ראשי/מבחן/עריכה במבחן/הגדרות כלליות חיים כולם בתוך אותו חלון ראשי (mw) —
    # אין חלון Qt נפרד לכל אחד מהם (זו בדיוק הסיבה שההתנגשות בין "הגדר דגל 0" לעורך
    # המתקדם בכלל קרתה: שניהם רשומים תחת mw). "עורך" עלול לרוץ גם בתוך מבחן (mw),
    # גם בהוספת שאלה וגם בדפדוף — לכן נבדק מול שלושתם. "דפדוף" נבדק מול חלון הדפדוף.
    _TAB_RELEVANT_WINDOWS = {
        0: ("mw",), 1: ("mw",), 2: ("mw",), 5: ("mw",),
        3: ("mw", "Browser", "AddCards"),
        4: ("mw", "Browser"),
    }

    def _live_shortcuts_for_tab(self, tab_index):
        from aqt.qt import QShortcut

        windows = [mw]
        for name in self._TAB_RELEVANT_WINDOWS.get(tab_index, ()):
            if name == "mw":
                continue
            with contextlib.suppress(Exception):
                entry = aqt_dialogs._dialogs.get(name)
                if entry and entry[1] is not None:
                    windows.append(entry[1])

        seen_ids = set()
        shortcuts = []
        for window in windows:
            if window is None or id(window) in seen_ids:
                continue
            seen_ids.add(id(window))
            # #364 — הרשימה הזמנית בחלון היא מקור האמת מיד לאחר שינוי, גם
            # לפני שהשינויים נשמרו וה-QShortcut של AnkiQt נרשם מחדש.
            shortcuts.extend(
                shortcut
                for shortcut in window.findChildren(QShortcut)
                if shortcut.key().toString().upper()
                not in self._stale_live_shortcut_values
            )
        return shortcuts

    def _update_all_ui_elements(self):
        for key, widget_info in self.ui_widgets.items():
            value = self.config_data.get(key, "")
            widget = widget_info['widget']
            if widget_info['type'] == 'shortcut':
                # #138 — the shortcut itself gets the available width; instructions
                # belong in a tooltip, especially under Windows display scaling.
                widget.setText(str(value) if value else "אן א קיצור")
                # #138 — retain the uniform width set from Ctrl+Shift+Alt+W
                # plus one third at creation, regardless of the current shortcut.
                widget.setToolTip(f"דריקט צו טוישן דעם קיצור קנעפל: {value or 'אן א קיצור'}")
            elif widget_info['type'] == 'color_display':
                self._update_button_color(widget, value)
            elif widget_info['type'] == 'checkbox':
                # תיקון: בדיקה מול "Y" במקום המרה לבוליאני פשוט
                is_checked = (str(value).upper() == "Y")
                widget.setChecked(is_checked)

    def _update_button_color(self, button, color_str):
        if not isinstance(color_str, str) or not color_str:
            return
        pixmap = QPixmap(95, 18)
        qcolor = QColor()
        qcolor.setNamedColor(color_str)
        pixmap.fill(qcolor)
        button.setIcon(QIcon(pixmap))
        button.setIconSize(QSize(95, 18))

    def update_config_bool(self, key, state):
        # תיקון: שמירה כ-Y/N כדי למנוע AttributeError
        self.config_data[key] = "Y" if state == Qt.CheckState.Checked.value else "N"

    def _conflict_values_for_tab(self, current_tab_idx, key):
        """ברענגט צוריק די ווערטן וואס ווארטן יעצט, אן דעם snapshot אלטן פון ווען דער פענסטער האט זיך געעפנט."""
        conflict_keys = set(get_keys_from_tab(current_tab_idx))

        if current_tab_idx == 0:
            if key in GLOBAL_MAIN_KEYS:
                conflict_keys.update(get_keys_from_tab(1))
                conflict_keys.update(get_keys_from_tab(2))
        elif current_tab_idx in [1, 2]:
            conflict_keys.update(get_keys_from_tab(1))
            conflict_keys.update(get_keys_from_tab(2))
            for glob_key in GLOBAL_MAIN_KEYS:
                value = self.config_data.get(glob_key)
                if value:
                    conflict_keys.add(value)

        # Editors can live inside the reviewer and Browser, and their window
        # shortcuts compete even when their controls do not have focus.
        if current_tab_idx in (1, 2, 3, 4):
            conflict_keys.update(get_keys_from_tab(3))
        if current_tab_idx == 3:
            conflict_keys.update(get_keys_from_tab(1))
            conflict_keys.update(get_keys_from_tab(2))
            conflict_keys.update(get_keys_from_tab(4))
        if current_tab_idx in (1, 2, 3):
            conflict_keys.update(get_keys_from_tab(0))
        values = set()
        if current_tab_idx == 2:
            # Inline cloze/image shortcuts are not rows in this dialog, but
            # compete inside the same WebEngine key handler.
            inline = mw.addonManager.getConfig('edit-field-review') or {}
            values.update(str(value).upper() for value in inline.get('shortcuts', {}).values() if value)
            conflict_keys.update(get_keys_from_tab(0))
        for conflict_key in conflict_keys:
            if conflict_key == key:
                continue
            value = self.config_data.get(conflict_key, conflict_key)
            if value and isinstance(value, str):
                values.add(value.upper())
                if conflict_key in ('window_browser first card', 'window_browser last card'):
                    values.add('SHIFT+' + value.upper())
        return values

    def show_get_shortcut_dialog(self, key):
        current_tab_idx = self.tabs.currentIndex()
        # #364 — בפתיחת חלון ההגדרות נבנה snapshot טרי; בזמן הקליטה הדיאלוג
        # מרענן אותו שוב דרך _conflict_values_for_tab.
        conflict_list = list(self._conflict_values_for_tab(current_tab_idx, key))

        # העברת אינדקס הטאב לדיאלוג (בשביל בדיקת דפדפן ספציפית)
        dialog = GetShortcut(self, key, conflict_list, current_tab_idx)
        dialog.exec()

    def show_get_color_dialog(self, key, button):
        current_color_str = self.config_data.get(key, "#000000")
        qcolor = QColor()
        qcolor.setNamedColor(current_color_str)

        new_color = QColorDialog.getColor(qcolor, self, "קלייבט אויס א קאליר")
        if new_color.isValid():
            self.config_data[key] = new_color.name()
            self._update_button_color(button, new_color.name())

    def update_shortcut(self, key, new_shortcut):
        # #364 — הערך הישן הופך stale מיד, כך שבחירת הקיצור הבא באותו חלון
        # כבר לא תציג התנגשות מול AnkiQt על קיצור שהמשתמש החליף.
        old_shortcut = str(self.config_data.get(key, "") or "").upper()
        if old_shortcut:
            self._stale_live_shortcut_values.add(old_shortcut)
        self.config_data[key] = new_shortcut
        self._update_all_ui_elements()

    def on_apply(self):
        invalid_navigation = [key for key in ("window_browser first card", "window_browser last card")
                              if _navigation_shortcut_has_shift(key, self.config_data.get(key, ""))]
        if invalid_navigation:
            showInfo("מען דארף אויסקלייבן א קיצור אן Shift צום ערשטן/לעצטן קארטל. צולייגן Shift צום קיצור וועט פארברייטערן די אויסוואל.", parent=self)
            return
        # #138 — טעינת גיבוי או config ישן יכולה לעקוף את GetShortcut; לפני
        # כתיבה חוסמים גם שם אות/Shift+אות בכל קיצורי שתי לשוניות העריכה.
        invalid_editing_shortcuts = []
        for tab_index in (2, 3):
            for key in get_keys_from_tab(tab_index):
                shortcut = self.config_data.get(key, "")
                if _unsafe_editing_letter_shortcut(shortcut):
                    invalid_editing_shortcuts.append(f"{key}: {shortcut}")
        if invalid_editing_shortcuts:
            showInfo(
                "מען קען נישט אפזיכערן אות קיצורים אן Ctrl אדער Alt אינעם רעדאקטירער אדער ביים רעדאקטירן אין א חזרה:\n"
                + "\n".join(invalid_editing_shortcuts),
                title="אומגילטיגער קיצור",
                parent=self,
            )
            return

        configs_to_write = {addon_id: mw.addonManager.getConfig(addon_id) or {} for addon_id in ADDON_CONFIG_MAP}
        configs_to_write['main'] = mw.addonManager.getConfig(__name__) or {}

        main_keys = get_all_addon_keys()
        for key in main_keys:
            if key in self.config_data:
                configs_to_write['main'][key] = self.config_data[key]

        # #138 — משמרים תאימות זמנית גם למפתחות underscore כדי שהגדרות קיימות לא יישברו בין גרסאות.
        for target_key, legacy_key in LEGACY_MAIN_KEY_ALIASES.items():
            if target_key in self.config_data:
                configs_to_write['main'][legacy_key] = self.config_data[target_key]

        color_array = []
        for i in range(1, 7):
            color = self.config_data.get(f'fore_color{i}', '#000000')
            shortcut = self.config_data.get(f'color{i}_shortcut', '')
            color_array.append([color, shortcut])
        configs_to_write['main']['keys'] = color_array

        for addon_id, key_map in ADDON_CONFIG_MAP.items():
            for source_path, target_key in key_map.items():
                if target_key in self.config_data:
                    _set_nested_config(configs_to_write[addon_id], source_path, self.config_data[target_key])

        formatting = configs_to_write['edit-field-review'].setdefault('special_formatting', {})
        for i in range(1, 7):
            row = formatting.setdefault(f'טעקסט קאליר {i}', {})
            row['command'] = 'foreColor'
            row.setdefault('enabled', True)
            arg = row.setdefault('arg', {})
            arg['type'] = 'color'
            if not arg.get('value'):
                arg['value'] = '#000000'

        mw.addonManager.writeConfig(__name__, configs_to_write['main'])
        for addon_id, conf in configs_to_write.items():
            if addon_id != 'main':
                with contextlib.suppress(Exception):
                    mw.addonManager.writeConfig(addon_id, conf)

        # #269 — מפעילים live-reload גם ב-edit-field-review, כדי שקיצורי פריסטים שנשמרו מכאן יחולו מיד בסרגל העריכה במבחן.
        import sys as _sys
        for _addon_id in ('1966460736', 'edit-field-review'):
            for _mod_name, _mod in list(_sys.modules.items()):
                if not _mod_name or not isinstance(_mod_name, str):
                    continue
                _mod_file = os.path.normcase(str(getattr(_mod, '__file__', '') or '')).replace('\\', '/')
                if _addon_id not in _mod_name and _addon_id not in _mod_file:
                    continue
                _reload = getattr(_mod, '_reload_config', None)
                if callable(_reload):
                    with contextlib.suppress(Exception):
                        _reload()

        try:
            custom_shortcuts.refresh_shortcuts()
            showInfo("די טוישן זענען מיט הצלחה אפגעזיכערט און אריינגעשטעלט געווארן.", title="קיצור קנעפל איינשטעלונגען")
        except Exception as exc:
            show_failure("די קיצור איינשטעלונגען זענען אפגעזיכערט, אבער נישט אריינגעשטעלט אין די אפענע פענסטער. מען דארף אנהייבן אנקי פון פריש כדי זיי אריינצושטעלן.", exc, parent=self)

        self.accept()

    def on_restore_defaults(self):
        if askUser("זענט איר זיכער אז איר ווילט צוריקברענגען די ברירת מחדל איינשטעלונגען?", title="צוריקברענגען ברירת מחדל"):
            defaults = {}
            config_path = join(self.addon_path, "config.json")
            try:
                with open(config_path, encoding="utf-8") as f:
                    defaults = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                defaults = {}
            temp_configs = {'main': defaults}
            for addon_id in ADDON_CONFIG_MAP:
                temp_configs[addon_id] = _load_addon_default_config(addon_id)
            self.config_data = load_all_configs(use_temp=True, temp_configs=temp_configs)
            self._update_all_ui_elements()
            showInfo("די ברירת מחדל איינשטעלונגען זענען צוריקגעברענגט (נאך נישט אפגעזיכערט). דריקט 'באשטעטיגן' צו אפזיכערן.")

    def on_save_settings(self):
        # #255 — גיבוי הגדרות משתמש חייב לייבא datetime לפני בניית שם הקובץ.
        now = datetime.now().strftime('%H-%M-%S')
        today = GregorianDate.today().to_heb().hebrew_date_string().replace('"', '')
        filename = f"גיבוי פון קיצור קנעפלעך {today} {now}.json"

        path = getSaveFile(self, "זיכער אפ א גיבוי", "export", "json", ".json", filename)
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            showInfo("דער גיבוי איז מיט הצלחה אפגעזיכערט.")
        except Exception as e:
            show_failure("דער קיצור גיבוי איז נישט אפגעזיכערט. קלייבט אויס אן אנדערן פאלדער און פרובירט נאכאמאל.", e, parent=self)

    def on_load_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "לאד א גיבוי", os.path.join(self.addon_path, "user_files"), "JSON Files (*.json)")
        if not path:
            return

        try:
            with open(path, encoding='utf-8') as f:
                loaded_data = json.load(f)

            if "tempconf1" in loaded_data:
                reply = askUser("מען האט דערקענט א גיבוי טעקע פון דער אלטער ווערסיע.\nאיבערבייטן און לאדענען אים?", title="דערקענט אן אלטע ווערסיע")
                if not reply:
                    return

                new_data = {}
                if "tempconf1" in loaded_data:
                    new_data.update(loaded_data["tempconf1"])

                legacy_map = {
                    "tempconf2": '444444441136455830', "tempconf3": '149564514', "tempconf4": '88ערוך שדה במהלך סקירה',
                    "tempconf5": '99תזמון_מחדש', "tempconf6": '1566569834', "tempconf8": 'CTRLF5_to_Refresh_the_Browser',
                    "tempconf9": '00000000הגדלת_גופן'
                }

                for temp_key, addon_id in legacy_map.items():
                    if temp_key in loaded_data and addon_id in ADDON_CONFIG_MAP:
                        legacy_conf = loaded_data[temp_key]
                        key_mapping = ADDON_CONFIG_MAP[addon_id]
                        for source_path, target_key in key_mapping.items():
                            val = _get_nested_config(legacy_conf, source_path)
                            if val is not None:
                                new_data[target_key] = val

                self.config_data.update(new_data)
            else:
                self.config_data.update(loaded_data)

            self._update_all_ui_elements()
            showInfo("די איינשטעלונגען זענען געלאדנט פונעם גיבוי. דריקט 'באשטעטיגן' כדי זיי אריינצושטעלן.")
        except Exception as e:
            show_failure("דער קיצור גיבוי איז נישט געלאדנט. קלייבט אויס א גילטיגע גיבוי טעקע און פרובירט נאכאמאל.", e, parent=self)


def open_settings_dialog():
    dialog = SettingsMenu()
    dialog.exec()

def setup_menu():
    action = QAction('איינשטעלן קיצור קנעפלעך', mw)
    # #317 — הוסר קיצור Shift+A קשיח שגרם ל-Qt ambiguous shortcut warning במהלך מבחן
    action.triggered.connect(open_settings_dialog)
    mw.form.menuCol.addAction(action)
    mw.form.menuCol.addSeparator()
    addon_path = dirname(__file__)
    action.setIcon(QIcon(join(addon_path, 'images', 'icon.png')))
    mw.addonManager.setConfigAction(__name__, lambda: True)

# Run setup
setup_menu()
