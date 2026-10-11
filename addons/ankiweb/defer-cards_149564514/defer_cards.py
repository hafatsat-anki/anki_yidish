# Copyright(C)| 2024 Carlos Duarte - Defer Cards
# Fork on     | Lovac42 code, in add-on "SlackersDelight" https://github.com/lovac42/SlackersDelight
# License     | GNU AGPL, version 3 ou posterior; http://www.gnu.org/licenses/agpl.html
# Source in   | https://github.com/cjdduarte/DeferCards

# == User Config =========================================

DEFERRED_DECK_NAME = "00 פעקל קארטלעך צו באארבעטן 00"
DEFERRED_DECK_NAMES = (
    DEFERRED_DECK_NAME,
    "0 פעקל קארטלעך צו באארבעטן 0",
    "00 חפיסת כרטיסים לטיפול 00",
    "0 חפיסת כרטיסים לטיפול 0",
)

# == End Config ==========================================
##########################################################

import anki
import aqt
from anki import decks
from anki.hooks import wrap
from anki.utils import int_time
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.reviewer import Reviewer
from aqt.utils import showInfo, showWarning, tooltip

from .config import Config

DEFERRED_DECK_DESC = """
<p><i>דער פעקל אנטהאלט
 קארטלעך צו באארבעטן שפעטער.</i></p><p>
<b>אכטונג!</b>נאכן לערנען א קארטל פון דעם פעקל<br>
גייט דאס קארטל צוריק צום אריגינעלן פעקל.<br>
עס איז רעקאמענדירט פאר איבערלערנען<br>
אדער איבעררעדאקטירן קארטלעך.<br>
מען קען יעצט רעדאקטירן שאלות מיט א קליק אויף "דורכבלעטערן".</i></p><br>"""

ADDON_NAME = "DeferCards"
conf = Config(ADDON_NAME)

class DeferCards:
    def __init__(self):
        self.timeId = int_time() % 100000
        gui_hooks.reviewer_will_show_context_menu.append(self.showContextMenu)

    def showContextMenu(self, r, m):
        hk = conf.get("hotkey", "_")
        a = m.addAction("שיקט צום באארבעטן")
        a.setShortcut(QKeySequence(hk))
        a.triggered.connect(self.defer)

    def defer(self):
        "main operations"
        card = mw.reviewer.card
        did = self.getDynId()
        if did and did != card.did:
            # Require reschedule for lrn card in filtered decks
            if card.odid and card.queue in (1, 3, 4):
                deck_conf = mw.col.decks.config_dict_for_deck_id(card.did)
                if not deck_conf.get('resched'):
                    return

            # #310 — הסרת SQL ישיר (UPDATE cards SET did) שגרם לעדכון כפול וחוסר עקביות.
            # swap() כבר מעדכן את card.did ושומר דרך update_card.
            self.swap(did, card)
            mw.reset()
            tooltip("דאס קארטל איז אריבערגעפירט צום פעקל פאר באארבעטן", period=1000)

    def getDynId(self, create=True):
        "Built or select Dyn deck"
        dyn = None
        for name in DEFERRED_DECK_NAMES:
            dyn = mw.col.decks.by_name(name)
            if dyn:
                break
        if not dyn:  # Create filtered deck
            if not create:
                return  # test only
            did = mw.col.decks.id(DEFERRED_DECK_NAME, type=decks.defaultDynamicDeck)
            dyn = mw.col.decks.get(did)
        elif not dyn['dyn']:  # Regular deck w/ same name
            showInfo(f"טוישט דעם נאמען פונעם פעקל {DEFERRED_DECK_NAME} קודם.")
            return False
        return dyn['id']

    def swap(self, dynId, card):
        "Swap card info"
        if not card.odid:
            card.odid = card.did
            if card.queue == 1:
                # fix bad cards during db check
                card.odue = mw.col.sched.today
            else:  # new/rev cards
                card.odue = card.due
                card.due = -self.timeId
                self.timeId += 1
        card.did = dynId
        mw.col.update_card(card)

sd = DeferCards()

# Friendly Warning Message
def desc(self, deck, _old):
    if deck['name'] not in DEFERRED_DECK_NAMES:
        return _old(self, deck)
    return DEFERRED_DECK_DESC

# Handing keybinds
def shortcutKeys(self, _old):
    ret = _old(self)
    ret.append((conf.get("hotkey", "_"), lambda: sd.defer()))
    return ret

# Prevent user from rebuilding this special deck
def sd_rebuildDyn(self, deck_id, _old=None):
    did = deck_id or self.col.decks.selected()
    dyn = mw.col.decks.get(did)
    if dyn['name'] in DEFERRED_DECK_NAMES:
        showWarning("מען קען נישט איבערבויען דעם פעקל.")
        return None
    return self.col._backend.rebuild_filtered_deck(deck_id)

# Prevent user from changing deck options
def sd_onDeckConf(self, deck=None, _old=None):
    if not deck:
        deck = self.col.decks.current()
    if deck['name'] in DEFERRED_DECK_NAMES:
        showWarning("מען קען נישט רעדאקטירן דעם פעקל.")
        return
    return _old(self, deck)

# Add button on bottom bar
def add_custom_button(self):
    if not conf.get("showButton", True):
        return

    js_code = f"""
    (function tryAddButton(attempts) {{
        if (document.getElementById('customButton')) return;

        var moreButton = document.querySelector("button[onclick*='more']")
                      || document.querySelector("td[class='stat'] > button[title*='M']");
        if (!moreButton) {{
            if (attempts > 0) setTimeout(function() {{ tryAddButton(attempts - 1); }}, 50);
            return;
        }}

        var newTd = document.createElement('td');
        newTd.setAttribute('width', '50');
        newTd.setAttribute('align', 'right');
        newTd.setAttribute('valign', 'top');
        newTd.className = 'stat';

        var customButton = document.createElement('button');
        customButton.id = 'customButton';
        customButton.innerHTML = 'שיקט צום באארבעטן<br>שפעטער';
        customButton.title = 'קיצור קנעפל: {conf.get("hotkey", "_")}';
        customButton.onclick = function() {{ pycmd('customButtonClick'); }};

        newTd.appendChild(customButton);
        var editTd = document.getElementById('edit');
        if (editTd) {{
            editTd.parentNode.insertBefore(newTd, editTd.nextSibling);
        }} else {{
            moreButton.parentNode.parentNode.insertBefore(newTd, moreButton.parentNode);
        }}
    }})(20);
    """
    self.bottom.web.eval(js_code)

@pyqtSlot()
def on_custom_button_click():
    sd.defer()

def custom_pycmd_handler(self, cmd, _old):
    if cmd == "customButtonClick":
        on_custom_button_click()
    else:
        _old(self, cmd)

Reviewer._shortcutKeys = wrap(Reviewer._shortcutKeys, shortcutKeys, 'around')
Reviewer._initWeb = wrap(Reviewer._initWeb, add_custom_button)
Reviewer._linkHandler = wrap(Reviewer._linkHandler, custom_pycmd_handler, "around")

aqt.main.AnkiQt.onDeckConf = wrap(aqt.main.AnkiQt.onDeckConf, sd_onDeckConf, 'around')
aqt.overview.Overview._desc = wrap(aqt.overview.Overview._desc, desc, 'around')
anki.scheduler.base.SchedulerBase.rebuild_filtered_deck = wrap(anki.scheduler.base.SchedulerBase.rebuild_filtered_deck, sd_rebuildDyn, 'around')
