import os
import weakref

from aqt import gui_hooks, mw
from aqt.qt import QKeySequence, QShortcut
from aqt.theme import theme_manager
from aqt.utils import tooltip
from bs4 import BeautifulSoup

from .config import gc
from .dialog import ExtraWysiwygEditorForField
from .helpers import (
    addon_path,
    addonfoldername,
    hiliters_tinymce,
    maybe_pre_process_html,
    readfile,
    user_files_folder,
)

if os.path.isfile(os.path.join(user_files_folder, "additional_editors.py")):
    from .user_files.additional_editors import additional_editors_dict
else:
    additional_editors_dict = {}


if os.path.isfile(os.path.join(user_files_folder, "additional_buttons_menuentries.py")):
    from .user_files.additional_buttons_menuentries import get_additional_arglist
else:
    def get_additional_arglist():
        return []


mw.addonManager.setWebExports(__name__, r"((user_files[/\\])?web[/\\].*)")


def internal_images_to_file(editor, html):
    if "data:image/" in html:
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all("img", src=lambda src: src.startswith("data:image/")):
            try:
                src = img["src"]
            except KeyError:
                continue
            else:
                img['src'] = editor.inlinedImageToFilename(src)
        html = str(soup)
    return html


def download_external_images(editor, html):
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        try:
            src = img["src"]
        except KeyError:
            continue
        else:
            if editor.isURL(src):
                fname = editor._retrieveURL(src)
                if fname:
                    img["src"] = fname
    html = str(soup)
    return html


def editor_update_field(editor):
    if not hasattr(editor, "edited_field_content") or not isinstance(
        editor.edited_field_content, str
    ):
        tooltip("אן אומבאקאנטע טעות אין דעם צוגאב. די פעולה איז אפגעזאגט...")
        return

    html = editor.edited_field_content
    # pasting images into TinyMCE6 creates inline images which in turn slow down Anki
    # see e.g. https://forums.ankiweb.net/t/anki-browse-extremely-laggy/32533/8
    if gc("use Anki's built-in html processing"):
        # the following should convert inline images, save external images and remove some
        # problematic tags and it should work in 2.1.22 and 2.1.65.
        html = editor._pastePreFilter(html=html, internal=False)
    else:
        html = internal_images_to_file(editor, html)
        html = download_external_images(editor, html)

    editor.note.fields[editor.myfield] = html
    editor.edited_field_content = ""
    if not editor.addMode:
        # #254 — Anki 24+ שומר רשומות דרך collection.update_note במקום note.flush הישן.
        mw.col.update_note(editor.note)
    editor.loadNote(focusTo=editor.myfield)


def on_dialog_finished(editor, status):
    if status:
        editor.saveNow(lambda e=editor: editor_update_field(e))


