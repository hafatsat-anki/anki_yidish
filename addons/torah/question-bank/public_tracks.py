"""Settings for automatic public tracks; importing happens outside this dialog."""
import json
from pathlib import Path

from aqt import mw, gui_hooks
from aqt.qt import QCheckBox, QComboBox, QDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, Qt, QVBoxLayout
from aqt.utils import showInfo

from .config import gc
from .daily_track import _today_str
# #458 — שימוש בממיר התאריך הקיים של התוסף לתצוגת תאריך עברי.
from .hebrew_date_edit import date_label
from .learning_catalog import source_description
from .public_learning import ACTIVE_TRACKS, lesson_for, source_roots


class PublicTracksDialog(QDialog):
    def __init__(self, parent=None, embedded=False):
        super().__init__(parent or mw)
        if embedded:
            self.setWindowFlags(Qt.WindowType.Widget)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._profile = mw.pm.name
        self._tree = json.loads(Path(__file__).with_name("repo_struct.json").read_text(encoding="utf-8"))
        self._settings = dict((gc("public_tracks_by_profile") or {}).get(self._profile, {}))
        self._current_key = None
        self._drafts = {}
        # #458 — מספר בקשה מונע מתוצאה של מסלול קודם להחליף מסלול נוכחי.
        self._lesson_request = 0
        layout = QVBoxLayout(self)
        self.track = QComboBox()
        for key, title in ACTIVE_TRACKS.items():
            self.track.addItem(title, key)
        self.track.setVisible(not embedded)
        layout.addWidget(self.track)
        # #458 — מציגים את ההספק הצפוי ואת סטטוס הטעינה בתוך בחירת המסלול.
        self.expected_lesson = QLabel("דער ערווארטעטער הספק פאר היינט: לאדט…")
        self.expected_lesson.setWordWrap(True)
        layout.addWidget(self.expected_lesson)
        self.enabled = QCheckBox("לייגט אויטאמאטיש אריין שאלות לויטן לערנען סדר")
        layout.addWidget(self.enabled)
        self.ask_before = QCheckBox("פרעגט יעדן טאג איידער מען לייגט צו שאלות")
        self.allow_dupes = QCheckBox("אימפארטירט אויך שאלות וואס זענען שוין פריער אימפארטירט")
        self.allow_dupes.setToolTip("קען שאפן טאפלטע רשומות")
        self.group_by_book = QCheckBox("גרופירט לויט מסכת אנשטאט לויטן לערנען טאג")
        for widget in (self.ask_before, self.allow_dupes, self.group_by_book):
            layout.addWidget(widget)
        layout.addWidget(QLabel("שאלות פון:"))
        self.source_search = QLineEdit()
        self.source_search.setPlaceholderText("זוכן א רב אדער מקור…")
        self.source_search.textChanged.connect(self._filter_sources)
        layout.addWidget(self.source_search)
        self.sources = QListWidget()
        self.sources.setWordWrap(True)
        self.sources.setMinimumHeight(120)
        layout.addWidget(self.sources, 1)
        note = QLabel("די איינשטעלונגען ווערן אפגעזיכערט פארן יעצטיגן פראפיל. דער הספק טוישט זיך לויט דער טאג טוישן צייט אין די Anki איינשטעלונגען. שאלות אן אן איינדייטיגן פלאץ ווערן נישט אויטאמאטיש אימפארטירט.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.enabled.toggled.connect(self._toggle)
        self.track.currentIndexChanged.connect(self._track_changed)
        self._track_changed()

    def _toggle(self, enabled):
        for widget in (self.ask_before, self.allow_dupes, self.group_by_book, self.source_search, self.sources):
            widget.setEnabled(enabled)

    def _filter_sources(self, text):
        for index in range(self.sources.count()):
            item = self.sources.item(index)
            item.setHidden(text.strip() not in item.text())

    def _stash_current(self):
        if self._current_key is not None:
            self._drafts[self._current_key] = {
                "enabled": self.enabled.isChecked(),
                "ask_before_import": self.ask_before.isChecked(),
                "allow_dupes": self.allow_dupes.isChecked(),
                "group_by_book": self.group_by_book.isChecked(),
                "sources": self._selected_sources(),
            }

    def _selected_sources(self):
        return [self.sources.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.sources.count())
                if self.sources.item(i).checkState() == Qt.CheckState.Checked]

    def _track_changed(self, *_):
        self._stash_current()
        self._current_key = self.track.currentData()
        # #458 — מאפסים מיד את התצוגה ומתחילים את החישוב בלי לחסום את הניווט.
        self._lesson_request += 1
        request = self._lesson_request
        key = self._current_key
        self.expected_lesson.setText("דער ערווארטעטער הספק פאר היינט: לאדט…")
        # Start the potentially heavy calendar lookup before rebuilding the
        # source list, so route navigation and the calculation proceed together.
        self._load_expected_lesson(key, request)
        saved = self._drafts.get(self._current_key, self._settings.get(self._current_key, {}))
        self.enabled.setChecked(saved.get("enabled", False))
        self.ask_before.setChecked(saved.get("ask_before_import", True))
        self.allow_dupes.setChecked(saved.get("allow_dupes", False))
        self.group_by_book.setChecked(saved.get("group_by_book", False))
        self.sources.clear()
        self.source_search.clear()
        for path, title in source_roots(self._tree, self._current_key):
            label, detail = source_description(path, title)
            item = QListWidgetItem(title)
            item.setToolTip(label + "\n" + detail)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if path in saved.get("sources", []) else Qt.CheckState.Unchecked)
            self.sources.addItem(item)
        self._toggle(self.enabled.isChecked())

    def _load_expected_lesson(self, key, request):
        if not key:
            self.expected_lesson.setText("קיין לערנען סדר איז נישט אויסגעקליבן")
            return

        # #458 — היום הלוגי של Anki מכבד את שעת החלפת היום, והתווית מוצגת בעברית.
        today = _today_str()
        hebrew_today = date_label(today)

        def done(future):
            if request != self._lesson_request or key != self._current_key:
                return
            try:
                lesson = future.result()
            except (ValueError, KeyError, OSError) as error:
                self.expected_lesson.setText(f"מען קען נישט אויסרעכענען דעם היינטיגן הספק: {error}")
            except Exception:
                self.expected_lesson.setText("מען קען נישט אויסרעכענען דעם ערווארטעטן היינטיגן הספק.")
            else:
                # #458 — מציגים את התאריך העברי לצד הדף/הסימן שחושב למסלול.
                text = f"דער ערווארטעטער היינטיגער הספק ({hebrew_today}): {lesson.label}"
                if not lesson.mapped:
                    text += "\nנישט אלע שאלות פון דעם הספק זענען אויטאמאטיש צוגעפאסט."
                if lesson.forecast:
                    text += "\nדאס איז א פאראויסשאצונג און עס קען זיך טוישן."
                self.expected_lesson.setText(text)

        taskman = getattr(mw, "taskman", None)
        run_in_background = getattr(taskman, "run_in_background", None)
        if run_in_background is None:
            # Keeps isolated UI tests and partially initialized windows usable;
            # Anki always supplies taskman during normal operation.
            class _ImmediateResult:
                def __init__(self, value=None, error=None):
                    self._value = value
                    self._error = error

                def result(self):
                    if self._error is not None:
                        raise self._error
                    return self._value

            try:
                result = _ImmediateResult(value=lesson_for(key, today))
            except Exception as error:
                result = _ImmediateResult(error=error)
            done(result)
            return

        run_in_background(lambda: lesson_for(key, today), done)

    def _save(self):
        if mw.pm.name != self._profile:
            return False
        self._stash_current()
        for key, draft in self._drafts.items():
            if draft["enabled"] and not draft["sources"]:
                showInfo(f"קלייבט אויס מקורות איידער איר אקטיווירט {ACTIVE_TRACKS[key]}.", parent=self)
                return False
        config = mw.addonManager.getConfig(__name__) or {}
        profile = config.setdefault("public_tracks_by_profile", {}).setdefault(self._profile, {})
        for key, draft in self._drafts.items():
            saved = dict(profile.get(key, {}))
            if saved.get("sources") != draft["sources"]:
                saved.pop("last_imported", None)
                saved.pop("imported_days", None)
                saved["start_day"] = _today_str()
            if draft["enabled"] and not saved.get("start_day") and not saved.get("last_imported"):
                saved["start_day"] = _today_str()
            profile[key] = {**saved, **draft}
        mw.addonManager.writeConfig(__name__, config)
        self._settings = dict(profile)
        return True


def open_public_tracks():
    from .daily_manager import open_daily_manager
    open_daily_manager("amud")


def _on_profile_open():
    from .public_auto_import import start_daily_imports
    start_daily_imports()


gui_hooks.profile_did_open.append(_on_profile_open)
