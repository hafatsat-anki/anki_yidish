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






class CurrentViewList:

   def __init__(self, browser):
      self.browser = browser
      # Use this as a cache to avoid retrieving that too many times
      self.all_note_ids = None
      self.all_card_ids = None
      self.selected_notes = None
      self.selected_cards = None



   def get_note_ids(self):
      if self.all_note_ids is None:
         self.all_note_ids = sorted(self.browser.table._model._state.get_note_ids(self.browser.table._model._items))
      return self.all_note_ids

   def _get_cards_ids_from_notes(self, note_ids):
      card_ids = []
      for note_id in note_ids:
         # card_ids.extend(sorted(self.browser.col.card_ids_of_note(note_id)))
         note = self.get_note(note_id)
         if note is not None:
            card_ids.extend(sorted([card.id for card in note.cards()]))
      return card_ids


   def get_selected_note_ids(self):
      if self.selected_notes is None:
         self.selected_notes = sorted(self.browser.selected_notes())
      return self.selected_notes


   def get_note(self, note_id):
      return self.browser.col.get_note(note_id)

   def get_card(self, card_id):
      return self.browser.col.get_card(card_id)



   # Updates the due dates of all the cards of the note of note_id
   # Usually called after swapping two cards : if the moved cards (cards of the selected
   # note, provided in note_id) is new, update its due date to still be in increasing
   # order together with the creation date. Find the first new previous card and use
   # the same due date.

   # Finds the first preceding card which is new (usually to get its due date).
   # Include cards of note_id in search if `include` is true, exclude them otherwise
   def get_previous_new_card(self, note_id, include=True):

      note_index = self.get_note_ids().index(note_id)

      previous_note_ids = self.get_note_ids()[:note_index + 1] if include else self.get_note_ids()[:note_index]

      # Traverse previous cards starting by the last one
      for previous_note_id in reversed(previous_note_ids):
         for previous_card_id in reversed(self._get_cards_ids_from_notes([previous_note_id])):
            current_card = self.get_card(previous_card_id)
            # If the card is new, we return it, otherwise we keep looking
            if current_card.ivl == 0:
               return current_card

      return None




   # Copys an appropriate due date for the cards of to_note
   # Principle : for each copied card, see if its original was new (i.e. ivl = 0). If so, don't touch due date, otherwise lookup the neareset previous new card, and take same due date
   def copy_due(self, from_note, to_note):

      for _i, original_card in enumerate(from_note.cards()):

         # It may happen that generated number of cards of new note != number of cards of original note :
         # happens when there are empty_cards that would be generated : thos are inhibited
         # Hence : look only for corresponding matching card in original cards. We use "ord" memeber
         # which is the indice of the card for that notetype
         corresponding_cards = [card for card in to_note.cards() if card.ord == original_card.ord]
         # There should be only one maching card with same "ord"
         if len(corresponding_cards) != 1:
            continue

         new_card = corresponding_cards[0]

         # if the original is a new card, use its due date, otherwise find the first preceding new card
         previous_card = original_card if original_card.ivl == 0 else self.get_previous_new_card(from_note.id)

         new_card.due = previous_card.due if previous_card is not None else 1000000
         new_card.ivl = 0
         self.browser.col.update_card(new_card)

   def place_new_cards_after_original(self, original_note, duplicated_note):
      """Place duplicated new cards immediately after their originals safely."""
      # #389 — במקום לשנות note.id כדי לכפות סמיכות, משתמשים במיקום הרשמי
      # של כרטיסים חדשים. shift_existing מפנה מקום בלי לכתוב ישירות ל-SQL.
      duplicates_by_ord = {card.ord: card for card in duplicated_note.cards()}
      pairs = []
      for original_card in original_note.cards():
         duplicated_card = duplicates_by_ord.get(original_card.ord)
         if duplicated_card is None:
            continue
         if (
            original_card.queue == 0
            and original_card.type == 0
            and duplicated_card.queue == 0
            and duplicated_card.type == 0
         ):
            pairs.append((int(original_card.due), duplicated_card.id))

      # עובדים מהסוף להתחלה כדי שהזזת כרטיס מוקדם לא תשנה את יעד הזוג הבא.
      for original_position, duplicated_card_id in sorted(pairs, reverse=True):
         self.browser.col.sched.reposition_new_cards(
            [duplicated_card_id],
            starting_from=max(1, original_position + 1),
            step_size=1,
            randomize=False,
            shift_existing=True,
         )

   # Copy the schedule information from the cards of a note to the cards of another note.
   # The notes should be of same type (i.e. have same number of cards at least)
   def copy_schedule(self, original_note, note_copy):
      original_cards = original_note.cards()
      note_copy.cards()
      for _i, original_card in enumerate(original_cards):
         # It may happen that generated number of cards of new note != number of cards of original note :
         # happens when there are empty_cards that would be generated : thos are inhibited
         # Hence : look only for corresponding matching card in original cards. We use "ord" memeber
         # which is the indice of the card for that notetype
         corresponding_cards = [card for card in note_copy.cards() if card.ord == original_card.ord]
         # There should be only one maching card with same "ord"
         if len(corresponding_cards) != 1:
            continue

         new_card = corresponding_cards[0]
         new_card.left = original_card.left
         new_card.due = original_card.due
         new_card.queue = original_card.queue
         new_card.type = original_card.type
         new_card.reps = original_card.reps
         new_card.mod = original_card.mod
         new_card.flags = original_card.flags
         new_card.ivl = original_card.ivl
         new_card.factor = original_card.factor
         new_card.lapses = original_card.lapses
         new_card.odue = original_card.odue
         self.browser.col.update_card(new_card)


