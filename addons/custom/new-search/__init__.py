import contextlib
import re
import sys
from datetime import date
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import showInfo


# #153 — stylesheet מרכזי לחלון החיפוש המתקדם כדי לשמור על קריאות במצב יום ולילה.
def _advanced_search_stylesheet() -> str:
    if theme_manager.night_mode:
        return """
            QDockWidget, QWidget { background: #242628; color: #f0f0f0; }
            QLabel, QCheckBox, QRadioButton { color: #f0f0f0; background: transparent; }
            QLineEdit, QComboBox, QSpinBox, QScrollArea {
                background: #303336; color: #f5f5f5; border: 1px solid #555; border-radius: 3px;
            }
            QComboBox QAbstractItemView { background: #303336; color: #f5f5f5; selection-background-color: #3f6fa8; }
            QToolButton { color: #f0f0f0; background: transparent; }
        """
    return """
        QDockWidget, QWidget { background: #ffffff; color: #202020; }
        QLabel, QCheckBox, QRadioButton { color: #202020; background: transparent; }
        QLineEdit, QComboBox, QSpinBox, QScrollArea {
            background: #ffffff; color: #202020; border: 1px solid #c8c8c8; border-radius: 3px;
        }
        QComboBox QAbstractItemView { background: #ffffff; color: #202020; selection-background-color: #e8f1ff; }
    """


def _collapsible_button_stylesheet() -> str:
    # #153 — כותרות אזורי החיפוש מקבלות צבע מפורש לפי מצב התצוגה כדי שלא ייעלמו במצב כהה.
    if theme_manager.night_mode:
        return (
            "QToolButton{font-weight:bold;font-size:12px;border:none;"
            "text-align:right;padding:4px 0;color:#f0f0f0;background:transparent;}"
            "QToolButton:hover{color:#8fc8ff;}"
        )
    return (
        "QToolButton{font-weight:bold;font-size:12px;border:none;"
        "text-align:right;padding:4px 0;color:#2a2a2a;background:transparent;}"
        "QToolButton:hover{color:#005f9e;}"
    )


def _reset_button_stylesheet() -> str:
    if theme_manager.night_mode:
        return (
            "QToolButton{border:none;color:#c8c8c8;font-size:14px;background:transparent;}"
            "QToolButton:hover{color:#ffb199;}"
        )
    return (
        "QToolButton{border:none;color:#777;font-size:14px;background:transparent;}"
        "QToolButton:hover{color:#cc4400;}"
    )


class SelectAllSpinBox(QSpinBox):
    # #152 — לחיצה על שדה מספרי בחיפוש המתקדם מסמנת את כל הערך להחלפה מהירה.
    def _select_all_later(self) -> None:
        QTimer.singleShot(0, self.lineEdit().selectAll)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._select_all_later()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._select_all_later()


def _retrievability_query_parts(min_value: int, max_value: int) -> list[str]:
    # #152 — Anki משתמש ב-prop:r לערך יכולת אחזור בין 0 ל-1; ה-UI מציג אחוזים למשתמש.
    parts: list[str] = []
    if min_value:
        parts.append(f"prop:r>={min_value / 100:.2f}")
    if max_value:
        parts.append(f"prop:r<={max_value / 100:.2f}")
    return parts

def _load_pyluach_hebrew_date():
    try:
        from pyluach.dates import HebrewDate as _HebDate  # type: ignore
        return _HebDate
    except ImportError:
        pass

    candidates = [
        Path(__file__).resolve().parents[1] / "shared_libs",
        Path(__file__).resolve().parents[2] / "shared_libs",
        Path(__file__).resolve().parents[3] / "shared_libs",
    ]
    for candidate in candidates:
        if candidate.exists() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
            try:
                from pyluach.dates import HebrewDate as _HebDate  # type: ignore
                return _HebDate
            except ImportError:
                continue

    return None


PyluachHebrewDate = _load_pyluach_hebrew_date()


_XRID_TOKEN_RE = re.compile(r"xrid:(\d+):(\d+):([la]):([0-9]+):([0-9]+):(\d+)")


def _query_revlog_cids(
    start_ms: int,
    end_ms: int,
    is_last_mode: bool,
    ease_vals: list[int],
    type_vals: list[int],
    min_reviews: int,
) -> list[int]:
    ease_clause = ""
    type_clause = ""
    ease_params: list[int] = []
    type_params: list[int] = []

    if ease_vals:
        ease_clause = f" AND ease IN ({','.join('?' for _ in ease_vals)})"
        ease_params.extend(ease_vals)
    if type_vals:
        type_clause = f" AND type IN ({','.join('?' for _ in type_vals)})"
        type_params.extend(type_vals)

    if is_last_mode:
        sql = (
            "SELECT r.cid FROM revlog r "
            "JOIN ("
            "  SELECT cid, max(id) AS max_id FROM revlog "
            "  WHERE id BETWEEN ? AND ?"
            f"{type_clause}"
            "  GROUP BY cid"
            ") t ON r.cid = t.cid AND r.id = t.max_id "
            "WHERE 1=1"
            f"{ease_clause}"
            f"{type_clause}"
        )
        params = [start_ms, end_ms]
        params.extend(type_params)
        params.extend(ease_params)
        params.extend(type_params)

        if min_reviews:
            sql += (
                " AND (SELECT count() FROM revlog "
                "WHERE cid = r.cid AND id BETWEEN ? AND ?"
                f"{type_clause}"
                ") >= ?"
            )
            params.extend([start_ms, end_ms])
            params.extend(type_params)
            params.append(min_reviews)
    else:
        sql = (
            "SELECT cid FROM revlog WHERE id BETWEEN ? AND ?"
            f"{ease_clause}{type_clause} "
            "GROUP BY cid"
        )
        params = [start_ms, end_ms]
        params.extend(ease_params)
        params.extend(type_params)
        if min_reviews:
            sql += " HAVING count() >= ?"
            params.append(min_reviews)

    return [int(cid) for (cid,) in mw.col.db.all(sql, *params)]


def _parse_digit_list(raw: str, allowed: set[int]) -> list[int]:
    if raw == "0":
        return []
    vals: list[int] = []
    for ch in raw:
        val = int(ch)
        if val in allowed and val not in vals:
            vals.append(val)
    return vals


def _on_browser_will_search(search_context):
    search = search_context.search
    match = _XRID_TOKEN_RE.search(search)
    if not match:
        return

    start_ms = int(match.group(1))
    end_ms = int(match.group(2))
    is_last_mode = match.group(3) == "l"
    ease_vals = _parse_digit_list(match.group(4), {1, 2, 3, 4})
    type_vals = _parse_digit_list(match.group(5), {0, 1, 2, 3})
    min_reviews = int(match.group(6))

    found_ids = _query_revlog_cids(
        start_ms, end_ms, is_last_mode, ease_vals, type_vals, min_reviews
    )

    cleaned_search = _XRID_TOKEN_RE.sub("", search).strip()
    # Always update search so Anki never sees the unknown xrid: token
    search_context.search = cleaned_search if cleaned_search else ""

    if cleaned_search:
        try:
            other_ids = set(mw.col.find_cards(cleaned_search))
            final_ids = [cid for cid in found_ids if cid in other_ids]
        except Exception:
            final_ids = found_ids
    else:
        final_ids = found_ids

    search_context.ids = final_ids


# --- Hebrew Date Converter Implementation (Embedded to avoid dependencies) ---
class HebDate:
    def __init__(self):
        pass


    @staticmethod
    def gematria(num):
        # Simple Gematria for 1-999
        if num <= 0:
            return str(num)
        letters = [
            (400, "ת"), (300, "ש"), (200, "ר"), (100, "ק"),
            (90, "צ"), (80, "פ"), (70, "ע"), (60, "ס"), (50, "נ"), (40, "מ"), (30, "ל"), (20, "כ"), (10, "י"),
            (9, "ט"), (8, "ח"), (7, "ז"), (6, "ו"), (5, "ה"), (4, "ד"), (3, "ג"), (2, "ב"), (1, "א")
        ]
        res = ""
        # Handle 15/16 logic
        if num == 15:
            return "טו"
        if num == 16:
            return "טז"

        for val, let in letters:
            while num >= val:
                res += let
                num -= val

        # Add geresh or gershayim
        if len(res) == 1:
            res += "'"
        elif len(res) > 1:
            res = res[:-1] + '"' + res[-1]
        return res

# Since implementing the full calendar math in one file is too risky for bugs,
# we will use the following library-free approach:
# We'll try to find 'hebdatelib' (from the user's list) or standard simple mapping.
# If unavailable, we show a polite message.



class HebrewDateComboWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._months_order = [7, 8, 9, 10, 11, 12, 13, 1, 2, 3, 4, 5, 6]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.day_combo = QComboBox()
        self.month_combo = QComboBox()
        self.year_combo = QComboBox()

        self.day_combo.setEditable(True)
        self.month_combo.setEditable(True)
        self.year_combo.setEditable(True)
        self.day_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.month_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.year_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        layout.addWidget(self.day_combo)
        layout.addWidget(self.month_combo)
        layout.addWidget(self.year_combo)

        self._populate_years()
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        self.year_combo.lineEdit().editingFinished.connect(
            lambda: self._sync_combo_to_text(self.year_combo)
        )
        self.month_combo.lineEdit().editingFinished.connect(
            lambda: self._sync_combo_to_text(self.month_combo)
        )
        self.day_combo.lineEdit().editingFinished.connect(
            lambda: self._sync_combo_to_text(self.day_combo)
        )
        self._on_year_changed()

    def _hebrew_year_label(self, year: int) -> str:
        if PyluachHebrewDate is not None:
            try:
                return PyluachHebrewDate(year, 7, 1).hebrew_year(False)
            except Exception:
                pass
        return HebDate.gematria(year % 1000)

    def _sync_combo_to_text(self, combo: QComboBox) -> None:
        text = combo.currentText().strip()
        if not text:
            return

        idx = combo.findText(text, Qt.MatchFlag.MatchFixedString)
        if idx < 0:
            idx = combo.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _populate_years(self) -> None:
        # תשס"ה = 5765
        start_year = 5765
        end_year = 5810
        if PyluachHebrewDate is not None:
            try:
                end_year = max(end_year, PyluachHebrewDate.today().year + 2)
            except Exception:
                pass

        for year in range(start_year, end_year + 1):
            label = self._hebrew_year_label(year)
            self.year_combo.addItem(label, year)

    def _month_items_for_year(self, year: int) -> list[tuple[str, int]]:
        items: list[tuple[str, int]] = []
        for month in self._months_order:
            if PyluachHebrewDate is None:
                items.append((str(month), month))
                continue
            try:
                name = PyluachHebrewDate(year, month, 1).month_name(hebrew=True)
                items.append((name, month))
            except Exception:
                continue
        return items

    def _on_year_changed(self) -> None:
        year = self.selected_year()
        prev_month = self.selected_month()

        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        for name, month in self._month_items_for_year(year):
            self.month_combo.addItem(name, month)
        self.month_combo.blockSignals(False)

        if prev_month is not None:
            idx = self.month_combo.findData(prev_month)
            if idx >= 0:
                self.month_combo.setCurrentIndex(idx)

        self._on_month_changed()

    def _on_month_changed(self) -> None:
        year = self.selected_year()
        month = self.selected_month()
        prev_day = self.selected_day()

        max_days = 30
        if PyluachHebrewDate is not None and month is not None:
            for day in range(30, 0, -1):
                try:
                    PyluachHebrewDate(year, month, day)
                    max_days = day
                    break
                except Exception:
                    continue

        self.day_combo.clear()
        for day in range(1, max_days + 1):
            self.day_combo.addItem(HebDate.gematria(day), day)

        if prev_day is not None:
            idx = self.day_combo.findData(min(prev_day, max_days))
            if idx >= 0:
                self.day_combo.setCurrentIndex(idx)

    def selected_year(self) -> int:
        return int(self.year_combo.currentData())

    def selected_month(self) -> int | None:
        val = self.month_combo.currentData()
        return int(val) if val is not None else None

    def selected_day(self) -> int | None:
        val = self.day_combo.currentData()
        return int(val) if val is not None else None

    def set_qdate(self, qdate: QDate) -> None:
        if PyluachHebrewDate is None:
            return
        try:
            py = date(qdate.year(), qdate.month(), qdate.day())
            heb = PyluachHebrewDate.from_pydate(py)
        except Exception:
            return

        year_idx = self.year_combo.findData(heb.year)
        if year_idx >= 0:
            self.year_combo.setCurrentIndex(year_idx)
        month_idx = self.month_combo.findData(heb.month)
        if month_idx >= 0:
            self.month_combo.setCurrentIndex(month_idx)
        day_idx = self.day_combo.findData(heb.day)
        if day_idx >= 0:
            self.day_combo.setCurrentIndex(day_idx)

    def qdate(self) -> QDate:
        if PyluachHebrewDate is None:
            return QDate.currentDate()

        year = self.selected_year()
        month = self.selected_month()
        day = self.selected_day()
        if month is None or day is None:
            return QDate.currentDate()

        try:
            py = PyluachHebrewDate(year, month, day).to_pydate()
            return QDate(py.year, py.month, py.day)
        except Exception:
            return QDate.currentDate()


