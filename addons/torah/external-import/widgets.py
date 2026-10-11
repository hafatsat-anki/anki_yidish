# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
import time
from collections.abc import Collection, Iterable

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import showInfo
from _shared_libs.haf_notifications import warn_once

from .collection_manager import NameId
from .config import config
from .note_previewer import NotePreviewer

WIDGET_HEIGHT = 29


class SpinBox(QSpinBox):
    def __init__(self, min_val: int, max_val: int, step: int, value: int):
        super().__init__()
        self.setRange(min_val, max_val)
        self.setSingleStep(step)
        self.setValue(value)


class ProfileNameLabel(QLabel):
    def __init__(self, *args):
        super().__init__(*args)
        font = QFont()
        font.setBold(True)
        self.setFont(font)


class ComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMaximumHeight(WIDGET_HEIGHT)

        # 86. Add search capability to Combos
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Setup Completer for "Contains" filtering and Case Insensitivity
        completer = self.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(completer)

        # Make sure it keeps focus easily
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def focusInEvent(self, e):
        # Select all text when clicked so user can type immediately
        super().focusInEvent(e)
        QTimer.singleShot(0, self.lineEdit().selectAll)

    def all_items(self) -> Iterable[str]:
        for i in range(self.count()):
            yield self.itemText(i)

    def current_data_safe(self):
        if self.currentIndex() != -1:
            return self.currentData()

        # If index is -1 (typed text), try to find exact text match
        text = self.currentText()
        idx = self.findText(text)
        if idx != -1:
            return self.itemData(idx)

        return None

class Next_notes_button(QPushButton):
    def __init__(self, count:int, next:bool = True):
        super().__init__()
        qconnect(self.clicked, lambda: self.on_clicked())
        self.next = next
        self.setText(">" if self.next else "<")
        self.count = count

    def on_clicked(self):
        self.max_notes = (self.count, self.count + config['max_displayed_notes'] if self.next else self.count - config['max_displayed_notes'])
        return self.max_notes

class DeckCombo(ComboBox):
    def set_decks(self, decks: Iterable[NameId]):
        self.clear()
        for deck_name, deck_id in decks:
            self.addItem(deck_name, deck_id)

    def current_deck(self) -> NameId:
        return NameId(self.currentText(), self.current_data_safe())

