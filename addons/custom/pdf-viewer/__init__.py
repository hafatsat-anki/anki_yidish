"""
PDF Viewer
עפנט PDF אין א באזונדערן פענסטער פונעם חזרה און רעדאקטירער.

חזרה: מוסטער ___שם_קובץ____עמוד מוחלפת בלחצן. לחיצה פותחת חלון PDF.
רעדאקטירער: קנעפל PDF אינעם סרגל → אויסקלייבן א טעקע → פענסטער PDF עפנט זיך און דער סינטאקס ווערט אריינגעלייגט אינעם פעלד.
"""
import base64
import json
import os
import re
from pathlib import Path
from typing import Any
from weakref import WeakKeyDictionary

from aqt import gui_hooks, mw
from aqt.qt import (
    QDialog,
    QFileDialog,
    QInputDialog,
    QKeySequence,
    QShortcut,
    Qt,
    QUrl,
    QVBoxLayout,
)
from aqt.utils import tooltip
from _shared_libs.haf_notifications import show_failure

try:
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False


# #346 — פתיחת קובץ במפעיל ברירת המחדל של המערכת, בכל שלוש הפלטפורמות.
# os.startfile קיים בווינדוס בלבד ואינו מוגדר כלל במק ובלינוקס.
def _open_with_system_viewer(path: str) -> None:
    import subprocess
    import sys

    if os.name == "nt":
        os.startfile(path)  # noqa: S606 — ווינדוס בלבד
    elif sys.platform == "darwin":
        subprocess.call(("open", path))
    else:
        subprocess.call(("xdg-open", path))


# ── Config ─────────────────────────────────────────────────────────────────────

def _get_config() -> dict:
    return mw.addonManager.getConfig(__name__) or {}


# #187 — shortcut-manager שומר את קיצור כפתור PDF בקונפיג של התוסף, והעורך קורא אותו בכל פתיחה/רענון.
def _editor_shortcut() -> str:
    return str(_get_config().get("editor_shortcut") or "Ctrl+Shift+P")


def _qt_shortcut_text(shortcut: str) -> str:
    return "+".join(part.strip() for part in str(shortcut).split("+") if part.strip())


def _pdf_folder() -> str:
    folder = _get_config().get("pdf_folder", "")
    if not folder:
        folder = str(Path.home() / "Documents" / "Ankifiles")
    return folder


def _resolve_path(filename: str) -> str:
    """Return absolute path: keep absolute paths as-is, resolve relative to pdf_folder."""
    if os.path.isabs(filename):
        return filename
    return os.path.join(_pdf_folder(), filename)


# ── PDF window ─────────────────────────────────────────────────────────────────

_open_dialogs: list = []  # keep references to prevent garbage collection


def _open_pdf_window(path: str, page: int = 1, parent=None) -> None:
    """Open the PDF in a non-modal Qt window."""
    if not os.path.isfile(path):
        tooltip(f"די טעקע איז נישט געפונען געווארן:\n{path}")
        return

    if not _HAS_WEBENGINE:
        # #346 — os.startfile קיים בווינדוס בלבד; במק ובלינוקס יש לפתוח את
        # הקובץ בעזרת המפעיל של המערכת, אחרת נזרקת AttributeError
        _open_with_system_viewer(path)
        return

    dlg = QDialog(parent or mw)
    dlg.setWindowTitle(os.path.basename(path))
    dlg.resize(960, 760)
    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(0, 0, 0, 0)

    view = QWebEngineView()
    # חיוני: בלי שני הדגלים האלה הדפדפן לא מציג PDF
    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

    url = QUrl.fromLocalFile(path)
    url.setFragment(f"page={page}")
    view.load(url)
    layout.addWidget(view)

    _open_dialogs.append(dlg)
    dlg.finished.connect(
        lambda: _open_dialogs.remove(dlg) if dlg in _open_dialogs else None
    )
    dlg.show()


# ── Reviewer ───────────────────────────────────────────────────────────────────

_PAT = re.compile(r"___(.+?)____(\d*)", re.UNICODE)
_PYCMD = "pdf_open:"


