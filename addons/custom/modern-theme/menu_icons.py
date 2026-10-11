"""Original geometric menu icons; About uses a neutral information symbol."""
from functools import lru_cache
import re

from aqt import gui_hooks, mw
from aqt.qt import QIcon, QMenu, QPixmap, QTimer


# Drawn for this project, without importing an external icon collection.
SHAPES = {
    "write-note": '<path d="M12 3H4v18h14v-7M8 8h3M8 12h2m3 3 1-4 6-6 3 3-6 6zM18 7l3 3"/>',
    "question-bank": '<path d="M3 5h4v16H3zM7 3h4v18H7m8-16a3 3 0 0 1 6 0c0 2-3 2-3 4m0 3v.5M14 16h8v5h-8z"/>',
    "refresh": '<path d="M20 9a8 8 0 1 0 0 7M20 3v6h-6"/>',
    "update-note": '<path d="M12 3H4v18h7M8 7h3M8 11h3m3 4a4 4 0 1 1 1 5m-1-9v4h4"/>',
    "change-type": '<path d="M3 3h7v7H3zM14 14h7v7h-7zM14 5h5v5m-3-3 3 3 3-3M10 19H5v-5m-3 3 3-3 3 3"/>',
    "unlimited": '<path d="M3 6h18M6 3h12M12 15c-2-5-9-5-9 0s7 5 9 0 9-5 9 0-7 5-9 0z"/>',
    "repair-schedule": '<path d="M12 3a9 9 0 1 0 9 9M7 12h5V7m3-4 2 2 3-3a4 4 0 0 1-5 6l-4 4m4-9 1-2"/>',
    "optimize": '<path d="M3 3v18h18M6 17c6 0 3-10 9-10h5m-3-3 3 3-3 3"/>',
    "merge": '<path d="M3 3h6v6H3zM15 3h6v6h-6zM6 12l6 5 6-5m-6 5v5m-3-3 3 3 3-3"/>',
    "chart": '<path d="M3 3v18h18M7 17v-5m5 5V6m5 11V9"/>',
    "study": '<path d="M3 4h8v16H3zM6 8h2m-2 4h2m7-6 7 6-7 6z"/>',
    "defer": '<path d="M3 3h11v6M3 3v18h8M6 7h5m-5 4h3m3 4h10m-4-4 4 4-4 4"/>',
    "undo": '<path d="M9 4 3 9l6 5M3 9h10a7 7 0 0 1 0 14"/>',
    "redo": '<path d="m15 4 6 5-6 5m6-5H11a7 7 0 0 0 0 14"/>',
    "profile": '<circle cx="9" cy="7" r="3"/><path d="M2 21v-3a7 7 0 0 1 12-5m3-8h5l-2-2m2 2-2 2m2 10h-6l2-2m-2 2 2 2"/>',
    "import": '<path d="M3 14v7h18v-7M12 2v14m-5-5 5 5 5-5"/>',
    "export": '<path d="M3 14v7h18v-7M12 16V2M7 7l5-5 5 5"/>',
    "backup": '<path d="M4 3h13l3 3v15H4zM8 3v6h8V3M8 21v-7h8v7"/>',
    "restore": '<path d="M4 4v6h6M4 10a9 9 0 1 1 0 7M12 6v7l4 2"/>',
    "sync": '<path d="M3 9a9 9 0 0 1 16-4l2 3m0-6v6h-6M21 15a9 9 0 0 1-16 4l-2-3m0 6v-6h6"/>',
    "settings": '<path d="M4 3v18M12 3v18M20 3v18"/><rect x="1" y="6" width="6" height="4" rx="1"/><rect x="9" y="14" width="6" height="4" rx="1"/><rect x="17" y="8" width="6" height="4" rx="1"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
    "check": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="m6 12 4 4 8-9"/>',
    "media": '<rect x="2" y="3" width="20" height="18" rx="2"/><circle cx="8" cy="8" r="2"/><path d="m3 18 6-6 4 4 4-7 4 9"/>',
    "empty": '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M9 12h6"/>',
    "addons": '<rect x="2" y="2" width="8" height="8" rx="2"/><rect x="14" y="2" width="8" height="8" rx="2"/><rect x="2" y="14" width="8" height="8" rx="2"/><path d="M14 18h8m-4-4v8"/>',
    "view": '<path d="M1 12c6-11 16-11 22 0-6 11-16 11-22 0z"/><circle cx="12" cy="12" r="4"/>',
    "zoom": '<circle cx="10" cy="10" r="7"/><path d="m15 15 7 7M6 10h8m-4-4v8"/>',
    "zoom-out": '<circle cx="10" cy="10" r="7"/><path d="m15 15 7 7M6 10h8"/>',
    "search": '<circle cx="10" cy="10" r="7"/><path d="m15 15 7 7"/>',
    "replace": '<path d="M3 5h16l-3-3m3 3-3 3M21 19H5l3-3m-3 3 3 3M4 13h4m-2-2v4M15 12h6"/>',
    "filter": '<path d="M2 3h20l-8 10v7l-4 2v-9z"/>',
    "cards": '<rect x="7" y="6" width="15" height="16" rx="2"/><path d="M17 3H3v15M11 11h7m-7 5h5"/>',
    "note": '<path d="M4 2h12l4 4v16H4zM15 2v5h5M8 11h8m-8 4h8m-8 4h5"/>',
    "deck": '<path d="M3 7h7l2 3h9v11H3zM5 7V3h14v7"/>',
    "edit": '<path d="m3 21 2-7L17 2l5 5L10 19zM5 14l5 5M14 5l5 5"/>',
    "delete": '<path d="M3 6h18M9 6V2h6v4M5 6l1 16h12l1-16M10 10v8m4-8v8"/>',
    "copy": '<rect x="8" y="8" width="13" height="14" rx="2"/><path d="M16 5V2H3v15h2"/>',
    "tag": '<path d="M3 3h9l10 10-9 9L3 12z"/><circle cx="8" cy="8" r="1.5"/>',
    "tag-remove": '<path d="M3 3h9l10 10-9 9L3 12zM10 13h7"/><circle cx="7" cy="7" r="1"/>',
    "flag": '<path d="M5 23V2m0 1h14l-4 5 4 5H5"/>',
    "star": '<path d="m12 2 3 6 7 1-5 5 1 8-6-4-6 4 1-8-5-5 7-1z"/>',
    "pause": '<rect x="4" y="3" width="5" height="18" rx="1"/><rect x="15" y="3" width="5" height="18" rx="1"/>',
    "bury": '<path d="M3 17h18M6 21h12M12 2v12m-5-5 5 5 5-5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="17" rx="2"/><path d="M7 2v6m10-6v6M3 11h18m-13 5h2m4 0h2"/>',
    "sort": '<path d="M5 2v20m-3-4 3 4 3-4M11 5h11M11 11h8m-8 6h5"/>',
    "next": '<path d="m8 3 9 9-9 9"/>',
    "previous": '<path d="m16 3-9 9 9 9"/>',
    "first": '<path d="M4 3v18m16-18-9 9 9 9"/>',
    "last": '<path d="M20 3v18M4 3l9 9-9 9"/>',
    "close": '<path d="m5 5 14 14M5 19 19 5"/>',
    "select": '<rect x="2" y="2" width="20" height="20" rx="2" stroke-dasharray="3 3"/><path d="m6 12 4 4 8-9"/>',
    "invert": '<circle cx="12" cy="12" r="9"/><path d="M12 3v18M6 7h6m-8 5h8m-6 5h6"/>',
    "layout": '<rect x="2" y="3" width="20" height="18" rx="2"/><path d="M9 3v18m0-9h13"/>',
    "sidebar": '<rect x="2" y="3" width="20" height="18" rx="2"/><path d="M15 3v18m3-13h1m-1 4h1m-1 4h1M6 9l3 3-3 3"/>',
    "toolbar": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 11h20M6 8h1m4 0h1m4 0h1"/>',
    "layout-auto": '<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/><rect x="7" y="7" width="10" height="10" rx="2"/><path d="m10 13 2-3 2 3"/>',
    "layout-vertical": '<rect x="3" y="2" width="18" height="8" rx="2"/><rect x="3" y="14" width="18" height="8" rx="2"/>',
    "layout-horizontal": '<rect x="2" y="3" width="8" height="18" rx="2"/><rect x="14" y="3" width="8" height="18" rx="2"/>',
    "display-order": '<path d="M3 5h10M3 12h7M3 19h4m10-15v16m-3-3 3 3 3-3"/><circle cx="19" cy="5" r="2"/>',
    "grade": '<path d="M4 3h16v18H4zM8 7h8M8 16v1m4-4v4m4-7v7"/>',
    "fullscreen": '<path d="M9 2H2v7m13-7h7v7M2 15v7h7m13-7v7h-7"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 11v7m0-12v1"/>',
    "book": '<path d="M12 5v17M2 3c4-1 7 0 10 2 3-2 6-3 10-2v17c-4-1-7 0-10 2-3-2-6-3-10-2z"/>',
    "print": '<path d="M6 8V2h12v6M6 18H2V8h20v10h-4M6 14h12v8H6zM17 11h2"/>',
    "keyboard": '<rect x="1" y="5" width="22" height="14" rx="2"/><path d="M5 9h1m3 0h1m3 0h1m3 0h1M5 13h1m3 0h1m3 0h1m3 0h1M7 16h10"/>',
    "bug": '<ellipse cx="12" cy="14" rx="5" ry="7"/><path d="M9 7 7 3m8 4 2-4M3 9l4 3m10 0 4-3M2 16h5m10 0h5M5 23l3-4m8 0 3 4M12 9v11"/>',
}

