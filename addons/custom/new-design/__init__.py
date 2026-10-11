# #151 — תיקון: פינות מעוגלות דרך DWM במקום window flags שגרמו לתקיעות.
# כל שאר הקוד נשמר כמו המקור.
import ctypes

import aqt.fields
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.theme import theme_manager
from PyQt6 import QtCore

# #346 — ctypes.windll קיים בווינדוס בלבד. במק ובלינוקס הגישה אליו זורקת
# AttributeError כבר בשלב הייבוא, וטעינת התוסף כולו נכשלת עם
# "Add-on startup failed". DWM (Desktop Window Manager) הוא ממשק של ווינדוס
# לפינות מעוגלות; במערכות אחרות אין לו מקבילה ואין בו צורך, ולכן _dwm נשאר
# None ופונקציית הפינות המעוגלות הופכת ל-no-op. שאר עיצוב התוסף פועל כרגיל.
_dwm = ctypes.windll.dwmapi if hasattr(ctypes, "windll") else None
_DWMWA_WINDOW_CORNER_PREFERENCE = 33
_DWMWCP_ROUND = 2


def is_night_mode():
    return theme_manager.night_mode

night_mode_on = is_night_mode


# #342 (+#351 שנסגר ככפול): תחת דרייבר וידאו Vulkan ההתאמות של התוסף (יצירת native window
# handles לתפריטים דרך winId + החלפת stylesheet גלובלי) גורמות ל-webviews שחורים בחלון
# הדפדוף ("דפדף בחפיסה" וחלון העריכה). ב-OpenGL ושאר הדרייברים אין בעיה, לכן תחת Vulkan
# מדלגים על כל ההתאמות — התפריטים יוצגו בעיצוב ברירת המחדל של אנקי.
def _vulkan_driver_active() -> bool:
    import os
    if os.environ.get("QSG_RHI_BACKEND", "").lower() == "vulkan":
        return True
    try:
        from aqt.profiles import VideoDriver
        vulkan = getattr(VideoDriver, "Vulkan", None)
        return vulkan is not None and mw.pm.video_driver() == vulkan
    except (ImportError, AttributeError):
        return False


_VULKAN = _vulkan_driver_active()


# #151 — DWM פינות מעוגלות ברמת Windows 11, במקום FramelessWindowHint + WA_TranslucentBackground
def _apply_dwm_round_corners(hwnd):
    # #346 — במק ובלינוקס אין DWM; הפינות המעוגלות פשוט אינן מוחלות
    if _dwm is None:
        return
    preference = ctypes.c_int(_DWMWCP_ROUND)
    _dwm.DwmSetWindowAttribute(
        hwnd,
        _DWMWA_WINDOW_CORNER_PREFERENCE,
        ctypes.byref(preference),
        ctypes.sizeof(preference),
    )


def menu_style(m):
    # #342: אין נגיעה ב-winId תחת Vulkan
    if _VULKAN:
        return
    try:
        hwnd = int(m.winId())
        if hwnd:
            _apply_dwm_round_corners(hwnd)
    except (AttributeError, RuntimeError, OSError):
        pass


# #151 — event filter שמחיל DWM על כל QMenu שנפתח (כולל תפריטי הקשר דינמיים)
class _MenuRoundCornersFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show and isinstance(obj, QMenu):
            if not obj.property("_haf_dwm_rounded"):
                # #342 סבב 3: תחת Vulkan אסור לכפות יצירת native window (winId על תפריט
                # שטרם הוצג שבר את רינדור ה-webview). בזמן Show החלון בדרך כלל כבר קיים —
                # windowHandle() רק ניגש אליו. אם עדיין אין handle תחת Vulkan, מדלגים
                # בלי לסמן את התפריט, כדי לנסות שוב בפתיחה הבאה.
                wh = obj.windowHandle()
                if wh is None and _VULKAN:
                    return False
                obj.setProperty("_haf_dwm_rounded", True)
                try:
                    hwnd = int(wh.winId()) if wh is not None else int(obj.winId())
                    if hwnd:
                        _apply_dwm_round_corners(hwnd)
                except (RuntimeError, OSError):
                    pass
        return False


# #342 סבב 3: ה-event filter פעיל גם תחת Vulkan — הוא מעגל פינות רק לתפריטים שכבר
# נוצר להם native window (בזמן Show), ולכן אינו כופה יצירה מוקדמת ששוברת את ה-webview.
_menu_filter = _MenuRoundCornersFilter(mw.app)
mw.app.installEventFilter(_menu_filter)


menu_style(mw.form.menuCol)
menu_style(mw.form.menuEdit)
menu_style(mw.form.menuTools)
menu_style(mw.form.menuCol)
menu_style(mw.form.menuqt_accel_view)
menu_style(mw.form.menuHelp)
if hasattr(mw, "addon_col_menu"):
    menu_style(mw.addon_col_menu)