def _reviewer_card_will_show(text: str, card, kind: str) -> str:
    """Replace ___filename____N with a clickable button."""
    def _replace(m: re.Match) -> str:
        filename = m.group(1).strip()
        page = int(m.group(2) or "1")
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        full_path = _resolve_path(filename)
        payload = base64.b64encode(
            json.dumps({"path": full_path, "page": page}).encode()
        ).decode()
        label = f"📄 {os.path.basename(filename)} — בלאט {page}"
        # #issue — כשהכפתור נמצא בתוך שדה שedit-field-review הופך ל-contenteditable,
        # הדפדפן מבטל את ה-onclick. contenteditable="false" מוציא את הכפתור מהאזור הנערך.
        return (
            f'<button onclick="pycmd(\'{_PYCMD}{payload}\')" '
            f'contenteditable="false" '
            f'style="padding:8px 18px;cursor:pointer;font-size:14px;'
            f'border-radius:5px;background:#4a90d9;color:#fff;border:none;'
            f'margin:6px 0;display:inline-block;">{label}</button>'
        )
    return _PAT.sub(_replace, text)


def _on_pycmd(
    handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    if not message.startswith(_PYCMD):
        return handled
    try:
        data = json.loads(base64.b64decode(message[len(_PYCMD):]))
        _open_pdf_window(data["path"], int(data.get("page", 1)))
    except Exception as exc:
        show_failure("די טעקעPDF האט זיך נישט געעפנט. קוקט צי זי איז פאראן און מען קען זי עפענען, און פרובירט נאכאמאל.", exc)
    return (True, None)


gui_hooks.card_will_show.append(_reviewer_card_will_show)
gui_hooks.webview_did_receive_js_message.append(_on_pycmd)


# ── Editor button ──────────────────────────────────────────────────────────────

# #187 — שומרים את קיצורי PDF לפי מופע Editor כדי לרענן קיצור בלי להפעיל מחדש את Anki.
_pdf_editor_shortcuts = WeakKeyDictionary()


# #187 — שומרים QShortcut עצמאי כדי שאפשר יהיה לשנות את קיצור PDF בלי לפתוח מחדש את חלון העורך.
def _set_pdf_editor_shortcut(editor, shortcut: str, handler) -> None:
    key_sequence = QKeySequence(_qt_shortcut_text(shortcut))
    shortcut_obj = _pdf_editor_shortcuts.get(editor)
    if shortcut_obj is None:
        shortcut_obj = QShortcut(key_sequence, editor.widget)
        shortcut_obj.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut_obj.activated.connect(handler)
        _pdf_editor_shortcuts[editor] = shortcut_obj
    else:
        shortcut_obj.setKey(key_sequence)


def _reload_config() -> None:
    # #187 — לאחר Apply ב-shortcut-manager מעדכנים עורכים פתוחים ואת tooltip של כפתור PDF.
    shortcut = _editor_shortcut()
    dead = []
    for editor in list(_pdf_editor_shortcuts.keys()):
        try:
            _set_pdf_editor_shortcut(editor, shortcut, lambda editor=editor: None)
            if editor.web:
                tip = f"עפנט/לייגט אריין א טעקע PDF ({shortcut})"
                editor.web.eval(
                    "var btn=document.getElementById('InsertPdf');"
                    f"if(btn) btn.title={json.dumps(tip)};"
                )
        except RuntimeError:
            dead.append(editor)
    for editor in dead:
        try:
            del _pdf_editor_shortcuts[editor]
        except Exception:
            pass


def _add_pdf_button(buttons: list, editor) -> list:
    def _on_click(editor=editor) -> None:
        path, _ = QFileDialog.getOpenFileName(
            editor.parentWindow, "קלייבט אויס א טעקע PDF", str(Path.home()), "PDF files (*.pdf)"
        )
        if not path:
            return

        page, ok = QInputDialog.getInt(
            editor.parentWindow, "בלאט", "וועלכן בלאט צו ווייזן?", 1, 1, 9999, 1
        )
        if not ok:
            page = 1

        _open_pdf_window(path, page, parent=editor.parentWindow)

        text = f"___{path}____{page}"
        editor.web.eval(
            f"document.execCommand('insertText', false, {json.dumps(text)});"
        )

    shortcut = _editor_shortcut()
    btn = editor.addButton(
        None,
        "InsertPdf",
        _on_click,
        tip=f"עפנט/לייגט אריין א טעקע PDF ({shortcut})",
        label="PDF",
        keys=None,
    )
    # #187 — הקיצור נוצר ידנית כדי ש-shortcut-manager יוכל לרענן אותו בזמן אמת.
    _set_pdf_editor_shortcut(editor, shortcut, _on_click)
    buttons.append(btn)
    return buttons


gui_hooks.editor_did_init_buttons.append(_add_pdf_button)
