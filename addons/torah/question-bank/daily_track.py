"""
daily_track.py — הספק יומי מותאם אישית
מאפשר למשתמש להגדיר מסלולי לימוד אישיים מתוך המאגר ולקבל ייבוא אוטומטי
(מלא או חלקי) בכל יום / בכל פתיחה.
"""
import json
import os
import shutil
from datetime import datetime, timedelta

from anki.collection import Collection
from anki.utils import tmpdir
from aqt import mw
from aqt.gui_hooks import profile_did_open
from aqt.qt import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QSortFilterProxyModel,
    QSpinBox,
    QStandardItem,
    QStandardItemModel,
    Qt,
    QTreeView,
    QVBoxLayout,
)
from aqt.utils import showText, tooltip
from _shared_libs.haf_notifications import show_failure

# #307 — מנגנון חיפוש זהה למאגר: ordered subsequence על אסימונים, בלי גימטריא
from .search_match import _is_ordered_subsequence, _tokens

_SEARCH_TEXT_ROLE = Qt.ItemDataRole.UserRole + 10


def _ordered_multi_term_match(search_text: str, filter_terms: list[str]) -> bool:
    tokens = _tokens(search_text)
    token_index = 0
    for term in filter_terms:
        matched = False
        while token_index < len(tokens):
            if _is_ordered_subsequence(term, tokens[token_index]):
                matched = True
                token_index += 1
                break
            token_index += 1
        if not matched:
            return False
    return True


class _FilePickerProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_terms: list[str] = []

    def setFilterText(self, text: str):
        self._filter_terms = [t.lower() for t in text.split() if t]
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._filter_terms:
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)
        search_text = self.sourceModel().data(index, _SEARCH_TEXT_ROLE) or ""
        if not search_text:
            search_text = str(self.sourceModel().data(index) or "").lower()
        if _ordered_multi_term_match(search_text, self._filter_terms):
            return True
        rows = self.sourceModel().rowCount(index)
        for r in range(rows):
            if self.filterAcceptsRow(r, index):
                return True
        return False

from .config import gc
from .custom_importer import importFromFolder
from .import_templates import getOrCreateModels, repo_notetypes_names

_REPO_STRUCT = os.path.join(os.path.dirname(__file__), "repo_struct.json")


def _folder_of(path: str) -> str:
    parts = [p for p in (path or "").split("/") if p]
    return "/".join(parts[:-1]) if len(parts) > 1 else ""


def _scope_folder_for_start_file(start_file: str) -> str:
    """Return the route scope folder so tracks continue to the next sibling book."""
    file_folder = _folder_of(start_file)
    parent_folder = _folder_of(file_folder)
    return parent_folder or file_folder


# ────────────────────────────────────────────────────────────────
# ניווט במבנה המאגר
# ────────────────────────────────────────────────────────────────

def _load_tree() -> dict:
    with open(_REPO_STRUCT, encoding='utf-8') as f:
        return json.load(f)


def get_all_files_in_folder(folder_path: str) -> list:
    """מחזיר רשימה ממוינת של נתיבי קבצים תחת folder_path."""
    if not folder_path:
        return []
    tree = _load_tree()
    parts = [p for p in folder_path.split("/") if p]
    # parts[0] = "מאגר השאלות" (השורש המשתמע)
    node = tree
    for part in parts[1:]:
        found = None
        for child in node.get("children", []):
            if child.get("name") == part:
                found = child
                break
        if found is None:
            return []
        node = found

    files = []

    def _collect(n, path):
        name = n.get("name", "")
        if n.get("type") == "file" and name.endswith(".txt"):
            files.append(path + "/" + name)
        elif n.get("type") == "directory":
            for child in n.get("children", []):
                _collect(child, path + "/" + name)

    for child in node.get("children", []):
        _collect(child, folder_path)

    return sorted(files)


# ────────────────────────────────────────────────────────────────
# Config helpers
# ────────────────────────────────────────────────────────────────

def _profile_key() -> str:
    name = mw.pm.name
    if not name:
        raise RuntimeError("מען קען נישט דערקענען א פראפיל פארן טעגליכן נאכפאלגן")
    return name


