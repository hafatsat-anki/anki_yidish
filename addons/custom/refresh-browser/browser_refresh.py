
"""
Anki Add-on: Refresh Browser List

Refreshes browser view and optionally changes the sorting column
(e.g. to show newly added cards since last search)

Copyright: (c) Glutanimate 2016-2017 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

# Do not modify the following line


from .config import getConfig

######## USER CONFIGURATION START ########

SORTING_COLUMN = "noteCrt"
# Custom column sorting applied on hotkey toggle
#   - only works if that column is active in the first place
#   - set to note creation time by default ("noteCrt")
#   - can be disabled by setting SORTING_COLUM = ""
#
# Valid Values (regular browser):
#
# 'question' 'answer' 'template' 'deck' 'noteFld' 'noteCrt' 'noteMod'
# 'cardMod' 'cardDue' 'cardIvl' 'cardEase' 'cardReps' 'cardLapses'
# 'noteTags' 'note'
#
# Additional values (advanced browser):
#
# 'cfirst' 'clast' 'cavgtime' 'ctottime' 'ntags' 'coverdueivl' 'cprevivl'


######## USER CONFIGURATION END ########

from aqt import gui_hooks
from aqt.browser import Browser
from aqt.qt import *

from _shared_libs.haf_logging import get_logger

logger = get_logger("refresh_browser")
_refresh_actions = []
def debug(t):
    logger.debug(t)
    pass

def refreshView(self):
    debug("Calling refreshView()")
    self.onSearchActivated()

def setupMenu(self):
    menu = self.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('פריש אויף')
    a.setShortcut(QKeySequence(getConfig("ShortCut","CTRL+F5")))
    a.triggered.connect(self.refreshView)
    _refresh_actions.append(a)


def _reload_config():
    # #138 — QAction של חלון דפדוף פתוח לא קורא config מחדש לבד, לכן מעדכנים את הקיצור הקיים בזמן Apply.
    from .config import newConf
    newConf(None)
    shortcut = QKeySequence(getConfig("ShortCut", "CTRL+F5"))
    dead = []
    for action in list(_refresh_actions):
        try:
            action.setShortcut(shortcut)
        except RuntimeError:
            dead.append(action)
    for action in dead:
        _refresh_actions.remove(action)

Browser.refreshView = refreshView
gui_hooks.browser_menus_did_init.append(setupMenu)
