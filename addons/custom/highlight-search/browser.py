
import contextlib
import unicodedata

from anki.hooks import wrap
from aqt import mw
from aqt.browser import Browser
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QCheckBox

from .config import config as internal_config
from .libaddon.platform import checkAnkiVersion
from .search import QueryLanguageVersion, SearchTokenizer
from .webview import clear_highlights, highlight_terms

_SEARCH_PLACEHOLDER: str | None

if checkAnkiVersion("2.1.41"):
    _SEARCH_PLACEHOLDER = None
else:
    try:
        from aqt.utils import tr

        _SEARCH_PLACEHOLDER = tr(tr.browsing_type_here_to_search)
    except Exception:

        _SEARCH_PLACEHOLDER = "<שרייבט דא דעם טעקסט צו זוכן: דריקט Enter צו ווייזן דעם יעצטיגן פעקל>"

_query_language_version = QueryLanguageVersion.ANKI2124 if checkAnkiVersion("2.1.24") else QueryLanguageVersion.ANKI2100

_search_tokenizer = SearchTokenizer(_query_language_version)


def on_browser_did_change_row(
        browser: Browser, current: int | None = None, previous: int | None = None
):
    if not hasattr(browser, "_highlight_results") or not browser._highlight_results:
        return

    search_text = browser.form.searchEdit.lineEdit().text()
    search_text = unicodedata.normalize("NFC", search_text)

    if not search_text or search_text == _SEARCH_PLACEHOLDER:
        return

    tokens = _search_tokenizer.tokenize(search_text)
    searchable_tokens = _search_tokenizer.get_searchable_tokens(tokens)

    if not searchable_tokens:
        return

    highlight_terms(browser.editor.web, searchable_tokens)


def select_all_matching_cards(browser: Browser):
    matching_cids = _find_from_search_entry(browser)
    _set_card_selection(browser, matching_cids)


def select_next_matching_card(browser: Browser):
    matching_cids = _find_from_search_entry(browser)
    current_cid: int | None = None if not browser.card else browser.card.id

    next_index = matching_cids.index(current_cid) + 1 if current_cid and current_cid in matching_cids else None

    if next_index is None or next_index >= len(matching_cids):
        next_index = 0

    next_cid = matching_cids[next_index]
    _set_card_selection(browser, [next_cid])


def _find_from_search_entry(browser: Browser):
    search_text = browser.form.searchEdit.lineEdit().text().strip()
    return list(browser.col.find_cards(search_text, order=True))


def _set_card_selection(browser: Browser, cids: list[int]):
    browser.form.tableView.selectionModel().clear()
    browser.model.selectedCards = {cid: True for cid in cids}
    browser.model.restoreSelection()




def on_browser_will_show(browser: Browser):
    # שימוש ב-internal_config לקריאה מהירה של קיצורי מקשים
    shortcut = QShortcut(
        QKeySequence(internal_config["local"]["hotkey_select_next_matching_card"]),
        browser.form.searchEdit,
    )
    shortcut.activated.connect(lambda: select_next_matching_card(browser))

    shortcut = QShortcut(
        QKeySequence(internal_config["local"]["hotkey_select_all_matching_cards"]),
        browser.form.searchEdit,
    )
    shortcut.activated.connect(lambda: select_all_matching_cards(browser))


def on_browser_menus_did_init(browser: Browser):
    # קריאת ברירת המחדל
    browser._highlight_results = internal_config["local"].get("highlight_by_default", True)


# -----------------------------------------------------------------------------
# Preferences Functions (The Clean Way)
# -----------------------------------------------------------------------------

def pref_checkbox_state_changed(state):
    """Saves config using standard Anki API."""
    is_checked = (state != 0)

    # עדכון בזיכרון המיידי (כדי שהשינוי יורגש מיד בחלון הדפדפן)
    internal_config["local"]["highlight_by_default"] = is_checked

    # שמירה לדיסק בדרך הבטוחה
    addon_id = __name__.split('.')[0]
    conf = mw.addonManager.getConfig(addon_id)
    if not conf:
        conf = {}
    if "local" not in conf:
        conf["local"] = {}

    conf["local"]["highlight_by_default"] = is_checked
    mw.addonManager.writeConfig(addon_id, conf)


def highlight_results_toggle_pref(self):
    """Adds the checkbox to the main Anki preferences window."""
    self.form.highlight_toggle = QCheckBox('צייכן אויס ווערטער אין זוך רעזולטאטן', self.form.tabWidget)

    # קריאה ישירה מהקונפיג של אנקי
    addon_id = __name__.split('.')[0]
    conf = mw.addonManager.getConfig(addon_id)

    current_val = True
    if conf and "local" in conf:
        current_val = conf["local"].get("highlight_by_default", True)

    self.form.highlight_toggle.setChecked(current_val)

    # חיבור לפונקציית השמירה
    self.form.highlight_toggle.stateChanged.connect(pref_checkbox_state_changed)

    # הוספה ל-Layout
    try:
        self.form.gridLayout_2.addWidget(self.form.highlight_toggle, 5, 0, 1, 2)
    except AttributeError:
        with contextlib.suppress(AttributeError, RuntimeError):
            self.form.tabWidget.widget(0).layout().addWidget(self.form.highlight_toggle)


def initialize_browser():

    from aqt.gui_hooks import browser_menus_did_init
    browser_menus_did_init.append(on_browser_menus_did_init)

    try:
        from aqt.gui_hooks import browser_did_change_row
        browser_did_change_row.append(on_browser_did_change_row)
    except (ImportError, ModuleNotFoundError):
        Browser._onRowChanged = wrap(
            Browser._onRowChanged, on_browser_did_change_row, "after"
        )

    try:
        from aqt.gui_hooks import browser_will_show
        browser_will_show.append(on_browser_will_show)
    except (ImportError, ModuleNotFoundError):
        Browser.setupSearch = wrap(Browser.setupSearch, on_browser_will_show, "after")