ACTION_ICONS = {
    "actionUndo": "undo", "actionRedo": "redo", "actionSwitchProfile": "profile",
    "actionImport": "import", "actionExport": "export", "action_create_backup": "backup",
    "action_open_backup": "restore", "actionPreferences": "settings", "actionFullDatabaseCheck": "check",
    "actionCheckMediaDatabase": "media", "actionEmptyCards": "empty", "actionAdd_ons": "addons",
    "actionStudyDeck": "deck", "actionCreateFiltered": "filter", "actionNoteTypes": "cards",
    "actionExit": "close", "actionFullScreen": "fullscreen", "actionZoomIn": "zoom",
    "actionZoomOut": "zoom-out", "actionResetZoom": "restore", "action_upgrade_downgrade": "sync",
    "actionDocumentation": "book", "actionDonate": "star", "actionSelectAll": "select",
    "actionInvertSelection": "invert", "actionFind": "search", "actionNote": "note",
    "actionNextCard": "next", "actionPreviousCard": "previous", "actionGuide": "book",
    "actionChangeModel": "change-type", "actionSelectNotes": "select", "actionFindReplace": "replace",
    "actionSidebarFilter": "filter", "actionCardList": "cards", "actionFindDuplicates": "copy",
    "actionReposition": "sort", "actionFirstCard": "first", "actionLastCard": "last",
    "actionClose": "close", "action_Info": "info", "actionAdd_Tags": "tag",
    "actionRemove_Tags": "tag-remove", "actionToggle_Suspend": "pause", "actionDelete": "delete",
    "actionAdd": "write-note", "actionChange_Deck": "deck", "actionSidebar": "sidebar",
    "actionClear_Unused_Tags": "tag-remove", "actionManage_Note_Types": "cards", "actionToggle_Mark": "star",
    "actionCreateFilteredDeck": "filter", "action_set_due_date": "calendar", "action_grade_now": "grade",
    "action_forget": "restore", "action_toggle_mode": "layout", "actionCopy": "copy",
    "actionToggleSidebar": "sidebar", "actionLayoutAuto": "layout-auto", "actionLayoutVertical": "layout-vertical",
    "actionLayoutHorizontal": "layout-horizontal", "actionbrowsing_toggle_showing_cards_notes": "cards",
    "action_toggle_bury": "bury", "menuEdit": "edit", "menuCol": "deck", "menuTools": "settings",
    "menuqt_accel_view": "view", "menuHelp": "book", "menu_Help": "book", "menuJump": "next",
    "menu_Cards": "cards", "menu_Notes": "note", "menuFlag": "flag", "menuLayout": "layout",
    "toggleSidebar": "sidebar", "toggleFastbar": "toolbar", "toggleBury": "bury",
}
FLAG_COLORS = {"Red": "#d94b48", "Orange": "#e18b36", "Green": "#45996a", "Blue": "#4b82cf",
               "Pink": "#dc73a1", "Turquoise": "#3baaa9", "Purple": "#9270cc"}