def _style_addon_col_menu():
    if hasattr(mw, "addon_col_menu"):
        menu_style(mw.addon_col_menu)


gui_hooks.main_window_did_init.append(_style_addon_col_menu)


# #151 — תפריטי menubar (כולל menuCol) לא נתפסים ב-event filter רגיל,
# לכן מחילים DWM כשהתפריט נפתח בפועל דרך aboutToShow.
def _connect_menubar_dwm(menu):
    def _on_about_to_show():
        # #342 סבב 3: תחת Vulkan מעגלים רק אם ה-native window כבר קיים; aboutToShow נורה
        # לפני ההצגה, וכפיית winId בשלב הזה שברה את ה-webview. אם אין עדיין handle —
        # ה-event filter יתפוס את התפריט ברגע ה-Show.
        try:
            if _VULKAN:
                wh = menu.windowHandle()
                if wh is None:
                    return
                hwnd = int(wh.winId())
            else:
                hwnd = int(menu.winId())
            if hwnd:
                _apply_dwm_round_corners(hwnd)
        except (RuntimeError, OSError):
            pass
    menu.aboutToShow.connect(_on_about_to_show)


for _mb_menu in mw.form.menubar.findChildren(QMenu):
    _connect_menubar_dwm(_mb_menu)

mw.form.menuqt_accel_view.setTitle("אויסשטעל גרייס")


def borwser_menu_style(browser):
    menu_style(browser.form.menuEdit)
    menu_style(browser.form.menu_Cards)
    menu_style(browser.form.menu_Notes)
    menu_style(browser.form.menuJump)
    menu_style(browser.form.menu_Help)
    menu_style(browser.form.menuFlag)
    menu_style(browser.form.menuqt_accel_view)
    menu_style(browser.form.menuLayout)
    def getMenu(parent, menuName):
        menubar = parent.form.menubar
        for a in menubar.actions():
            if menuName == a.text():
                return a.parent()
        else:
            return menubar.addMenu(menuName)
    menu=getMenu(browser, "זוכן און איבערבייטן")
    menu_style(menu)


def table_context_menu(m):
    menu = QMenu()
    menu_style(menu)


gui_hooks.browser_menus_did_init.append(table_context_menu)


def on_context_menu_event(web, menu):
    menu_style(menu)


def Deck_menu_event(menu, web):
    menu_style(menu)


def ssDeck_menu_event(w, menu, e, r):
    menu_style(menu)


def setup_hooks():
    gui_hooks.webview_will_show_context_menu.append(on_context_menu_event)
    gui_hooks.editor_will_show_context_menu.append(on_context_menu_event)
    gui_hooks.browser_menus_did_init.append(borwser_menu_style)
    gui_hooks.browser_will_show_context_menu.append(on_context_menu_event)
    gui_hooks.reviewer_will_show_context_menu.append(on_context_menu_event)
    gui_hooks.add_cards_will_show_history_menu.append(on_context_menu_event)
    gui_hooks.browser_header_will_show_context_menu.append(Deck_menu_event)
    gui_hooks.browser_sidebar_will_show_context_menu.append(ssDeck_menu_event)


setup_hooks()


def new_menu_style():
    if night_mode_on():
        return ("""
                    QMenu{
        background-color: #272828!important;
                              border: solid 2px rgba(0, 0, 0, 1);
                          border-radius: 8px;

                    }
                    QMenu::item {
                            background-color: transparent;
                            font-size:12px;
                            padding:3px 15px;
                            margin:5px 10px;
        color:  #d7d7d7;
                            font-weight: 460;
                    }
                    QMenu::item:selected {
                            background-color: rgb(195, 195, 195);
                            border-radius: 4px;
                    } """)
    else:
        return ("""
                    QMenu{
                          background-color: hsla(0,0%,98%,.9);
                          border: solid 2px rgba(0, 0, 0, 1);
                          border-radius: 8px;

                    }
                    QMenu::item {
                            background-color: transparent;
                            font-size:12px;
                            padding:3px 15px;
                            margin:5px 10px;
                            color: rgb(26, 26, 26);
                            font-weight: 460;
                    }
                    QMenu::item:selected {
                            background-color: rgb(195, 195, 195);
                            border-radius: 4px;
                    }
                """)


