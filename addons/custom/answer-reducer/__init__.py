
# מזהה התוסף, צריך להיות ייחודי
ADDON_NAME = "PassFailHebrew"

import aqt.gui_hooks as gui_hooks
import aqt.preferences
from anki.cards import Card
from anki.hooks import wrap
from anki.utils import point_version
from aqt import mw
from aqt.qt import *
from aqt.reviewer import Reviewer

# --- פונקציות עזר לניהול הגדרות ---

def get_config():
    """לייענט דעם צוגאב איינשטעלונגען טעקע."""
    return mw.addonManager.getConfig(__name__)

def write_config(key, value):
    """שרייבט א טויש אינעם צוגאב איינשטעלונגען טעקע."""
    conf = get_config()
    conf[key] = value
    mw.addonManager.writeConfig(__name__, conf)

def is_addon_enabled():
    """קוקט צי דער צוגאב איז איינגעשאלטן אין די איינשטעלונגען."""
    config = get_config()
    return config.get("isEnabled", False)

# --- לוגיקת החלפת הכפתורים ---

def replace_buttons_hook(buttons_tuple: tuple, reviewer: Reviewer, card: Card) -> tuple:
    """
    די פונקציע ווערט אויפגערופן פארן ווייזן די ענטפער קנעפלעך.
    ווען דער צוגאב איז איינגעשאלטן, טוישט זי זיי צו צוויי קנעפלעך אויף יידיש.
    """
    if not is_addon_enabled():
        return buttons_tuple # אם התוסף כבוי, החזר את הכפתורים המקוריים

    fail_text = "איך ווייס נישט"
    pass_text = "איך ווייס"

    # כפתור 'לא עבר' תמיד מחזיר 1 (Again)
    # כפתור 'עבר' מחזיר את רמת הקלות של 'טוב' (Good), בדרך כלל 3
    return (
        (1, fail_text),
        (reviewer._defaultEase(), pass_text)
    )

def remap_ease_hook(ease_tuple: tuple, reviewer: Reviewer, card: Card) -> tuple:
    """
    באארבעט קלאוויאטור קיצורים (1, 2, 3, 4).
    ווען דער צוגאב איז איינגעשאלטן, וועט יעדע דרוק חוץ '1' זיך פירן ווי א דרוק אויף 'געקענט' (Good).
    """
    if not is_addon_enabled():
        return ease_tuple

    (should_continue, ease) = ease_tuple
    # אם המשתמש לחץ על 1, זה 'לא עבר'. כל דבר אחר הוא 'עבר'.
    if ease > 1:
        return (should_continue, reviewer._defaultEase())
    return ease_tuple


# --- הוספת אפשרות להגדרות של אנקי ---

def on_pref_checkbox_state_changed(state):
    """זיכערט אפ דעם באניצער נייע אויסוואל."""
    write_config("isEnabled", bool(state))

def add_addon_checkbox_to_preferences(preferences_dialog: aqt.preferences.Preferences):
    """לייגט צו א סימון קעסטל אינעם אנקי איינשטעלונגען פענסטער."""
    # יצירת תיבת הסימון
    checkbox = QCheckBox("ווייז נאר צוויי ענטפער קנעפלעך (געקענט/נישט געקענט)")
    checkbox.setChecked(is_addon_enabled())

    # חיבור הפעולה של שינוי מצב לפונקציה השומרת
    checkbox.stateChanged.connect(on_pref_checkbox_state_changed)

    # הוספת תיבת הסימון ללשונית "חזרה" בחלון ההגדרות
    preferences_dialog.form.verticalLayout_5.addWidget(checkbox)


# --- רישום הפונקציות לאנקי ---

def initialize():
    """די הויפט פונקציע וואס צינדט אן דעם צוגאב."""

    # הוספת ההגדרה לחלון ההגדרות של אנקי
    aqt.preferences.Preferences.setup_global = wrap(
        aqt.preferences.Preferences.setup_global,
        add_addon_checkbox_to_preferences,
        "after"
    )

    # הרצת ה-hooks שמחליפים את הכפתורים והתנהגות המקשים
    # משתמש ב-hooks החדשים אם גרסת אנקי תומכת
    if point_version() >= 31:
        gui_hooks.reviewer_will_init_answer_buttons.append(replace_buttons_hook)
    else:
        # תמיכה בגרסאות ישנות יותר
        Reviewer._answerButtonList = wrap(Reviewer._answerButtonList, lambda self, _old: replace_buttons_hook(_old(self), self, self.card), 'around')

    if point_version() >= 20:
        gui_hooks.reviewer_will_answer_card.append(remap_ease_hook)
    else:
        # תמיכה בגרסאות ישנות יותר
        def old_remap(self, ease, _old):
            if self.card:
                (_, new_ease) = remap_ease_hook((True, ease), self, self.card)
                return _old(self, new_ease)
            return _old(self, ease)
        Reviewer._answerCard = wrap(Reviewer._answerCard, old_remap, 'around')

# הפעלת התוסף
initialize()