def get_settings(chosen_name):
    if chosen_name in ["T6", "TM"]:
        defau1 = ("undo redo fontfamily blocks alignleft aligncenter alignright alignjustify "
                  "link unlink charmap cleanup nextCloze sameCloze code codesample")
        tb1 = gc("TinyMCE6-toolbar1", defau1)
        defau2 = ("bold italic underline strikethrough superscript subscript forecolor backcolor "
                  "removeformat hr blockquote numlist bullist anchor outdent indent table ltr rtl")
        tb2 = gc("TinyMCE6-toolbar2", defau2)
        return {
            "js_file": "tinymce6/js/tinymce/tinymce.min.js",
            "jssavecmd": "tinyMCE.activeEditor.getContent();",
            "wintitle": "אנקי - רעדאקטירן דאס יעצטיגע פעלד אינעם פארגעשריטענעם רעדאקטאר",
            "dialogname": "tinymce6",
            "webpath": f"/_addons/{addonfoldername}/web/",
            "body_except_for_field_content": readfile(
                addon_path, "template_tiny6_body.html"
            )
            % {
                "FONTSIZE": gc("fontSize"),
                "FONTNAME": gc("font"),
                #  https://www.tiny.cloud/blog/dark-mode-tinymce-rich-text-editor/
                # #279 — רקע לבן במצב יום במקום אפור, כדי שתיבת הטקסט תיראה נקייה
                "CUSTOMBGCOLOR": ""
                        if theme_manager.night_mode
                        else "this.getDoc().body.style.backgroundColor = '#ffffff';",
                # https://www.tiny.cloud/blog/dark-mode-tinymce-rich-text-editor/
                "CONTENTCSS": '"dark",' if theme_manager.night_mode else "",
                # #279 — כיוון RTL קבוע; config ישן ב-meta.json דורס את config.json ולכן לא מסתמכים על gc
                "DIRECTIONALITY": "rtl",
                # #279 — נתיב מוחלט דרך שרת התוספים של Anki מונע טעינת תרגום TinyMCE מהמיקום הלא נכון ב-WebView.
                "LANGURL": f"/_addons/{addonfoldername}/web/tinymce6/js/tinymce/langs/yi.js",
                "SKIN": "oxide-dark" if theme_manager.night_mode else "oxide",
                "THEME": "silver",
                "TOOLBAR1": tb1,
                "TOOLBAR2": tb2,
                "HILITERS": hiliters_tinymce
                        if gc("show background color buttons")
                        else "",
                "SCUT-Superscript": gc("dialog shortcut: superscript", "Ctrl+107"),
                "SCUT-Subscript": gc("dialog shortcut: subscript", "Ctrl+187"),
                "SCUT-RemoveFormat": gc("dialog shortcut: removeFormat", "Ctrl+r"),
                "SCUT-CodeEditor": gc("dialog shortcut: codeEditor", "Ctrl+Shift+X"),
                "SCUT-indent": gc("dialog shortcut: indent", "Ctrl+M"),
                "SCUT-outdent": gc("dialog shortcut: outdent", "Ctrl+Alt+M"),
                "SCUT-nextCloze": gc("dialog shortcut: nextCloze", "F7"),
                "SCUT-addCloze": gc("dialog shortcut: addCloze", "F8"),
                "SCUT-InsertUnorderedList": gc("dialog shortcut: insertUnorderedList", "F9"),
                "SCUT-InsertOrderedList": gc("dialog shortcut: insertOrderedList", "F10"),
                "SCUT-upperCase": gc("dialog shortcut: upperCase", "Ctrl+Alt+U"),
                "SCUT-lowerCase": gc("dialog shortcut: lowerCase", "Ctrl+Alt+L"),
                "SCUT-SpecialCharacter": gc("dialog shortcut: special character", "Ctrl+E"),
            },
        }
    for js_editor_name, settings_dict in additional_editors_dict.items():
        if chosen_name == js_editor_name:
            return settings_dict


def show_wysiwyg_dialog(editor, field, editorname):
    field_content = editor.note.fields[field]

    content_surrounded_with_div = False
    if field_content.startswith("<div>") and field_content.endswith("</div>"):
        content_surrounded_with_div = True

    settings = get_settings(editorname)
    html = maybe_pre_process_html(field_content)
    bodyhtml = settings["body_except_for_field_content"].replace("CONTENTCONTENT", html)
    dialog = ExtraWysiwygEditorForField(
        editor=editor,
        bodyhtml=bodyhtml,
        js_file=settings["js_file"],
        js_save_command=settings["jssavecmd"],
        wintitle=settings["wintitle"],
        dialogname=settings["dialogname"],
        content_surrounded_with_div=content_surrounded_with_div,
        web_path=settings["webpath"],
    )
    # exec_() doesn't work, see  https://stackoverflow.com/questions/39638749/
    dialog.finished.connect(
        lambda status, func=on_dialog_finished, e=editor: func(e, status)
    )
    dialog.setModal(True)
    dialog.show()
    dialog.web.setFocus()


def external_editor_start(editor, editorname):
    if editor.currentField is None:
        tooltip("קיין פעלד איז נישט אויסגעקליבן. די פעולה איז אפגעזאגט.")
        return
    editor.myfield = editor.currentField
    editor.saveNow(
        lambda e=editor, f=editor.myfield, n=editorname: show_wysiwyg_dialog(e, f, n)
    )


def keystr(k):
    key = QKeySequence(k)
    return key.toString(QKeySequence.SequenceFormat.NativeText)