def _get_tracks(profile_key: str = None) -> list:
    key = profile_key or _profile_key()
    by_profile = gc("daily_tracks_by_profile") or {}
    if not isinstance(by_profile, dict):
        by_profile = {}
    return list(by_profile.get(key, []))


def _save_tracks(tracks: list, profile_key: str = None):
    key = profile_key or _profile_key()
    conf = mw.addonManager.getConfig(__name__)
    by_profile = conf.get("daily_tracks_by_profile") or {}
    if not isinstance(by_profile, dict):
        by_profile = {}
    by_profile[key] = tracks
    conf["daily_tracks_by_profile"] = by_profile
    mw.addonManager.writeConfig(__name__, conf)


def _today_str() -> str:
    try:
        rollover = mw.col.conf.get("rollover", 4)
    except Exception:
        rollover = 4
    return str((datetime.now() - timedelta(hours=rollover)).date())


# ────────────────────────────────────────────────────────────────
# בורר קובץ מהמאגר
# ────────────────────────────────────────────────────────────────

class _FilePickerItem(QStandardItem):
    def __init__(self, display: str, raw_path: str = ""):
        super().__init__(display)
        self.raw_path = raw_path


class FilePicker(QDialog):
    def __init__(self, parent=None, source_root=""):
        super().__init__(parent or mw)
        self.source_root = source_root
        self.setWindowTitle("קלייבט אויס אן אנהייב טעקע פונעם מאגר")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.selected_file_path = ""

        layout = QVBoxLayout(self)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("זוכן...")
        layout.addWidget(self.filter_edit)

        self.tree_view = QTreeView()
        self.tree_view.header().setVisible(False)
        layout.addWidget(self.tree_view)

        self.path_label = QLabel("נישט אויסגעקליבן")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("באשטעטיקן")
        self.ok_btn.setEnabled(False)
        cancel_btn = QPushButton("אפזאגן")
        self.ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(self.ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        self._model = QStandardItemModel()
        # #307 — שימוש ב-_FilePickerProxyModel כדי שהחיפוש יהיה זהה למאגר השאלות
        self._proxy = _FilePickerProxyModel()
        self._proxy.setSourceModel(self._model)
        self.tree_view.setModel(self._proxy)

        self.filter_edit.textChanged.connect(self._on_filter)
        self.tree_view.clicked.connect(self._on_item_clicked)

        self._build_tree()
        self.resize(380, 550)

    def _build_tree(self):
        tree = _load_tree()

        # #307 — בניית נתיב תצוגה מלא לכל פריט עבור _SEARCH_TEXT_ROLE
        def _add(node, parent_item, raw_path, display_path):
            name = node.get("name", "")
            path = raw_path + "/" + name
            if self.source_root and not (path == self.source_root or path.startswith(self.source_root + "/") or self.source_root.startswith(path + "/")):
                return
            t = node.get("type", "")
            display = name[:-1] if name.endswith("$") else name
            display = display.replace("%", " ").replace("_", " ")
            full_display = f"{display_path}::{display}" if display_path else display
            if t == "directory":
                item = _FilePickerItem(display)
                item.setEditable(False)
                item.setData(full_display.lower(), _SEARCH_TEXT_ROLE)
                parent_item.appendRow(item)
                for child in node.get("children", []):
                    _add(child, item, raw_path + "/" + name, full_display)
            elif t == "file" and name.endswith(".txt"):
                file_path = raw_path + "/" + name
                label = display[:-4] if display.endswith(".txt") else display
                item_display = f"{display_path}::{label}" if display_path else label
                item = _FilePickerItem(label, raw_path=file_path)
                item.setEditable(False)
                item.setData(item_display.lower(), _SEARCH_TEXT_ROLE)
                parent_item.appendRow(item)

        for child in tree.get("children", []):
            _add(child, self._model, "מאגר השאלות", "")

    def _on_filter(self, text):
        # #307 — חיפוש מרובה מונחים כמו במאגר
        self._proxy.setFilterText(text)
        if text:
            self.tree_view.expandAll()
        else:
            self.tree_view.collapseAll()

    def _on_item_clicked(self, proxy_idx):
        src_idx = self._proxy.mapToSource(proxy_idx)
        item = self._model.itemFromIndex(src_idx)
        if isinstance(item, _FilePickerItem) and item.raw_path:
            self.selected_file_path = item.raw_path
            self.path_label.setText(item.raw_path)
            self.ok_btn.setEnabled(True)
        else:
            self.selected_file_path = ""
            self.path_label.setText("נישט אויסגעקליבן — קלייבט אויס א טעקע (נישט א תיקיה)")
            self.ok_btn.setEnabled(False)


# ────────────────────────────────────────────────────────────────
# חלון עריכת מסלול
# ────────────────────────────────────────────────────────────────

class TrackEditDialog(QDialog):
    def __init__(self, track: dict = None, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("רעדאקטירן א לערנען סדר" if track else "נייער לערנען סדר")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.result_track = None
        self._file_path = track["start_file"] if track else ""
        self._root_folder = track["root_folder"] if track else ""
        if track and track.get("start_file"):
            # Keep older tracks compatible: if scope was the current book only,
            # expand it to parent scope so progression continues to next book.
            old_book_scope = _folder_of(track.get("start_file", ""))
            if self._root_folder == old_book_scope:
                self._root_folder = _scope_folder_for_start_file(track["start_file"])

        layout = QVBoxLayout(self)

        # שם
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("נאמען פונעם לערנען סדר:"))
        self.name_edit = QLineEdit(track["name"] if track else "")
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        from aqt.qt import QComboBox
        from .learning_catalog import source_catalog, source_description
        self.source_combo = QComboBox()
        self.source_combo.addItem("קלייבט אויס א רב / מקור פאר שאלות…", "")
        for path in sorted(source_catalog()):
            label, detail = source_description(path)
            self.source_combo.addItem(path.split("/")[1] + " — " + label, path)
            self.source_combo.setItemData(self.source_combo.count() - 1, detail, Qt.ItemDataRole.ToolTipRole)
            if self._file_path.startswith(path + "/"):
                self.source_combo.setCurrentIndex(self.source_combo.count() - 1)
        layout.addWidget(QLabel("רב / מקור (איין מקור פאר יעדן פערזענליכן לערנען סדר):"))
        layout.addWidget(self.source_combo)
        self.source_combo.currentIndexChanged.connect(self._source_changed)

        # קובץ התחלה
        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("אנהייב טעקע:"))
        short = self._file_path.split("/")[-1] if self._file_path else "נישט אויסגעקליבן"
        self.file_label = QLabel(short)
        self.file_label.setWordWrap(True)
        file_row.addWidget(self.file_label, 1)
        pick_btn = QPushButton("אויסקלייבן...")
        pick_btn.clicked.connect(self._pick_file)
        file_row.addWidget(pick_btn)
        layout.addLayout(file_row)

        # ייבוא חלקי
        self.partial_cb = QCheckBox(
            "טיילווייז אימפארטירן — מען קען זיך אפשטעלן אינמיטן א טעקע און דארף נישט אימפארטירן די גאנצע טעקע"
        )
        self.partial_cb.setChecked(track.get("partial_files", False) if track else False)
        layout.addWidget(self.partial_cb)

        partial_hint = QLabel(
            "<small><i>"
            "ביים טיילווייזן אימפארט עפנט זיך אן אויסוואל פענצטער מיט דער יעצטיגער טעקע און צוויי קומענדיגע טעקעס.<br>"
            "אינעם פענצטער קענט איר אנצייכענען גענוי וועלכע שאלות צו אימפארטירן.<br>"
            "שאלות וואס איר האט שוין פריער אימפארטירט <b>ווערן נישט נאכאמאל געוויזן</b>.<br>"
            "ווען אלע שאלות פון דער יעצטיגער טעקע זענען אימפארטירט, גייט דער לערנען סדר אויטאמאטיש צו דער קומענדיגער טעקע."
            "</i></small>"
        )
        partial_hint.setWordWrap(True)
        layout.addWidget(partial_hint)

        # קצב
        adv_row = QHBoxLayout()
        adv_row.addWidget(QLabel("טעמפא — טעקעס צו אימפארטירן ביי יעדן מאל:"))
        self.advance_spin = QSpinBox()
        self.advance_spin.setRange(1, 20)
        self.advance_spin.setValue(track.get("advance_by", 1) if track else 1)
        adv_row.addWidget(self.advance_spin)
        adv_row.addStretch()
        layout.addLayout(adv_row)

        # אישיו #406: שליטת הצגת לוג הייבוא נמצאת בתוך חלון עריכת המסלול, ליד קצב הייבוא.
        default_show_log = bool(gc("show_import_log", True))
        self.show_log_cb = QCheckBox("ווייזט דעם רעקארד נאכן אויטאמאטישן אימפארט")
        self.show_log_cb.setChecked(
            bool(track.get("show_import_log", default_show_log)) if track else default_show_log
        )
        layout.addWidget(self.show_log_cb)

        self.partial_cb.toggled.connect(lambda c: self.advance_spin.setEnabled(not c))
        self.advance_spin.setEnabled(not self.partial_cb.isChecked())

        # תזמון
        trig_row = QHBoxLayout()
        trig_row.addWidget(QLabel("תזמון:"))
        self.trig_daily = QRadioButton("איינמאל א טאג")
        self.trig_open = QRadioButton("ביי יעדן עפענען")
        if track and track.get("trigger") == "on_open":
            self.trig_open.setChecked(True)
        else:
            self.trig_daily.setChecked(True)
        trig_row.addWidget(self.trig_daily)
        trig_row.addWidget(self.trig_open)
        trig_row.addStretch()
        layout.addLayout(trig_row)

        # כפתורים
        btns = QHBoxLayout()
        ok_btn = QPushButton("באשטעטיקן")
        cancel_btn = QPushButton("אפזאגן")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def _source_changed(self):
        source = self.source_combo.currentData()
        if source and not self._file_path.startswith(source + "/"):
            self._file_path = ""
            self._root_folder = ""
            self.file_label.setText("נישט אויסגעקליבן — קלייבט אויס א טעקע פונעם נייעם מקור")

    def _pick_file(self):
        picker = FilePicker(self, source_root=self.source_combo.currentData() or "")
        if picker.exec() and picker.selected_file_path:
            self._file_path = picker.selected_file_path
            self._root_folder = _scope_folder_for_start_file(self._file_path)
            self.file_label.setText(self._file_path.split("/")[-1])
            for i in range(1, self.source_combo.count()):
                if self._file_path.startswith(self.source_combo.itemData(i) + "/"):
                    self.source_combo.setCurrentIndex(i)
                    break

    def _on_accept(self):
        from aqt.utils import showInfo
        name = self.name_edit.text().strip()
        if not name:
            showInfo("לייגט אריין א נאמען פארן לערנען סדר")
            return
        if not self._file_path:
            showInfo("קלייבט אויס אן אנהייב טעקע")
            return

        self._root_folder = _scope_folder_for_start_file(self._file_path)
        files = get_all_files_in_folder(self._root_folder)
        try:
            idx = files.index(self._file_path)
        except ValueError:
            idx = 0

        self.result_track = {
            "name": name,
            "root_folder": self._root_folder,
            "start_file": self._file_path,
            "current_file_index": idx,
            "advance_by": self.advance_spin.value(),
            "partial_files": self.partial_cb.isChecked(),
            # אישיו #406: שומרים את הבחירה לכל מסלול כדי שהייבוא האוטומטי יכבד אותה.
            "show_import_log": self.show_log_cb.isChecked(),
            "partial_done_guids": [],
            "trigger": "on_open" if self.trig_open.isChecked() else "daily",
            "last_triggered": "",
            "enabled": True,
        }
        self.accept()


