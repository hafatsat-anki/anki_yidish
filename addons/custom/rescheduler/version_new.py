"""
Copyright (C) 2018- ignd

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from aqt.utils import showInfo, tooltip

from _shared_libs.haf_logging import get_logger

from .config import gc
from .mydialog import MultiPrompt

logger = get_logger("rescheduler")


def add_reviewer_shortcuts(state: str, shortcuts: list):
    if state != "review":
        return
    cut = gc('access_dialog_from_reviewer')
    if cut:
        shortcuts.append((cut, prompt_new_interval))


gui_hooks.state_shortcuts_will_change.append(add_reviewer_shortcuts)
#if gc('add_entry_to_context_menu'):
#    addHook('AnkiWebView.contextMenuEvent', reviewer_context_menu)



from aqt.operations import CollectionOp
from aqt.operations.scheduling import forget_cards


def prompt_new_interval():
    card = mw.reviewer.card
    m = MultiPrompt()
    if not m.exec():
        tooltip('אפגעזאגט')
    else:
        if m.days == 0:
            forget_cards(
                parent=mw,
                card_ids=[card.id],
            ).run_in_background()
        else:
            # "Set Due Date" defaults to not adjusting the card interval, including ‘!’ will also reset the interval
            days_string = str(m.days)
            # work around old Rememorize Syntax:
            #   neg: change only due (this is the new Anki default for positive ints)
            #   pos: change due+ivl (old Anki default, in new Anki it also requires an "!"")
            if m.days > 0:
                days_string += "!"
            if m.days < 0:
                days_string = days_string[1:]  # remove leading minus
            logger.debug(f"days_string for cid '{card.id}' is {days_string}")
            CollectionOp(mw, lambda col: col.sched.set_due_date([card.id], days_string, None)).success(lambda _: tooltip("דער נייער צייטפלאן איז געמאכט געווארן")).run_in_background()

        mw.reviewer._answeredIds.append(card.id)
        mw.autosave()
        mw.reset()
###########################################################################################

from anki.cards import Card


def templates_for_card(card: Card, browser: bool) -> tuple[str, str]:
    template = card.template()
    if browser:
        q, a = template.get("bqfmt"), template.get("bafmt")
    else:
        q, a = None, None
    q = q or template.get("qfmt")
    a = a or template.get("afmt")
    return a, "123" #, a  # type: ignore

def showfields():

    showInfo(str(mw.reviewer.card()))





#######################################################################



def add_entry(reviewer, menu):
    # add context menu entry
    # work in progress, adding a shortcut for the entry doesn't work
    entry = [["שטעל א דאטום אליין", gc('access_dialog_from_reviewer') , prompt_new_interval],]
    reviewer._addMenuItems(menu, entry)

gui_hooks.reviewer_will_show_context_menu.append(add_entry)


#// adding button links to link handler function
def linkHandler_wrap(reviewer, url):
    # sched_ver = mw.col.sched.version
    if url == "resched":
        prompt_new_interval()
    else:
        Review_linkHandelr_Original(reviewer, url)

Review_linkHandelr_Original = Reviewer._linkHandler
Reviewer._linkHandler = linkHandler_wrap
