import contextlib
import json
import os.path
from collections import defaultdict
from collections.abc import Collection
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.operations.deck import add_deck_dialog
from aqt.qt import *
from aqt.utils import disable_help_button, getFile, restoreGeom, saveGeom, showInfo, tooltip
from PyQt6 import QtCore

from .collection_manager import CollectionManager, NameId, sorted_decks_and_ids
from .common import ADDON_NAME, LogDebug
from .config import config
from .note_importer import ImportResult, import_note
from .settings_dialog import CroProSettingsDialog
from .widgets import WIDGET_HEIGHT, ComboBox, DeckCombo, NoteList, ProfileNameLabel, StatusBar

logDebug = LogDebug()

class search_edit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.main_dialog = None
    def keyPressEvent(self, evt):
        if evt.key() == QtCore.Qt.Key.Key_Enter or evt.key() == QtCore.Qt.Key.Key_Return:
            self.main_dialog.update_notes_list()
        else:
            super().keyPressEvent(evt)

#############################################################################
# UI layout
#############################################################################

class MainDialogUI(QDialog):
    name = "אימפארטירן איינציגע שאלות פון א טעקע"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_bar = StatusBar()
        self.SearchResultLabel = QLabel()
        self.into_profile_label = ProfileNameLabel()
        self.current_profile_deck_combo = DeckCombo()
        self.import_button = QPushButton('אימפארטירן')
        self.settings_button = QPushButton('איינשטעלונגען')
        self.new_deck_button = QPushButton('שאפט א פעקל')
        self.prev_cards_button = QPushButton('< פריערדיגער')
        self.prev_cards_button.setMinimumWidth(60)
        self.prev_cards_button.setToolTip(f"גייט צו{config['max_displayed_notes']} פריערדיגע רשומות")
        self.next_cards_button = QPushButton('קומענדיגער >')
        self.next_cards_button.setMinimumWidth(60)
        self.next_cards_button.setToolTip(f"גייט צו{config['max_displayed_notes']} קומענדיגע רשומות")
        self.selected_count_label = QLabel('0 אויסגעקליבן')
        self.range:int = 0
        self.search_term_edit = search_edit()
        self.search_term_edit.main_dialog = self
        self.get_apkg_label = QLabel('אימפארטירט פון א טעקע:')
        self.get_apkg_button = QPushButton('קליקט דא אויסצוקלייבן א פעקל')
        self.other_profile_deck_combo = DeckCombo()
        self.filter_button = QPushButton('פילטערן')
        self.filter_button.setFocus()

        # כפתורי שליטה בבחירה
        self.select_page_btn = QPushButton("צייכנט אן דעם בלאט")
        self.select_all_btn = QPushButton("צייכנט אן אלעס")
        self.deselect_all_btn = QPushButton("נעמט אראפ דעם אויסוואל")
        self.show_selection_btn = QPushButton("ווייזט די אויסגעקליבענע")

        self.note_list = NoteList()
        self.note_type_selection_combo = ComboBox()
        self.init_ui()

    def init_ui(self):
        self.search_term_edit.setPlaceholderText('<זוכן קארטלעך>')
        self.setLayout(self.make_main_layout())
        self.setWindowTitle(ADDON_NAME)
        self.set_default_sizes()

    def make_filter_row(self) -> QLayout:
        filter_row = QHBoxLayout()
        filter_row.addWidget(self.search_term_edit)
        filter_row.addWidget(self.filter_button)
        return filter_row

    def make_main_layout(self) -> QLayout:
        main_vbox = QVBoxLayout()
        main_vbox.addLayout(self.make_other_profile_settings_box())
        main_vbox.addLayout(self.dest_row())
        main_vbox.addLayout(self.make_filter_row())
        main_vbox.addLayout(self.search_result_box())
        main_vbox.addLayout(self.label_box())
        main_vbox.addWidget(self.note_list)
        main_vbox.addLayout(self.status_bar)
        main_vbox.addLayout(self.make_input_row())
        return main_vbox

    def label_box(self) -> QLayout:
        label_row = QHBoxLayout()

        # הוראות
        info_label = QLabel('צייכנט אן די רשומות צו אימפארטירן (Shift פאר א רייע, רווח צו אנצייכענען):')
        label_row.addWidget(info_label)

        label_row.addStretch(1)

        # כפתורי בחירה
        label_row.addWidget(self.select_page_btn)
        label_row.addWidget(self.select_all_btn)
        label_row.addWidget(self.deselect_all_btn)
        label_row.addWidget(self.show_selection_btn)

        return label_row

    def search_result_box(self) -> QLayout:
        label_row = QHBoxLayout()
        label_row.addWidget(self.SearchResultLabel)
        label_row.addWidget(self.prev_cards_button)
        label_row.addWidget(self.next_cards_button)
        label_row.addStretch(1)
        label_row.addWidget(self.selected_count_label)
        self.prev_cards_button.hide()
        self.next_cards_button.hide()
        return label_row

    def make_other_profile_settings_box(self) -> QLayout:
        self.other_profile_deck_row = QHBoxLayout()
        self.other_profile_deck_row.addWidget(self.get_apkg_label)
        self.other_profile_deck_row.addWidget(self.get_apkg_button)
        self.other_profile_deck_row.addWidget(QLabel('פעקל צו ווייזן:'))
        self.other_profile_deck_row.addWidget(self.other_profile_deck_combo)
        return self.other_profile_deck_row

    def set_default_sizes(self):
        combo_min_width = 120
        self.setMinimumSize(640, 480)
        for w in (
            self.import_button,
            self.new_deck_button,
            self.settings_button,
            self.filter_button,
            self.search_term_edit,
        ):
            w.setMinimumHeight(WIDGET_HEIGHT)
        for combo in (
            self.other_profile_deck_combo,
            self.current_profile_deck_combo,
            self.note_type_selection_combo,
        ):
            combo.setMinimumWidth(combo_min_width)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.SearchResultLabel.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

    def set_count(self, found: int, displayed: int, page_start: int = 0):
        if found == 0:
            self.SearchResultLabel.setText('קיין רשומות זענען נישט געפונען געווארן')
            self.SearchResultLabel.setStyleSheet('QLabel { color: red; }')
            self.prev_cards_button.hide()
            self.next_cards_button.hide()
        elif found <= displayed:
            self.SearchResultLabel.setText(f'{found} רשומות געפונען')
            self.SearchResultLabel.setStyleSheet('QLabel { color: green; }')
            self.prev_cards_button.hide()
            self.next_cards_button.hide()
        else:
            page_num = page_start // displayed + 1
            total_pages = (found + displayed - 1) // displayed
            self.SearchResultLabel.setText(f'בלאט {page_num} פון {total_pages} ({found} רשומות)')
            self.SearchResultLabel.setStyleSheet('QLabel { color: orange; }')
            self.next_cards_button.setVisible(page_start + displayed < found)
            self.prev_cards_button.setVisible(page_start > 0)
        if self.SearchResultLabel.isHidden():
            self.SearchResultLabel.show()

    def dest_row(self) -> QLayout:
        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel('אימפארטירט צום פעקל:'))
        dest_row.addWidget(self.current_profile_deck_combo)
        dest_row.addWidget(self.new_deck_button)
        dest_row.addWidget(QLabel('טוישט דעם שאלה סארט צו:'))
        dest_row.addWidget(self.note_type_selection_combo)
        return dest_row

    def make_input_row(self) -> QLayout:
        import_row = QHBoxLayout()
        import_row.addStretch(1)
        import_row.addWidget(self.settings_button)
        import_row.addWidget(self.import_button)
        return import_row

