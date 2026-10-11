"""Import mapped daily lessons at profile opening, without a question picker."""
from datetime import date, timedelta
import json
from pathlib import Path

from anki.collection import CsvMetadata
from aqt import mw, gui_hooks
from aqt.qt import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QTimer, Qt, QVBoxLayout
from aqt.utils import askUser, showInfo, showText

from .archive_access import archive_path
from .config import gc
from .custom_importer import importFromFolder
from .daily_track import _today_str
from .import_templates import getOrCreateModels, repo_notetypes_names
from .hebrew_date_edit import date_label
from .public_learning import ACTIVE_TRACKS, calendar_data, candidate_files, lesson_for, plan_rows

_run = None


def history_start(saved, today):
    if saved.get("start_day"):
        return saved["start_day"]
    if saved.get("last_imported"):
        return (date.fromisoformat(saved["last_imported"]) + timedelta(days=1)).isoformat()
    return today


def due_lessons(key, saved, today):
    calendar = calendar_data()["calendars"][key]
    first = history_start(saved, today)
    day = date.fromisoformat(max(first, calendar["start"]))
    last = date.fromisoformat(today)
    if today > calendar["end"]:
        raise ValueError(f"דער קאלענדאר פון {ACTIVE_TRACKS[key]} איז פארענדיגט; דערהיינטיגט עס איידער איר אימפארטירט ווייטער.")
    completed = set(saved.get("imported_days", []))
    if saved.get("last_imported"):
        completed.add(saved["last_imported"])
    lessons = {}
    while day <= last:
        lesson = lesson_for(key, day.isoformat())
        if lesson.mapped and not lesson.review and lesson.day not in completed:
            # Or Menachem has fewer questions than calendar days. Empty days
            # should not repeatedly prompt for an import that cannot happen.
            if key != "chofetz" or candidate_files({}, lesson, saved.get("sources", []))[0]:
                lessons[lesson.day] = lesson
        day += timedelta(days=1)
    return list(lessons.values())


def choose_lessons(title, lessons):
    dialog = QDialog(mw)
    dialog.setWindowTitle(title)
    dialog.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    size = dialog.screen().availableGeometry()
    dialog.resize(min(480, size.width() - 40), min(420, size.height() - 80))
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("צייכנט אן די הספקים וואס איר האט שוין געלערנט:"))
    listing = QListWidget()
    listing.setWordWrap(True)
    for lesson in lessons:
        item = QListWidgetItem(f"{date_label(lesson.day)} — {lesson.label}")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        listing.addItem(item)
    layout.addWidget(listing)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return []
    return [lesson for i, lesson in enumerate(lessons) if listing.item(i).checkState() == Qt.CheckState.Checked]


def start_daily_imports():
    global _run
    if _run is not None or not mw.col:
        return
    token = object()
    _run = token
    profile_name, collection = mw.pm.name, mw.col
    # Defer until all profile-open hooks (including the original daf importer) finish.
    QTimer.singleShot(0, lambda: _start(token, profile_name, collection))