class ChipWidget(QFrame):
    removed = pyqtSignal(str)
    text_changed = pyqtSignal(str)

    def __init__(self, label: str, value: str, parent=None):
        super().__init__(parent)
        self._value = value
        self._editing = False
        self.setFrameShape(QFrame.Shape.StyledPanel)
        # #153 — צבעי chip מותאמים למצב לילה כדי שטקסט חיפוש מתקדם יישאר קריא.
        if theme_manager.night_mode:
            self.setStyleSheet(
                "ChipWidget { background: #303a44; color: #f0f0f0; border-radius: 8px;"
                " border: 1px solid #5f7f9f; margin: 1px; }"
            )
        else:
            self.setStyleSheet(
                "ChipWidget { background: #ddeeff; color: #202020; border-radius: 8px;"
                " border: 1px solid #99bbdd; margin: 1px; }"
            )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 2, 2, 2)
        lay.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(0)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet("background: transparent; border: none;")
        self._lbl.setCursor(Qt.CursorShape.IBeamCursor)
        self._lbl.setToolTip("דריקט צו רעדאקטירן")
        # #152 — טקסט ארוך בתוך chip לא מקבל רוחב מינימלי ענק שדוחף החוצה את כפתור הביטול.
        self._lbl.setMinimumWidth(0)
        self._lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

        self._edit = QLineEdit(label)
        self._edit.setMinimumWidth(0)
        self._edit.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        if theme_manager.night_mode:
            self._edit.setStyleSheet(
                "QLineEdit { background: #242628; color: #f5f5f5; border: 1px solid #6aa0ff;"
                " border-radius: 4px; padding: 0 2px; }"
            )
        else:
            self._edit.setStyleSheet(
                "QLineEdit { background: white; color: #202020; border: 1px solid #0d6efd;"
                " border-radius: 4px; padding: 0 2px; }"
            )
        self._edit.hide()
        self._edit.installEventFilter(self)
        self._edit.editingFinished.connect(self._commit_edit)

        btn = QToolButton()
        btn.setText("\u2715")
        btn.setFixedSize(16, 16)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet(
            "QToolButton { border: none; color: #555; font-size: 10px;"
            " background: transparent; }"
            "QToolButton:hover { color: #cc0000; }"
        )
        btn.clicked.connect(lambda: self.removed.emit(self._value))
        lay.addWidget(self._lbl, 1)
        lay.addWidget(self._edit, 1)
        lay.addWidget(btn)

    def mousePressEvent(self, event):
        if not self._editing:
            self._start_edit()
        super().mousePressEvent(event)

    def _start_edit(self):
        self._editing = True
        self._edit.setText(self._lbl.text())
        self._lbl.hide()
        self._edit.show()
        self._edit.selectAll()
        self._edit.setFocus()

    def _commit_edit(self):
        if not self._editing:
            return
        self._editing = False
        new_text = self._edit.text().strip() or self._lbl.text()
        self._edit.hide()
        self._lbl.setText(new_text)
        self._lbl.show()
        if new_text != self._value:
            self._value = new_text
            self.text_changed.emit(new_text)

    def _cancel_edit(self):
        if not self._editing:
            return
        self._editing = False
        self._edit.hide()
        self._lbl.show()

    def eventFilter(self, obj, event):
        if obj is self._edit and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self._cancel_edit()
                return True
        return super().eventFilter(obj, event)


class MultiSelectWidget(QWidget):
    """Combo box with chips display for multi-value selection."""
    selectionChanged = pyqtSignal()

    def __init__(self, placeholder: str = "\u05d1\u05d7\u05e8...", parent=None):
        super().__init__(parent)
        self._selected: dict[str, str] = {}  # value -> label
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self._combo.setMinimumContentsLength(12)
        self._combo.lineEdit().setPlaceholderText(placeholder)
        self._combo.lineEdit().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._combo.completer().setCompletionMode(
            QCompleter.CompletionMode.PopupCompletion
        )
        self._combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self._combo.completer().popup().setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )

        self._chips_container = QWidget()
        self._chips_layout = QVBoxLayout(self._chips_container)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(2)
        self._chips_container.setVisible(False)

        main_layout.addWidget(self._combo)
        main_layout.addWidget(self._chips_container)
        self._combo.activated.connect(self._on_activated)

    def add_item(self, label: str, value: str) -> None:
        self._combo.addItem(label, value)

    def _on_activated(self, idx: int) -> None:
        value = self._combo.itemData(idx)
        label = self._combo.itemText(idx)
        if not value or value in self._selected:
            return
        self._add_chip(label, value)
        self._combo.lineEdit().clear()

    def _add_chip(self, label: str, value: str) -> None:
        chip = ChipWidget(label, value)
        chip.removed.connect(self._remove_chip)
        self._chips_layout.addWidget(chip)
        self._selected[value] = label
        self._chips_container.setVisible(True)
        self.selectionChanged.emit()

    def _remove_chip(self, value: str) -> None:
        for i in range(self._chips_layout.count()):
            item = self._chips_layout.itemAt(i)
            if item and item.widget() and getattr(item.widget(), "_value", None) == value:
                item.widget().deleteLater()
                break
        self._selected.pop(value, None)
        if not self._selected:
            self._chips_container.setVisible(False)
        self.selectionChanged.emit()

    def selected_values(self) -> list[str]:
        return list(self._selected.keys())

    def clear_selection(self) -> None:
        for value in list(self._selected.keys()):
            self._remove_chip(value)


_SAVED_TERMS_FILE = Path(__file__).parent / "saved_terms.json"


