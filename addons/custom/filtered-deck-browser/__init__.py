import aqt
from aqt import browser, gui_hooks, mw
from aqt.utils import KeyboardModifiersPressed


def create_filter_string(browser):
    cids = browser.selectedNotesAsCards() if browser.table.is_notes_mode() else browser.selected_cards()
    search_string = ""
    for note_id in cids:
        search_string += f'''cid:{note_id} OR '''
    create_filtered_deck(search_string[:-3])


def create_filtered_deck(filter_string):
    search = filter_string
    if mw.col.sched_ver() != 1 and KeyboardModifiersPressed().alt:
        aqt.dialogs.open("FilteredDeckConfigDialog", mw, search_2=search)
    else:
        aqt.dialogs.open("FilteredDeckConfigDialog", mw, search=search)


browser.Browser.create_filter_string = create_filter_string


def setupMenu(browser):
    menu = browser.form.menuEdit
    menu.addSeparator()
    a = menu.addAction("שאף א געפילטערטן פעקל מיט די אנגעצייכנטע פראגעס...")
    a.triggered.connect(browser.create_filter_string)
    menu.insertAction(browser.form.actionCreateFilteredDeck, a)
    menu.addSeparator()


gui_hooks.browser_menus_did_init.append(setupMenu)
