import aqt
from anki.cards import Card
from anki.utils import html_to_text_line
from aqt import gui_hooks
from aqt.qt import QTimer
from PyQt6.QtWidgets import QMenu

answered_cards = {}


def in_browser(find):
    browser = aqt.dialogs.open("Browser", aqt.mw)
    browser.search_for(f"{find}")
    browser.update_history()


def menu_update(menu: QMenu):
    menu.clear()
    for cid, label in answered_cards.items():
        a = menu.addAction(label[:36] + "...")
        a.triggered.connect(lambda checked=False, card_id=cid: in_browser(f"cid:{card_id}"))


def move_answered_menu_to_bottom(menu: QMenu, separator_action, answered_action):
    for action in (separator_action, answered_action):
        if action in menu.actions():
            menu.removeAction(action)
    if menu.actions() and not menu.actions()[-1].isSeparator():
        menu.addAction(separator_action)
    menu.addAction(answered_action)


# #232 - run after all context-menu hooks so later add-ons cannot push this submenu upward again.
def queue_answered_menu_move(menu: QMenu, separator_action, answered_action):
    move_answered_menu_to_bottom(menu, separator_action, answered_action)
    QTimer.singleShot(0, lambda: move_answered_menu_to_bottom(menu, separator_action, answered_action))


def show_context_menu(r, m):
    separator_action = m.addSeparator()
    answered_menu = m.addMenu("פראגעס וואס מען האט געענטפערט אין דער חזרה")
    answered_action = answered_menu.menuAction()
    answered_menu.aboutToShow.connect(lambda menu=answered_menu: menu_update(menu))
    m.aboutToShow.connect(
        lambda menu=m, sep=separator_action, action=answered_action: move_answered_menu_to_bottom(menu, sep, action)
    )
    queue_answered_menu_move(m, separator_action, answered_action)


gui_hooks.reviewer_will_show_context_menu.append(show_context_menu)


def show_hide_after_reload(self, card: Card, ease):
    label = html_to_text_line(card.note().fields[0])
    cid = card.id
    answered_cards[cid] = label


gui_hooks.reviewer_did_answer_card.append(show_hide_after_reload)


def clear_answered_cards(state, old_state):
    global answered_cards
    answered_cards = {}


gui_hooks.state_will_change.append(clear_answered_cards)