def _load_saved_terms() -> list[str]:
    try:
        import json
        if _SAVED_TERMS_FILE.exists():
            data = json.loads(_SAVED_TERMS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [str(t) for t in data]
    except Exception:
        pass
    return []


def _save_saved_terms(terms: list[str]) -> None:
    try:
        import json
        _SAVED_TERMS_FILE.write_text(
            json.dumps(terms, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


_OP_CYCLE: dict[str, str] = {"AND": "OR", "OR": "IMPLICIT", "IMPLICIT": "AND"}


class _ChainDropZone(QWidget):
    """Container for term rows — handles drop-to-reorder and draws the drop indicator."""
    drop_reorder = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._drop_y: int = -1

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            self._drop_y = int(event.position().y())
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._drop_y = -1
        self.update()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            from_idx = int(event.mimeData().text())
            drop_y = int(event.position().y())
            layout = self.layout()
            to_idx = layout.count()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    w = item.widget()
                    if drop_y < w.y() + w.height() // 2:
                        to_idx = i
                        break
            self._drop_y = -1
            self.update()
            event.acceptProposedAction()
            # Defer so drag.exec() fully unwinds before rebuild
            QTimer.singleShot(0, lambda f=from_idx, t=to_idx: self.drop_reorder.emit(f, t))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drop_y >= 0:
            p = QPainter(self)
            # דיווח מעבר פרופיל — a widget can be torn down between the base
            # paintEvent and QPainter construction. Never end an inactive
            # painter, which emits "QPainter::end: Painter not active".
            if p.isActive():
                pen = QPen(QColor("#007acc"), 2)
                p.setPen(pen)
                p.drawLine(0, self._drop_y, self.width(), self._drop_y)
                p.end()


class _TermRow(QWidget):
    """Single row in the chain: [⠿] [און/אדער/···] [(] ["] [chip] ["] [)]"""
    removed = pyqtSignal(int)
    op_toggled = pyqtSignal(int)
    paren_changed = pyqtSignal(int, str, bool)
    exact_changed = pyqtSignal(int, bool)
    term_changed = pyqtSignal(int, str)
    search_triggered = pyqtSignal()

    _OP_TEXTS = {"AND": "און", "OR": "אדער", "IMPLICIT": "···"}
    _OP_TOOLTIPS = {
        "AND": "און (AND) — ביידע תנאים מוזן פאסן\nדריקט צו איבערבייטן",
        "OR": "אדער (OR) — איינער איז גענוג\nדריקט צו איבערבייטן",
        "IMPLICIT": "אן אן אפעראטאר — AND ברירת מחדל\nדריקט צו איבערבייטן",
    }
    _OP_STYLES = {
        "AND": (
            "QPushButton{font-size:10px;font-weight:bold;"
            "background:#d4edda;border:1.5px solid #28a745;"
            "border-radius:4px;color:#155724;padding:0 4px;}"
            "QPushButton:hover{background:#b8dfc5;}"
        ),
        "OR": (
            "QPushButton{font-size:10px;font-weight:bold;"
            "background:#fff3cd;border:1.5px solid #e0a800;"
            "border-radius:4px;color:#856404;padding:0 4px;}"
            "QPushButton:hover{background:#ffe07d;}"
        ),
        "IMPLICIT": (
            "QPushButton{font-size:9px;"
            "background:transparent;border:1px dashed #ccc;"
            "border-radius:4px;color:#ccc;padding:0 2px;}"
            "QPushButton:hover{border-color:#999;color:#999;}"
        ),
    }

    def __init__(self, idx: int, entry: dict, parent=None):
        super().__init__(parent)
        self._idx = idx
        self._drag_start_pos: QPoint | None = None
        self._dragging = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 1, 0, 1)
        lay.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Drag grip
        self._grip = QLabel("⠿")
        self._grip.setFixedWidth(14)
        self._grip.setCursor(Qt.CursorShape.SizeAllCursor)
        self._grip.setStyleSheet("color: #bbb; font-size: 13px;")
        self._grip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._grip.setToolTip("שלעפט צו טוישן דעם סדר")
        lay.addWidget(self._grip)

        # Operator button slot (row 0 gets an empty spacer)
        if idx > 0:
            op = entry.get("op", "AND")
            self._op_btn: QPushButton | None = QPushButton(self._OP_TEXTS[op])
            self._op_btn.setFixedSize(42, 22)
            self._op_btn.setToolTip(self._OP_TOOLTIPS[op])
            self._op_btn.setStyleSheet(self._OP_STYLES[op])
            self._op_btn.clicked.connect(lambda: self.op_toggled.emit(self._idx))
            lay.addWidget(self._op_btn)
        else:
            self._op_btn = None
            spc = QWidget()
            spc.setFixedSize(42, 22)
            lay.addWidget(spc)

        # Open paren (
        self._btn_open = QToolButton()
        self._btn_open.setText("(")
        self._btn_open.setFixedSize(18, 22)
        self._btn_open.setCheckable(True)
        self._btn_open.setChecked(entry.get("open", False))
        self._btn_open.setStyleSheet(_TermRow._paren_ss(entry.get("open", False)))
        self._btn_open.setToolTip("לייגט צו אן עפנענדיגן קלאמער פאר דעם זוך אויסדרוק")
        self._btn_open.toggled.connect(self._on_open_toggled)
        lay.addWidget(self._btn_open)

        # Opening quote "
        self._lbl_q_open = QToolButton()
        self._lbl_q_open.setText("“")
        self._lbl_q_open.setFixedSize(16, 22)
        self._lbl_q_open.setCheckable(True)
        self._lbl_q_open.setChecked(entry.get("exact", False))
        self._lbl_q_open.setStyleSheet(_TermRow._quote_ss(entry.get("exact", False)))
        self._lbl_q_open.setToolTip('"גענויער אויסדרוק" — נעמט ארום מיט גענזלעך צו זוכן א גענויעם זאץ')
        self._lbl_q_open.toggled.connect(self._on_exact_toggled)
        lay.addWidget(self._lbl_q_open)

        # Chip
        chip = ChipWidget(entry["term"], entry["term"])
        chip.removed.connect(lambda _: self.removed.emit(self._idx))
        chip.text_changed.connect(lambda v: self.term_changed.emit(self._idx, v))
        lay.addWidget(chip, 1)

        # Closing quote "
        self._lbl_q_close = QToolButton()
        self._lbl_q_close.setText("”")
        self._lbl_q_close.setFixedSize(16, 22)
        self._lbl_q_close.setCheckable(True)
        self._lbl_q_close.setChecked(entry.get("exact", False))
        self._lbl_q_close.setStyleSheet(_TermRow._quote_ss(entry.get("exact", False)))
        self._lbl_q_close.setToolTip('"גענויער אויסדרוק" — נעמט ארום מיט גענזלעך צו זוכן א גענויעם זאץ')
        self._lbl_q_close.toggled.connect(self._on_exact_toggled)
        lay.addWidget(self._lbl_q_close)

        # Close paren )
        self._btn_close = QToolButton()
        self._btn_close.setText(")")
        self._btn_close.setFixedSize(18, 22)
        self._btn_close.setCheckable(True)
        self._btn_close.setChecked(entry.get("close", False))
        self._btn_close.setStyleSheet(_TermRow._paren_ss(entry.get("close", False)))
        self._btn_close.setToolTip("לייגט צו א פארמאכנדיגן קלאמער נאך דעם זוך אויסדרוק")
        self._btn_close.toggled.connect(self._on_close_toggled)
        lay.addWidget(self._btn_close)

    def _on_open_toggled(self, v: bool) -> None:
        if self._dragging:
            return
        self._btn_open.setStyleSheet(_TermRow._paren_ss(v))
        self.paren_changed.emit(self._idx, "open", v)

    def _on_close_toggled(self, v: bool) -> None:
        if self._dragging:
            return
        self._btn_close.setStyleSheet(_TermRow._paren_ss(v))
        self.paren_changed.emit(self._idx, "close", v)

    def _on_exact_toggled(self, v: bool) -> None:
        if self._dragging:
            return
        for btn in (self._lbl_q_open, self._lbl_q_close):
            btn.blockSignals(True)
            btn.setChecked(v)
            btn.setStyleSheet(_TermRow._quote_ss(v))
            btn.blockSignals(False)
        self.exact_changed.emit(self._idx, v)

    @staticmethod
    def _quote_ss(active: bool) -> str:
        if active:
            return (
                "QToolButton{border:none;background:transparent;"
                "color:#0d6efd;font-weight:bold;font-size:14px;}"
            )
        return (
            "QToolButton{border:none;background:transparent;color:#ccc;font-size:14px;}"
            "QToolButton:hover{color:#0d6efd;}"
        )

    @staticmethod
    def _paren_ss(active: bool) -> str:
        if active:
            return (
                "QToolButton{border:1px solid #6f42c1;border-radius:3px;"
                "background:#e2d9f3;color:#6f42c1;font-weight:bold;font-size:13px;}"
            )
        return (
            "QToolButton{border:1px solid #ddd;border-radius:3px;"
            "background:transparent;color:#ccc;font-size:13px;}"
            "QToolButton:hover{color:#6f42c1;border-color:#9f76d8;}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            grip_rect = QRect(self._grip.mapTo(self, QPoint(0, 0)), self._grip.size())
            if grip_rect.contains(pos):
                self._drag_start_pos = pos
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is not None and not self._dragging:
            pos = event.position().toPoint()
            if (pos - self._drag_start_pos).manhattanLength() > 8:
                self._dragging = True
                self._lbl_q_open.blockSignals(True)
                self._lbl_q_close.blockSignals(True)
                self._btn_open.blockSignals(True)
                self._btn_close.blockSignals(True)
                drag = QDrag(self)
                mime = QMimeData()
                mime.setText(str(self._idx))
                drag.setMimeData(mime)
                drag.setPixmap(self.grab())
                drag.setHotSpot(self._drag_start_pos)
                self._drag_start_pos = None
                drag.exec(Qt.DropAction.MoveAction)
                # drag.exec() returns after drop — widget may have been rebuilt
                try:
                    self._lbl_q_open.blockSignals(False)
                    self._lbl_q_close.blockSignals(False)
                    self._btn_open.blockSignals(False)
                    self._btn_close.blockSignals(False)
                    self._dragging = False
                except RuntimeError:
                    pass
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


class TermChainWidget(QWidget):
    """א פרייער זוך פעלד מיט א קייט פון אויסדרוקן, AND/OR/IMPLICIT, קלאמערן און שלעפן מיטן מויז."""
    search_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._terms: list[dict] = []  # {"op", "term", "open", "close"}
        self._saved: list[str] = _load_saved_terms()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # --- Input row ---
        input_row = QHBoxLayout()
        input_row.setSpacing(4)

        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        # #319 — מוודא שהקומבובוקס נמתח לרוחב המלא של השורה
        self._combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self._combo.setMinimumContentsLength(10)
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo.lineEdit().setPlaceholderText("טייפט א ווארט אדער אן אויסדרוק...")
        self._combo.lineEdit().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self._combo.completer().popup().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._refresh_combo_items()

        self._btn_add = QToolButton()
        self._btn_add.setText("לייג צו")
        self._btn_add.setToolTip("לייגט צו אן אויסדרוק צו דער קייט (Enter)")
        self._btn_add.clicked.connect(self._on_add)
        self._combo.lineEdit().returnPressed.connect(self._on_add)

        self.chk_exact = QToolButton()
        self.chk_exact.setText('""')
        self.chk_exact.setFixedSize(24, 22)
        self.chk_exact.setCheckable(True)
        self.chk_exact.setToolTip('"גענויער אויסדרוק" — דער אויסדרוק וועט ווערן ארומגענומען מיט גענזלעך (זוכן א גענויעם זאץ)')
        self.chk_exact.setStyleSheet(
            "QToolButton{border:1px solid #ddd;border-radius:3px;"
            "background:transparent;color:#aaa;font-size:11px;}"
            "QToolButton:checked{border:1.5px solid #0d6efd;"
            "background:#cfe2ff;color:#0a3977;font-weight:bold;}"
            "QToolButton:hover{color:#0d6efd;border-color:#84b0fc;}"
        )

        self.chk_nc = QCheckBox("אן ניקוד")
        self.chk_nc.setToolTip("זוכט אן זיך צו ווענדן אין ניקוד און טעמים")

        self._btn_reset = QToolButton()
        self._btn_reset.setText("↺")
        self._btn_reset.setToolTip("מעקט אויס דעם פרייען טעקסט")
        self._btn_reset.setFixedSize(20, 20)
        self._btn_reset.setStyleSheet(
            "QToolButton { border: none; color: #aaa; font-size: 14px; }"
            "QToolButton:hover { color: #cc4400; }"
        )
        self._btn_reset.clicked.connect(self.clear)

        input_row.addWidget(self._combo, 1)
        input_row.addWidget(self._btn_add)
        main_layout.addLayout(input_row)

        # #319 — שורת אפשרויות נמתחת לרוחב מלא
        options_row = QHBoxLayout()
        options_row.setSpacing(4)
        options_row.addWidget(self.chk_exact)
        options_row.addWidget(self.chk_nc, 1)
        options_row.addWidget(self._btn_reset)
        main_layout.addLayout(options_row)

        # --- Chain area (drop target) ---
        self._chain_widget = _ChainDropZone()
        self._chain_layout = QVBoxLayout(self._chain_widget)
        self._chain_layout.setContentsMargins(0, 0, 0, 0)
        self._chain_layout.setSpacing(2)
        self._chain_widget.drop_reorder.connect(self._on_drop_reorder)
        self._chain_widget.setVisible(False)
        main_layout.addWidget(self._chain_widget)

    def _refresh_combo_items(self) -> None:
        current_text = self._combo.currentText() if self._combo.count() > 0 else ""
        self._combo.clear()
        for t in self._saved:
            self._combo.addItem(t, t)
        self._combo.setCurrentText(current_text)

    def _on_add(self) -> None:
        text = self._combo.currentText().strip()
        if not text:
            return
        raw = text
        if self.chk_nc.isChecked():
            words = text.split()
            text = " ".join(f"nc:{w}" for w in words)
        exact = self.chk_exact.isChecked()
        self._terms.append({"op": "AND", "term": text, "open": False, "close": False, "exact": exact})
        self._rebuild_chain()
        if raw and raw not in self._saved:
            self._saved.insert(0, raw)
            if len(self._saved) > 50:
                self._saved = self._saved[:50]
            _save_saved_terms(self._saved)
            self._refresh_combo_items()
        self._combo.lineEdit().clear()

    def _rebuild_chain(self) -> None:
        while self._chain_layout.count():
            item = self._chain_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for idx, entry in enumerate(self._terms):
            if idx > 0:
                merge_btn = QPushButton("⊕ פארבינד")
                merge_btn.setFixedHeight(18)
                merge_btn.setToolTip("פארבינדט די צוויי אויסדרוקן צו איין גענויעם אויסדרוק")
                merge_btn.setStyleSheet(
                    "QPushButton{border:1px dashed #aaa;border-radius:3px;"
                    "background:#f5f5f5;color:#888;font-size:10px;padding:0 6px;}"
                    "QPushButton:hover{border-color:#0d6efd;color:#0d6efd;"
                    "background:#e8f0fe;}"
                )
                merge_btn.clicked.connect(lambda checked=False, i=idx: self._on_merge(i - 1))
                self._chain_layout.addWidget(merge_btn)
            row = _TermRow(idx, entry)
            row.removed.connect(self._on_remove)
            row.op_toggled.connect(self._on_op_toggle)
            row.paren_changed.connect(self._on_paren_change)
            row.exact_changed.connect(self._on_exact_change)
            row.term_changed.connect(self._on_term_change)
            row.search_triggered.connect(self.search_triggered.emit)
            self._chain_layout.addWidget(row)
        self._chain_widget.setVisible(bool(self._terms))

    def _on_remove(self, idx: int) -> None:
        if 0 <= idx < len(self._terms):
            del self._terms[idx]
            self._rebuild_chain()

    def _on_op_toggle(self, idx: int) -> None:
        if 0 <= idx < len(self._terms):
            entry = self._terms[idx]
            entry["op"] = _OP_CYCLE[entry["op"]]
            self._rebuild_chain()

    def _on_paren_change(self, idx: int, which: str, value: bool) -> None:
        if 0 <= idx < len(self._terms):
            self._terms[idx][which] = value

    def _on_exact_change(self, idx: int, value: bool) -> None:
        if 0 <= idx < len(self._terms):
            self._terms[idx]["exact"] = value

    def _on_term_change(self, idx: int, new_term: str) -> None:
        if 0 <= idx < len(self._terms):
            self._terms[idx]["term"] = new_term

    def _on_term_change(self, idx: int, new_term: str) -> None:
        if 0 <= idx < len(self._terms):
            self._terms[idx]["term"] = new_term

    def _on_merge(self, idx: int) -> None:
        """Merge term at idx with term at idx+1 into one term."""
        if not (0 <= idx < len(self._terms) - 1):
            return
        a = self._terms[idx]
        b = self._terms[idx + 1]
        # Strip existing outer quotes from both terms before joining
        def _strip_quotes(t: str) -> str:
            t = t.strip()
            if t.startswith('"') and t.endswith('"') and len(t) > 1:
                return t[1:-1]
            return t
        merged_term = _strip_quotes(a["term"]) + " " + _strip_quotes(b["term"])
        merged: dict = {
            "op": a["op"],
            "term": merged_term,
            "open": a.get("open", False),
            "close": b.get("close", False),
            "exact": a.get("exact", False) or b.get("exact", False),
        }
        self._terms[idx : idx + 2] = [merged]
        self._rebuild_chain()

    def _on_drop_reorder(self, from_idx: int, to_idx: int) -> None:
        n = len(self._terms)
        if from_idx == to_idx or not (0 <= from_idx < n):
            return
        entry = self._terms.pop(from_idx)
        if to_idx > from_idx:
            to_idx -= 1
        to_idx = max(0, min(to_idx, len(self._terms)))
        self._terms.insert(to_idx, entry)
        if self._terms:
            self._terms[0]["op"] = "AND"
        self._rebuild_chain()

    def get_query(self) -> str:
        if not self._terms:
            return ""
        tokens: list[str] = []
        for idx, entry in enumerate(self._terms):
            if idx > 0 and entry.get("op") == "OR":
                tokens.append("OR")
            # AND and IMPLICIT: Anki's default (space = AND), no token needed
            if entry.get("open"):
                tokens.append("(")
            term = f'"{entry["term"]}"' if entry.get("exact") else entry["term"]
            tokens.append(term)
            if entry.get("close"):
                tokens.append(")")
        return " ".join(tokens)

    def clear(self) -> None:
        self._terms.clear()
        self._rebuild_chain()
        self._combo.lineEdit().clear()


# --- GUI CODE ---


class _DockEnterFilter(QObject):
    """Intercepts Return/Enter key presses anywhere in the dock and triggers search."""
    def __init__(self, dock: "AdvancedSearchDock"):
        super().__init__(dock)
        self._dock = dock

    def eventFilter(self, obj, event):  # type: ignore[override]
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                focused = QApplication.focusWidget()
                if focused is not None and self._dock.isAncestorOf(focused):
                    QTimer.singleShot(0, self._dock.perform_search)
        return False


class AdvancedSearchDock(QDockWidget):
    def __init__(self, browser):
        super().__init__("פארגעשריטענע זוכעניש", browser)
        self.browser = browser
        self.setObjectName("hafAdvancedSearchDock")
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
        title_bar = QWidget(self)
        title_bar.setFixedHeight(0)
        self.setTitleBarWidget(title_bar)

        # Setup Main Widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        # RTL Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5) # שוליים דקים
        self.main_widget.setLayout(self.main_layout)
        self.main_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Scroll Area setup
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll.setWidget(self.scroll_content)

        self.main_layout.addWidget(self.scroll)

        # Button at the bottom
        self.btn_search = QPushButton("זוך יעצט")
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005f9e;
            }
        """)
        self.btn_search.clicked.connect(self.perform_search)
        self.main_layout.addWidget(self.btn_search)

        self._enter_filter = _DockEnterFilter(self)
        QApplication.instance().installEventFilter(self._enter_filter)
        # #185 — "תמיד" יכול להיבחר אוטומטית כשמשנים פרמטר חזרות, ואז לחזור ל"ללא" כשהכול מתאפס.
        self._revlog_range_auto_always = False
        self._setting_revlog_range = False

        self.setup_ui()
        self.setStyleSheet(_advanced_search_stylesheet())

    def _day_cutoff_seconds(self) -> int:
        try:
            return int(mw.col.sched.day_cutoff)
        except AttributeError:
            return int(mw.col.sched.dayCutoff)  # type: ignore[attr-defined]

    def _revlog_range_ms(self) -> tuple[int, int] | None:
        if not self.chk_revlog_enabled.isChecked():
            return None

        cutoff = self._day_cutoff_seconds()
        today = QDate.currentDate()

        preset = self.combo_revlog_range.currentData()
        # #185 — במצב מאופס טווח החזרות הוא "ללא", ולכן אין ליצור טווח revlog גם אם ה-state הפנימי הופעל בטעות.
        if preset == "none":
            return None
        # #185 — "תמיד" מפעיל סינון revlog על כל ההיסטוריה עד cutoff הנוכחי.
        if preset == "always":
            start = 0
            end = cutoff
            return int(start * 1000), int(end * 1000)
        if preset == "today":
            start = cutoff - 86400
            end = cutoff
        elif preset == "yesterday":
            start = cutoff - (2 * 86400)
            end = cutoff - 86400
        elif preset == "last7":
            start = cutoff - (7 * 86400)
            end = cutoff
        elif preset == "last30":
            start = cutoff - (30 * 86400)
            end = cutoff
        else:
            from_date = self.revlog_date_from.qdate()
            to_date = self.revlog_date_to.qdate()
            if to_date < from_date:
                from_date, to_date = to_date, from_date

            days_from = from_date.daysTo(today)
            days_to = to_date.daysTo(today)

            start = (cutoff - 86400) - (days_from * 86400)
            end = cutoff - (days_to * 86400)

        return int(start * 1000), int(end * 1000)


    def _build_xrid_token(self) -> str | None:
        range_ms = self._revlog_range_ms()
        if range_ms is None:
            return None

        start_ms, end_ms = range_ms

        ease_vals = []
        if self.chk_ease_again.isChecked():
            ease_vals.append(1)
        if self.chk_ease_hard.isChecked():
            ease_vals.append(2)
        if self.chk_ease_good.isChecked():
            ease_vals.append(3)
        if self.chk_ease_easy.isChecked():
            ease_vals.append(4)

        type_vals = []
        if self.chk_type_learn.isChecked():
            type_vals.append(0)
        if self.chk_type_review.isChecked():
            type_vals.append(1)
        if self.chk_type_relearn.isChecked():
            type_vals.append(2)
        if self.chk_type_filtered.isChecked():
            type_vals.append(3)

        mode = "l" if self.rb_revlog_last.isChecked() else "a"
        ease_raw = "".join(str(v) for v in ease_vals) if ease_vals else "0"
        type_raw = "".join(str(v) for v in type_vals) if type_vals else "0"
        min_reviews = self.spin_revlog_min_reps.value()

        return (
            f"xrid:{start_ms}:{end_ms}:{mode}:{ease_raw}:{type_raw}:{min_reviews}"
        )

    def _make_collapsible(self, title: str, collapsed: bool = True, reset_fn=None) -> QVBoxLayout:
        header_w = QWidget()
        header_lay = QHBoxLayout(header_w)
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(2)

        btn = QToolButton()
        btn.setText(("\u25b6 " if collapsed else "\u25bc ") + title)
        btn.setCheckable(True)
        btn.setChecked(not collapsed)
        btn.setStyleSheet(_collapsible_button_stylesheet())
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_lay.addWidget(btn, 1)

        if reset_fn is not None:
            rst_btn = QToolButton()
            rst_btn.setText("\u21ba")
            rst_btn.setToolTip("\u05d0\u05d9\u05e4\u05d5\u05e1 \u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d4")
            rst_btn.setFixedSize(20, 20)
            rst_btn.setStyleSheet(_reset_button_stylesheet())
            rst_btn.clicked.connect(reset_fn)
            header_lay.addWidget(rst_btn)

        self.scroll_layout.addWidget(header_w)
        container = QWidget()
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(4, 0, 4, 4)
        content_layout.setSpacing(4)
        container.setVisible(not collapsed)
        self.scroll_layout.addWidget(container)

        def _toggle(checked: bool, b=btn, t=title, c=container):
            c.setVisible(checked)
            b.setText(("\u25bc " if checked else "\u25b6 ") + t)

        btn.toggled.connect(_toggle)
        return content_layout

    def _set_revlog_controls_enabled(self, enabled: bool) -> None:
        for widget in self._revlog_control_widgets:
            # #185 — הפרמטרים נשארים נגישים גם כשהסינון כבוי, כדי ששינוי פרמטר יוכל להפעיל אותו אוטומטית.
            widget.setEnabled(True)

    def _reset_revlog_filters(self) -> None:
        # #185 — איפוס מחזיר לברירת המחדל בלי להפעיל שוב את checkbox דרך אותות של widgets.
        self._resetting_revlog = True
        try:
            self.chk_revlog_enabled.setChecked(False)
            # #185 — איפוס ידני מבטל גם את מצב "תמיד" שנבחר אוטומטית.
            self._revlog_range_auto_always = False
            self.combo_revlog_range.setCurrentIndex(0)
            self.revlog_date_from.set_qdate(QDate.currentDate().addDays(-7))
            self.revlog_date_to.set_qdate(QDate.currentDate())
            for widget in [
                self.chk_ease_again, self.chk_ease_hard,
                self.chk_ease_good, self.chk_ease_easy,
                self.chk_type_learn, self.chk_type_review,
                self.chk_type_relearn, self.chk_type_filtered,
            ]:
                widget.setChecked(False)
            self.rb_revlog_last.setChecked(True)
            self.spin_revlog_min_reps.setValue(0)
        finally:
            self._resetting_revlog = False

    def _revlog_has_non_range_parameter(self) -> bool:
        # #185 — שינוי דירוג/סוג/מצב/כמות מפעיל את טווח "תמיד" כאשר הטווח עדיין "ללא".
        if self.rb_revlog_any.isChecked():
            return True
        if self.spin_revlog_min_reps.value() > 0:
            return True
        return any(widget.isChecked() for widget in [
            self.chk_ease_again, self.chk_ease_hard,
            self.chk_ease_good, self.chk_ease_easy,
            self.chk_type_learn, self.chk_type_review,
            self.chk_type_relearn, self.chk_type_filtered,
        ])

    def _set_revlog_range_data(self, data: str, auto_always: bool = False) -> None:
        # #185 — שינוי פנימי של הטווח מונע מה-handler להתייחס אליו כבחירה ידנית של המשתמש.
        idx = self.combo_revlog_range.findData(data)
        if idx < 0:
            return
        self._setting_revlog_range = True
        try:
            self.combo_revlog_range.setCurrentIndex(idx)
        finally:
            self._setting_revlog_range = False
        self._revlog_range_auto_always = auto_always
        self._update_revlog_custom_dates_visibility()

    def _update_revlog_custom_dates_visibility(self) -> None:
        # #185 — שדות תאריך מותאם מוצגים רק בטווח מותאם, לא ב"ללא" או "תמיד".
        self._revlog_custom_dates.setVisible(
            self.combo_revlog_range.currentData() == "custom"
        )

    def _on_revlog_range_changed(self, *_args) -> None:
        # #185 — בחירה ידנית של טווח מבטלת את סימון ה"תמיד" האוטומטי.
        self._update_revlog_custom_dates_visibility()
        if not getattr(self, "_setting_revlog_range", False) and not getattr(self, "_resetting_revlog", False):
            self._revlog_range_auto_always = False
        self._maybe_enable_revlog_from_parameter()

    def _revlog_has_parameter(self) -> bool:
        # #185 — רק בחירה שאינה "ללא" נחשבת פרמטר חזרות שמפעיל את הסינון האוטומטי.
        if self.combo_revlog_range.currentData() not in ("none", None):
            return True
        if self.rb_revlog_any.isChecked():
            return True
        if self.spin_revlog_min_reps.value() > 0:
            return True
        return any(widget.isChecked() for widget in [
            self.chk_ease_again, self.chk_ease_hard,
            self.chk_ease_good, self.chk_ease_easy,
            self.chk_type_learn, self.chk_type_review,
            self.chk_type_relearn, self.chk_type_filtered,
        ])

    def _maybe_enable_revlog_from_parameter(self, *_args) -> None:
        if getattr(self, "_resetting_revlog", False):
            return
        # #185 — שינוי ראשון בפרמטר חזרות בוחר אוטומטית "תמיד" במקום להשאיר "ללא" שמנטרל את הסינון.
        has_non_range_parameter = self._revlog_has_non_range_parameter()
        if self.combo_revlog_range.currentData() == "none" and has_non_range_parameter:
            self._set_revlog_range_data("always", auto_always=True)
        elif self.combo_revlog_range.currentData() == "always" and self._revlog_range_auto_always and not has_non_range_parameter:
            self._set_revlog_range_data("none", auto_always=False)
        if self._revlog_has_parameter():
            self.chk_revlog_enabled.setChecked(True)
        else:
            # #185 — כשכל הפרמטרים בסקשן חזרו לברירת מחדל, מסירים גם את הוי של סינון לפי חזרות.
            self.chk_revlog_enabled.setChecked(False)

    def _connect_revlog_auto_enable(self) -> None:
        self.combo_revlog_range.currentIndexChanged.connect(self._on_revlog_range_changed)
        for widget in [
            self.chk_ease_again, self.chk_ease_hard,
            self.chk_ease_good, self.chk_ease_easy,
            self.chk_type_learn, self.chk_type_review,
            self.chk_type_relearn, self.chk_type_filtered,
            self.rb_revlog_last, self.rb_revlog_any,
        ]:
            widget.toggled.connect(self._maybe_enable_revlog_from_parameter)
        self.spin_revlog_min_reps.valueChanged.connect(self._maybe_enable_revlog_from_parameter)
        for date_widget in (self.revlog_date_from, self.revlog_date_to):
            for combo in (date_widget.day_combo, date_widget.month_combo, date_widget.year_combo):
                combo.currentIndexChanged.connect(self._maybe_enable_revlog_from_parameter)

    def setup_ui(self):
        # --- Free Text + Term Chain (always visible, at top) ---
        self.term_chain = TermChainWidget()
        self.term_chain.search_triggered.connect(self.perform_search)
        self.main_layout.insertWidget(0, self.term_chain)

        # --- Context Section (collapsible, open by default) ---
        lay_ctx = self._make_collapsible(
            "פלאץ און סארט", collapsed=False,
            reset_fn=lambda: (
                self.deck_selector.clear_selection(),
                self.note_selector.clear_selection(),
                self.tag_selector.clear_selection(),
            )
        )

        lay_ctx.addWidget(QLabel("פעקלעך:"))
        self.deck_selector = MultiSelectWidget("אלע פעקלעך")
        if self.browser.col:
            for name in sorted(self.browser.col.decks.all_names()):
                self.deck_selector.add_item(name, f'deck:"{name}"')
        lay_ctx.addWidget(self.deck_selector)

        lay_ctx.addWidget(QLabel("סארט רשומה:"))
        self.note_selector = MultiSelectWidget("אלע סארטן רשומה")
        if self.browser.col:
            for name in sorted(self.browser.col.models.all_names()):
                self.note_selector.add_item(name, f'note:"{name}"')
        lay_ctx.addWidget(self.note_selector)

        lay_ctx.addWidget(QLabel("צעטלעך:"))
        self.tag_selector = MultiSelectWidget("טייפט א צעטל...")
        if self.browser.col:
            for tag in sorted(self.browser.col.tags.all()):
                self.tag_selector.add_item(tag, tag)
        lay_ctx.addWidget(self.tag_selector)

        # #347 — חיפוש בשדה מסוים: בחירת שם שדה (מכל סוגי הרשומה) + טקסט לחיפוש בתוכו.
        # מתורגם לתחביר field:value של אנקי ("שם שדה:*טקסט*").
        lay_field = self._make_collapsible(
            "זוכן אין א באזונדערן פעלד",
            reset_fn=lambda: (
                self.field_name_combo.setCurrentIndex(-1),
                self.field_name_combo.lineEdit().clear(),
                self.field_text_edit.clear(),
                self.chk_field_exact.setChecked(False),
            )
        )
        lay_field.addWidget(QLabel("פעלד נאמען:"))
        self.field_name_combo = QComboBox()
        self.field_name_combo.setEditable(True)
        self.field_name_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        # #347 סבב 2: בלי מדיניות רוחב הקומבו מתרחב לרוחב שם השדה הארוך ביותר ומפוצץ
        # את הדוק (רוחב מרבי 300px) — התוכן זלג ונעלם מעבר לגבול. כמו שאר הקומבו בדוק.
        self.field_name_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.field_name_combo.setMinimumContentsLength(12)
        self.field_name_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.field_name_combo.lineEdit().setPlaceholderText("קלייבט אויס אדער טייפט א פעלד נאמען...")
        self.field_name_combo.lineEdit().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.field_name_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.field_name_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        if self.browser.col:
            field_names: set[str] = set()
            for model in self.browser.col.models.all():
                for fld in model.get("flds", []):
                    field_names.add(fld.get("name", ""))
            for name in sorted(n for n in field_names if n):
                self.field_name_combo.addItem(name)
        self.field_name_combo.setCurrentIndex(-1)
        lay_field.addWidget(self.field_name_combo)
        lay_field.addWidget(QLabel("טעקסט צו זוכן אינעם פעלד:"))
        self.field_text_edit = QLineEdit()
        self.field_text_edit.setPlaceholderText("לאזט ליידיג צו זוכן יעדע קארטל וואס דער פעלד איז אנגעפילט")
        lay_field.addWidget(self.field_text_edit)
        self.chk_field_exact = QCheckBox("גענויע התאמה (דער גאנצער פעלד אינהאלט)")
        self.chk_field_exact.setToolTip("אנגעצייכנט: דער גאנצער פעלד איז גלייך צום טעקסט. נישט אנגעצייכנט: דער פעלד אנטהאלט דעם טעקסט.")
        lay_field.addWidget(self.chk_field_exact)
        self.add_separator()

        # --- Status (collapsible) ---
        lay2 = self._make_collapsible(
            "קארטל מצב",
            reset_fn=lambda: [w.setChecked(False) for w in [
                self.chk_new, self.chk_learn, self.chk_review,
                self.chk_due, self.chk_suspended, self.chk_buried
            ]]
        )
        self.chk_new = QCheckBox("ניי")
        self.chk_learn = QCheckBox("ביים לערנען")
        self.chk_review = QCheckBox("ביים חזרן")
        self.chk_due = QCheckBox("ווארט פאר היינט")
        self.chk_suspended = QCheckBox("אפגעשטעלט")
        self.chk_buried = QCheckBox("באזייטיגט ביז מארגן")
        for w in [self.chk_new, self.chk_learn, self.chk_review,
                  self.chk_due, self.chk_suspended, self.chk_buried]:
            lay2.addWidget(w)

        # --- Flags (collapsible) ---
        lay3 = self._make_collapsible(
            "פענער",
            reset_fn=lambda: self.combo_flag.setCurrentIndex(0)
        )
        self.combo_flag = QComboBox()
        for label, val in [
            ("אן פילטער", ""), ("רויט", "flag:1"), ("אראנזש", "flag:2"),
            ("גרין", "flag:3"), ("בלוי", "flag:4"), ("ראזע", "flag:5"),
            ("טורקיז", "flag:6"), ("לילא", "flag:7"),
        ]:
            self.combo_flag.addItem(label, val)
        lay3.addWidget(self.combo_flag)

        # --- Date Range (collapsible) ---
        lay4 = self._make_collapsible(
            "דאטום מרווח",
            reset_fn=lambda: self.rb_none.setChecked(True)
        )
        self.radio_group_date = QButtonGroup(self)
        self.rb_none = QRadioButton("אן")
        self.rb_none.setChecked(True)
        self.rb_added = QRadioButton("צוגעלייגט")
        self.rb_rated = QRadioButton("געלערנט")
        self.rb_due = QRadioButton("געפלאנטער דאטום")
        for rb in [self.rb_none, self.rb_added, self.rb_rated, self.rb_due]:
            self.radio_group_date.addButton(rb)
        r_layout = QGridLayout()
        r_layout.addWidget(self.rb_none, 0, 0)
        r_layout.addWidget(self.rb_added, 0, 1)
        r_layout.addWidget(self.rb_rated, 1, 0)
        r_layout.addWidget(self.rb_due, 1, 1)
        lay4.addLayout(r_layout)

        self._date_fields_container = QWidget()
        dfc_lay = QVBoxLayout(self._date_fields_container)
        dfc_lay.setContentsMargins(0, 0, 0, 0)
        dfc_lay.setSpacing(4)
        dfc_lay.addWidget(QLabel("פון דאטום:"))
        self.date_from = HebrewDateComboWidget()
        self.date_from.set_qdate(QDate.currentDate().addDays(-7))
        dfc_lay.addWidget(self.date_from)
        dfc_lay.addWidget(QLabel("ביז דאטום:"))
        self.date_to = HebrewDateComboWidget()
        self.date_to.set_qdate(QDate.currentDate())
        dfc_lay.addWidget(self.date_to)
        self._date_fields_container.setVisible(False)
        lay4.addWidget(self._date_fields_container)
        for rb in [self.rb_added, self.rb_rated, self.rb_due, self.rb_none]:
            rb.toggled.connect(
                lambda _: self._date_fields_container.setVisible(
                    not self.rb_none.isChecked()
                )
            )

        # --- Metrics (collapsible) ---
        lay5 = self._make_collapsible(
            "מאסן (מרווח)",
            reset_fn=lambda: [w.setValue(0) for w in [
                self.spin_ivl_min, self.spin_ivl_max,
                self.spin_reps_min, self.spin_reps_max,
                self.spin_lapses_min, self.spin_lapses_max,
                self.spin_retr_min, self.spin_retr_max
            ]]
        )
        metrics_layout = QGridLayout()
        metrics_layout.addWidget(QLabel("מאס"), 0, 0)
        metrics_layout.addWidget(QLabel("מינימום"), 0, 1)
        metrics_layout.addWidget(QLabel("מאקסימום"), 0, 2)
        metrics_layout.addWidget(QLabel("מרווח:"), 1, 0)
        self.spin_ivl_min = self.create_spin()
        self.spin_ivl_max = self.create_spin()
        metrics_layout.addWidget(self.spin_ivl_min, 1, 1)
        metrics_layout.addWidget(self.spin_ivl_max, 1, 2)
        metrics_layout.addWidget(QLabel("חזרות:"), 2, 0)
        self.spin_reps_min = self.create_spin()
        self.spin_reps_max = self.create_spin()
        metrics_layout.addWidget(self.spin_reps_min, 2, 1)
        metrics_layout.addWidget(self.spin_reps_max, 2, 2)
        metrics_layout.addWidget(QLabel("דורכפאלן:"), 3, 0)
        self.spin_lapses_min = self.create_spin()
        self.spin_lapses_max = self.create_spin()
        metrics_layout.addWidget(self.spin_lapses_min, 3, 1)
        metrics_layout.addWidget(self.spin_lapses_max, 3, 2)
        # #152 — טווח יכולת אחזור נוסף לאותו אזור מדדים כדי לבנות prop:r בחיפוש.
        metrics_layout.addWidget(QLabel("מעגליכקייט צו דערמאנען:"), 4, 0)
        self.spin_retr_min = self.create_percent_spin()
        self.spin_retr_max = self.create_percent_spin()
        metrics_layout.addWidget(self.spin_retr_min, 4, 1)
        metrics_layout.addWidget(self.spin_retr_max, 4, 2)
        lay5.addLayout(metrics_layout)

        # --- Revlog (collapsible) ---
        lay6 = self._make_collapsible(
            "חזרות (revlog)",
            reset_fn=self._reset_revlog_filters
        )
        # #185 — ה-checkbox נמחק מהממשק; נשאר state פנימי שמופעל אוטומטית רק כשנבחר פרמטר חזרות ממשי.
        self.chk_revlog_enabled = QCheckBox()
        self.chk_revlog_enabled.setVisible(False)

        lay6.addWidget(QLabel("צייט מרווח:"))
        self.combo_revlog_range = QComboBox()
        # #185 — ברירת המחדל הגלויה היא ללא סינון חזרות, כדי שמצב מאופס לא ייראה כאילו הוא מסנן לפי היום.
        self.combo_revlog_range.addItem("אן", "none")
        # #185 — טווח "תמיד" משמש כאשר המשתמש בוחר פרמטר revlog בלי לבחור טווח תאריכים מסוים.
        self.combo_revlog_range.addItem("אלעמאל", "always")
        self.combo_revlog_range.addItem("היינט", "today")
        self.combo_revlog_range.addItem("נעכטן", "yesterday")
        self.combo_revlog_range.addItem("7 לעצטע טעג", "last7")
        self.combo_revlog_range.addItem("30 לעצטע טעג", "last30")
        self.combo_revlog_range.addItem("אייגענער מרווח", "custom")
        lay6.addWidget(self.combo_revlog_range)

        self._revlog_custom_dates = QWidget()
        rcd_lay = QVBoxLayout(self._revlog_custom_dates)
        rcd_lay.setContentsMargins(0, 0, 0, 0)
        rcd_lay.setSpacing(4)
        rcd_lay.addWidget(QLabel("פון דאטום:"))
        self.revlog_date_from = HebrewDateComboWidget()
        self.revlog_date_from.set_qdate(QDate.currentDate().addDays(-7))
        rcd_lay.addWidget(self.revlog_date_from)
        rcd_lay.addWidget(QLabel("ביז דאטום:"))
        self.revlog_date_to = HebrewDateComboWidget()
        self.revlog_date_to.set_qdate(QDate.currentDate())
        rcd_lay.addWidget(self.revlog_date_to)
        self._revlog_custom_dates.setVisible(False)
        lay6.addWidget(self._revlog_custom_dates)
        # #185 — visibility של תאריך מותאם מנוהל יחד עם בחירת "תמיד" אוטומטית בחיבור המרכזי של סינוני revlog.

        lay6.addWidget(QLabel("אפשאצונגען:"))
        ease_layout = QGridLayout()
        self.chk_ease_again = QCheckBox("נאכאמאל")
        self.chk_ease_hard = QCheckBox("שווער")
        self.chk_ease_good = QCheckBox("גוט")
        self.chk_ease_easy = QCheckBox("גרינג")
        ease_layout.addWidget(self.chk_ease_again, 0, 0)
        ease_layout.addWidget(self.chk_ease_hard, 0, 1)
        ease_layout.addWidget(self.chk_ease_good, 1, 0)
        ease_layout.addWidget(self.chk_ease_easy, 1, 1)
        lay6.addLayout(ease_layout)

        lay6.addWidget(QLabel("אפשאצונג מצב:"))
        self.rb_revlog_last = QRadioButton("די לעצטע אפשאצונג אינעם מרווח")
        self.rb_revlog_any = QRadioButton("יעדע אפשאצונג אינעם מרווח")
        self.rb_revlog_last.setChecked(True)
        lay6.addWidget(self.rb_revlog_last)
        lay6.addWidget(self.rb_revlog_any)

        lay6.addWidget(QLabel("חזרה סארט:"))
        type_layout = QGridLayout()
        self.chk_type_learn = QCheckBox("לערנען")
        self.chk_type_review = QCheckBox("חזרה")
        self.chk_type_relearn = QCheckBox("איבערלערנען")
        self.chk_type_filtered = QCheckBox("געפילטערטע")
        type_layout.addWidget(self.chk_type_learn, 0, 0)
        type_layout.addWidget(self.chk_type_review, 0, 1)
        type_layout.addWidget(self.chk_type_relearn, 1, 0)
        type_layout.addWidget(self.chk_type_filtered, 1, 1)
        lay6.addLayout(type_layout)

        lay6.addWidget(QLabel("מינימום חזרות אינעם מרווח:"))
        self.spin_revlog_min_reps = self.create_spin()
        lay6.addWidget(self.spin_revlog_min_reps)

        self._revlog_control_widgets = [
            self.combo_revlog_range,
            self._revlog_custom_dates,
            self.chk_ease_again,
            self.chk_ease_hard,
            self.chk_ease_good,
            self.chk_ease_easy,
            self.rb_revlog_last,
            self.rb_revlog_any,
            self.chk_type_learn,
            self.chk_type_review,
            self.chk_type_relearn,
            self.chk_type_filtered,
            self.spin_revlog_min_reps,
        ]
        self.chk_revlog_enabled.toggled.connect(self._set_revlog_controls_enabled)
        self._connect_revlog_auto_enable()
        self._set_revlog_controls_enabled(False)

        self.scroll_layout.addStretch()


    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #eee;")
        self.scroll_layout.addWidget(line)


    def create_spin(self):
        sb = SelectAllSpinBox()
        sb.setRange(0, 10000)
        sb.setValue(0)
        sb.setStyleSheet("padding: 3px;")
        return sb

    def create_percent_spin(self):
        # #152 — שדה אחוזים ייעודי ליכולת אחזור מונע הכנסת ערכים מחוץ לטווח 0-100.
        sb = SelectAllSpinBox()
        sb.setRange(0, 100)
        sb.setValue(0)
        sb.setSuffix("%")
        sb.setStyleSheet("padding: 3px;")
        return sb

    def get_date_query(self):
        if self.rb_none.isChecked():
            return []

        q_start = self.date_from.qdate()
        q_end = self.date_to.qdate()
        today = QDate.currentDate()

        days_ago_start = q_start.daysTo(today)
        days_ago_end = q_end.daysTo(today)

        if days_ago_start < days_ago_end:
            days_ago_start, days_ago_end = days_ago_end, days_ago_start

        str_start = q_start.toString("yyyy-MM-dd")
        str_end = q_end.toString("yyyy-MM-dd")

        parts = []
        if self.rb_added.isChecked():
            parts.append(f"added:{days_ago_start}")
            if days_ago_end > 0:
                parts.append(f"-added:{days_ago_end}")
        elif self.rb_rated.isChecked():
            parts.append(f"rated:{days_ago_start}")
            if days_ago_end > 0:
                parts.append(f"-rated:{days_ago_end}")
        elif self.rb_due.isChecked():
            # #issue — prop:due דורש מספר שלם (ימים יחסי להיום), לא מחרוזת תאריך
            parts.append(f"prop:due>={-days_ago_start}")
            parts.append(f"prop:due<={-days_ago_end}")

        return parts

    def perform_search(self):
        parts = []

        # Text chain
        chain_query = self.term_chain.get_query()
        if chain_query:
            parts.append(chain_query)

        # Context
        for deck_val in self.deck_selector.selected_values():
            if deck_val:
                parts.append(deck_val)
        selected_notes = self.note_selector.selected_values()
        if selected_notes:
            if len(selected_notes) == 1:
                parts.append(selected_notes[0])
            else:
                parts.append("(" + " OR ".join(selected_notes) + ")")
        selected_tags = self.tag_selector.selected_values()
        if selected_tags:
            if len(selected_tags) == 1:
                parts.append(f"tag:{selected_tags[0]}")
            else:
                parts.append("(" + " OR ".join(f"tag:{t}" for t in selected_tags) + ")")

        # #347 — חיפוש בשדה מסוים
        field_name = self.field_name_combo.currentText().strip()
        if field_name:
            field_text = self.field_text_edit.text().strip().replace('"', '\\"')
            if self.chk_field_exact.isChecked() and field_text:
                parts.append(f'"{field_name}:{field_text}"')
            elif field_text:
                parts.append(f'"{field_name}:*{field_text}*"')
            else:
                # שדה נבחר בלי טקסט — כל הכרטיסים שהשדה אינו ריק בהם
                parts.append(f'"{field_name}:_*"')

        # Status
        status = []
        if self.chk_new.isChecked():
            status.append("is:new")
        if self.chk_learn.isChecked():
            status.append("is:learn")
        if self.chk_review.isChecked():
            status.append("is:review")
        if self.chk_due.isChecked():
            status.append("is:due")
        if self.chk_suspended.isChecked():
            status.append("is:suspended")
        if self.chk_buried.isChecked():
            status.append("is:buried")
        if status:
            parts.append(f"({' or '.join(status)})" if len(status) > 1 else status[0])

        # Flags
        if self.combo_flag.currentData():
            parts.append(self.combo_flag.currentData())

        # Dates
        parts.extend(self.get_date_query())

        # Metrics (range)
        if self.spin_ivl_min.value():
            parts.append(f"prop:ivl>={self.spin_ivl_min.value()}")
        if self.spin_ivl_max.value():
            parts.append(f"prop:ivl<={self.spin_ivl_max.value()}")
        if self.spin_reps_min.value():
            parts.append(f"prop:reps>={self.spin_reps_min.value()}")
        if self.spin_reps_max.value():
            parts.append(f"prop:reps<={self.spin_reps_max.value()}")
        if self.spin_lapses_min.value():
            parts.append(f"prop:lapses>={self.spin_lapses_min.value()}")
        if self.spin_lapses_max.value():
            parts.append(f"prop:lapses<={self.spin_lapses_max.value()}")
        parts.extend(_retrievability_query_parts(self.spin_retr_min.value(), self.spin_retr_max.value()))

        xrid_token = self._build_xrid_token()
        if xrid_token is not None:
            parts.append(xrid_token)

        self.browser.search_for(" ".join(parts))

def _add_to_fastbar(browser) -> None:
    if not hasattr(browser, "fbar") or not hasattr(browser, "adv_search_dock"):
        return
    action = browser.adv_search_dock.toggleViewAction()
    action.setText("זוכעניש\nפארגעשריטן")
    for mod in list(sys.modules.values()):
        if hasattr(mod, "icon") and "qtawesome" in getattr(mod, "__name__", ""):
            try:
                from aqt.theme import theme_manager
                _icon = mod.icon(
                    "fa.search-plus",
                    color="white" if theme_manager.night_mode else "black",
                )
                action.setIcon(_icon)
            except Exception:
                pass
            break
    # Insert as first action in the toolbar
    actions = browser.fbar.actions()
    if actions:
        browser.fbar.insertAction(actions[0], action)
    else:
        browser.fbar.addAction(action)


def setup_browser_dock(browser):
    if hasattr(browser, "adv_search_dock"):
        return
    dock = AdvancedSearchDock(browser)
    browser.adv_search_dock = dock
    browser.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    dock.hide()
    # Qt עלול לשחזר מצב פתוח מהפעלה קודמת — מכריחים סגור בפתיחת הדפדוף
    QTimer.singleShot(0, dock.hide)

    toggle = dock.toggleViewAction()
    toggle.setText("פארגעשריטענע זוכעניש (זייט סרגל)")
    toggle.setShortcut(QKeySequence("Ctrl+Shift+F"))

    def _activate_search_tab(checked):
        if not checked:
            # #296 — לחיצה נוספת סוגרת את הדוק
            dock.hide()
            return
        # #296 — tabify רק בפעם הראשונה שהמשתמש מפעיל חיפוש מתקדם
        if not getattr(dock, '_tabified', False):
            dock._tabified = True
            # #152 — מציגים את טאבי דוק הצד למעלה
            with contextlib.suppress(Exception):
                browser.setTabPosition(Qt.DockWidgetArea.RightDockWidgetArea, QTabWidget.TabPosition.North)
            if hasattr(browser, "sidebarDockWidget"):
                browser.tabifyDockWidget(browser.sidebarDockWidget, dock)
        # #152 — לאחר לחיצה על חיפוש מתקדם הטאב שלו עולה לחזית
        dock.show()
        dock.raise_()
        dock.setFocus()

    toggle.triggered.connect(lambda checked: QTimer.singleShot(0, lambda: _activate_search_tab(checked)))

    mb = browser.menuBar()
    view_menu = None
    if mb:
        for a in mb.actions():
            if a.text().replace("&", "") in ["View", "אויסשטעל", "Views"]:
                view_menu = a.menu()
                break
    if view_menu:
        view_menu.addSeparator()
        view_menu.addAction(toggle)
    elif mb:
        mb.addAction(toggle)

    def _finalize():
        _add_to_fastbar(browser)

    QTimer.singleShot(0, _finalize)


gui_hooks.browser_menus_did_init.append(setup_browser_dock)
gui_hooks.browser_will_search.append(_on_browser_will_search)


# ─── Advanced Search Panel for Filtered Deck Dialog ───────────────────────────

class _FilteredDeckAdvPanel(QWidget):
    """Floating advanced search panel for FilteredDeckConfigDialog.
    Contains the full criteria UI (term chain + collapsible sections)
    and writes the built query into dialog.form.search."""

    def __init__(self, dialog) -> None:
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.Tool)
        self._dialog = dialog

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # #253 — בחלון חפיסה מסוננת זהו סינון חפיסות, לא חיפוש דפדפן רגיל.
        self.setWindowTitle("פארגעשריטענע פילטער")
        self.setMinimumWidth(280)
        self.resize(310, 560)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(_advanced_search_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(4)

        # Term chain (always visible at top)
        self.term_chain = TermChainWidget()
        self.term_chain.search_triggered.connect(self._apply)
        main_layout.addWidget(self.term_chain)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(sep)

        # Scroll area for collapsible sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

        self._setup_sections()
        self.scroll_layout.addStretch()

        # Apply button
        btn = QPushButton("◀ לייג אריין אינעם זוך פעלד")
        btn.setStyleSheet(
            "QPushButton{background:#007acc;color:white;font-weight:bold;"
            "padding:6px;border-radius:4px;}"
            "QPushButton:hover{background:#005f9e;}"
        )
        btn.clicked.connect(self._apply)
        main_layout.addWidget(btn)

    # ── helpers ────────────────────────────────────────────────────────────────

    def _make_collapsible(self, title: str, collapsed: bool = True, reset_fn=None) -> QVBoxLayout:
        header_w = QWidget()
        header_lay = QHBoxLayout(header_w)
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(2)
        btn = QToolButton()
        btn.setText(("▶ " if collapsed else "▼ ") + title)
        btn.setCheckable(True)
        btn.setChecked(not collapsed)
        btn.setStyleSheet(_collapsible_button_stylesheet())
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_lay.addWidget(btn, 1)
        if reset_fn is not None:
            rst = QToolButton()
            rst.setText("↺")
            rst.setFixedSize(20, 20)
            rst.setStyleSheet(_reset_button_stylesheet())
            rst.clicked.connect(reset_fn)
            header_lay.addWidget(rst)
        self.scroll_layout.addWidget(header_w)
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(4, 0, 4, 4)
        cl.setSpacing(4)
        container.setVisible(not collapsed)
        self.scroll_layout.addWidget(container)
        def _toggle(checked, b=btn, t=title, c=container):
            c.setVisible(checked)
            b.setText(("▼ " if checked else "▶ ") + t)
        btn.toggled.connect(_toggle)
        return cl

    def _create_spin(self) -> QSpinBox:
        sb = SelectAllSpinBox()
        sb.setRange(0, 10000)
        sb.setValue(0)
        sb.setStyleSheet("padding:3px;")
        return sb

    def _create_percent_spin(self) -> QSpinBox:
        # #152 — אותו בקר אחוזים גם בחיפוש מתקדם של חפיסה מסוננת.
        sb = SelectAllSpinBox()
        sb.setRange(0, 100)
        sb.setValue(0)
        sb.setSuffix("%")
        sb.setStyleSheet("padding:3px;")
        return sb

    # ── UI sections ─────────────────────────────────────────────────────────────

    def _setup_sections(self) -> None:
        col = mw.col

        # --- Context ---
        lay_ctx = self._make_collapsible(
            "פלאץ און סארט", collapsed=False,
            reset_fn=lambda: (
                self.deck_selector.clear_selection(),
                self.note_selector.clear_selection(),
                self.tag_selector.clear_selection(),
            ),
        )
        lay_ctx.addWidget(QLabel("פעקלעך:"))
        self.deck_selector = MultiSelectWidget("אלע פעקלעך")
        if col:
            for name in sorted(col.decks.all_names()):
                self.deck_selector.add_item(name, f'deck:"{name}"')
        lay_ctx.addWidget(self.deck_selector)

        lay_ctx.addWidget(QLabel("סארט רשומה:"))
        self.note_selector = MultiSelectWidget("אלע סארטן רשומה")
        if col:
            for name in sorted(col.models.all_names()):
                self.note_selector.add_item(name, f'note:"{name}"')
        lay_ctx.addWidget(self.note_selector)

        lay_ctx.addWidget(QLabel("צעטלעך:"))
        self.tag_selector = MultiSelectWidget("טייפט א צעטל...")
        if col:
            for tag in sorted(col.tags.all()):
                self.tag_selector.add_item(tag, tag)
        lay_ctx.addWidget(self.tag_selector)

        # --- Card Status ---
        lay2 = self._make_collapsible(
            "קארטל מצב",
            reset_fn=lambda: [w.setChecked(False) for w in [
                self.chk_new, self.chk_learn, self.chk_review,
                self.chk_due, self.chk_suspended, self.chk_buried,
            ]],
        )
        self.chk_new = QCheckBox("ניי")
        self.chk_learn = QCheckBox("ביים לערנען")
        self.chk_review = QCheckBox("ביים חזרן")
        self.chk_due = QCheckBox("ווארט פאר היינט")
        self.chk_suspended = QCheckBox("אפגעשטעלט")
        self.chk_buried = QCheckBox("באזייטיגט ביז מארגן")
        for w in [self.chk_new, self.chk_learn, self.chk_review,
                  self.chk_due, self.chk_suspended, self.chk_buried]:
            lay2.addWidget(w)

        # --- Flags ---
        lay3 = self._make_collapsible(
            "פענער", reset_fn=lambda: self.combo_flag.setCurrentIndex(0)
        )
        self.combo_flag = QComboBox()
        for label, val in [
            ("אן פילטער", ""), ("רויט", "flag:1"), ("אראנזש", "flag:2"),
            ("גרין", "flag:3"), ("בלוי", "flag:4"), ("ראזע", "flag:5"),
            ("טורקיז", "flag:6"), ("לילא", "flag:7"),
        ]:
            self.combo_flag.addItem(label, val)
        lay3.addWidget(self.combo_flag)

        # --- Date Range ---
        lay4 = self._make_collapsible(
            "דאטום מרווח", reset_fn=lambda: self.rb_none.setChecked(True)
        )
        self.radio_group_date = QButtonGroup(self)
        self.rb_none = QRadioButton("אן")
        self.rb_none.setChecked(True)
        self.rb_added = QRadioButton("צוגעלייגט")
        self.rb_rated = QRadioButton("געלערנט")
        self.rb_due = QRadioButton("געפלאנטער דאטום")
        for rb in [self.rb_none, self.rb_added, self.rb_rated, self.rb_due]:
            self.radio_group_date.addButton(rb)
        r_layout = QGridLayout()
        r_layout.addWidget(self.rb_none, 0, 0)
        r_layout.addWidget(self.rb_added, 0, 1)
        r_layout.addWidget(self.rb_rated, 1, 0)
        r_layout.addWidget(self.rb_due, 1, 1)
        lay4.addLayout(r_layout)
        self._date_fields_container = QWidget()
        dfc_lay = QVBoxLayout(self._date_fields_container)
        dfc_lay.setContentsMargins(0, 0, 0, 0)
        dfc_lay.setSpacing(4)
        dfc_lay.addWidget(QLabel("פון דאטום:"))
        self.date_from = HebrewDateComboWidget()
        self.date_from.set_qdate(QDate.currentDate().addDays(-7))
        dfc_lay.addWidget(self.date_from)
        dfc_lay.addWidget(QLabel("ביז דאטום:"))
        self.date_to = HebrewDateComboWidget()
        self.date_to.set_qdate(QDate.currentDate())
        dfc_lay.addWidget(self.date_to)
        self._date_fields_container.setVisible(False)
        lay4.addWidget(self._date_fields_container)
        for rb in [self.rb_added, self.rb_rated, self.rb_due, self.rb_none]:
            rb.toggled.connect(
                lambda _: self._date_fields_container.setVisible(not self.rb_none.isChecked())
            )

        # --- Metrics ---
        lay5 = self._make_collapsible(
            "מאסן (מרווח)",
            reset_fn=lambda: [w.setValue(0) for w in [
                self.spin_ivl_min, self.spin_ivl_max,
                self.spin_reps_min, self.spin_reps_max,
                self.spin_lapses_min, self.spin_lapses_max,
                self.spin_retr_min, self.spin_retr_max,
            ]],
        )
        metrics_layout = QGridLayout()
        metrics_layout.addWidget(QLabel("מאס"), 0, 0)
        metrics_layout.addWidget(QLabel("מינ׳'"), 0, 1)
        metrics_layout.addWidget(QLabel("מאקס׳'"), 0, 2)
        metrics_layout.addWidget(QLabel("מרווח:"), 1, 0)
        self.spin_ivl_min = self._create_spin()
        self.spin_ivl_max = self._create_spin()
        metrics_layout.addWidget(self.spin_ivl_min, 1, 1)
        metrics_layout.addWidget(self.spin_ivl_max, 1, 2)
        metrics_layout.addWidget(QLabel("חזרות:"), 2, 0)
        self.spin_reps_min = self._create_spin()
        self.spin_reps_max = self._create_spin()
        metrics_layout.addWidget(self.spin_reps_min, 2, 1)
        metrics_layout.addWidget(self.spin_reps_max, 2, 2)
        metrics_layout.addWidget(QLabel("דורכפאלן:"), 3, 0)
        self.spin_lapses_min = self._create_spin()
        self.spin_lapses_max = self._create_spin()
        metrics_layout.addWidget(self.spin_lapses_min, 3, 1)
        metrics_layout.addWidget(self.spin_lapses_max, 3, 2)
        # #152 — טווח יכולת אחזור זמין גם בבונה החיפוש של חפיסות מסוננות.
        metrics_layout.addWidget(QLabel("מעגליכקייט צו דערמאנען:"), 4, 0)
        self.spin_retr_min = self._create_percent_spin()
        self.spin_retr_max = self._create_percent_spin()
        metrics_layout.addWidget(self.spin_retr_min, 4, 1)
        metrics_layout.addWidget(self.spin_retr_max, 4, 2)
        lay5.addLayout(metrics_layout)

    # ── query building ──────────────────────────────────────────────────────────

    def _get_date_query(self) -> list[str]:
        if self.rb_none.isChecked():
            return []
        q_start = self.date_from.qdate()
        q_end = self.date_to.qdate()
        today = QDate.currentDate()
        days_ago_start = q_start.daysTo(today)
        days_ago_end = q_end.daysTo(today)
        if days_ago_start < days_ago_end:
            days_ago_start, days_ago_end = days_ago_end, days_ago_start
        str_start = q_start.toString("yyyy-MM-dd")
        str_end = q_end.toString("yyyy-MM-dd")
        parts: list[str] = []
        if self.rb_added.isChecked():
            parts.append(f"added:{days_ago_start}")
            if days_ago_end > 0:
                parts.append(f"-added:{days_ago_end}")
        elif self.rb_rated.isChecked():
            parts.append(f"rated:{days_ago_start}")
            if days_ago_end > 0:
                parts.append(f"-rated:{days_ago_end}")
        elif self.rb_due.isChecked():
            # #issue — prop:due דורש מספר שלם (ימים יחסי להיום), לא מחרוזת תאריך
            parts.append(f"prop:due>={-days_ago_start}")
            parts.append(f"prop:due<={-days_ago_end}")
        return parts

    def _apply(self) -> None:
        parts: list[str] = []
        chain_query = self.term_chain.get_query()
        if chain_query:
            parts.append(chain_query)
        for deck_val in self.deck_selector.selected_values():
            if deck_val:
                parts.append(deck_val)
        selected_notes = self.note_selector.selected_values()
        if selected_notes:
            if len(selected_notes) == 1:
                parts.append(selected_notes[0])
            else:
                parts.append("(" + " OR ".join(selected_notes) + ")")
        selected_tags = self.tag_selector.selected_values()
        if selected_tags:
            if len(selected_tags) == 1:
                parts.append(f"tag:{selected_tags[0]}")
            else:
                parts.append("(" + " OR ".join(f"tag:{t}" for t in selected_tags) + ")")
        status = []
        if self.chk_new.isChecked():
            status.append("is:new")
        if self.chk_learn.isChecked():
            status.append("is:learn")
        if self.chk_review.isChecked():
            status.append("is:review")
        if self.chk_due.isChecked():
            status.append("is:due")
        if self.chk_suspended.isChecked():
            status.append("is:suspended")
        if self.chk_buried.isChecked():
            status.append("is:buried")
        if status:
            parts.append(f"({' or '.join(status)})" if len(status) > 1 else status[0])
        if self.combo_flag.currentData():
            parts.append(self.combo_flag.currentData())
        parts.extend(self._get_date_query())
        if self.spin_ivl_min.value():
            parts.append(f"prop:ivl>={self.spin_ivl_min.value()}")
        if self.spin_ivl_max.value():
            parts.append(f"prop:ivl<={self.spin_ivl_max.value()}")
        if self.spin_reps_min.value():
            parts.append(f"prop:reps>={self.spin_reps_min.value()}")
        if self.spin_reps_max.value():
            parts.append(f"prop:reps<={self.spin_reps_max.value()}")
        if self.spin_lapses_min.value():
            parts.append(f"prop:lapses>={self.spin_lapses_min.value()}")
        if self.spin_lapses_max.value():
            parts.append(f"prop:lapses<={self.spin_lapses_max.value()}")
        parts.extend(_retrievability_query_parts(self.spin_retr_min.value(), self.spin_retr_max.value()))
        try:
            self._dialog.form.search.setText(" ".join(parts))
            self._dialog.form.search.setFocus()
        except RuntimeError:
            self.close()

    # ── positioning ─────────────────────────────────────────────────────────────

    def _reposition(self) -> None:
        try:
            if not self._dialog.isVisible():
                return
            dlg_geo = self._dialog.frameGeometry()
        except RuntimeError:
            self.close()
            return
        panel_w = max(self.width(), 300)
        panel_h = dlg_geo.height()
        self.resize(panel_w, panel_h)
        screen = QApplication.screenAt(dlg_geo.center())
        if screen is None:
            screen = QApplication.primaryScreen()
        sr = screen.availableGeometry()
        x = dlg_geo.x() - panel_w - 6
        if x < sr.x():
            x = dlg_geo.right() + 6
        y = max(sr.y(), min(dlg_geo.y(), sr.bottom() - panel_h))
        self.move(x, y)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._reposition)


class _DlgTrackFilter(QObject):
    """Repositions the advanced panel when the dialog moves/resizes,
    and closes it when the dialog closes."""

    def __init__(self, panel: "_FilteredDeckAdvPanel", dialog) -> None:
        super().__init__(dialog)
        self._panel = panel

    def eventFilter(self, obj, event) -> bool:
        et = event.type()
        if et in (QEvent.Type.Move, QEvent.Type.Resize):
            if self._panel.isVisible():
                self._panel._reposition()
        elif et == QEvent.Type.Close:
            self._panel.close()
        return False


def _setup_filtered_deck_adv_search(dialog, _deck) -> None:
    """Hook: filtered_deck_dialog_did_load_deck.
    Injects an advanced-search toggle button next to the search field; clicking it
    shows/hides the floating advanced-search panel."""
    if hasattr(dialog, "_adv_panel"):
        return  # idempotent

    panel = _FilteredDeckAdvPanel(dialog)
    dialog._adv_panel = panel

    # search row is in groupBox → gridLayout, row 1, col 1 is empty
    grid = dialog.form.groupBox.layout()
    # #184 — בחפיסה מסוננת משתמשים בטקסט ברור במקום סמל זכוכית מגדלת שהיה נראה כמו חיפוש רגיל.
    # #253 — ניסוח ייעודי לסינון חפיסות בחלון יצירת חפיסה מסוננת.
    adv_btn = QPushButton("פארגעשריטענע פילטער")
    adv_btn.setCheckable(True)
    adv_btn.setMinimumSize(94, 26)
    adv_btn.setMaximumHeight(26)
    adv_btn.setToolTip("פארגעשריטענע פילטער — בויט א פילטער שאילתה מיטן אויסשטעל")
    if theme_manager.night_mode:
        adv_btn.setStyleSheet(
            "QPushButton{border:1px solid #666;border-radius:4px;background:#303336;"
            "color:#f0f0f0;font-size:12px;padding:0 8px;}"
            "QPushButton:checked{background:#244d7a;border-color:#6aa0ff;}"
            "QPushButton:hover{background:#3a3f44;}"
        )
    else:
        adv_btn.setStyleSheet(
            "QPushButton{border:1px solid #bbb;border-radius:4px;background:#f5f5f5;"
            "color:#202020;font-size:12px;padding:0 8px;}"
            "QPushButton:checked{background:#cfe2ff;border-color:#0d6efd;}"
            "QPushButton:hover{background:#e0e0e0;}"
        )

    def _on_toggle(checked: bool) -> None:
        if checked:
            panel.show()
            panel._reposition()
        else:
            panel.hide()

    adv_btn.toggled.connect(_on_toggle)

    # guard against RuntimeError when dialog closes (both widgets destroyed together)
    def _on_panel_destroyed(_=None) -> None:
        try:
            adv_btn.setChecked(False)
        except RuntimeError:
            pass

    panel.destroyed.connect(_on_panel_destroyed)
    grid.addWidget(adv_btn, 1, 1, 1, 1)

    track_filter = _DlgTrackFilter(panel, dialog)
    dialog.installEventFilter(track_filter)


gui_hooks.filtered_deck_dialog_did_load_deck.append(_setup_filtered_deck_adv_search)

