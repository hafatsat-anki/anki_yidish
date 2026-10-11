"""One entry point for public calendars and personal question-bank tracks."""
from copy import deepcopy

from aqt import mw
from aqt.qt import (
    QApplication, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, Qt,
)
from aqt.utils import askUser

from .config import gc
from .learning_catalog import group_for
from .public_learning import ACTIVE_TRACKS
from .public_tracks import PublicTracksDialog


class DailyManager(QDialog):
    def __init__(self, key="daf", parent=None):
        super().__init__(parent or mw)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle("טעגליכע הספקים")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        available = self.screen().availableGeometry()
        self.resize(min(760, available.width() - 40), min(570, available.height() - 80))
        self.profile = mw.pm.name
        self._saved_public_state = None
        self._saved_custom_state = None
        self._saved_panel_states = {}
        layout = QVBoxLayout(self)
        self.heading = QLabel("טעגליכע הספקים — לערנען סדרים איינשטעלונגען")
        self.heading.setWordWrap(True)
        layout.addWidget(self.heading)
        body = QSplitter(Qt.Orientation.Horizontal)
        body.setChildrenCollapsible(False)
        side_widget = QWidget()
        side_widget.setMinimumWidth(100)
        sidebar = QVBoxLayout(side_widget)
        sidebar.setContentsMargins(0, 0, 0, 0)
        search = QLineEdit()
        search.setPlaceholderText("זוכן א לערנען סדר…")
        sidebar.addWidget(search)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("לערנען סדרים")
        self.tree.setMinimumWidth(100)
        self.tree.setWordWrap(True)
        sidebar.addWidget(self.tree)
        body.addWidget(side_widget)
        self.stack = QStackedWidget()
        self.stack.setMinimumSize(100, 100)
        self.stack.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        body.addWidget(self.stack)
        body.setStretchFactor(1, 1)
        body.setSizes([180, 540])
        layout.addWidget(body, 1)
        self.public = PublicTracksDialog(self, embedded=True)
        self.public_scroll = self._scroll_panel(self.public)
        self.stack.addWidget(self.public_scroll)
        self.panels = {}
        self.items = {}
        groups = {}
        for route, title in {"daf": "דף היומי", **ACTIVE_TRACKS, "custom": "פערזענליך צוגעפאסט"}.items():
            group = "פערזענליך צוגעפאסט" if route == "custom" else ("משנה ותלמוד" if route == "daf" else group_for(route))
            if group not in groups:
                groups[group] = QTreeWidgetItem(self.tree, [group])
            item = QTreeWidgetItem(groups[group], [title])
            item.setData(0, Qt.ItemDataRole.UserRole, route)
            self.items[route] = item
        self.tree.expandAll()
        self.tree.currentItemChanged.connect(self._select)
        search.textChanged.connect(self._filter)
        self.status = QLabel("די אויסוואל פון מקורות ווערט אפגעזיכערט באזונדער פאר יעדן לערנען סדר. דער צאל שאלות באווייזט נישט אז אלע זאכן ווערן געדעקט.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        files = QPushButton("פרטים פונעם אינהאלט אין די טעקעס")
        from .source_files import show_source_files
        files.clicked.connect(lambda: show_source_files(self))
        buttons.addWidget(files)
        save = QPushButton("אפזיכערן")
        save.clicked.connect(self._save)
        close = QPushButton("פארמאכן")
        close.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(save)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.tree.setCurrentItem(self.items.get(key, self.items["daf"]))
        self._remember_saved_state()

    def _scroll_panel(self, panel):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumSize(0, 0)
        scroll.setWidget(panel)
        return scroll

    def _filter(self, text):
        for key, item in self.items.items():
            item.setHidden(text.strip() not in item.text(0))
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            group.setHidden(all(group.child(j).isHidden() for j in range(group.childCount())))

    def _select(self, item, previous=None):
        if not item:
            return
        key = item.data(0, Qt.ItemDataRole.UserRole)
        if not key:
            return
        self.heading.setText("טעגליכע הספקים — " + item.text(0))
        if key in ACTIVE_TRACKS:
            self.public.track.setCurrentIndex(self.public.track.findData(key))
            self.stack.setCurrentWidget(self.public_scroll)
            return
        if key not in self.panels:
            if key == "daf":
                from .daf_hayomi import settings_dialog
                panel = settings_dialog(self)
                panel.buttonBox.hide()
            else:
                from .daily_track import TrackManagerDialog
                panel = TrackManagerDialog(self)
                for button in panel.findChildren(QPushButton):
                    if button.text() in ("אפזיכערן און פארמאכן", "אפזאגן"):
                        button.hide()
            panel.setWindowFlags(Qt.WindowType.Widget)
            scroll = self._scroll_panel(panel)
            self.stack.addWidget(scroll)
            self.panels[key] = (panel, scroll)
            self._saved_panel_states[key] = self._panel_state(panel)
        self.stack.setCurrentWidget(self.panels[key][1])

    @staticmethod
    def _normalise_public_state(settings):
        state = {}
        for key in ACTIVE_TRACKS:
            saved = settings.get(key, {}) or {}
            sources = saved.get("sources", []) or []
            if not isinstance(sources, (list, tuple)):
                sources = [sources]
            state[key] = (
                bool(saved.get("enabled", False)),
                bool(saved.get("ask_before_import", True)),
                bool(saved.get("allow_dupes", False)),
                bool(saved.get("group_by_book", False)),
                tuple(sources),
            )
        return state

    def _public_state(self):
        self.public._stash_current()
        settings = deepcopy(self.public._settings)
        for key, draft in self.public._drafts.items():
            saved = dict(settings.get(key, {}) or {})
            saved.update(deepcopy(draft))
            settings[key] = saved
        return self._normalise_public_state(settings)

    @staticmethod
    def _panel_state(panel):
        if hasattr(panel, "daf_on"):
            profiles = []
            model = panel.model
            index = 0
            while model.item(index):
                item = model.item(index)
                if item.checkState() == Qt.CheckState.Checked:
                    profiles.append(item.text())
                index += 1
            return (
                bool(panel.daf_on.isChecked()),
                bool(panel.ask_before_import.isChecked()),
                bool(panel.daf_allow_dupes.isChecked()),
                bool(panel.group_by_masechet.isChecked()),
                bool(panel.import_to_each_profile.isChecked()),
                tuple(
                    checkbox.property("source_name") or checkbox.text()
                    for checkbox in panel.rab_actions
                    if checkbox.isChecked()
                ),
                tuple(profiles),
            )
        if hasattr(panel, "_tracks"):
            panel._capture_enabled()
            return bool(panel.enabled_cb.isChecked()), deepcopy(panel._tracks)
        return None

    def _custom_state(self):
        panel_data = self.panels.get("custom")
        if panel_data is None:
            return self._saved_custom_state
        panel = panel_data[0]
        panel._capture_enabled()
        return bool(panel.enabled_cb.isChecked()), deepcopy(panel._tracks)

    def _saved_custom_config_state(self):
        enabled_by_profile = gc("daily_tracks_enabled_by_profile") or {}
        tracks_by_profile = gc("daily_tracks_by_profile") or {}
        if not isinstance(enabled_by_profile, dict):
            enabled_by_profile = {}
        if not isinstance(tracks_by_profile, dict):
            tracks_by_profile = {}
        return (
            bool(enabled_by_profile.get(self.profile, False)),
            deepcopy(tracks_by_profile.get(self.profile, []) or []),
        )

    def _remember_saved_state(self):
        self._saved_public_state = self._public_state()
        self._saved_custom_state = self._saved_custom_config_state()
        self._saved_panel_states = {
            key: self._panel_state(panel)
            for key, (panel, _) in self.panels.items()
        }

    def _has_unsaved_changes(self):
        if self._public_state() != self._saved_public_state:
            return True
        if self._custom_state() != self._saved_custom_state:
            return True
        for key, (panel, _) in self.panels.items():
            if key == "custom":
                continue
            if self._panel_state(panel) != self._saved_panel_states.get(key):
                return True
        return False

    def _save(self):
        if mw.pm.name != self.profile:
            return False
        if not self.public._save():
            return False
        for panel, _ in self.panels.values():
            panel.save_settings()
        self._remember_saved_state()
        self.status.setText("די איינשטעלונגען זענען אפגעזיכערט. דאס אפזיכערן אימפארטירט נישט קיין שאלות.")
        return True

    def reject(self):
        if self._has_unsaved_changes() and askUser("אפזיכערן די איינשטעלונגען איידער מען פארמאכט?", parent=self):
            if not self._save():
                return
        super().reject()

    def closeEvent(self, event):
        event.ignore()
        self.reject()


_manager = None


def _forget_manager(manager):
    global _manager
    if _manager is manager:
        _manager = None


def _release_manager(manager):
    global _manager
    if _manager is manager:
        _manager = None


def show_daily_manager(key="daf", parent=None):
    global _manager
    owner = parent or QApplication.activeModalWidget() or QApplication.activeWindow() or mw
    if _manager is not None and (owner is _manager or _manager.isAncestorOf(owner)):
        owner = _manager.parentWidget() or mw
    if _manager is None or _manager.profile != mw.pm.name:
        if _manager is not None:
            _manager.hide()
        _manager = DailyManager(key, parent=owner)
        manager = _manager
        manager.finished.connect(lambda _: _release_manager(manager))
        manager.destroyed.connect(lambda: _forget_manager(manager))
    else:
        if _manager.parentWidget() is not owner:
            _manager.setParent(owner, Qt.WindowType.Dialog)
            _manager.setWindowModality(Qt.WindowModality.WindowModal)
        _manager.tree.setCurrentItem(_manager.items.get(key, _manager.items["daf"]))
    _manager.show()
    _manager.raise_()
    _manager.activateWindow()
    return _manager


def open_daily_manager(key="daf", parent=None):
    return show_daily_manager(key, parent=parent)