#############################################################################
# UI logic
#############################################################################

class WindowState:
    def __init__(self, window: MainDialogUI):
        self._window = window
        self._json_filepath = os.path.join(os.path.dirname(__file__), 'user_files', 'window_state.json')
        self._map = {
            "from_deck": self._window.other_profile_deck_combo,
            "to_deck": self._window.current_profile_deck_combo,
            "note_type": self._window.note_type_selection_combo,
        }
        self._state = defaultdict(dict)

    def save(self):
        for key, widget in self._map.items():
            self._state[mw.pm.name][key] = widget.currentText()
        try:
            os.makedirs(os.path.dirname(self._json_filepath), exist_ok=True)
            with open(self._json_filepath, 'w', encoding='utf8') as of:
                json.dump(self._state, of, indent=4, ensure_ascii=False)
        except Exception:
            from _shared_libs.haf_notifications import warn_once
            warn_once("external-import:window", "דער צושטאנד פונעם אימפארט פענצטער איז נישט אפגעזיכערט. די אויסוואלן אינעם פענצטער קענען זיך צוריקשטעלן ביים קומענדיגן עפענען.")
        saveGeom(self._window, self._window.name)
        logDebug('saved window state.')

    def _load(self) -> bool:
        if self._state:
            return True
        elif os.path.isfile(self._json_filepath):
            try:
                with open(self._json_filepath, encoding='utf8') as f:
                    self._state.update(json.load(f))
                return True
            except (OSError, json.JSONDecodeError, ValueError):
                return False
        else:
            return False

    def restore(self):
        if self._load() and (profile_settings := self._state.get(mw.pm.name)):
            for key, widget in self._map.items():
                if (value := profile_settings[key]) in widget.all_items():
                    widget.setCurrentText(value)
        restoreGeom(self._window, self._window.name, adjustSize=True)