class StatusBar(QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_success_label()
        self._add_dupes_label()
        self.addStretch()
        self.hide()

    def _add_dupes_label(self):
        self._dupes_label = QLabel()
        self._dupes_label.setStyleSheet('QLabel { color: #FF8C00; }')
        self.addWidget(self._dupes_label)

    def _add_success_label(self):
        self._success_label = QLabel()
        self._success_label.setStyleSheet('QLabel { color: #228B22; }')
        self.addWidget(self._success_label)

    def hide(self):
        self._dupes_label.hide()
        self._success_label.hide()

    def set_status(self, successes: int, dupes: int):
        status_info =""
        if successes:
            status_info +=f'{successes} רשומות מיט הצלחה אימפארטירט.'
            self._success_label.setText(f'{successes} רשומות מיט הצלחה אימפארטירט.')
            self._success_label.show()
        else:
            self._success_label.hide()

        if dupes:
            if status_info != "":
                status_info += "\n"
            status_info += f'{dupes} רשומות איבערגעהיפט ווייל זיי עקזיסטירן שוין.'
            self._dupes_label.setText(f'{dupes} רשומות איבערגעהיפט ווייל זיי עקזיסטירן שוין.')
            self._dupes_label.show()
        else:
            self._dupes_label.hide()
        if status_info != "":
            showInfo(status_info)


class ItemBox(QWidget):
    class ItemButton(QPushButton):
        _close_icon = QIcon(QPixmap(os.path.join(os.path.dirname(__file__), 'img', 'close.png')))

        def __init__(self, item_box: 'ItemBox', text: str):
            super().__init__(text)
            self.item_box = item_box
            self.setStyleSheet('''
                QPushButton {
                    background-color: #eef0f2;
                    color: #292c31;
                    border-radius: 12px;
                    padding: 3px 6px;
                    border: 0px;
                }
            ''')
            self.setIcon(self._close_icon)
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            qconnect(self.clicked, lambda: self.item_box.remove_item(text))

    def __init__(self, parent: QWidget, initial_values: list[str]):
        super().__init__(parent=parent)
        self.items = dict.fromkeys(initial_values)
        self.setLayout(self._make_layout())

    def values(self) -> list[str]:
        return list(self.items)

    def _make_layout(self) -> QLayout:
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        for text in self.items:
            self._add_item(text)
        self.layout.addStretch()
        return self.layout

    def count(self) -> int:
        # The last element in the layout is a stretch.
        return self.layout.count() - 1

    def _add_item(self, text: str) -> None:
        b = self.items[text] = self.ItemButton(self, text)
        self.layout.insertWidget(self.count(), b)

    def remove_item(self, text: str) -> None:
        if widget := self.items.pop(text, None):
            widget.deleteLater()

    def new_item(self, edit: QLineEdit) -> None:
        separators = (',', ' ', ';')
        if (text := edit.text()).endswith(separators):
            text = text.strip(''.join(separators))
            if text and text not in self.items:
                self._add_item(text)
                edit.setText('')

class NoteList(QWidget):
    """Lists notes and previews them."""
    _role = Qt.ItemDataRole.UserRole

    # סיגנל שיודיע לדיאלוג הראשי כשמשהו משתנה
    selectionChanged = pyqtSignal(object, bool) # note_id, is_checked

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._note_list = QListWidget(self)
        self._previewer = NotePreviewer(self)
        self._other_media_dir = None
        self._enable_previewer = True

        self._last_clicked_row = -1 # למעקב אחרי Shift range
        self._ignore_next_click = False # למניעת ביטול בעת לחיצה על הריבוע
        self._last_changed_time = 0

        self._drag_check_state: Qt.CheckState | None = None  # None כשאין גרירה
        self._is_dragging = False
        self._drag_current_row = -1

        self._setup_ui()

        # Connect currentItemChanged for previewing
        self._note_list.currentItemChanged.connect(self._on_current_item_changed)
        # Connect check state changes
        self._note_list.itemChanged.connect(self._on_item_changed)
        # הוספת התמיכה בסימון מתקדם
        self._note_list.itemClicked.connect(self._on_item_clicked)
        # שים לב: הסרנו את itemSelectionChanged שגרם לקריסה
        # תמיכה בגרירה לסימון
        self._note_list.viewport().installEventFilter(self)

    def _setup_ui(self):
        self.setLayout(layout := QHBoxLayout())
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        layout.addWidget(splitter := QSplitter(Qt.Orientation.Horizontal))
        splitter.addWidget(self._note_list)
        splitter.addWidget(self._previewer)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, True)
        splitter.setSizes([200, 100])

        self._note_list.setAlternatingRowColors(True)
        self._note_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._note_list.setContentsMargins(0, 0, 0, 0)

        self._previewer.setHidden(True)

    def eventFilter(self, obj, event):
        """מטפל בגרירת עכבר לסימון checkbox וב-Shift+Click"""
        if obj is self._note_list.viewport():
            t = event.type()
            if t == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                modifiers = QApplication.keyboardModifiers()
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    # --- Shift+Click: סמן טווח ---
                    item = self._note_list.itemAt(event.pos())
                    if item and self._last_clicked_row != -1:
                        current_row = self._note_list.row(item)
                        start = min(self._last_clicked_row, current_row)
                        end = max(self._last_clicked_row, current_row)
                        self._note_list.blockSignals(True)
                        for i in range(start, end + 1):
                            it = self._note_list.item(i)
                            it.setCheckState(Qt.CheckState.Checked)
                            note = it.data(self._role)
                            if note:
                                self.selectionChanged.emit(note.id, True)
                        self._note_list.blockSignals(False)
                    return True  # חוסם את האירוע — מונע מ-Qt לעשות ExtendedSelection
                elif (item := self._note_list.itemAt(event.pos())):
                    self._drag_check_state = (
                        Qt.CheckState.Unchecked
                        if item.checkState() == Qt.CheckState.Checked
                        else Qt.CheckState.Checked
                    )
                    self._drag_current_row = self._note_list.row(item)
                    self._is_dragging = False

            elif t == QEvent.Type.MouseMove and self._drag_check_state is not None:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    item = self._note_list.itemAt(event.pos())
                    if item:
                        row = self._note_list.row(item)
                        if row != self._drag_current_row:
                            if not self._is_dragging:
                                self._is_dragging = True
                            # סמן כל השורות מהמיקום הקודם עד הנוכחי (כולל שדות)
                            step = 1 if row > self._drag_current_row else -1
                            self._note_list.blockSignals(True)
                            for r in range(self._drag_current_row, row + step, step):
                                it = self._note_list.item(r)
                                if it:
                                    it.setCheckState(self._drag_check_state)
                                    note = it.data(self._role)
                                    if note:
                                        self.selectionChanged.emit(note.id, self._drag_check_state == Qt.CheckState.Checked)
                            self._note_list.blockSignals(False)
                            self._drag_current_row = row

            elif t == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                was_dragging = self._is_dragging
                self._last_clicked_row = self._drag_current_row
                self._drag_check_state = None
                self._is_dragging = False
                self._drag_current_row = -1
                if was_dragging:
                    return True  # מונע את itemClicked מלהפעיל טוגל נוסף

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """מאפשר להפוך סימון של פריטים נבחרים ע"י מקש רווח"""
        if event.key() == Qt.Key.Key_Space:
            self.toggle_selection_checks()
        else:
            super().keyPressEvent(event)

    def toggle_selection_checks(self):
        """הופך את הסימון (V) של כל השורות המסומנות בכחול (Highlight)"""
        selected_items = self._note_list.selectedItems()
        if not selected_items:
            return

        # בדיקה האם הרוב מסומן או לא, כדי להחליט אם לסמן הכל או לבטל הכל
        checked_count = sum(1 for item in selected_items if item.checkState() == Qt.CheckState.Checked)
        new_state = Qt.CheckState.Unchecked if checked_count == len(selected_items) else Qt.CheckState.Checked

        self._note_list.blockSignals(True)
        for item in selected_items:
            item.setCheckState(new_state)
            note = item.data(self._role)
            self.selectionChanged.emit(note.id, new_state == Qt.CheckState.Checked)
        self._note_list.blockSignals(False)

    def _on_current_item_changed(self, current: QListWidgetItem, _previous: QListWidgetItem):
        if current is None or self._enable_previewer is False:
            self._previewer.setHidden(True)
        else:
            self._previewer.setHidden(False)
            self._previewer.load_note(current.data(self._role), self._other_media_dir)

    def _on_item_changed(self, item: QListWidgetItem):
        # מעדכן timestamp כדי לדעת שהשינוי בוצע כרגע (למשל ע"י לחיצה ישירה על הריבוע)
        self._last_changed_time = time.time()

        note = item.data(self._role)
        if note:
            is_checked = item.checkState() == Qt.CheckState.Checked
            self.selectionChanged.emit(note.id, is_checked)

    def _on_item_clicked(self, item: QListWidgetItem):
        """מטפל בלחיצה על שורה לסימון הצ'קבוקס, כולל תמיכה חכמה ב-Shift"""
        current_row = self._note_list.row(item)
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.KeyboardModifier.ShiftModifier and self._last_clicked_row != -1:
            # --- טיפול בטווח (SHIFT) בצורה ידנית ---
            start = min(self._last_clicked_row, current_row)
            end = max(self._last_clicked_row, current_row)
            target_state = Qt.CheckState.Checked

            self._note_list.blockSignals(True)
            for i in range(start, end + 1):
                it = self._note_list.item(i)
                it.setCheckState(target_state)
                note = it.data(self._role)
                self.selectionChanged.emit(note.id, True)
            self._note_list.blockSignals(False)

        else:
            # --- טיפול בקליק רגיל ---
            # אם השינוי קרה ממש עכשיו, סימן שלחצו על הריבוע עצמו
            if time.time() - self._last_changed_time < 0.1:
                self._last_clicked_row = current_row
                return

            self._last_clicked_row = current_row

            if modifiers == Qt.KeyboardModifier.NoModifier:
                 new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                 item.setCheckState(new_state)
                 self._on_item_changed(item)

    def check_all(self):
        """מסמן V בכל השורות ברשימה"""
        self._note_list.blockSignals(True)
        for i in range(self._note_list.count()):
            item = self._note_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
            note = item.data(self._role)
            self.selectionChanged.emit(note.id, True)
        self._note_list.blockSignals(False)


    def uncheck_all_silent(self):
        """מבטל V מכל השורות ללא שליחת סיגנלים"""
        self._note_list.blockSignals(True)
        for i in range(self._note_list.count()):
            self._note_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self._note_list.blockSignals(False)

    # --- פונקציות תאימות לקוד הישן ---

    def selected_notes(self) -> Collection[Note]:
        """מחזיר את כל הרשומות שהצ'קבוקס שלהן מסומן ב-V"""
        notes = []
        for i in range(self._note_list.count()):
            item = self._note_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                notes.append(item.data(self._role))
        return notes


    def checked_count(self) -> int:
        """מחזיר כמה שורות מסומנות כרגע ב-V"""
        return sum(
            1 for i in range(self._note_list.count())
            if self._note_list.item(i).checkState() == Qt.CheckState.Checked
        )

    def clear_selection(self):
        self._note_list.clearSelection()

    def clear(self):
        self._note_list.clear()
        self._last_clicked_row = -1

    def _mark_item_imported(self, item: QListWidgetItem) -> None:
        # #139 — צבעי סימון שונים למצב יום/לילה שומרים על קריאות אחרי ייבוא חלקי.
        item.setBackground(QColor("#305c3a" if theme_manager.night_mode else "#d3f8d3"))
        item.setForeground(QColor("#f5fff5" if theme_manager.night_mode else "#1d3b21"))
        item.setToolTip("אימפארטירט אין דער יעצטיגער סעסיע")

    def _mark_item_skipped_duplicate(self, item: QListWidgetItem) -> None:
        # #139 — כפולים שדולגו מסומנים בכתום נפרד מהירוק של ייבוא מוצלח.
        item.setBackground(QColor("#704214" if theme_manager.night_mode else "#ffe0a3"))
        item.setForeground(QColor("#fff7ea" if theme_manager.night_mode else "#5a3100"))
        item.setToolTip("איבערגעהיפט ווייל די רשומה עקזיסטירט שוין")

    def _create_item(self, note: Note, hide_fields: list[str], is_selected: bool, is_imported: bool = False) -> QListWidgetItem:
        def is_hidden(field_name: str) -> bool:
            field_name = field_name.lower()
            return any(hidden_field.lower() in field_name for hidden_field in hide_fields)

        item = QListWidgetItem()
        item.setText(' | '.join(
            html_to_text_line(field_content)
            for field_name, field_content in note.items()
            if not is_hidden(field_name) and field_content.strip())
        )
        item.setData(self._role, note)

        # הגדרת Checkbox
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if is_selected else Qt.CheckState.Unchecked)
        if is_imported:
            self._mark_item_imported(item)

        return item

    def set_notes(self, notes: Iterable[Note], hide_fields: list[str], media_dir: str, previewer: bool = True, selected_ids: set = None, imported_ids: set = None):
        if selected_ids is None:
            selected_ids = set()
        if imported_ids is None:
            imported_ids = set()
        self._other_media_dir = media_dir
        self._enable_previewer = previewer

        # חסימת סיגנלים בזמן הבנייה כדי לא להפעיל את ה-selectionChanged סתם
        self._note_list.blockSignals(True)
        self.clear()

        # materialize ה-map כדי לתפוס exceptions מ-get_note לפני האיטרציה
        try:
            notes_list = list(notes)
        except Exception:
            warn_once("external-import:note-list", "מען קען נישט לאדן די ליסטע פון רשומות צו אימפארטירן. באנייט דעם זוכן איידער איר קלייבט אויס רשומות.")
            notes_list = []

        for note in notes_list:
            is_selected = note.id in selected_ids
            try:
                item = self._create_item(note, hide_fields, is_selected, note.id in imported_ids)
                self._note_list.addItem(item)
            except Exception:
                pass
        self._note_list.blockSignals(False)

    def add_notes(self, notes: Iterable[Note], hide_fields: list[str], media_dir: str, previewer: bool = True, selected_ids: set = None, imported_ids: set = None):
        if selected_ids is None:
            selected_ids = set()
        if imported_ids is None:
            imported_ids = set()
        self._other_media_dir = media_dir
        self._enable_previewer = previewer

        self._note_list.blockSignals(True)
        for note in notes:
            is_selected = note.id in selected_ids
            item = self._create_item(note, hide_fields, is_selected, note.id in imported_ids)
            self._note_list.addItem(item)
        self._note_list.blockSignals(False)
    def mark_imported(self, imported_note_ids: list):
        self._note_list.blockSignals(True)
        for i in range(self._note_list.count()):
            item = self._note_list.item(i)
            note = item.data(self._role)
            if note.id in imported_note_ids:
                item.setCheckState(Qt.CheckState.Unchecked)
                self._mark_item_imported(item)
        self._note_list.blockSignals(False)

    def mark_skipped_duplicates(self, skipped_note_ids: list):
        self._note_list.blockSignals(True)
        for i in range(self._note_list.count()):
            item = self._note_list.item(i)
            note = item.data(self._role)
            if note.id in skipped_note_ids:
                item.setCheckState(Qt.CheckState.Unchecked)
                self._mark_item_skipped_duplicate(item)
        self._note_list.blockSignals(False)