# ────────────────────────────────────────────────────────────────
# חלון ניהול מסלולים
# ────────────────────────────────────────────────────────────────

class TrackManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self._profile = _profile_key()
        self.setWindowTitle(f"די טעגליכע הספקים — {self._profile}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(540, 430)
        self._tracks = _get_tracks(self._profile)

        layout = QVBoxLayout(self)

        self.enabled_cb = QCheckBox("אקטיווירט פערזענליך צוגעפאסטע הספקים")
        enabled_by_profile = gc("daily_tracks_enabled_by_profile") or {}
        self.enabled_cb.setChecked(bool(enabled_by_profile.get(self._profile, False)))
        layout.addWidget(self.enabled_cb)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        hint = QLabel("טאפלט קליק צו רעדאקטירן  |  אנצייכענען/אפצייכענען צו אקטיווירן/אויסלעשן  |  נומערן = די יעצטיגע טעקע פון אלע טעקעס")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("לייגט צו א לערנען סדר")
        self.edit_btn = QPushButton("רעדאקטירן")
        self.del_btn = QPushButton("אויסמעקן")
        add_btn.clicked.connect(self._add_track)
        self.edit_btn.clicked.connect(self._edit_track)
        self.del_btn.clicked.connect(self._del_track)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        ok_row = QHBoxLayout()
        ok_btn = QPushButton("אפזיכערן און פארמאכן")
        cancel_btn = QPushButton("אפזאגן")
        ok_btn.clicked.connect(self._save_and_close)
        cancel_btn.clicked.connect(self.reject)
        ok_row.addStretch()
        ok_row.addWidget(ok_btn)
        ok_row.addWidget(cancel_btn)
        layout.addLayout(ok_row)

        self.list_widget.itemDoubleClicked.connect(lambda _: self._edit_track())
        self.list_widget.currentRowChanged.connect(lambda _: self._update_btns())

        self._refresh_list()
        self._update_btns()

    def _refresh_list(self):
        self.list_widget.clear()
        for t in self._tracks:
            files = get_all_files_in_folder(t.get("root_folder", ""))
            total = len(files)
            current = t.get("current_file_index", 0)
            trigger = "טעגליך" if t.get("trigger") != "on_open" else "יעדעס עפענען"
            mode = "טיילווייז" if t.get("partial_files") else f'{t.get("advance_by", 1)} טעקעס'
            label = f"{t['name']}  |  {current}/{total}  |  {mode}  |  {trigger}"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if t.get("enabled") else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)

    def _update_btns(self):
        has = self.list_widget.currentRow() >= 0
        self.edit_btn.setEnabled(has)
        self.del_btn.setEnabled(has)

    def _add_track(self):
        self._capture_enabled()
        dlg = TrackEditDialog(parent=self)
        if dlg.exec() and dlg.result_track:
            self._tracks.append(dlg.result_track)
            self._refresh_list()

    def _edit_track(self):
        self._capture_enabled()
        row = self.list_widget.currentRow()
        if row < 0:
            return
        old = self._tracks[row]
        dlg = TrackEditDialog(track=old, parent=self)
        if dlg.exec() and dlg.result_track:
            new = dlg.result_track
            # שמירת ההתקדמות אם התיקייה לא השתנתה
            if new["root_folder"] == old.get("root_folder"):
                new["current_file_index"] = old.get("current_file_index", new["current_file_index"])
                new["partial_done_guids"] = old.get("partial_done_guids", [])
                new["last_triggered"] = old.get("last_triggered", "")
            self._tracks[row] = new
            self._refresh_list()

    def _del_track(self):
        self._capture_enabled()
        row = self.list_widget.currentRow()
        if row >= 0:
            self._tracks.pop(row)
            self._refresh_list()

    def _capture_enabled(self):
        for i in range(self.list_widget.count()):
            if i < len(self._tracks):
                item = self.list_widget.item(i)
                self._tracks[i]["enabled"] = (item.checkState() == Qt.CheckState.Checked)

    def save_settings(self):
        self._capture_enabled()
        conf = mw.addonManager.getConfig(__name__)
        # שמירת enabled_by_profile
        enabled_by_profile = conf.get("daily_tracks_enabled_by_profile") or {}
        if not isinstance(enabled_by_profile, dict):
            enabled_by_profile = {}
        enabled_by_profile[self._profile] = self.enabled_cb.isChecked()
        conf["daily_tracks_enabled_by_profile"] = enabled_by_profile
        # שמירת המסלולים לפרופיל הנוכחי
        by_profile = conf.get("daily_tracks_by_profile") or {}
        if not isinstance(by_profile, dict):
            by_profile = {}
        by_profile[self._profile] = self._tracks
        conf["daily_tracks_by_profile"] = by_profile
        mw.addonManager.writeConfig(__name__, conf)

    def _save_and_close(self):
        self.save_settings()
        self.accept()