class MainDialog(MainDialogUI):
    def __init__(self, current_col="",temp_col:Collection = None, temp_col_path:str = None, col_list=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_col:str = current_col
        self.col_list = col_list
        self.col_dict = {}
        self._checked_ids = set()
        self._imported_session_ids = set()
        self.window_state = WindowState(self)
        self.other_col = CollectionManager()
        self.connect_elements()
        self.temp_col_path = temp_col_path
        self.temp_col = temp_col
        disable_help_button(self)

    def connect_elements(self):
        qconnect(self.get_apkg_button.clicked, self.get_apkg)
        qconnect(self.settings_button.clicked, self.on_open_settings)
        qconnect(self.import_button.clicked, self.do_import)
        qconnect(self.filter_button.clicked, self.update_notes_list)
        qconnect(self.new_deck_button.clicked, self.on_new_deck)
        qconnect(self.search_term_edit.editingFinished, self.update_notes_list)
        qconnect(self.other_profile_deck_combo.currentIndexChanged, self.update_notes_list)
        qconnect(self.next_cards_button.clicked, lambda :self.update_notes_list(next_notes=True))
        qconnect(self.prev_cards_button.clicked, lambda :self.update_notes_list(prev_notes=True))

        # חיבור כפתורי הבחירה
        qconnect(self.select_page_btn.clicked, self.note_list.check_all)
        qconnect(self.select_all_btn.clicked, self._select_all_global)
        qconnect(self.deselect_all_btn.clicked, self._clear_all_selections)
        qconnect(self.show_selection_btn.clicked, self._show_selection_dialog)
        qconnect(self.note_list.selectionChanged, self._on_note_check_changed)

    def show(self):
        super().show()
        if self.current_col == "" and self.col_list is None and self.temp_col_path is None:# normal use
            self.get_apkg()
        elif self.col_list is not None:
            self.other_profile_deck_row.deleteLater()
            self.settings_button.deleteLater()
            self.populate_ui()
            self.update_notes_list()

        elif self.temp_col_path is not None:
            self.current_col = self.temp_col_path
            self.settings_button.hide()
            self.get_apkg_label.hide()
            self.get_apkg_button.hide()
            self.open_temp_col()
            self.populate_other_profile_decks()
            self.populate_ui()
            self.update_notes_list()

        else:
            self.get_apkg_button.setText(self.current_col.replace("\\", "/").split("/")[-1])
            self.other_col.open(self.current_col)
            self.populate_other_profile_decks()
            self.populate_ui()
            self.search_term_edit.setFocus()

    def populate_ui(self):
        self.status_bar.hide()
        self.populate_note_type_selection_combo()
        self.populate_current_profile_decks()
        self.into_profile_label.setText(mw.pm.name or 'אומבאקאנט')
        self.window_state.restore()

    def populate_note_type_selection_combo(self):
        self.note_type_selection_combo.clear()
        self.note_type_selection_combo.addItem(*NameId.none_type())
        for note_type in mw.col.models.all_names_and_ids():
            self.note_type_selection_combo.addItem(note_type.name, note_type.id)

    def on_new_deck(self):
        existing_ids = {d.id for d in mw.col.decks.all_names_and_ids()}
        if op := add_deck_dialog(parent=self):
            op.success(lambda _out: self._on_deck_created(existing_ids)).run_in_background()

    def _on_deck_created(self, old_ids):
        self.populate_current_profile_decks()
        for i in range(self.current_profile_deck_combo.count()):
            did = self.current_profile_deck_combo.itemData(i)
            if did not in old_ids and did != -1:
                self.current_profile_deck_combo.setCurrentIndex(i)
                return

    def get_apkg(self):
        col_name = getFile(parent=mw,
            title="טיילווייז אימפארטירן פעקלעך",
            cb=None,
            filter="*.apkg *.colpkg"
        )
        if isinstance(col_name, str):
            self.current_col = col_name
            self.open_apkg()

    def open_temp_col(self):
        col_name = self.current_col
        if not self.other_col.is_opened or col_name != self.other_col.name:
            self.other_col.open(col_name, self.temp_col)
            self.populate_other_profile_decks()

    def open_apkg(self):
        col_name = self.current_col
        if not self.other_col.is_opened or col_name != self.other_col.name:
            self.get_apkg_button.setText(col_name.replace("\\", "/").split("/")[-1])
            self.other_col.open(col_name)
            self.populate_other_profile_decks()
            self.populate_ui()

    def populate_current_profile_decks(self):
        logDebug("populating current profile decks...")
        self.current_profile_deck_combo.set_decks(sorted_decks_and_ids(mw.col))
        self.current_profile_deck_combo.addItem("אן ענדערונג פונעם אריגינעל", -1)
        # #bugfix — בחירה לפי index מבטיחה שנבחר ה-sentinel (data=-1) ולא חפיסה אמיתית באותו שם
        self.current_profile_deck_combo.setCurrentIndex(self.current_profile_deck_combo.count() - 1)

    def populate_other_profile_decks(self):
        logDebug("populating other profile decks...")
        self.other_profile_deck_combo.set_decks([
            self.other_col.col_name_and_id(), *self.other_col.deck_names_and_ids(),
        ])

    def update_notes_list(self, next_notes:bool = False, prev_notes:bool = False ):
        note_limit_end = config['max_displayed_notes']
        self.search_term_edit.setFocus()
        self.SearchResultLabel.hide()
        if next_notes:
            self.range += note_limit_end
        elif prev_notes:
            if self.range - note_limit_end >= 0:
                self.range -= note_limit_end
            else:
                self.range = 0
        else:
            self.range = 0

        if self.col_list is None:
            if self.temp_col_path is None:
                self.open_apkg()
            if not self.search_term_edit.text() and not config['allow_empty_search']:
                return
            if self.other_profile_deck_combo.count() < 1:
                return
            try:
                deck = self.other_profile_deck_combo.current_deck()
                search_text = self.search_term_edit.text()
                note_ids = self.other_col.find_notes(deck, search_text)
                # #139 — בהגדרת הסתרה מסירים מהרשימה שאלות שכבר יובאו בסשן הנוכחי.
                if config.get("hide_imported_in_session"):
                    note_ids = [nid for nid in note_ids if nid not in self._imported_session_ids]
                limited_note_ids = note_ids[self.range:self.range + note_limit_end]
                len_total_nids = len(note_ids)
                self.note_list.set_notes(
                    map(self.other_col.get_note, limited_note_ids),
                    hide_fields=config['hidden_fields'],
                    media_dir=self.other_col.media_dir,
                    previewer=config['preview_on_right_side'],
                    selected_ids=self._checked_ids,
                    imported_ids=self._imported_session_ids if config.get("mark_imported_in_session") else set(),
                )
            except Exception as e:
                from _shared_libs.haf_notifications import show_failure
                show_failure("מען קען נישט ווייזן די רשומות צו אימפארטירן. קאנטראלירט דעם מקור פון די שאלות און די זוכן באדינגונגען און פרובירט נאכאמאל.", e, parent=self)
                return
        else: #מאגר השאלות
            try:
                len_total_nids = 0
                self.note_list.clear()
                for col_path in self.col_list:
                    col_file = col_path
                    cm = CollectionManager()
                    cm.open(col_file)
                    self.col_dict[col_file] = cm
                    note_ids = cm.find_notes(cm.col_name_and_id(), self.search_term_edit.text())
                    if config.get("hide_imported_in_session"):
                        note_ids = [nid for nid in note_ids if nid not in self._imported_session_ids]
                    local_start = max(0, self.range - len_total_nids)
                    local_end = self.range + note_limit_end - len_total_nids
                    if local_end > 0 and local_start < len(note_ids):
                        limited_note_ids = note_ids[local_start:local_end]
                        self.note_list.add_notes(
                            map(cm.get_note, limited_note_ids),
                            hide_fields=config['hidden_fields'],
                            media_dir=cm.media_dir,
                            previewer=config['preview_on_right_side'],
                            selected_ids=self._checked_ids,
                            imported_ids=self._imported_session_ids if config.get("mark_imported_in_session") else set(),
                        )
                    len_total_nids += len(note_ids)
            except Exception as e:
                from _shared_libs.haf_notifications import show_failure
                show_failure("מען קען נישט ווייזן די רשומות פונעם שאלות מאגר. קאנטראלירט די מקורות און די זוכן באדינגונגען און פרובירט נאכאמאל.", e, parent=self)
                return
        self.set_count(len_total_nids, note_limit_end, self.range)

    def do_import(self):
        logDebug('beginning import')
        # #multi-page-import — קח את כל הרשומות המסומנות מכל העמודים (לא רק מהעמוד הנוכחי).
        notes = self._get_all_checked_notes_for_import()

        # clear the selection
        self.note_list.clear_selection()

        logDebug(f'importing {len(notes)} notes')

        results = []
        imported_note_ids = []
        imported_source_ids = []
        skipped_duplicate_source_ids = []

        total_notes = len(notes)
        mw.progress.start(label=f"אימפארטירט רשומות... (0/{total_notes})", immediate=True)
        try:
            for index, note in enumerate(notes, start=1):
                mw.progress.update(label=f"אימפארטירט רשומות... ({index}/{total_notes})")
                QApplication.processEvents()

                deck_name = self.current_profile_deck_combo.currentText()
                if self.current_profile_deck_combo.currentData() == -1:
                    card_ids = note.card_ids()
                    if card_ids:
                        note_did = self.other_col.col.db.scalar(
                            "SELECT did FROM cards WHERE id = ?", card_ids[0]
                        )
                        if note_did:
                            found_name = self.other_col.col.decks.name_if_exists(note_did)
                            if found_name:
                                deck_name = found_name
                result, note_id = import_note(
                    other_note=note,
                    model_id=self.note_type_selection_combo.current_data_safe(),
                    deck_name=deck_name,
                )
                results.append(result)
                if note_id is not None:
                    imported_note_ids.append(note_id)
                    imported_source_ids.append(note.id)
                elif result == ImportResult.dupe:
                    skipped_duplicate_source_ids.append(note.id)
        finally:
            mw.progress.finish()

        logDebug(f"imported note IDs: {imported_note_ids}")

        # #139 — לאחר ייבוא חלקי מסמנים או מסתירים את המקורות שיובאו, לפי ההגדרה.
        if imported_source_ids:
            self._imported_session_ids.update(imported_source_ids)
            self._checked_ids.difference_update(imported_source_ids)
            if config.get("hide_imported_in_session"):
                self.update_notes_list()
            elif config.get("mark_imported_in_session"):
                self.note_list.mark_imported(imported_source_ids)
            self._update_selection_label()

        # #139 — רשומות שדולגו כי הן כבר קיימות נשארות ברשימה ומסומנות בכתום, כדי שהמשתמש יבין למה לא יובאו.
        if skipped_duplicate_source_ids and config.get("mark_imported_in_session"):
            self._checked_ids.difference_update(skipped_duplicate_source_ids)
            self.note_list.mark_skipped_duplicates(skipped_duplicate_source_ids)
            self._update_selection_label()

        self.status_bar.set_status(results.count(ImportResult.success), results.count(ImportResult.dupe))
        mw.reset()

        # #148 — איחוד סוגי רשומות כפולים שנוצרו בייבוא מפרופיל אחר
        # ביטול של זה כדי לבדוק אם עובד טוב גם בלי פתרון משל בית חולים מתחת לגשר
        if imported_note_ids:
            from . import note_type_consolidator
            note_type_consolidator.run_auto_consolidation(manual=False, force=True)

    def _on_note_check_changed(self, note_id, is_checked):
        if is_checked:
            self._checked_ids.add(note_id)
        else:
            self._checked_ids.discard(note_id)
        self._update_selection_label()

    def _update_selection_label(self):
        count = len(self._checked_ids)
        self.selected_count_label.setText(f'{count} אויסגעקליבן')
        self.show_selection_btn.setText(f'ווייזט די אויסגעקליבענע ({count})')

    def _get_all_checked_notes_for_import(self) -> list:
        """#multi-page-import — מחזיר Note objects לכל ה-IDs ב-_checked_ids מכל העמודים,
        לא רק מהעמוד הנוכחי שמוצג ב-NoteList."""
        if not self._checked_ids:
            return []

        from anki.errors import NotFoundError

        notes = []
        if self.col_list is None:
            # מצב אוסף בודד (apkg / temp_col)
            for nid in self._checked_ids:
                try:
                    notes.append(self.other_col.get_note(nid))
                except Exception as exc:
                    raise RuntimeError(f"דער אימפארט איז אפגעשטעלט: מען קען נישט לייענען די אנגעצייכנטע רשומה {nid}") from exc
        else:
            # מאגר שאלות — כמה אוספים; מחפש כל ID בכל האוספים
            for nid in self._checked_ids:
                for col_file in self.col_list:
                    cm = self.col_dict.get(col_file)
                    if cm is None:
                        continue
                    try:
                        notes.append(cm.get_note(nid))
                        break  # נמצא — עוברים ל-ID הבא
                    except NotFoundError:
                        continue
                else:
                    raise RuntimeError(f"דער אימפארט איז אפגעשטעלט: די אנגעצייכנטע רשומה {nid} איז נישט געפונען געווארן אין די מקור זאמלונגען")
        return notes

    def _collect_matching_note_ids(self) -> set:
        """אוסף את כל מזהי הרשומות שתואמות לפילטר הנוכחי בכל העמודים."""
        if self.col_list is None:
            if self.temp_col_path is None and not self.other_col.is_opened:
                self.open_apkg()
            if not self.other_col.is_opened:
                return set()
            return set(self.other_col.find_notes(
                self.other_profile_deck_combo.current_deck(),
                self.search_term_edit.text(),
            ))

        all_ids = set()
        for col_file in self.col_list:
            cm = self.col_dict.get(col_file)
            if cm is None:
                cm = CollectionManager()
                cm.open(col_file)
                self.col_dict[col_file] = cm
            note_ids = cm.find_notes(cm.col_name_and_id(), self.search_term_edit.text())
            all_ids.update(note_ids)
        return all_ids

    def _select_all_global(self):
        """צייכנט אן אלע רשומות אויף אלע בלעטער"""
        note_ids = self._collect_matching_note_ids()
        if not note_ids:
            return
        self._checked_ids.update(note_ids)
        self.note_list.check_all()
        self._update_selection_label()

    def _clear_all_selections(self):
        """נעמט אראפ אלע אויסוואלן אויף אלע בלעטער"""
        self._checked_ids.clear()
        self.note_list.uncheck_all_silent()
        self._update_selection_label()

    def _show_selection_dialog(self):
        """ווייזט א פענצטער מיט די אויסגעקליבענע רשומות"""
        total = len(self._checked_ids)
        if total == 0:
            showInfo('קיין רשומות זענען נישט אויסגעקליבן.')
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f'אויסגעקליבענע רשומות ({total})')
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f'<b>{total} רשומות אויסגעקליבן אינגאנצן</b>'))

        # רשומות מסומנות בעמוד הנוכחי
        visible_checked = self.note_list.selected_notes()
        if visible_checked:
            layout.addWidget(QLabel(f'אויפן יעצטיגן בלאט ({len(visible_checked)}):'))
            list_widget = QListWidget()
            for note in visible_checked:
                text = note.fields[0] if note.fields else str(note.id)
                text = re.sub(r'<[^>]+>', '', text).strip()
                list_widget.addItem(text[:120] or str(note.id))
            layout.addWidget(list_widget)

        off_page = total - len(visible_checked)
        if off_page > 0:
            layout.addWidget(QLabel(f'{off_page} נאך רשומות אויסגעקליבן אויף אנדערע בלעטער'))

        close_btn = QPushButton('פארמאכן')
        close_btn.clicked.connect(dialog.close)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def on_open_settings(self):
        self.close()
        dialog = CroProSettingsDialog(main_form=self, current_col=self.current_col, parent=mw)
        dialog.exec()

    def done(self, result_code):
        self.window_state.save()
        self.other_col.close_all()
        # #issue — NotePreviewer (AnkiWebView) רשום ב-theme_did_change; קריאה ל-cleanup() מונעת RuntimeError לאחר סגירת הדיאלוג
        try:
            self.note_list._previewer.cleanup()
        except Exception:
            pass
        return super().done(result_code)

    def reset(self):
        gui_hooks.profile_will_close.remove(self.reset)
        self.deleteLater()

def init():
    mw._cropro_main_dialog = MainDialog
    d = MainDialog
    def show_window():
        b = d(parent=mw)
        b.show()
        gui_hooks.profile_will_close.append(b.reset)
    root_menu = mw.form.menuCol
    action = QAction(ADDON_NAME, root_menu)
    action.setIcon(QIcon(f"{Path(__file__).parent.resolve()}/file_open.png"))
    qconnect(action.triggered, show_window)
    root_menu.insertAction(mw.form.menuCol.actions()[4], action)

