from __future__ import annotations

import datetime

import aqt
from anki.collection import OpChangesWithId
from anki.decks import DeckCollapseScope
from aqt import mw
from aqt.operations import CollectionOp
from aqt.operations.deck import add_deck, set_deck_collapsed
from aqt.qt import *
from aqt.utils import getOnlyText, showInfo, tr
from _shared_libs.haf_notifications import show_failure


def retlen(deck_name) -> int:
    return len(mw.col.find_cards(deck_name))


def inBrowser(find=""):
    try:
        if retlen("") == 0:
            showInfo(
                " עס זענען יעצט נישט דא קיין פראגעס אין דער זאמלונג. \n קוקט אין די מדריכים אינעם מעניו \"הילף\" פאר אינפארמאציע ווי צו נוצן דעם פראגראם גוט און ווירקזאם. \nפאר בירורים און פראגעס קען מען זיך ווענדן צום טעכנישן הילף אימעיל: anki4tora@gmail.com\nמיט הצלחה!")
            return
        elif retlen(find) == 0:
            showInfo("קיין קארטלעך זענען נישט געפונען געווארן לויט דער זוכעניש")
            return
        browser = aqt.dialogs.open("Browser", aqt.mw)
        browser.search_for(f"{find}")
    except Exception as e:
        show_failure("דער דורכבלעטערער פענסטער האט זיך נישט געעפנט פאר דער געבעטן זוכעניש. עפנט אים דורכן דורכבלעטערן מעניו און פרובירט די זוכעניש פון פריש.", e)
    # browser.update_history()


def safe_division(n, d):
    return n / d if d else 0


def get_beginning_of_current_day_epoch():
    # באג timezone תוקן: שימוש ב-API של אנקי שמטפל נכון באיזורי זמן ובהגדרת rollover
    return mw.col.sched.day_cutoff - 86400



# פונקציות לחפיסות ספציפיות

def collapse_deck(did):
        set_deck_collapsed(
            parent=mw,
            deck_id=did,
            collapsed=False,
            scope=DeckCollapseScope.REVIEWER,
        ).run_in_background()
        mw.moveToState("deckBrowser")
def add_sub_deck_dialog(
        did: int,
        *,
        parent: QWidget,
        default_text: str = "",
) -> CollectionOp[OpChangesWithId] | None:
    deck = aqt.mw.col.decks.get(did)
    deckName = deck['name']
    if name := getOnlyText(
            tr.decks_new_deck_name(), default=default_text, parent=parent
    ).strip():
        collapse_deck(did)
        return add_deck(parent=parent, name=deckName + "::" + name)
    else:
        return None


def on_create(did: int) -> None:
    if op := add_sub_deck_dialog(did, parent=mw):
        op.run_in_background()

def AddCard(did):
    mw.col.decks.select(did)
    mw.onAddCard()
