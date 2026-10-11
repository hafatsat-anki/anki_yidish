import os
from pathlib import Path

import anki
from aqt import gui_hooks, mw
from aqt.editor import Editor, EditorWebView
from aqt.qt import QT_VERSION_STR, QMenu
from aqt.utils import tooltip

from .annotation import AnnotateDialog

ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
ICONS_PATH = os.path.join(os.path.dirname(__file__), "icons")
QT6 = QT_VERSION_STR.split(".")[0] == "6"

def open_annotate_window(editor, name="", path="", src="", create_new=False):
    mw.annodial = AnnotateDialog(
        editor, name=name, path=path, src=src, create_new=create_new)


def add_context_menu_action(wv: EditorWebView, m: QMenu):
    context_data = wv.lastContextMenuRequest() if QT6 else wv.page().contextMenuData()
    url = context_data.mediaUrl()
    image_name = url.fileName()
    # Using url.path() doesn't return the absolute path
    # Conpatibility: 2.1.0+
    image_path = Path(mw.col.media.dir()) / image_name
    if url.isValid() and image_path.is_file():
        a = m.addAction("רעדאקטירט א בילד")
        a.triggered.connect(lambda _, path=image_path, nm=image_name: open_annotate_window(
            wv.editor, name=nm, path=path, src=url.toString()))


def insert_js(web_content, context):
    if not isinstance(context, Editor):
        return
    web_content.js.append(f"/_addons/{ADDON_PACKAGE}/web/editor.js")


def setup_editor_buttons(btns, editor):
    hotkey = "Ctrl + Shift + I"
    icon = os.path.join(ICONS_PATH, "draw.svg")
    # Compatibility: 2.1.0+
    b = editor.addButton(icon, "Draw Image",
                         lambda o=editor: open_annotate_window(
                             o, create_new=True),
                         tip=f"מאלן ({hotkey})",
                         keys=hotkey, disables=True)

    btns.append(b)
    return btns


def on_editor_note_load(js: str, note: anki.notes.Note, editor: Editor):
    js += "\naddonAnno.addListener();"
    return js




mw.addonManager.setWebExports(__name__, r"web/editor.js")
mw.addonManager.setConfigAction(__name__, lambda: True)
gui_hooks.editor_will_show_context_menu.append(add_context_menu_action)
gui_hooks.editor_did_init_buttons.append(setup_editor_buttons)
gui_hooks.webview_will_set_content.append(insert_js)
gui_hooks.editor_will_load_note.append(on_editor_note_load)  # 2.1.24+
