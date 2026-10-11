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

from aqt import mw
from aqt.utils import tooltip

from . import config, helpers


def duplicateCards(browser):

   # Get deck of first selected card
   cids = browser.selectedCards()
   nids = browser.selectedNotes()
   if not cids:
      if not nids:
         tooltip("קיין רשומות זענען נישט אויסגעקליבן געווארן")
      else:
         tooltip("קיין קארטלעך זענען נישט אויסגעקליבן געווארן")
      return



   list_view = helpers.CurrentViewList(browser)

   selected_note_ids = list_view.get_selected_note_ids()
   sum_cards_dupl = 0
   newly_selected_note_ids = []

   # Duplicate each selelected note
   for note_id in selected_note_ids:
      # Make a duplicate of that note
      original_note = browser.col.get_note(note_id)
      sum_cards_dupl += 1
      # Create new note
      duplicated_note = browser.col.new_note(original_note.note_type())
      # Copy tags and fields (all model fields) from original note
      duplicated_note.tags = original_note.tags
      duplicated_note.fields = original_note.fields
      # Add note to database
      mw.col.add_note(note=duplicated_note, deck_id=original_note.cards()[0].did)

      if config.getUserOption("Add 'duplicate' tag"):
         duplicated_note.add_tag('קאפיע')

      # Copy the entire schedule info : cards of duplicated_note are considered
      if config.getUserOption("Also duplicate schedule"):
         list_view.copy_schedule(original_note, duplicated_note)
      # or find an appropriate due for the cards of duplicated_note (which are
      # thus considered as new cards)
      else:
         list_view.copy_due(original_note, duplicated_note)

      # #389 — משמרים את יכולת המיקום ליד המקור עבור כרטיסים חדשים באמצעות
      # API ה-reposition הרשמי, בלי לשנות note.id או card.id.
      list_view.place_new_cards_after_original(original_note, duplicated_note)
      newly_selected_note_ids.append(duplicated_note.id)

      # Mark note and cards as modified and set for sync
      duplicated_note.usn = browser.col.usn()
      for card in duplicated_note.cards():
         card.usn = browser.col.usn()
         browser.col.update_card(card)
      browser.col.update_note(duplicated_note)

   browser.col.save()

   # Reset collection and main window

   mw.col.reset()
   mw.reset()
   browser.onSearchActivated()
   if sum_cards_dupl == 1:
      tooltip("איין רשומה איז מיט הצלחה קאפירט געווארן. די נייע קארטלעך זענען געשטעלט נעבן דעם אריגינאל.")
   else:
      tooltip(str(sum_cards_dupl) + " רשומות זענען מיט הצלחה קאפירט געווארן. די נייע קארטלעך זענען געשטעלט נעבן דעם אריגינאל.")

   browser.table.reset()
   browser.search()

   # select the newly created note(s)
   if (browser.table.is_notes_mode()):
      rows_to_reselect = browser.table._model.get_item_rows(newly_selected_note_ids)
      browser.table.clear_selection()
      browser.table._select_rows(rows_to_reselect)
   else:
      rows_to_reselect = browser.table._model.get_item_rows(list_view._get_cards_ids_from_notes(newly_selected_note_ids))
      browser.table.clear_selection()
      browser.table._select_rows(rows_to_reselect)
