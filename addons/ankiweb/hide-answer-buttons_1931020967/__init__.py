# 2021 - Matthias Metelka @kleinerpirat

import json
from typing import Any

from aqt import mw
from aqt.editor import Editor
from aqt.gui_hooks import editor_did_load_note, webview_will_set_content
from aqt.webview import WebContent

mw.addonManager.setWebExports(__name__, r"(user_files)/.*\.(css|js)|(web)/.*\.(js)")
config = mw.addonManager.getConfig(__name__)

def append_webcontent(webcontent : WebContent, context : Any):
    if isinstance(context, Editor):
        addon_package = context.mw.addonManager.addonFromModule(__name__)
        base_path = f"/_addons/{addon_package}"

        webcontent.js.append(f"{base_path}/web/hide.js")


def run_hide_stuff(editor: Editor, *args):
    # #379 — eval מתוך editor_did_init_buttons רץ לפני שה-WebView מוכן
    # ועלול לחסום את הופעת העורך. הסקריפט כבר צורף ל-WebContent, ולכן
    # מפעילים את ההגדרות וההסתרה רק אחרי טעינת הפתק הראשונה.
    editor.web.eval(
        f"Hider.hide({json.dumps(config)});"
        "Hider.hide_buttons();"
    )

webview_will_set_content.append(append_webcontent)
editor_did_load_note.append(run_hide_stuff)
