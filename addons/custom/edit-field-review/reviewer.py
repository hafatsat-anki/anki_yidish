import base64
import contextlib
import json
from typing import Any

import anki
import aqt

# from anki.buildinfo import version as ankiversion
from anki.cards import Card
from anki.notes import Note
from anki.template import TemplateRenderContext
from aqt.reviewer import ReviewerBottomBar
from aqt.utils import showText, tooltip

from .ankiaddonconfig import ConfigManager
from .editbar import *
from .semieditor import semiEditorWebView
from .shortcut_guard import InlineEditingShortcutGuard

ERROR_MSG = "ERROR - Edit Field During Review Cloze\n{}"

editorwv = semiEditorWebView()
_shortcut_guard = InlineEditingShortcutGuard(mw, lambda: conf.to_json())
mw.app.installEventFilter(_shortcut_guard)
gui_hooks.reviewer_did_show_question.append(_shortcut_guard.reset)
gui_hooks.state_did_change.append(_shortcut_guard.reset)


class FldNotFoundError(Exception):
    def __init__(self, fld: str):
        self.fld = fld

    def __str__(self) -> str:
        return f"Field {self.fld} not found in note. Please check your note type."


conf = ConfigManager()

def myRevHtml() -> str:
    conf.load()  # update config when reviewer is launched

    # config should not have any single quote values
    js = f"EFDRC.registerConfig({json.dumps(conf.to_json())});"
    js += "EFDRC.setupReviewer()"
    return f"<script>{js}</script>"


def _reload_config() -> None:
    # #138 — shortcut-manager יכול לעדכן קיצורי JS בחלון מבחן פתוח בלי להפעיל את Anki מחדש.
    conf.load()
    reviewer = getattr(mw, "reviewer", None)
    web = getattr(reviewer, "web", None)
    if web:
        web.eval(f"if (window.EFDRC) {{ EFDRC.registerConfig({json.dumps(conf.to_json())}); EFDRC.setupReviewer(); }}")


def edit_filter(txt: str, field: str, filt: str, ctx: TemplateRenderContext) -> str:
    if filt != "edit":
        return txt
    # Encode field to escape special characters.
    class_name = ""
    if conf["outline"]:
        class_name += "EFDRC-outline "
    if conf["ctrl_click"]:
        class_name += "EFDRC-ctrl "
    field = base64.b64encode(field.encode("utf-8")).decode("ascii")
    txt = """<{} data-EFDRCfield="{}" class="{}">{}</{}>""".format(
        conf["tag"],
        field,
        class_name,
        txt,
        conf["tag"],
    )
    return txt


def serve_card(txt: str, card: Card, kind: str) -> str:
    return txt + "<script>EFDRC.serveCard()</script>"


# #178 — saveField מקבל מצב autosave שבו אין הסתרת toolbar ואין רענון כפוי של Reviewer.
def saveField(note: Note, fld: str, val: str, hide_toolbar: bool = True) -> None:
    # #178 — autosave שומר בלי לסגור את סרגל העריכה; שמירה סופית עדיין מסתירה אותו כבעבר.
    if hide_toolbar:
        # #178 — בזמן סגירת חלון/פרופיל ייתכן שה-toolbar כבר לא קיים; אסור שזה יפיל את השמירה עצמה.
        with contextlib.suppress(Exception):
            mw.reviewer.more_toolbar.hide()
    if fld == "Tags":
        # aqt.editor.Editor.saveTags
        tags = mw.col.tags.split(val)
        if note.tags == tags:
            return
        note.tags = tags
    elif fld not in note:
        raise FldNotFoundError(fld)
    else:
        # aqt.editor.Editor.onBridgeCmd
        txt = Editor.mungeHTML(editorwv.editor, val)
        if note[fld] == txt:
            return
        note[fld] = txt
    mw.col.update_note(note)


def _note_for_autosave(reviewer: Reviewer, nid: int) -> Note:
    # #178 — autosave שומר לפי nid גם אם המשתמש כבר עבר לכרטיס הבא לפני שה-debounce הסתיים.
    with contextlib.suppress(Exception):
        current_note = reviewer.card.note()
        if current_note.id == nid:
            return current_note
    # #178 — אם ה-Reviewer כבר לא מחזיק כרטיס פעיל, עדיין טוענים את הרשומה ישירות מהאוסף.
    return mw.col.get_note(nid)


