# "Duplicate and Reorder" Anki add-on
# Copyright (C) 2020 Régis Martinez (regis.martinez3@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


#  Duplicate And Reorder(DNR) addon



from anki import hooks
from anki.browser import BrowserConfig
from aqt import browser, gui_hooks
from aqt.qt import *
from aqt.utils import shortcut

from . import duplicate

browser.Browser.dnrDuplicateCards = duplicate.duplicateCards

# browser.Browser.dnrResetNewDueOrder = reorder.resetNewDueOrder

# Set menus and corresponding actions
def setupDNRActions(browser):

   # Duplicate current selected card(s)
   dnrDuplicateCardsAction = QAction("מאך א קאפיע פון דער רשומה", browser)
   dnrDuplicateCardsAction.setShortcut(shortcut("Alt+ג"))
   dnrDuplicateCardsAction.triggered.connect(browser.dnrDuplicateCards)
   browser.form.dnrDuplicateCardsAction = dnrDuplicateCardsAction



   browser.form.menu_Notes.addSeparator()
   browser.form.menu_Notes.addAction(dnrDuplicateCardsAction)

   # browser.form.menu_Notes.addAction(dnrResetNewDueOrder)

   # Set the actions active only if the cards are sorted by creations date.
   # This is necessary because the reposition is done considering the current
   # ordering in the browser
   dnrUpdateActions(browser, browser.table.is_notes_mode())


def dnrOnSortChanged(self, idx, ord):
   dnrUpdateActions(self.browser, self.browser.table.is_notes_mode())


def dnrOnBrowserModeChanged(self, checked):
   dnrUpdateActions(self, checked)

# Set the actions active only if the cards are sorted by creations date.
# This is necessary because the reposition is done considering the current
# ordering in the browser
def dnrUpdateActions(browser, is_note_mode):
   sort_key = BrowserConfig.sort_column_key(is_note_mode)
   browser.col.get_browser_column(browser.col.get_config(sort_key))

#   browser.form.dnrDuplicateCardsAction.setEnabled(isCreatedSort)

   # self.browser.form.dnrResetNewDueOrder.setEnabled(isCreatedSort)

gui_hooks.browser_menus_did_init.append(setupDNRActions)

# Ask notifications for sorting change
browser.table.Table._on_sort_column_changed = hooks.wrap(
    browser.table.Table._on_sort_column_changed, dnrOnSortChanged
)

browser.Browser.on_table_state_changed = hooks.wrap(
    browser.Browser.on_table_state_changed, dnrOnBrowserModeChanged
)