# Specific add-on commands take precedence over broad translated keywords.
LABEL_ICONS = {
    "ווייז סדר": "display-order",
    "זייט סרגל": "sidebar",
    "באהאלט דעם זייט סרגל": "sidebar",
    "ווייז דעם זייט סרגל": "sidebar",
    "שאץ אפ יעצט": "grade",
    "פראגע זאמלונג": "question-bank",
    "איינשטעלן קיצור קנעפלעך": "keyboard",
    "דערהיינטיג פאר נייע רשומות": "update-note",
    "נעם אוועק די טעגליכע חזרה גרעניץ": "unlimited",
    "פריש אויף": "refresh",
    "מאך א קאפיע פון דער רשומה": "copy",
    "טויש דעם סארט רשומה (געמישטע אויסוואל)": "change-type",
    "טוישן און איבערבייטן פעלד אינהאלט": "replace",
    "פאררעכטונג פון די מרווחים פון fsrs": "repair-schedule",
    "שטים אפ fsrs פאר אלע גרופעס איינשטעלונגען": "optimize",
    "קוקן פאר דאפלטע סארטן רשומה": "merge",
    "ווייז אדער באהאלט קארטל אינפארמאציע ביים חזרן": "info",
    "שאף א געפילטערטן פעקל מיט די אנגעצייכנטע פראגעס": "filter",
    "שרייבט א פראגע": "write-note",
    "הייב אן א חזרה": "study",
    "סטאטיסטיק": "chart",
    "סיכום": "chart",
    "בוי פון פריש": "refresh",
    "ליידיג אויס": "empty",
    "פילטערט פראגעס": "filter",
    "צוגעפאסט לערנען": "settings",
    "ברענג צוריק פון באזייטיגן": "restore",
    "פיר אריבער צום באהאנדלען": "defer",
    "קאלענדאר גילטיגקייט באריכט — אויב ער איז אומגילטיג, שיקט צום אנטוויקלער": "calendar",
}
TEXT_ICONS = (
    (("סינכראניזירן", "סינכראניזירן", "sync"), "sync"),
    (("באריכט", "bug"), "bug"), (("קיצורים פון", "shortcut"), "keyboard"),
    (("דרוק ארויס", "print"), "print"), (("זוכן און איבערבייטן", "find and replace"), "replace"),
    (("זוכעניש", "זוך", "געפין", "search", "find"), "search"),
    (("צוריקברענגען", "ברענג צוריק", "restore"), "restore"), (("גיבוי", "backup"), "backup"),
    (("עקספארטירן", "עקספארטירן", "export"), "export"), (("אימפארטירן", "אימפארטירן", "import"), "import"),
    (("מעק אויס", "אויסמעק", "delete", "remove"), "delete"), (("קאפיר", "copy", "duplicate"), "copy"),
    (("צעטלעך", "tag"), "tag"), (("סארטן רשומה", "note types"), "cards"),
    (("הספק", "צייטפלאן", "schedule", "due"), "calendar"),
    (("בדיקה", "check"), "check"), (("פרעפערענצן", "איינשטעלונגען", "זאמלונג כלים", "settings", "preferences"), "settings"),
    (("אויסשטעל", "גרייס", "view", "zoom"), "view"), (("צוגאבן", "add-ons"), "addons"),
    (("רעדאקטיר", "רעדאקטירן", "edit", "rename"), "edit"), (("פעקל", "deck"), "deck"),
    (("מדריך", "הילף", "help", "guide"), "book"), (("פארמאכן", "close", "quit"), "close"),
)