def _reload_reviewer_if_current(reviewer: Reviewer, nid: int) -> None:
    # #178 — שמירה מאוחרת של כרטיס קודם לא צריכה לרענן כרטיס אחר שכבר מוצג למשתמש.
    with contextlib.suppress(Exception):
        if reviewer.card.note().id == nid:
            reload_reviewer(reviewer)


def get_value(note: Note, fld: str) -> str:
    if fld == "Tags":
        return note.string_tags().strip(" ")
    if fld in note:
        return note[fld]
    raise FldNotFoundError(fld)


def reload_reviewer(reviewer: Reviewer) -> None:
    cid = reviewer.card.id
    timer_started = reviewer.card.timer_started
    reviewer.card = mw.col.get_card(cid)
    reviewer.card.timer_started = timer_started
    if reviewer.state == "question":
        reviewer._showQuestion()
    elif reviewer.state == "answer":
        reviewer._showAnswer()


def handle_pycmd_message(
        handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    if not isinstance(context, Reviewer):
        return handled
    reviewer: Reviewer = context
    if message.startswith("EFDRC!preset#"):
        from .editbar import _apply_style_preset_in_review
        name = message.split("#", 1)[1]
        if name in {f"preset_{i}" for i in range(1, 6)}:
            _apply_style_preset_in_review(reviewer, int(name[-1]) - 1)
        return (True, None)
    if message.startswith("EFDRC!savefinal64#"):
        # #178 — שמירה סופית מקודדת base64 ונשמרת לפי nid גם אם blur/pagehide הגיעו אחרי מעבר חלון או כרטיס.
        errmsg = "Something unexpected occured. The edit may not have been saved."
        nidstr, fld, encoded_val = message.replace("EFDRC!savefinal64#", "").split("#", 2)
        nid = int(nidstr)
        try:
            note = _note_for_autosave(reviewer, nid)
        except Exception:
            tooltip(ERROR_MSG.format(errmsg))
            return (True, None)
        fld = base64.b64decode(fld, validate=True).decode("utf-8")
        new_val = base64.b64decode(encoded_val, validate=True).decode("utf-8")
        try:
            saveField(note, fld, new_val)
            _reload_reviewer_if_current(reviewer, nid)
            return (True, None)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return (True, None)

    if message.startswith("EFDRC!save64#"):
        # #178 — autosave מקבל HTML מקודד base64 כדי לשמור גם תוכן שמכיל #/שורות/עברית בלי לשבור parsing.
        errmsg = "Something unexpected occured. The edit may not have been saved."
        nidstr, fld, encoded_val = message.replace("EFDRC!save64#", "").split("#", 2)
        nid = int(nidstr)
        try:
            # #178 — מעבר כרטיס מהיר לא מבטל autosave שכבר נשלח מהכרטיס הקודם.
            note = _note_for_autosave(reviewer, nid)
        except Exception:
            tooltip(ERROR_MSG.format(errmsg))
            return (True, None)
        fld = base64.b64decode(fld, validate=True).decode("utf-8")
        new_val = base64.b64decode(encoded_val, validate=True).decode("utf-8")
        try:
            saveField(note, fld, new_val, hide_toolbar=False)
            return (True, None)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return (True, None)

    if message.startswith("EFDRC!save#"):
        # #178 — תאימות לאחור להודעות autosave ישנות אם כרטיס נטען לפני עדכון ה-JS.
        errmsg = "Something unexpected occured. The edit may not have been saved."
        nidstr, fld, new_val = message.replace("EFDRC!save#", "").split("#", 2)
        nid = int(nidstr)
        try:
            # #178 — תאימות לאחור עדיין שומרת לפי nid ולא רק לפי הכרטיס הפעיל כרגע.
            note = _note_for_autosave(reviewer, nid)
        except Exception:
            tooltip(ERROR_MSG.format(errmsg))
            return (True, None)
        fld = base64.b64decode(fld, validate=True).decode("utf-8")
        try:
            saveField(note, fld, new_val, hide_toolbar=False)
            return (True, None)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return (True, None)

    if message.startswith("EFDRC#"):
        # #178 — תאימות לאחור: גם מסלול שמירה סופית ישן שומר לפי nid ולא נזרק אם הכרטיס הפעיל כבר השתנה.
        errmsg = "Something unexpected occured. The edit may not have been saved."
        nidstr, fld, new_val = message.replace("EFDRC#", "").split("#", 2)
        nid = int(nidstr)
        try:
            note = _note_for_autosave(reviewer, nid)
        except Exception:
            tooltip(ERROR_MSG.format(errmsg))
            return (True, None)
        fld = base64.b64decode(fld, validate=True).decode("utf-8")
        try:
            saveField(note, fld, new_val)
            _reload_reviewer_if_current(reviewer, nid)
            return (True, None)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return (True, None)

    # Replace reviewer field html if it is different from real field value.
    # For example, clozes, mathjax, audio.
    elif message.startswith("EFDRC!focuson#"):
        _shortcut_guard.editing = True
        mw.reviewer.more_toolbar.show()

        fld = message.replace("EFDRC!focuson#", "")
        decoded_fld = base64.b64decode(fld, validate=True).decode("utf-8")
        note = reviewer.card.note()
        try:
            val = get_value(note, decoded_fld)
        except FldNotFoundError as e:
            tooltip(ERROR_MSG.format(str(e)))
            return (True, None)
        encoded_val = base64.b64encode(val.encode("utf-8")).decode("ascii")
        reviewer.web.eval(f"EFDRC.showRawField('{encoded_val}', '{note.id}', '{fld}')")

        # Reset timer from Speed Focus Mode add-on.
        reviewer.bottom.web.eval("window.EFDRCResetTimer()")
        return (True, None)

    elif message == "EFDRC!reload":
        _shortcut_guard.reset()
        reload_reviewer(reviewer)
        return (True, None)
        # Catch ctrl key presses from bottom.web.
    elif message == "EFDRC!ctrldown":
        reviewer.web.eval("EFDRC.ctrldown()")
        return (True, None)
    elif message == "EFDRC!ctrlup":
        reviewer.web.eval("EFDRC.ctrlup()")
        return (True, None)

    elif message == "EFDRC!paste":
        # From aqt.editor.Editor._onPaste, doPaste.
        mime = mw.app.clipboard().mimeData(mode=QClipboard.Mode.Clipboard)
        html, internal = editorwv._processMime(mime)
        #print(internal)
        html = editorwv.editor._pastePreFilter(html, internal)
        #print(html)
        reviewer.web.eval(
            f"EFDRC.pasteHTML({json.dumps(html)}, {json.dumps(internal)}, true);"
        )
        return (True, None)

    elif message.startswith("EFDRC!debug#"):
        fld = message.replace("EFDRC!debug#", "")
        from _shared_libs.haf_logging import get_logger
        get_logger("edit_field_review").debug("Editor diagnostic: %s", fld)
        return (True, None)
    return handled


def url_from_fname(file_name: str) -> str:
    addon_package = mw.addonManager.addonFromModule(__name__)
    return f"/_addons/{addon_package}/web/{file_name}"


def on_webview(web_content: aqt.webview.WebContent, context: Any | None) -> None:
    if isinstance(context, Reviewer):
        # #161 — load the shared implementation before global_card/editorfontsize.
        from _shared_libs.haf_rtl import inject_rtl_editing
        inject_rtl_editing(web_content)
        web_content.body += myRevHtml()
        web_content.body += f'<script type="module" src="{url_from_fname("editor/editor.js")}"></script>'
        js_contents = ["global_card.js", "resize.js","editorfontsize.js"]
        for file_name in js_contents:
            web_content.js.append(url_from_fname(file_name))
        jquery_ui = "js/vendor/jquery-ui.min.js"
        if jquery_ui not in web_content.js:
            web_content.js.append(jquery_ui)
        web_content.css.append(url_from_fname("global_card.css"))

    elif isinstance(context, ReviewerBottomBar):
        web_content.js.append(url_from_fname("bottom.js"))

    else:
        with contextlib.suppress(AttributeError):
            mw.reviewer.more_toolbar.hide()

mw.addonManager.setWebExports(__name__, r"web/.*")
gui_hooks.webview_will_set_content.append(on_webview)
gui_hooks.webview_did_receive_js_message.append(handle_pycmd_message)
gui_hooks.card_will_show.append(serve_card)
anki.hooks.field_filter.append(edit_filter)
