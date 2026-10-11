import pathlib

from aqt import gui_hooks, mw
from aqt.qt import *

# #189 — open_window טוען את ברירות המחדל בעצמו לפני פתיחת דיאלוג modeless.
from .printDialog import open_window

q = QAction(mw)
q.setText("דרוקן און עקספארטירן צו ווארד")
# Ctrl+E belongs to Anki export and blocked custom study after rebinding.
q.setShortcut(QKeySequence((mw.addonManager.getConfig(__name__) or {}).get(
    "print_shortcut", "Ctrl+Alt+Shift+F11")))
mw.form.menuCol.addSeparator()
filename = str(pathlib.Path(__file__).parent.resolve())
icon = QIcon(filename + "/print.png")
q.setIcon(icon)
mw.form.menuCol.addAction(q)
# #189 — מחברים רק את open_window כדי שחלון ההדפסה לא ייפתח דרך exec ואז ייחסם מול Browser.
q.triggered.connect(lambda _checked=False: open_window())


def _reload_config():
    q.setShortcut(QKeySequence((mw.addonManager.getConfig(__name__) or {}).get(
        "print_shortcut", "Ctrl+Alt+Shift+F11")))


def _open_print_for_deck(deck_id: int) -> None:
    open_window(deck_id=deck_id)


def _add_print_to_deck_context_menu(menu: QMenu, deck_id: int) -> None:
    # #265 — קליק ימני על חפיסה פותח את חלון ההדפסה כשהחפיסה כבר נבחרת, אחרי ייצוא.
    action = QAction("דרוקן", menu)
    qconnect(action.triggered, lambda _checked=False, deck_id=deck_id: _open_print_for_deck(deck_id))
    actions = menu.actions()
    insert_before = None
    for index, existing_action in enumerate(actions):
        text = existing_action.text().replace("&", "")
        if "עקספארטירן" in text or "Export" in text:
            next_index = index + 1
            insert_before = actions[next_index] if next_index < len(actions) else None
            break
    if insert_before is None and len(actions) >= 3:
        insert_before = actions[3]
    if insert_before:
        menu.insertAction(insert_before, action)
    else:
        menu.addAction(action)


gui_hooks.deck_browser_will_show_options_menu.append(_add_print_to_deck_context_menu)


mw.addonManager.setConfigAction(__name__, lambda: True)