def new_menubar_style():
    if night_mode_on():
        return ("""QMenuBar {
        background-color: #272828!important;
        /* spacing: 3px; /* spacing between menu bar items */
    }

    QMenuBar::item {
                            background-color: transparent;
                            font-size:12px;
                            padding:3px;
                            margin:5px;
        color:  #d7d7d7;
                            font-weight: 460;
    }

    QMenuBar::item:selected { /* when selected using mouse or keyboard */
                            background-color: #EAEAEA;
                            border-radius: 4px;
    }

    QMenuBar::item:pressed {
        background: #888888;
    }""")
    else:
        return ("""QMenuBar {
        background-color: #F3F3F3;
        /* spacing: 3px; /* spacing between menu bar items */
    }

    QMenuBar::item {
                            background-color: transparent;
                            font-size:12px;
                            padding:3px;
                            margin:5px;
                            color: rgb(26, 26, 26);
                            font-weight: 460;
    }

    QMenuBar::item:selected { /* when selected using mouse or keyboard */
                            background-color: #EAEAEA;
                            border-radius: 4px;
    }

    QMenuBar::item:pressed {
        background: #888888;
    }""")


import aqt

app = aqt.mw.app

stylesheet = aqt.mw.app.styleSheet()
_new_stylesheet = (stylesheet.replace("""    QMenu {
        background-color: #fcfcfc;
        border: 1px solid #e4e4e4;
        padding: 4px;
    }
    QMenu::item {
        background-color: transparent;
        padding: 3px 14px;
        margin-bottom: 4px;
    }
    QMenu::item:selected {
        background-color: rgba(37, 99, 235, 0.5);
        border-radius: 5px;
    }""", new_menu_style())
.replace("""QMenuBar {
    border-bottom: 1px solid #e4e4e4;
}
 QMenuBar {
        border-bottom: 1px solid #e4e4e4;
    }
    QMenuBar::item {
        background-color: transparent;
        padding: 2px 4px;
        border-radius: 5px;
    }
    QMenuBar::item:selected {
        background-color: white;
    }""", new_menubar_style())
.replace("""padding: 0.75em 0 0.75em 0;""",
"""padding: 1px 0 0 0;""")
.replace("""QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        margin: 0 2px;
        left: 15px;
    }""",
"""QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        margin: 0;
        left: 15px;
    }
 """)
                  )

# #342 (סבב 2): ה-stylesheet מוחל גם תחת Vulkan — עיצוב QSS אינו נוגע ב-native handles
# ולכן אינו חשוד בשבירת ה-webview. רק קריאות winId/DWM (פינות מעוגלות) מדולגות תחת Vulkan.
app.setStyleSheet(_new_stylesheet)


# #345: חלון ההעדפות נחתך במסכים קטנים ואין פס גלילה — תוספים שונים מוסיפים שדות לטאבים
# והגובה חורג מהמסך. הפתרון: כל טאב נעטף ב-QScrollArea (ללא מסגרת — יורש את ערכת הנושא,
# כולל מצב לילה), וגובה החלון מוגבל לשטח המסך הזמין. רץ אחרי __init__ של הדיאלוג ולכן
# אחרי כל התוספות של שאר התוספים.
def _make_preferences_scrollable(self, *args, **kwargs):
    try:
        tab_widget = self.form.tabWidget
    except AttributeError:
        return
    for i in range(tab_widget.count()):
        page = tab_widget.widget(i)
        if isinstance(page, QScrollArea):
            continue
        title = tab_widget.tabText(i)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        tab_widget.removeTab(i)
        scroll.setWidget(page)
        tab_widget.insertTab(i, scroll, title)
    tab_widget.setCurrentIndex(0)
    screen = self.screen() or mw.screen()
    if screen:
        avail = screen.availableGeometry()
        self.resize(min(self.sizeHint().width() + 40, avail.width() - 40),
                    min(self.sizeHint().height() + 40, avail.height() - 80))
        # #345 — הגבלת הגודל לא מספיקה: החלון עלול להיפתח במיקום ששמור מריצה קודמת
        # (למשל על מסך שני שכבר לא מחובר, או במיקום שהיה תקין ברזולוציה גדולה יותר),
        # וכתוצאה מכך לזלוג מעבר לגבולות המסך הנוכחי גם כשגודלו תקין. מציבים מחדש את
        # החלון בתוך גבולות המסך הזמין אם הוא חורג מהם בכל כיוון שהוא.
        geo = self.geometry()
        x = min(max(geo.x(), avail.x()), avail.x() + avail.width() - geo.width())
        y = min(max(geo.y(), avail.y()), avail.y() + avail.height() - geo.height())
        if (x, y) != (geo.x(), geo.y()):
            self.move(x, y)


def _init_preferences_scroll():
    import aqt.preferences
    from anki.hooks import wrap
    aqt.preferences.Preferences.__init__ = wrap(
        aqt.preferences.Preferences.__init__, _make_preferences_scrollable, "after")


_init_preferences_scroll()