_shortcut_editors = weakref.WeakSet()


def _reload_config():
    for editor in list(_shortcut_editors):
        try:
            config = mw.addonManager.getConfig("shortcut-manager") or {}
            key = config.get("external_editor_open_advanced", gc("shortcut to open default dialog"))
            editor._external_default_shortcut.setKey(QKeySequence(key or ""))
        except RuntimeError:
            _shortcut_editors.discard(editor)


def setupEditorButtonsFilter(buttons, editor):
    _shortcut_editors.add(editor)
    cut_T6 = gc("TinyMCE6 - shortcut to open dialog")
    tip_T6 = "רעדאקטירט דאס יעצטיגע פעלד אינעם פארגעשריטענעם רעדאקטאר"
    if cut_T6:
        tip_T6 += f" ({keystr(cut_T6)})"

    use_default = True if not gc("_TinyMCE6 - enable") else False
    # #359 — קונפליקט: shortcut-manager קושר Ctrl+0 ל"הגדר דגל 0" בברירת המחדל, מה שגרם
    # לקיצור פתיחת העורך המתקדם (גם Ctrl+0 כברירת מחדל) לא לפעול בעת עריכה בתוך מבחן.
    # מעדיפים כעת ערך מ-shortcut-manager (ניתן להגדרה שם) עם נפילה חזרה לקונפיג המקומי.
    cut_default = None
    try:
        sm_config = mw.addonManager.getConfig("shortcut-manager") or {}
        cut_default = sm_config.get("external_editor_open_advanced")
    except Exception:
        cut_default = None
    if cut_default is None:
        cut_default = gc("shortcut to open default dialog")
    tip_default = f"רעדאקטירט דאס יעצטיגע פעלד אינעם פארגעשריטענעם רעדאקטאר ({keystr(cut_default)})"

    arglist = [
        #  0                        1           2             3          4       5
        # show                    shortcut     tooltip     functionarg  cmd   icon
        [gc("_TinyMCE6 - enable"), cut_T6,      tip_T6,     "T6",       "T6", None],
        # #254 — הכפתור המובנה מציג שם ברור למשתמש במקום הכותרת הטכנית TM.
        [use_default,             cut_default, tip_default, "TM",       "פארגעשריטענער רעדאקטאר", None],
    ]
    additional_arglist = get_additional_arglist()
    arglist.extend(additional_arglist)
    for line in arglist:
        if not line[0]:
            continue
        b = editor.addButton(
            icon=line[5],  # os.path.join(addon_path, "icons", "tm.png"),
            cmd=line[4],
            func=lambda e=editor, n=line[3]: external_editor_start(e, n),
            tip=line[2],
            # #359 — keystr() ממיר ל-NativeText (לתצוגה בלבד, כמו ב-tip_default למעלה).
            # editor.addButton בונה מ-keys ישירות QShortcut(QKeySequence(keys), ...),
            # שמצפה למחרוזת פורטבילית ("Ctrl+Shift+["), לא לטקסט NativeText מקומי.
            # בלוקאל עברי הסבב הכפול (config -> QKeySequence -> NativeText -> QKeySequence
            # מחדש בתוך addButton) הפיק לעיתים רצף לא תקין ש-Qt נכשל לפרסר בשקט —
            # QShortcut נרשם אך עם מקש ריק/לא פעיל. מעבירים את המחרוזת הגולמית ישירות.
            keys="" if line[3] == "TM" else (line[1] or ""),
        )
        if line[3] == "TM":
            old = getattr(editor, "_external_default_shortcut", None)
            if old is not None:
                old.setEnabled(False)
                old.deleteLater()
            editor._external_default_shortcut = QShortcut(
                QKeySequence(cut_default or ""), editor.widget,
                activated=lambda e=editor: external_editor_start(e, "TM"),
            )
        # #368 — the hook can run again for the same toolbar. Still rebuild
        # callbacks/shortcuts above, but emit each button only once.
        if b not in buttons:
            buttons.append(b)

    return buttons
gui_hooks.editor_did_init_buttons.append(setupEditorButtonsFilter)