@lru_cache(maxsize=128)
def menu_icon(name, color="#a27b50"):
    shape = SHAPES.get(name)
    if shape is None:
        return QIcon()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        color = "#a27b50"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
           f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
           + shape + "</svg>")
    icon = QIcon()
    # Raster variants keep fine lines sharp on both regular and high-DPI screens.
    for size in (24, 48, 72):
        pixmap = QPixmap()
        data = svg.replace('width="24" height="24"', f'width="{size}" height="{size}"')
        pixmap.loadFromData(data.encode("utf-8"), "SVG")
        icon.addPixmap(pixmap)
    return icon


def _style_action(action):
    name = action.objectName()
    if action.isSeparator():
        return
    if name == "actionAbout":
        action.setIcon(menu_icon("info"))
        action.setIconVisibleInMenu(True)
        return
    if action.property("haf_help_section"):
        return  # The guide add-on owns its original help SVGs.
    for color_name, color in FLAG_COLORS.items():
        if name == f"action{color_name}_Flag":
            action.setIcon(menu_icon("flag", color))
            action.setIconVisibleInMenu(True)
            return
    key = action.property("haf_menu_icon") or ACTION_ICONS.get(name)
    submenu = action.menu()
    if not key and submenu:
        key = ACTION_ICONS.get(submenu.objectName())
    if not key:
        text = action.text().replace("&", "").split("\t", 1)[0].strip().rstrip(".…").casefold()
        key = LABEL_ICONS.get(text)
        if not key:
            key = next((icon for terms, icon in TEXT_ICONS if any(term in text for term in terms)), None)
    # Unrecognized third-party actions retain their own icons instead of receiving
    # a misleading generic symbol. Column toggles also retain their state symbols.
    if key not in SHAPES:
        return
    action.setIcon(menu_icon(key, action.property("haf_menu_color") or "#a27b50"))
    action.setIconVisibleInMenu(True)


def style_menu(menu, seen=None):
    seen = set() if seen is None else seen
    if id(menu) in seen:
        return
    seen.add(id(menu))
    if not menu.property("haf_icons_connected"):
        menu.aboutToShow.connect(lambda: style_menu(menu))
        menu.setProperty("haf_icons_connected", True)
    for action in menu.actions():
        _style_action(action)
        if action.menu():
            style_menu(action.menu(), seen)


def style_window(window):
    for menu in window.findChildren(QMenu):
        style_menu(menu)


def _main():
    style_window(mw)


def _context(*args):
    for arg in args:
        if isinstance(arg, QMenu):
            style_menu(arg)


def install():
    if getattr(mw, "_haf_menu_icons_installed", False):
        return
    mw._haf_menu_icons_installed = True
    mw._haf_menu_icon = menu_icon
    gui_hooks.main_window_did_init.append(_main)
    gui_hooks.profile_did_open.append(_main)
    gui_hooks.browser_menus_did_init.append(style_window)
    gui_hooks.browser_will_show_context_menu.append(_context)
    gui_hooks.browser_header_will_show_context_menu.append(_context)
    gui_hooks.browser_sidebar_will_show_context_menu.append(_context)
    _main()
    QTimer.singleShot(0, _main)