def _start(token, profile_name, collection):
    global _run
    if _run is not token or mw.col is not collection or mw.pm.name != profile_name:
        return
    settings = (gc("public_tracks_by_profile") or {}).get(profile_name, {})
    queue = []
    try:
        tree = json.loads(Path(__file__).with_name("repo_struct.json").read_text(encoding="utf-8"))
        for key, saved in settings.items():
            if key not in ACTIVE_TRACKS or not saved.get("enabled") or not saved.get("sources"):
                continue
            try:
                if not saved.get("start_day"):
                    saved["start_day"] = history_start(saved, _today_str())
                    config = mw.addonManager.getConfig(__name__) or {}
                    config.setdefault("public_tracks_by_profile", {}).setdefault(profile_name, {}).setdefault(key, {})["start_day"] = saved["start_day"]
                    mw.addonManager.writeConfig(__name__, config)
                lessons = due_lessons(key, saved, _today_str())
            except (ValueError, KeyError, OSError) as error:
                from _shared_libs.haf_notifications import show_failure
                show_failure(f"מען קען נישט צוגרייטן דעם לערנען סדר '{ACTIVE_TRACKS[key]}'. קאנטראלירט דעם אנהייב דאטום און די מקורות אין די איינשטעלונגען פונעם לערנען סדר.", error)
                continue
            if len(lessons) > 1:
                lessons = choose_lessons(ACTIVE_TRACKS[key], lessons)
            elif lessons and saved.get("ask_before_import", True):
                if not askUser(f"{ACTIVE_TRACKS[key]}: {lessons[0].label}. האט איר געלערנט דעם הספק?", parent=mw):
                    continue
            queue.extend((lesson, dict(saved)) for lesson in lessons)
    except Exception:
        if _run is token:
            _run = None
        raise

    def valid():
        return _run is token and mw.col is collection and mw.pm.name == profile_name

    def next_lesson():
        global _run
        if not valid():
            return
        if not queue:
            _run = None
            return
        lesson, saved = queue.pop(0)
        try:
            files, _ = candidate_files(tree, lesson, saved["sources"])
        except (ValueError, KeyError, OSError) as error:
            from _shared_libs.haf_notifications import show_failure
            show_failure(f"מען קען נישט צוגרייטן {lesson.label}. קאנטראלירט די מקורות אין די איינשטעלונגען פונעם לערנען סדר און פרובירט נאכאמאל.", error)
            QTimer.singleShot(0, next_lesson)
            return
        if not files:
            showInfo(f"{lesson.label}: אין די אויסגעקליבענע מקורות זענען נישט דא קיין צוגעפאסטע שאלות.", parent=mw)
            QTimer.singleShot(0, next_lesson)
            return

        def done(future):
            try:
                rows = future.result()
                if not valid():
                    return
                current = (gc("public_tracks_by_profile") or {}).get(profile_name, {}).get(lesson.track, {})
                if not current.get("enabled") or any(current.get(key) != saved.get(key) for key in
                                                     ("sources", "allow_dupes", "group_by_book", "start_day")):
                    return  # Settings changed while the archive was being read.
                selected = {}
                for entry in rows:
                    if entry["status"] == "exact":
                        selected.setdefault(entry["file"], {})[entry["index"]] = entry["digest"]
                if not selected:
                    showInfo(f"{lesson.label}: נישטא קיין שאלות מיט אן איינדייטיגער צוטיילונג. דער הספק איז נישט אנגעצייכנט אלס אימפארטירט.", parent=mw)
                    return
                mw.progress.start(label=f"אימפארטירט {lesson.label}…", immediate=True)
                try:
                    for name in repo_notetypes_names:
                        getOrCreateModels(collection, name)
                    unit = lesson.book if saved.get("group_by_book") else lesson.label
                    log = importFromFolder(
                        list(selected), _col=collection,
                        allow_dupes=CsvMetadata.DUPLICATE if saved.get("allow_dupes") else CsvMetadata.PRESERVE,
                        selected_rows=selected,
                        public_deck=f"מסלולי לימוד::{ACTIVE_TRACKS[lesson.track]}::{unit}",
                        strict_errors=True, progress_manager=mw.progress,
                    )
                    if not valid():
                        return
                    config = mw.addonManager.getConfig(__name__) or {}
                    current = config.setdefault("public_tracks_by_profile", {}).setdefault(profile_name, {}).setdefault(lesson.track, {})
                    # Retain holes when the learner chooses only some missed lessons.
                    current.setdefault("start_day", history_start(saved, _today_str()))
                    days = set(current.get("imported_days", []))
                    days.add(lesson.day)
                    current["imported_days"] = sorted(days)
                    current["last_imported"] = max(days)
                    mw.addonManager.writeConfig(__name__, config)
                finally:
                    mw.progress.finish()
                if log:
                    showText(log, type="html", parent=mw)
            except Exception as error:
                if valid():
                    from _shared_libs.haf_notifications import show_failure
                    show_failure(f"אימפארט {lesson.label} איז נישט פארענדיגט. קאנטראלירט דעם פעקל און דעם צושטאנד פונעם הספק איידער איר פרובירט נאכאמאל.", error)
            finally:
                if valid():
                    QTimer.singleShot(0, next_lesson)

        mw.taskman.run_in_background(lambda: plan_rows(archive_path(), files, lesson), done)

    next_lesson()


def _stop():
    global _run
    _run = None


gui_hooks.profile_will_close.append(_stop)