# ────────────────────────────────────────────────────────────────
# לוגיקת ייבוא
# ────────────────────────────────────────────────────────────────

def _run_track(track_idx: int, profile_key: str = None):
    tracks = _get_tracks(profile_key)
    if track_idx >= len(tracks):
        return
    track = dict(tracks[track_idx])

    # Auto-migrate old tracks that were scoped only to the current book folder.
    start_file = track.get("start_file", "")
    if start_file:
        old_book_scope = _folder_of(start_file)
        if track.get("root_folder") == old_book_scope:
            track["root_folder"] = _scope_folder_for_start_file(start_file)
            tracks[track_idx]["root_folder"] = track["root_folder"]
            _save_tracks(tracks, profile_key)

    files = get_all_files_in_folder(track.get("root_folder", ""))
    if not files:
        return

    current_idx = track.get("current_file_index", 0)
    if current_idx >= len(files):
        tooltip(f"לערנען סדר '{track['name']}': פארענדיגט — אלע טעקעס זענען אימפארטירט")
        return

    if track.get("partial_files"):
        _run_partial_track(tracks, track_idx, track, files, current_idx, profile_key)
    else:
        _run_full_track(tracks, track_idx, track, files, current_idx, profile_key)


def _run_full_track(tracks, track_idx, track, files, current_idx, profile_key=None):
    advance = track.get("advance_by", 1)
    window = files[current_idx: current_idx + advance]

    for n in repo_notetypes_names:
        getOrCreateModels(mw.col, n)

    mw.progress.start(label=f"לערנען סדר '{track['name']}': אימפארטירט...", immediate=True)
    try:
        result = importFromFolder(window, _col=mw.col, allow_dupes=2, progress_manager=mw.progress)
    finally:
        mw.progress.finish()

    # אישיו #406: מסלול מלא מציג את הלוג רק אם המשתמש בחר זאת בחלון המסלול.
    if result and track.get("show_import_log", bool(gc("show_import_log", True))):
        showText(result, type="html")

    tracks[track_idx]["current_file_index"] = min(current_idx + advance, len(files))
    tracks[track_idx]["last_triggered"] = _today_str()
    _save_tracks(tracks, profile_key)


