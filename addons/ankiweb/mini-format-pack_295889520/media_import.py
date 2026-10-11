"""Enhance Anki's regular media picker with direct collection-media access."""

import base64
import binascii
import itertools
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, cast

from aqt.editor import Editor, audio, pics
from aqt.qt import (
    QApplication,
    QDialogButtonBox,
    QEvent,
    QFileDialog,
    QFileIconProvider,
    QIcon,
    QListView,
    QObject,
    QSize,
    QStandardPaths,
    QStyledItemDelegate,
    Qt,
    QTimer,
    QUrl,
    qconnect,
)
from aqt.utils import tr

_installed = False
_original_add_media = Editor._addMedia
_original_on_add_media = Editor.onAddMedia
_PROFILE_LAST_DIR_KEY = "mini_format_pack_last_media_picker_dir"
_PROFILE_PICKER_SIZE_KEY = "mini_format_pack_media_picker_size"
_THUMBNAIL_MIN_SIZE = 48
_THUMBNAIL_MAX_SIZE = 256
_THUMBNAIL_STEP = 16
_THUMBNAIL_DEFAULT_SIZE = 96


class _MediaThumbnailIconProvider(QFileIconProvider):
    """#375 — show the image itself instead of a generic file-type icon."""

    _IMAGE_SUFFIXES = {f".{ext.lower()}" for ext in pics}

    def __init__(self) -> None:
        super().__init__()

    def icon(self, info):
        if hasattr(info, "absoluteFilePath"):
            path = info.absoluteFilePath()
            if Path(path).suffix.lower() in self._IMAGE_SUFFIXES:
                thumbnail = QIcon(path)
                if not thumbnail.isNull():
                    return thumbnail
        return super().icon(info)


# #375 — QUrlModel של QFileDialog מסרב לעיתים ל-setData; delegate משנה את
# הטקסט המצויר בלבד ומשאיר את ה-URL והניווט המקוריים ללא שינוי.
class _HebrewSidebarDelegate(QStyledItemDelegate):
    _LABELS = {
        "Desktop": "דעסקטאפ",
        "Documents": "דאקומענטן",
        "Downloads": "אראפגעלאדענע טעקעס",
        "Pictures": "בילדער",
        "Music": "מוזיק",
        "Videos": "ווידעאס",
        "Movies": "ווידעאס",
        "Home": "באניצער טעקע",
    }

    def __init__(self, parent=None, path_labels=None):
        super().__init__(parent)
        self._path_labels = {
            self._normalize(path): label
            for path, label in (path_labels or {}).items()
            if path
        }

    @staticmethod
    def _normalize(value):
        if hasattr(value, "toLocalFile"):
            value = value.toLocalFile()
        return str(value).replace("\\", "/").rstrip("/").casefold()

    def _hebrew_label(self, value):
        if hasattr(value, "toLocalFile"):
            text = str(value.toLocalFile())
        else:
            text = str(value)
        normalized = self._normalize(text)
        if normalized in self._path_labels:
            return self._path_labels[normalized]
        if text in self._LABELS:
            return self._LABELS[text]
        # #375 — בחלק מגרסאות Qt ה-role מחזיר נתיב מלא ולא basename.
        return self._LABELS.get(normalized.rsplit("/", 1)[-1], text)

    def displayText(self, value, locale):
        return self._hebrew_label(value)

    def initStyleOption(self, option, index):
        # #375 — paint() מאתחל מחדש את ה-option, ולכן שינוי מוקדם של הטקסט
        # נדרס. התרגום מתבצע כאן, בשלב האחרון לפני הציור בפועל.
        super().initStyleOption(option, index)
        option.text = self._hebrew_label(index.data(Qt.ItemDataRole.DisplayRole))


class _ThumbnailZoomFilter(QObject):
    """Allow Ctrl+mouse-wheel to resize media thumbnails."""

    def __init__(self, view: QListView) -> None:
        super().__init__(view)
        self._view = view

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta:
                step = _THUMBNAIL_STEP if delta > 0 else -_THUMBNAIL_STEP
                current = self._view.iconSize().width() or _THUMBNAIL_DEFAULT_SIZE
                _apply_thumbnail_size(self._view, current + step)
                return True
        return super().eventFilter(watched, event)


def _apply_thumbnail_size(view: QListView, icon_edge: int) -> None:
    """Keep the picker in a vertical-scrolling thumbnail grid with captions below."""
    icon_edge = max(_THUMBNAIL_MIN_SIZE, min(_THUMBNAIL_MAX_SIZE, int(icon_edge)))
    view.setViewMode(QListView.ViewMode.IconMode)
    view.setFlow(QListView.Flow.LeftToRight)
    view.setWrapping(True)
    view.setResizeMode(QListView.ResizeMode.Adjust)
    view.setMovement(QListView.Movement.Static)
    view.setWordWrap(True)
    view.setUniformItemSizes(False)
    view.setSpacing(8)
    view.setIconSize(QSize(icon_edge, icon_edge))
    view.setGridSize(QSize(icon_edge + 32, icon_edge + 54))
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    view.setTextElideMode(Qt.TextElideMode.ElideMiddle)
    view.setStyleSheet(
        "QListView::item { padding: 4px; }"
    )


