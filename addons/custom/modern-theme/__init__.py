import ctypes
import gc
import os
import sys
import time
from typing import Any


# פתיחת חלון קונסול לצורך debug בזמן פיתוח
# #346 — ctypes.windll קיים בווינדוס בלבד; במק ולינוקס הגישה אליו זורקת
# AttributeError וטעינת התוסף כולו נכשלת. נוסף תנאי os.name == "nt" כדי
# שהתוסף ייטען כרגיל גם כשמשתנה הסביבה מוגדר במערכות שאינן ווינדוס.
if os.environ.get("ANKI_DEBUG_CONSOLE") and os.name == "nt":
    ctypes.windll.kernel32.AllocConsole()
    sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
    sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)

import aqt
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import tooltip

from .deck_browser import updateRenderingMethods, logger
from .deck_overview import updateRenderingDeckOverview
from .reviewer import renderReviewer

updateRenderingMethods()
updateRenderingDeckOverview()
renderReviewer()

# === Beta feedback (גירסת בדיקה) — קל להסרה: למחוק 2 שורות אלו ואת beta_feedback.py ===
from . import beta_feedback as _beta_feedback

_beta_feedback.setup()


class _FullscreenWindowControls(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self._panel = QFrame(parent)
        self._panel.setObjectName("hafFullscreenControls")
        self._panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._panel.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QHBoxLayout(self._panel)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self._minimize_button = self._button("_", "פארקלענער", self._parent.showMinimized)
        self._restore_button = self._button("□", "גיי ארויס פון פולן עקראן", self._restore_window)
        self._close_button = self._button("×", "פארמאכן", self._parent.close)
        self._close_button.setObjectName("hafFullscreenClose")

        layout.addWidget(self._minimize_button)
        layout.addWidget(self._restore_button)
        layout.addWidget(self._close_button)
        self._panel.hide()
        self._apply_style()

        parent.installEventFilter(self)
        gui_hooks.theme_did_change.append(self._on_theme_changed)
        QTimer.singleShot(0, self.update)

    def _button(self, text: str, tooltip_text: str, callback) -> QToolButton:
        button = QToolButton(self._panel)
        button.setText(text)
        button.setToolTip(tooltip_text)
        button.setAutoRaise(False)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.clicked.connect(callback)
        return button

    def _restore_window(self) -> None:
        self._parent.showNormal()
        QTimer.singleShot(0, self.update)

    def _on_theme_changed(self) -> None:
        self._apply_style()
        self.update()

    def _apply_style(self) -> None:
        if theme_manager.night_mode:
            panel_bg = "rgba(38, 38, 40, 0.94)"
            border = "rgba(255, 255, 255, 0.18)"
            text = "#f2f2f2"
            hover = "rgba(255, 255, 255, 0.16)"
        else:
            panel_bg = "rgba(255, 255, 255, 0.94)"
            border = "rgba(0, 0, 0, 0.16)"
            text = "#202020"
            hover = "rgba(0, 0, 0, 0.10)"
        self._panel.setStyleSheet(f"""
            QFrame#hafFullscreenControls {{
                background: {panel_bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QFrame#hafFullscreenControls QToolButton {{
                min-width: 30px;
                min-height: 28px;
                padding: 0;
                border: 0;
                border-radius: 4px;
                color: {text};
                background: transparent;
                font-size: 16px;
            }}
            QFrame#hafFullscreenControls QToolButton:hover {{
                background: {hover};
            }}
            QToolButton#hafFullscreenClose:hover {{
                background: #c42b1c;
                color: #ffffff;
            }}
        """)

    def _enabled(self) -> bool:
        try:
            config = mw.addonManager.getConfig(__name__) or {}
            return bool(config.get("show_fullscreen_window_controls", False))
        except Exception:
            return False

    def update(self) -> None:
        try:
            visible = self._enabled() and bool(self._parent.windowState() & Qt.WindowState.WindowFullScreen)
            self._panel.setVisible(visible)
            if visible:
                self._panel.adjustSize()
                # #281 — פקדי החלון מרחפים בפינה השמאלית העליונה מעל כל WebView, גם אחרי F11/תפריט.
                self._panel.move(8, 8)
                self._panel.raise_()
        except RuntimeError:
            pass

    def eventFilter(self, watched, event):
        if watched is self._parent and event.type() in (
            QEvent.Type.WindowStateChange,
            QEvent.Type.Resize,
            QEvent.Type.Show,
        ):
            QTimer.singleShot(0, self.update)
        return super().eventFilter(watched, event)


def _install_fullscreen_window_controls() -> None:
    if getattr(mw, "_haf_fullscreen_window_controls", None) is None:
        mw._haf_fullscreen_window_controls = _FullscreenWindowControls(mw)


QTimer.singleShot(0, _install_fullscreen_window_controls)


def _fullscreen_controls_config_value() -> bool:
    try:
        config = mw.addonManager.getConfig(__name__) or {}
        return bool(config.get("show_fullscreen_window_controls", False))
    except Exception:
        return False


def _set_fullscreen_controls_config(enabled: bool) -> None:
    config = mw.addonManager.getConfig(__name__) or {}
    config["show_fullscreen_window_controls"] = bool(enabled)
    mw.addonManager.writeConfig(__name__, config)


def _install_fullscreen_controls_view_action() -> None:
    # #281 — ברירת המחדל כבויה, והמשתמש מפעיל/מכבה את פקדי המסך המלא מתפריט תצוגה.
    if getattr(mw, "_haf_fullscreen_controls_view_action", None) is not None:
        return
    menu = getattr(mw, "addon_view_menu", mw.form.menuCol)
    if menu is None:
        return
    action = QAction("פענסטער קנעפלעך אין פולן עקראן", mw)
    action.setCheckable(True)
    action.setChecked(_fullscreen_controls_config_value())
    action.setToolTip("ווייז פארקלענערן, ארויסגיין פון פולן עקראן און פארמאכן קנעפלעך אויבן לינקס אין פולן עקראן")

    def _toggle(checked: bool) -> None:
        _set_fullscreen_controls_config(checked)
        controls = getattr(mw, "_haf_fullscreen_window_controls", None)
        if controls is not None:
            controls.update()

    action.toggled.connect(_toggle)
    menu.addSeparator()
    menu.addAction(action)
    mw._haf_fullscreen_controls_view_action = action


QTimer.singleShot(0, _install_fullscreen_controls_view_action)


def _install_preferences_logout_guard():
    try:
        from aqt.preferences import Preferences
    except Exception:
        return
    try:
        from aqt.qt import sip
    except Exception:
        try:
            from PyQt6 import sip
        except Exception:
            sip = None
    if getattr(Preferences, "_haf_modern_theme_logout_guard", False):
        return
    original_update_login_status = getattr(Preferences, "update_login_status", None)
    original_sync_logout = getattr(Preferences, "sync_logout", None)
    if original_update_login_status is None and original_sync_logout is None:
        return

    def _is_deleted(widget) -> bool:
        if widget is None or sip is None:
            return False
        try:
            return bool(sip.isdeleted(widget))
        except Exception:
            return False

    def _show_logout_done(self) -> None:
        try:
            form = getattr(self, "form", None)
            sync_label = getattr(form, "syncAnkiHubUser", None)
            if sync_label is not None and not _is_deleted(sync_label):
                sync_label.setText("נישט פארבונדן")
        except Exception:
            pass
        tooltip("די אפשיידונג איז פארענדיגט געווארן")

    if original_update_login_status is not None:
        def _safe_update_login_status(self, *args, **kwargs):
            try:
                form = getattr(self, "form", None)
                sync_label = getattr(form, "syncAnkiHubUser", None)
                if sync_label is None or _is_deleted(sync_label):
                    return None
                return original_update_login_status(self, *args, **kwargs)
            except RuntimeError as err:
                message = str(err)
                if "wrapped C/C++ object" in message and "has been deleted" in message:
                    return None
                raise

        Preferences.update_login_status = _safe_update_login_status

    if original_sync_logout is not None:
        def _safe_sync_logout(self, *args, **kwargs):
            try:
                result = original_sync_logout(self, *args, **kwargs)
            except RuntimeError as err:
                message = str(err)
                if "wrapped C/C++ object" in message and "has been deleted" in message:
                    result = None
                else:
                    raise
            QTimer.singleShot(0, lambda: _show_logout_done(self))
            return result

        Preferences.sync_logout = _safe_sync_logout
    Preferences._haf_modern_theme_logout_guard = True


_install_preferences_logout_guard()


def _add_beta_test_action():
    from aqt.qt import QAction
    action = QAction("🐞 פרובירן א טעות מעלדונג (Beta)", mw)
    def _trigger():
        mw.jjj(q)
    action.triggered.connect(_trigger)
    mw.form.menuCol.addSeparator()
    mw.form.menuCol.addAction(action)

#gui_hooks.profile_did_open.append(lambda: _add_beta_test_action())

addon = mw.addonManager.addonFromModule(__name__)
base = "/_addons/" + addon

# add the assests folder to the media server
mw.addonManager.setWebExports(__name__,
                              r"user_files/assets/.+(\.svg|\.png|\.css|\.woff|\woff2|\.jpeg|\.gif|\.tiff|\.bmp|\.jpg|\.js|\.TTF|\.ttf|\.otf)")


# add my css and js
def on_webview_will_set_content(web_content: aqt.webview.WebContent, context: Any | None):

    # add css and js to all contexts
    if isinstance(context, (aqt.deckbrowser.DeckBrowser, aqt.overview.Overview)):
        gc.collect()

        web_content.css.append(base + "/user_files/assets/css/bootstrap.min.css")
        web_content.css.append(base + "/user_files/assets/css/anki_modern.css")

        # web_content.js.append(base + "/user_files/assets/js/plotly-latest.min.js")
        web_content.js.append(base + "/user_files/assets/js/bootstrap.bundle.min.js")
        web_content.js.append(base + "/user_files/assets/js/lazy_tooltips.js")

    # add css and js to deck overview
    if isinstance(context, aqt.overview.Overview):
        web_content.css.append(base + "/user_files/assets/css/overview.css")

    if isinstance(context, aqt.deckbrowser.DeckBrowser):
        web_content.css.append(base + "/user_files/assets/css/deckbrowser.css")




    if isinstance(context, (aqt.reviewer.Reviewer)):
        web_content.css.append(base + "/user_files/assets/css/bootstrap.min.css")
        web_content.css.append(base + "/user_files/assets/css/anki_modern.css")
        web_content.css.append(base + "/user_files/assets/css/reviewer.css")
        web_content.js.append(base + "/user_files/assets/js/bootstrap.bundle.min.js")
        web_content.js.append(base + "/user_files/assets/js/lazy_tooltips.js")


gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

# אישיו #401: modern-theme אינו עוטף עוד את Browser.__init__ או את _closeWindow.
# Anki הוא הבעלים של מחזור חיי חלון הדפדוף ושל שמירת פריסת הסרגל; התוסף רק מעצב
# את החלון שכבר נוצר. כך נמנעת מלכתחילה יצירת שרשרת wrappers שגרמה לפתיחה כפולה.

from .menu_icons import install as _install_menu_icons

_install_menu_icons()


# אישיו #424: אין ל-modern-theme שום טריגר אוטומטי שמפעיל בקשת תרומה.
# אם קיים קישור תרומה יזום בתוסף אחר הוא נשאר נגיש, אך modern-theme אינו קורא לו בפתיחת פרופיל.


# בעיה 3: בדיקת כרטיסים ריקים — אחת לכל 10 פתיחות פרופיל.
# שומרים מונה ב-mw.pm.profile (נשמר אוטומטית עם הפרופיל, ללא כתיבה ידנית ל-meta.json).
_EMPTY_CARDS_INTERVAL = 10

def _check_empty_cards_on_startup():
    try:
        count = mw.pm.profile.get("empty_cards_check_count", 0) + 1
        mw.pm.profile["empty_cards_check_count"] = count
        if count < _EMPTY_CARDS_INTERVAL:
            return
        mw.pm.profile["empty_cards_check_count"] = 0
    except Exception as e:
        logger.warning("empty_cards check ERROR: %s", e)
        return

    def _query(col):
        try:
            return col.get_empty_cards()
        except Exception:
            return None

    def _on_done(report):
        if not report:
            return
        notes = getattr(report, "notes", None)
        if not notes:
            return
        try:
            from aqt.emptycards import show_empty_cards
            show_empty_cards(mw)
        except Exception:
            try:
                mw.form.actionEmptyCards.trigger()
            except Exception:
                pass

    def _run_check():
        # #177 — בזמן החלפת פרופיל לא מריצים Operation ברקע שעלול לחזור אחרי סגירת האוסף עם result לא צפוי.
        try:
            if not getattr(mw, "col", None):
                return
            _on_done(_query(mw.col))
        except Exception:
            pass

    QTimer.singleShot(1500, _run_check)


gui_hooks.profile_did_open.append(_check_empty_cards_on_startup)


# בעיות 6 + 7 + 12: ריענון המסך הראשי רק כשבאמת השתנו ספירות הכרטיסים, עם debounce
# - לא מרעננים על עריכת תוכן שאלה (note_text)
# - לא מרעננים בזמן צפייה במצב browser/reviewer (רק כשחזרנו ל-deckBrowser)
# - debounce של 400ms — אם מגיעים מספר אירועים ברצף (למשל מחיקה מרובה ב-browser),
#   נרענן רק פעם אחת בסוף כדי לא להאט את הממשק.
_refresh_timer: QTimer | None = None

def _do_refresh():
    if mw.state != "deckBrowser":
        return
    try:
        mw.col.decks.flush()
    except Exception:
        pass
    try:
        mw.deckBrowser.refresh()
    except Exception:
        try:
            mw.reset()
        except Exception:
            pass

def _schedule_refresh():
    global _refresh_timer
    if _refresh_timer is None:
        _refresh_timer = QTimer(mw)
        _refresh_timer.setSingleShot(True)
        _refresh_timer.timeout.connect(_do_refresh)
    _refresh_timer.start(400)

def _refresh_main_on_op(changes, handler):
    if handler is mw:
        return
    if mw.state != "deckBrowser":
        return
    try:
        # רק שינויים מבניים שמשפיעים על ספירת כרטיסים בחפיסות:
        # שינוי בעץ החפיסות (deck), הוספה/מחיקה/הזזת כרטיסים (card),
        # או שינוי בסוגי שאלה (notetype). עריכת טקסט בלבד (note_text) מתעלמים.
        if not (changes.deck or changes.card or changes.notetype):
            return
    except Exception:
        return
    _schedule_refresh()

# #188 — לא מחברים יותר hook ריענון אוטומטי למסך הראשי; עדכונים ידניים/פעולות Anki הרגילות נשארים, אבל התוסף לא מפעיל refresh מיוזמתו.
# gui_hooks.operation_did_execute.append(_refresh_main_on_op)


# #188 — אנקי יוצר טיימר 10 דקות שמחזיק reference ישיר ל-onRefreshTimer.
# מחליפים את ה-callback שלו כדי שלא ירענן את מסך החפיסות במחזוריות. מסמנים
# הצלחה רק לאחר שהטיימר נמצא בפועל, כך שטעינה מוקדמת של התוסף לא תמנע ניסיון חוזר.
def _refresh_timer_no_deck_browser():
    if mw.state == "overview":
        mw.overview.refresh()


def _patch_anki_refresh_timer() -> bool:
    if getattr(mw, "_haf_modern_theme_refresh_timer_patched", False):
        return True

    for timer in mw.findChildren(QTimer):
        if timer.interval() == 10 * 60 * 1000 and timer.isActive() and not timer.isSingleShot():
            timer.timeout.disconnect()
            timer.timeout.connect(_refresh_timer_no_deck_browser)
            mw._haf_modern_theme_refresh_timer_patched = True
            return True
    return False


# #356 — מרעננים פעם אחת בחילוף יום הלימוד. day_did_change מכסה את המסלול
# הרגיל; טיימר single-shot משלנו מתוזמן מחדש גם אחרי שינוי שעת החיתוך
# בהעדפות, בלי להחזיר polling כל 10 דקות.
def _schedule_modern_theme_day_rollover() -> None:
    if getattr(mw, "col", None) is None:
        return
    try:
        cutoff = int(mw.col.sched.day_cutoff)
    except Exception:
        return

    timer = getattr(mw, "_haf_modern_theme_day_rollover_timer", None)
    if timer is None:
        timer = QTimer(mw)
        timer.setSingleShot(True)
        timer.timeout.connect(_on_modern_theme_day_rollover_timer)
        mw._haf_modern_theme_day_rollover_timer = timer
    delay_ms = max(1, int((cutoff - time.time()) * 1000) + 250)
    timer.start(min(delay_ms, 2_147_483_647))


def _refresh_deck_browser_for_new_day(force: bool = False) -> None:
    if getattr(mw, "col", None) is None:
        return
    try:
        today = int(mw.col.sched.today)
    except Exception:
        return
    last_day = getattr(mw, "_haf_modern_theme_last_sched_day", None)
    mw._haf_modern_theme_last_sched_day = today
    _schedule_modern_theme_day_rollover()
    if not force and last_day == today:
        return
    if mw.state == "deckBrowser":
        QTimer.singleShot(0, lambda: mw.deckBrowser.refresh() if mw.state == "deckBrowser" else None)
    else:
        mw._haf_modern_theme_day_refresh_pending = True


def _on_modern_theme_day_rollover_timer() -> None:
    _refresh_deck_browser_for_new_day()
    _schedule_modern_theme_day_rollover()


def _on_modern_theme_state_changed(new_state, _old_state) -> None:
    if new_state != "deckBrowser":
        return
    if not getattr(mw, "_haf_modern_theme_day_refresh_pending", False):
        return
    mw._haf_modern_theme_day_refresh_pending = False
    QTimer.singleShot(0, lambda: mw.deckBrowser.refresh() if mw.state == "deckBrowser" else None)


def _on_modern_theme_profile_opened() -> None:
    # loadCollection כבר העביר את החלון ל-deckBrowser; רענון דחוי מבטיח שמסך
    # שנשמר מההרצה הקודמת לא יישאר עם ספירות היום הקודם.
    _patch_anki_refresh_timer()
    _refresh_deck_browser_for_new_day(force=True)


# #356 / סבב 10 — day_did_change אינו מובטח כאשר שעון Windows משתנה בזמן
# שהתוכנה ברקע. בחזרה לחלון בודקים את today הדינמי של backend; רענון מתבצע
# רק אם היום אכן השתנה, ולכן אין polling ואין רענונים מחזוריים מיותרים.
def _on_modern_theme_application_state_changed(state) -> None:
    if state != Qt.ApplicationState.ApplicationActive:
        return
    QTimer.singleShot(0, _refresh_deck_browser_for_new_day)


def _install_application_date_refresh() -> None:
    if getattr(mw, "_haf_modern_theme_application_date_refresh", False):
        return
    mw.app.applicationStateChanged.connect(
        _on_modern_theme_application_state_changed
    )
    mw._haf_modern_theme_application_date_refresh = True


def _install_rollover_preferences_hook() -> None:
    try:
        from aqt.preferences import Preferences
    except Exception:
        return
    if getattr(Preferences, "_haf_modern_theme_rollover_hook", False):
        return
    original_update_collection = getattr(Preferences, "update_collection", None)
    if original_update_collection is None:
        return

    def _update_collection_and_reschedule(self, on_done):
        def _after_preferences_saved():
            _refresh_deck_browser_for_new_day()
            _schedule_modern_theme_day_rollover()
            on_done()

        return original_update_collection(self, _after_preferences_saved)

    Preferences.update_collection = _update_collection_and_reschedule
    Preferences._haf_modern_theme_rollover_hook = True


gui_hooks.day_did_change.append(_refresh_deck_browser_for_new_day)
gui_hooks.state_did_change.append(_on_modern_theme_state_changed)
gui_hooks.profile_did_open.append(_on_modern_theme_profile_opened)
QTimer.singleShot(0, _patch_anki_refresh_timer)
_install_rollover_preferences_hook()
_install_application_date_refresh()


icons_dir = os.path.join(os.path.dirname(__file__), 'color_icons')