def _run_partial_track(tracks, track_idx, track, files, current_idx, profile_key=None):
    # חלון דינמי: 3 + בונוס מהסשן הקודם (כמה קבצים הסתיימו לחלוטין פעם שעברה)
    bonus = track.get("partial_window_bonus", 0)
    window = files[current_idx: current_idx + 3 + bonus]

    # יצירת אוסף זמני — מחיקה מחדש בכל פעם כדי לאפס GUIDים
    short_name = f"temp_daily_track_{track_idx}"
    temp_dir = os.path.join(tmpdir(), short_name)
    col_path = os.path.join(temp_dir, "collection.anki2")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)

    try:
        temp_col = Collection(col_path)
    except Exception as e:
        show_failure("מען קען נישט צוגרייטן די שאלות פארן טעגליכן לערנען סדר. עפנט אנקי איבער און פרובירט נאכאמאל.", e)
        return

    temp_col.decks.remove(d["id"] for d in temp_col.decks.all())
    for n in repo_notetypes_names:
        getOrCreateModels(temp_col, n)

    mw.progress.start(label=f"לערנען סדר '{track['name']}': לאדט טעקעס...", immediate=True)
    try:
        importFromFolder(window, temp_col, col_path=col_path, allow_dupes=2,
                         return_after_import=True)
    finally:
        mw.progress.finish()

    # מיפוי: נתיב קובץ → סט שדות ראשונים (לפני סינון) — ישמש לזיהוי כמה קבצים הסתיימו
    file_first_fields_map: dict[str, set] = {}
    for f_path in window:
        fname = f_path.split("/")[-1].replace(".txt", "")
        ffs = {
            flds.split('\x1f')[0]
            for flds in temp_col.db.list(
                "SELECT flds FROM notes WHERE tags LIKE ?", f"% {fname} %"
            )
            if flds
        }
        file_first_fields_map[f_path] = ffs

    # שדות ראשונים של הקובץ הנוכחי
    current_file_first_fields = file_first_fields_map.get(files[current_idx], set())

    # שדות ראשונים של כל הפתקים הקיימים ב-mw.col
    main_first_fields = {
        flds.split('\x1f')[0]
        for flds in mw.col.db.list("SELECT flds FROM notes")
        if flds
    }

    # אילו שאלות מהקובץ הנוכחי עדיין לא יובאו
    current_first_fields_remaining = current_file_first_fields - main_first_fields

    # סינון: מסיר מ-temp_col כל פתק שהשדה הראשון שלו כבר קיים ב-mw.col
    already_imported = [
        nid for nid, flds in temp_col.db.all("SELECT id, flds FROM notes")
        if flds and flds.split('\x1f')[0] in main_first_fields
    ]
    if already_imported:
        temp_col.remove_notes(already_imported)

    if not temp_col.db.scalar("SELECT count() FROM notes"):
        tooltip(f"לערנען סדר '{track['name']}': אלע שאלות פון דער יעצטיגער טעקע זענען שוין אימפארטירט")
        temp_col.close()
        if not current_first_fields_remaining:
            tracks[track_idx]["current_file_index"] = current_idx + 1
            tracks[track_idx]["partial_window_bonus"] = 0
            tracks[track_idx]["last_triggered"] = _today_str()
            _save_tracks(tracks, profile_key)
        return

    d = mw._cropro_main_dialog(parent=mw, temp_col=temp_col, temp_col_path=col_path)

    def _on_done():
        new_main_first_fields = {
            flds.split('\x1f')[0]
            for flds in mw.col.db.list("SELECT flds FROM notes")
            if flds
        }
        # סופרים כמה קבצים הסתיימו לחלוטין ברצף מהתחלה
        files_completed = 0
        for f_path in window:
            ffs = file_first_fields_map.get(f_path, set())
            if ffs and ffs.issubset(new_main_first_fields):
                files_completed += 1
            else:
                break  # עוצרים בקובץ הראשון שלא הסתיים

        if files_completed > 0:
            tracks[track_idx]["current_file_index"] = current_idx + files_completed

        # בפעם הבאה — מרחיבים את החלון בכמות הקבצים שהסתיימו
        tracks[track_idx]["partial_window_bonus"] = files_completed
        tracks[track_idx]["last_triggered"] = _today_str()
        _save_tracks(tracks, profile_key)

    d.finished.connect(_on_done)
    d.show()


# ────────────────────────────────────────────────────────────────
# הפעלה אוטומטית בפתיחת פרופיל
# ────────────────────────────────────────────────────────────────

def _should_trigger(track: dict) -> bool:
    if not track.get("enabled"):
        return False
    if track.get("trigger") == "on_open":
        return True
    last = track.get("last_triggered", "")
    try:
        return last != _today_str()
    except Exception:
        return True


def run_tracks_on_open():
    profile = _profile_key()
    enabled_by_profile = gc("daily_tracks_enabled_by_profile") or {}
    if not enabled_by_profile.get(profile):
        return
    tracks = _get_tracks(profile)
    for i, track in enumerate(tracks):
        if _should_trigger(track):
            _run_track(i, profile)


def open_track_manager():
    from .daily_manager import open_daily_manager
    open_daily_manager("custom")


profile_did_open.append(run_tracks_on_open)