def _windows_quick_access_entries() -> list[tuple[str, str]]:
    """Return Explorer's current Quick Access folders in Explorer order."""
    if os.name != "nt":
        return []
    # #375 — קריאה בזמן פתיחת החלון מ-Shell.Application משקפת במדויק
    # תיקיות שהוצמדו או הוסרו מגישה מהירה ב-Windows.
    script = r"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$folder = $shell.Namespace('shell:::{679F85CB-0220-4080-B29B-5540CC05AAB6}')
$items = @()
if ($null -ne $folder) {
  foreach ($item in @($folder.Items())) {
    $path = [string]$item.Path
    if ($path -and [System.IO.Directory]::Exists($path)) {
      $items += [PSCustomObject]@{ name = [string]$item.Name; path = $path }
    }
  }
}
$json = $items | ConvertTo-Json -Compress
if (-not $json) { $json = '[]' }
# stdout של Windows PowerShell אינו UTF-8 באופן עקבי. מעבירים רק ASCII
# ומפענחים את ה-JSON מ-UTF-8 בצד Python כדי ששמות עבריים לא יהפכו ל-?.
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
"""
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            check=True,
            capture_output=True,
            timeout=4,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        encoded_payload = completed.stdout.decode("ascii").strip()
        json_payload = base64.b64decode(encoded_payload).decode("utf-8-sig")
        payload = json.loads(json_payload or "[]")
        if isinstance(payload, dict):
            payload = [payload]
        return [
            (str(item.get("name") or Path(item["path"]).name), str(item["path"]))
            for item in payload
            if isinstance(item, dict) and item.get("path")
        ]
    except (
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
        KeyError,
        binascii.Error,
    ):
        return []


def _fallback_sidebar_entries() -> list[tuple[str, str]]:
    # #375 — קיצורי ברירת המחדל מוצגים תמיד אחרי Quick Access, גם כאשר
    # Windows Shell זמין. "מחשב" מפנה לשורש הכונן של תיקיית המשתמש.
    return [
        ("קאמפיוטער", Path.home().anchor),
        ("באניצער טעקע", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)),
        ("דעסקטאפ", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)),
        ("דאקומענטן", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)),
        ("אראפגעלאדענע טעקעס", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)),
        ("בילדער", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)),
        ("מוזיק", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation)),
        ("ווידעאס", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)),
    ]


def _initial_picker_size(dialog: QFileDialog, editor: Editor) -> QSize:
    """Restore a user size, otherwise default to at least 3/4 screen height."""
    saved = editor.mw.pm.profile.get(_PROFILE_PICKER_SIZE_KEY)
    if (
        isinstance(saved, (list, tuple))
        and len(saved) == 2
        and all(isinstance(value, int) and value > 0 for value in saved)
    ):
        return QSize(saved[0], saved[1])

    # #375 — זו ברירת מחדל בלבד. לאחר שינוי גודל ידני נשמר הגודל של המשתמש.
    current = dialog.sizeHint().expandedTo(dialog.minimumSizeHint())
    current = current.expandedTo(dialog.size())
    screen = editor.widget.screen() or QApplication.primaryScreen()
    screen_height = screen.availableGeometry().height() if screen else 0
    target_height = max(current.height(), int(screen_height * 0.75))
    return QSize(current.width(), target_height)


def _add_media_without_duplicate(
    editor: Editor, path: str, canDelete: bool = False
) -> str:
    """Use collection.media files in place; import all other files normally."""
    source = Path(path).resolve()
    media_dir = Path(editor.mw.col.media.dir()).resolve()
    if source.is_file() and source.parent == media_dir:
        return editor.fnameToLink(source.name)
    return _original_add_media(editor, path, canDelete)


def _show_media_picker(editor: Editor) -> None:
    """Show Anki's media picker with a shortcut to this profile's media folder."""
    extension_filter = " ".join(
        f"*.{extension}" for extension in sorted(itertools.chain(pics, audio))
    )
    name_filter = f"{tr.editing_media()} ({extension_filter})"

    dialog = QFileDialog(editor.widget, tr.editing_add_media())
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setNameFilter(name_filter)
    # משאירים את QFileDialog במצב List, אבל מגדירים ידנית את QListView
    # של הקבצים ל-IconMode כדי לקבל תמונות ממוזערות עם כיתוב מתחתיהן.
    dialog.setViewMode(QFileDialog.ViewMode.List)
    dialog._media_thumbnail_provider = _MediaThumbnailIconProvider()
    dialog.setIconProvider(dialog._media_thumbnail_provider)

    # התיקייה האחרונה נשמרת בפרופיל הפעיל, ולא בגלובל זמני של התוסף.
    last_dir = str(editor.mw.pm.profile.get(_PROFILE_LAST_DIR_KEY, "") or "")
    if last_dir and Path(last_dir).is_dir():
        dialog.setDirectory(last_dir)

    # הדיאלוג הלא-מקורי נדרש לכפתור media. משחזרים בו את Quick Access
    # החי של Explorer ומוסיפים מעליו את תיקיית המדיה של הפרופיל.
    quick_access = _windows_quick_access_entries()
    sidebar_entries = [
        ("אנקי מידיא", editor.mw.col.media.dir()),
        *quick_access,
        *_fallback_sidebar_entries(),
    ]
    unique_entries = list(dict.fromkeys((label, path) for label, path in sidebar_entries if path))
    dialog.setSidebarUrls(
        [QUrl.fromLocalFile(path) for _label, path in unique_entries]
    )

    sidebar = dialog.findChild(QListView, "sidebar")
    if sidebar is None:
        # objectName אינו יציב בין גרסאות Qt; מחפשים את רשימת הצד לפי
        # מודל שיש בו לפחות את רשומות הגישה המהירה שהוספנו.
        for candidate in dialog.findChildren(QListView):
            model = candidate.model()
            if model is not None and model.rowCount() >= len(unique_entries):
                sidebar = candidate
                break

    if sidebar is not None:
        model = sidebar.model()
        for row, (label, _path) in enumerate(unique_entries):
            model.setData(model.index(row, 0), label, Qt.ItemDataRole.DisplayRole)

        sidebar._hebrew_delegate = _HebrewSidebarDelegate(
            sidebar,
            path_labels={path: label for label, path in unique_entries},
        )
        sidebar.setItemDelegate(sidebar._hebrew_delegate)
        sidebar.setIconSize(QSize(14, 14))
        sidebar.setSpacing(0)
        sidebar.setUniformItemSizes(True)
        sidebar.setStyleSheet(
            "QListView::item { min-height: 18px; padding: 0 2px; }"
        )

    for file_view in dialog.findChildren(QListView):
        if file_view is sidebar:
            continue
        _apply_thumbnail_size(file_view, _THUMBNAIL_DEFAULT_SIZE)
        file_view._thumbnail_zoom_filter = _ThumbnailZoomFilter(file_view)
        file_view.viewport().installEventFilter(file_view._thumbnail_zoom_filter)

    button_box = dialog.findChild(QDialogButtonBox)
    if button_box is None:
        # A defensive fallback for an unexpected Qt implementation.
        _original_on_add_media(editor)
        return

    media_button = button_box.addButton(
        "נוצן טעקעס וואס זענען שוין אין די שאלות",
        QDialogButtonBox.ButtonRole.ActionRole,
    )
    qconnect(
        media_button.clicked,
        lambda: dialog.setDirectory(editor.mw.col.media.dir()),
    )

    initial_size = _initial_picker_size(dialog, editor)
    dialog.resize(initial_size)

    def accept() -> None:
        if files := dialog.selectedFiles():
            # שמירה לפי פרופיל כדי שכל משתמש יחזור לתיקייה שלו.
            editor.mw.pm.profile[_PROFILE_LAST_DIR_KEY] = str(Path(files[0]).parent)
            editor.mw.pm.save()
            editor.resolve_media(files[0])

    def cleanup(*_args: Any) -> None:
        # גם ניווט שבוטל נשמר, כדי שהפתיחה הבאה תחזור לתיקייה האחרונה.
        current_dir = dialog.directory().absolutePath()
        if current_dir and Path(current_dir).is_dir():
            editor.mw.pm.profile[_PROFILE_LAST_DIR_KEY] = current_dir

        # ברירת המחדל מחושבת בכל פתיחה, עד שהמשתמש משנה את הגודל.
        # לאחר שינוי נשמרים הרוחב והגובה לפרופיל הפעיל.
        final_size = dialog.size()
        if final_size != initial_size:
            editor.mw.pm.profile[_PROFILE_PICKER_SIZE_KEY] = [
                final_size.width(),
                final_size.height(),
            ]
        editor.mw.pm.save()
        if getattr(editor, "_question_bank_media_dialog", None) is dialog:
            delattr(editor, "_question_bank_media_dialog")

    qconnect(dialog.accepted, accept)
    qconnect(dialog.finished, cast(Callable[[int], None], cleanup))
    editor._question_bank_media_dialog = dialog
    dialog.open()

    # QFileDialog עשוי להחיל sizeHint נוסף בזמן open; מחזירים את גודל הפתיחה
    # לאחר סיום האירוע, לפני שהמשתמש מספיק לשנות אותו.
    QTimer.singleShot(0, lambda: dialog.resize(initial_size))
    editor.parentWindow.activateWindow()


def install_media_import_enhancement() -> None:
    global _installed
    if _installed:
        return
    Editor.onAddMedia = _show_media_picker
    # קובץ שכבר נמצא בתיקיית המדיה מקושר במקום להיווצר ממנו עותק נוסף.
    Editor._addMedia = _add_media_without_duplicate
    _installed = True