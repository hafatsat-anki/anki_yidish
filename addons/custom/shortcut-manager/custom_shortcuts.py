# Last updated to be useful for: Anki 2.1.45
import os
import warnings
import weakref

from anki.hooks import wrap
from aqt import dialogs as aqt_dialogs
from aqt import gui_hooks, mw
from aqt.qt import *

try:
    from aqt.utils import (
        showWarning,
        tr,
    )

    tr_import = True
except ImportError:
    from aqt.utils import showWarning

    tr_import = False
from aqt.editor import Editor
from aqt.toolbar import Toolbar

try:
    from aqt.editor import EditorMode

    editor_mode_import = True
except ImportError:
    editor_mode_import = False
from aqt.browser import Browser
from aqt.modelchooser import ModelChooser
from aqt.reviewer import Reviewer

try:
    from aqt.notetypechooser import NotetypeChooser

    notetypechooser_import = True
except ImportError:
    notetypechooser_import = False
import contextlib

from aqt.addcards import AddCards
from bs4 import BeautifulSoup

from . import cs_functions as functions
from .config_defaults import complete_shortcut_config

with contextlib.suppress(ImportError):
    from aqt.operations.notetype import update_notetype_legacy

# Anki before version 2.1.20 does not use aqt.gui_hooks
try:
    from aqt import gui_hooks

    new_hooks = True
except ImportError:
    new_hooks = False

# Gets config.json as config
config = complete_shortcut_config(mw.addonManager.getConfig(__name__))
_live_editors = weakref.WeakSet()
_live_browsers = weakref.WeakSet()
_live_add_windows = weakref.WeakSet()
_live_sidebar_toolbars = weakref.WeakSet()


def _remove_owned_shortcuts(owner, attribute):
    for shortcut in getattr(owner, attribute, []):
        with contextlib.suppress(RuntimeError):
            shortcut.setEnabled(False)
            shortcut.deleteLater()
    setattr(owner, attribute, [])


def _find_duplicates():
    browser = aqt_dialogs.open("Browser", mw)
    browser.onFindDupes()


def _refresh_menu_action_shortcut(action, key, callback):
    # Hidden menu actions do not activate on all distributions of Anki.
    # Keep one window shortcut and clear the action's competing binding.
    action.setShortcuts([])
    if not hasattr(action, "_cs_window_shortcut"):
        action._cs_window_shortcut = QShortcut(QKeySequence(), mw)
        action._cs_window_shortcut.activated.connect(callback)
    action._cs_window_shortcut.setKey(QKeySequence(key))
CS_CONFLICTSTR = "Custom Shortcut Conflicts: \n\n"
# config_scuts initialized after cs_traverseKeys
Qt_functions = {"Qt.Key_Enter": Qt.Key.Key_Enter,
                "Qt.Key_Return": Qt.Key.Key_Return,
                "Qt.Key_Escape": Qt.Key.Key_Escape,
                "Qt.Key_Space": Qt.Key.Key_Space,
                "Qt.Key_Tab": Qt.Key.Key_Tab,
                "Qt.Key_Backspace": Qt.Key.Key_Backspace,
                "Qt.Key_Delete": Qt.Key.Key_Delete,
                "Qt.Key_Left": Qt.Key.Key_Left,
                "Qt.Key_Down": Qt.Key.Key_Down,
                "Qt.Key_Right": Qt.Key.Key_Right,
                "Qt.Key_Up": Qt.Key.Key_Up,
                "Qt.Key_PageUp": Qt.Key.Key_PageUp,
                "Qt.Key_PageDown": Qt.Key.Key_PageDown,
                "<nop>": ""
                }


# There is a weird interaction with QShortcuts wherein if there are 2 (or more)
# QShortcuts mapped to the same key and function and both are enabled,
# the shortcut doesn't work

# There isn't an obvious way to get the original QShortcut objects, as
# The addons executes after the setup phase (which creates QShortcut objects)

def cs_traverseKeys(Rep, D):
    ret = {}
    for key in D:
        if key != "keys":
            if isinstance(D[key], dict):
                ret[key] = cs_traverseKeys(Rep, D[key])
            elif D[key] in Rep:
                ret[key] = Rep[D[key]]
            else:
                ret[key] = D[key]
    return ret


# Since QShortcuts cannot reveal their action (to the best of my knowledge),
# This map reconstructs what each QShortcut is supposed to do from its id
# The ids were found manually but so far have remained constant
mainShortcutIds = {-1: "main debug",
                   -2: "main deckbrowser",
                   -3: "main study",
                   -4: "main add",
                   -5: "main browse",
                   -6: "main stats",
                   -7: "main sync"
                   }

# Maps Anki's default key → action name (for saving references during first setup)
_main_default_key_to_action = {
    "Ctrl+:": "main debug",
    "D": "main deckbrowser",
    "S": "main study",
    "A": "main add",
    "B": "main browse",
    "T": "main stats",
    "Y": "main sync",
}
# Saved QShortcut objects keyed by action name, for refreshing without restart
_main_scut_objects = {}


# #138 — פתיחת סטטיסטיקה מתוך קיצור/סרגל אינה צריכה לפרש Shift שנשאר לחוץ
# כחיווי למסך הישן. פותחים במפורש את מסך הסטטיסטיקה החדש.
def _open_new_stats():
    if not mw._selectedDeck():
        return
    aqt_dialogs.open("NewDeckStats", mw)

# #138 — modern-theme also calls mw.onStats() directly from overview/reviewer.
# Route those entry points too; replacing the toolbar callback alone misses them.
type(mw).onStats = lambda self: _open_new_stats()

# This contains the processed shortcuts used for the rest of the functions
config_scuts = cs_traverseKeys(Qt_functions, config)

# The main shortcuts are now found by manually going through all QT shortcuts
# and replacing them with their custom shortcut equivalent

mainShortcutPairs = {
    "Ctrl+:": config_scuts["main debug"],
    "D": config_scuts["main deckbrowser"],
    "S": config_scuts["main study"],
    "A": config_scuts["main add"],
    "B": config_scuts["main browse"],
    "T": config_scuts["main stats"],
    "Y": config_scuts["main sync"],
}


# Finds all the shortcuts, figures out relevant ones from hardcoded shortcut check,
# and sets it to the right one
# This function has a side effect of changing the shortcut's id
def cs_main_setupShortcuts():
    mwShortcuts = mw.findChildren(QShortcut)
    # if functions.get_version() >= 50:
    for child in mwShortcuts:
        if child.key().toString() in mainShortcutPairs:
            oldScut = child.key().toString()
            newScut = mainShortcutPairs[oldScut]
            child.setKey(newScut)
            if oldScut in _main_default_key_to_action:
                action_name = _main_default_key_to_action[oldScut]
                _main_scut_objects[action_name] = child
                # #138 — QShortcut הישן מחזיק callback ל-mw.onStats שבודק Shift;
                # מחליפים רק את callback של פעולת הסטטיסטיקה במסך הראשי.
                if action_name == "main stats":
                    with contextlib.suppress(TypeError, RuntimeError):
                        child.activated.disconnect()
                    child.activated.connect(_open_new_stats)
            mainShortcutPairs.pop(oldScut)  # Only replace shortcuts once (the first time would be the main shortcut)


# Governs the shortcuts on the main toolbar
def cs_mt_setupShortcuts():
    m = mw.form
    # Goes through and includes anything on the duplicates list
    scuts_list = {
        "m_toolbox quit": [config_scuts["m_toolbox quit"]],
        "m_toolbox preferences": [config_scuts["m_toolbox preferences"]],
        "m_toolbox undo": [config_scuts["m_toolbox undo"]],
        "m_toolbox see documentation": [config_scuts["m_toolbox see documentation"]],
        "m_toolbox switch profile": [config_scuts["m_toolbox switch profile"]],
        "m_toolbox export": [config_scuts["m_toolbox export"]],
        "m_toolbox import": [config_scuts["m_toolbox import"]],
        "m_toolbox study": [config_scuts["m_toolbox study"]],
        "m_toolbox create filtered deck": [config_scuts["m_toolbox create filtered deck"]],
        "m_toolbox addons": [config_scuts["m_toolbox addons"]]
    }
    # for act,key in config_scuts["m_toolbox _duplicates"].items():
    #    scuts_list[act].append(key)
    m.actionExit.setShortcuts(scuts_list["m_toolbox quit"])
    m.actionPreferences.setShortcuts(scuts_list["m_toolbox preferences"])
    m.actionUndo.setShortcuts(scuts_list["m_toolbox undo"])
    m.actionDocumentation.setShortcuts(scuts_list["m_toolbox see documentation"])
    m.actionSwitchProfile.setShortcuts(scuts_list["m_toolbox switch profile"])
    m.actionExport.setShortcuts(scuts_list["m_toolbox export"])
    m.actionImport.setShortcuts(scuts_list["m_toolbox import"])
    m.actionStudyDeck.setShortcuts(scuts_list["m_toolbox study"])
    m.actionCreateFiltered.setShortcuts(scuts_list["m_toolbox create filtered deck"])
    m.actionAdd_ons.setShortcuts(scuts_list["m_toolbox addons"])
    _refresh_menu_action_shortcut(m.actionExit, config_scuts["m_toolbox quit"], mw.close)
    if not hasattr(mw, "_cs_duplicates_action"):
        mw._cs_duplicates_action = QAction(mw)
    duplicates = config_scuts.get("m_toolbox _duplicates", "")
    _refresh_menu_action_shortcut(mw._cs_duplicates_action,
                                 duplicates if isinstance(duplicates, str) else "", _find_duplicates)


# #318 — toggle auto-advance ישירות מהמבחן
def _toggle_auto_advance():
    reviewer = getattr(mw, "reviewer", None)
    if not reviewer:
        return
    new_state = not getattr(reviewer, "auto_advance_enabled", False)
    reviewer.auto_advance_enabled = new_state
    if new_state and hasattr(reviewer, "_auto_advance_to_answer_if_enabled"):
        reviewer._auto_advance_to_answer_if_enabled()
    elif not new_state and hasattr(reviewer, "_clear_auto_advance_timers"):
        reviewer._clear_auto_advance_timers()
    from aqt.utils import tooltip
    tooltip("אויטאמאטיש ווייטערגיין: " + ("איינגעשאלטן" if new_state else "אויסגעשאלטן"))


# Governs the shortcuts on the review window
# This replacement method is pretty blind but tries to minimize disruption
# Replaces shortcuts at the start first
# If other addons append shortcuts, this shouldn't bother those addons
def cs_review_context_menu(self, _old):
    """Keep Anki's menu hints in sync with the configured reviewer keys."""
    rows = _old(self)
    methods = {
        "bury_current_card": "reviewer bury card", "onBuryCard": "reviewer bury card",
        "bury_current_note": "reviewer bury note", "onBuryNote": "reviewer bury note",
        "suspend_current_card": "reviewer suspend card", "onSuspendCard": "reviewer suspend card",
        "suspend_current_note": "reviewer suspend note", "onSuspend": "reviewer suspend note",
        "toggle_mark_on_current_note": "reviewer mark card", "onMark": "reviewer mark card",
        "delete_current_note": "reviewer delete note", "onDelete": "reviewer delete note",
        "on_set_due": "reviewer set due date", "onOptions": "reviewer options menu",
        "on_card_info": "reviewer card info", "on_previous_card_info": "reviewer previous card info",
        "replayAudio": "reviewer replay audio 1", "on_pause_audio": "reviewer pause audio",
        "on_seek_backward": "reviewer seek backward", "on_seek_forward": "reviewer seek forward",
        "onRecordVoice": "reviewer record voice", "onReplayRecorded": "reviewer play recorded voice",
        "toggle_auto_advance": "reviewer toggle auto advance",
    }

    def update(items):
        for row in items:
            if not row:
                continue
            if len(row) == 2:
                update(row[1])
                continue
            key = methods.get(getattr(row[2], "__name__", ""))
            # #138 — תפריט Anki מייצר את שבעת הדגלים 1–7; 0 הוא ניקוי נפרד.
            if key is None and row[1] in {f"Ctrl+{flag}" for flag in range(1, 8)}:
                key = f"reviewer set flag {row[1][-1]}"
            if key is not None:
                configured = config_scuts.get(key, row[1])
                row[1] = "" if configured == "<nop>" else configured

    update(rows)
    return rows


def cs_review_setupShortcuts(self, _old):
    # More fragile replacement: For these shortcuts,
    # Their functions are lambdas, so we can't directly address them
    # I'm not completely satisfied by this option
    # #138 — כל שבעת קיצורי הדגלים של Anki ניתנים כעת להתאמה.
    new_scut_replacements = {
        **{
            f"Ctrl+{flag}": config_scuts[f"reviewer set flag {flag}"]
            for flag in range(1, 8)
        },
        "1": config_scuts["reviewer choice 1"],
        "2": config_scuts["reviewer choice 2"],
        "3": config_scuts["reviewer choice 3"],
        "4": config_scuts["reviewer choice 4"],
    }
    # Less fragile replacement: For these shortcuts, address them by pointer and replace shortcut.
    # #138 — Anki 25 renamed several Reviewer methods; resolve old/new names lazily so one missing name does not break all reviewer shortcuts.
    new_function_replacements = {}

    def add_reviewer_method(shortcuts, *names):
        for name in names:
            method = getattr(self, name, None)
            if method:
                new_function_replacements[method] = shortcuts
                return

    new_function_replacements[self.mw.onEditCurrent] = [config_scuts["reviewer edit current"]]
    add_reviewer_method([
        config_scuts["reviewer flip card 1"],
        config_scuts["reviewer flip card 2"],
        config_scuts["reviewer flip card 3"],
    ], "onEnterKey")
    add_reviewer_method([
        config_scuts["reviewer replay audio 1"],
        config_scuts["reviewer replay audio 2"],
    ], "replayAudio")
    add_reviewer_method([config_scuts["reviewer mark card"]], "onMark", "toggle_mark_on_current_note")
    add_reviewer_method([config_scuts["reviewer bury note"]], "onBuryNote", "bury_current_note")
    add_reviewer_method([config_scuts["reviewer bury card"]], "onBuryCard", "bury_current_card")
    add_reviewer_method([config_scuts["reviewer suspend note"]], "onSuspend", "suspend_current_note")
    add_reviewer_method([config_scuts["reviewer suspend card"]], "onSuspendCard", "suspend_current_card")
    add_reviewer_method([config_scuts["reviewer delete note"]], "onDelete", "delete_current_note")
    add_reviewer_method([config_scuts["reviewer play recorded voice"]], "onReplayRecorded")
    add_reviewer_method([config_scuts["reviewer record voice"]], "onRecordVoice")
    add_reviewer_method([config_scuts["reviewer options menu"]], "onOptions")
    add_reviewer_method([config_scuts["reviewer more options"]], "showContextMenu")
    add_reviewer_method([config_scuts["reviewer set due date"]], "on_set_due")
    add_reviewer_method([config_scuts["reviewer card info"]], "on_card_info")
    add_reviewer_method([config_scuts["reviewer pause audio"]], "on_pause_audio")
    add_reviewer_method([config_scuts["reviewer seek backward"]], "on_seek_backward")
    add_reviewer_method([config_scuts["reviewer seek forward"]], "on_seek_forward")
    cuts = _old(self)
    # User bindings take precedence over unmanaged built-ins, e.g. flag 0
    # assigned Ctrl+Alt+N versus Anki's hard-coded "forget current card".
    assigned = {value.replace(" ", "").upper() for key, value in config_scuts.items()
                if key.startswith("reviewer ") and isinstance(value, str)
                and value and value.lower() not in ("<nop>", "none")}
    cuts = [row for row in cuts if not (
        isinstance(row[0], str) and row[0].replace(" ", "").upper() in assigned
        and row[1] not in new_function_replacements and row[0] not in new_scut_replacements
    )]
    # Order is important: shortcut-based replacement should come first
    functions.reviewer_find_and_replace_scuts(cuts, new_scut_replacements)

    # #138 — ל-Anki אין שורת Ctrl+0 מובנית. רושמים ישירות את הקיצור שהמשתמש
    # הגדיר עם callback הרשמי set_flag_func(0), במקום להוסיף Ctrl+0 ואז לנסות להחליפו.
    clear_flag_key = str(config_scuts.get("reviewer set flag 0", "") or "").strip()
    clear_flag_func_factory = getattr(self, "set_flag_func", None)
    clear_flag_func = clear_flag_func_factory(0) if callable(clear_flag_func_factory) else None
    if not clear_flag_func:
        set_flag = getattr(self, "set_flag_on_current_card", None) or getattr(self, "setFlag", None)
        if callable(set_flag):
            clear_flag_func = lambda: set_flag(0)
    if clear_flag_func and clear_flag_key and clear_flag_key.lower() not in {"<nop>", "none"}:
        cuts.append((clear_flag_key, clear_flag_func))

    add_reviewer_method([config_scuts["reviewer previous card info"]], "on_previous_card_info")
    functions.reviewer_find_and_replace_functions(cuts, new_function_replacements)
    for scut in config_scuts["reviewer _duplicates"]:
        cuts.append((config_scuts["reviewer _duplicates"][scut], self.sToF(scut)))
    # #318 — החלפת קיצור ה-auto-advance המקורי של אנקי (Shift+A) בקיצור מותאם,
    # כדי שגם התפריט More יציג את הקיצור הנכון
    aa_key = config_scuts.get("reviewer toggle auto advance", "")
    if aa_key and aa_key != "<nop>":
        replaced = False
        for i, (scut, func) in enumerate(cuts):
            if scut == "Shift+A":
                cuts[i] = (aa_key, _toggle_auto_advance)
                replaced = True
                break
        if not replaced:
            cuts.append((aa_key, _toggle_auto_advance))
    return cuts


# The function to setup shortcuts on the Editor
# Something funky is going on with the default MathJax and LaTeX shortcuts
# It does not affect the function (as I currently know of)
def cs_editor_focus_tags(self):
    # #138 — Anki 25.09 השאיר onFocusTags ישן שמנסה לגשת ל-self.tags, אף
    # ששדה התגיות עבר ל-Svelte. אם widget ישן קיים משתמשים בו; אחרת מפעילים
    # בתוך ה-WebView את קיצור התגיות המקורי של Anki, שמרחיב וממקד את השדה.
    tags_widget = getattr(self, "tags", None)
    if tags_widget is not None:
        tags_widget.setFocus()
        return
    self.web.eval("""
        // #138 — local scope permits repeated calls in the same WebView.
        (() => {
        const focusTagsEvent = new KeyboardEvent("keydown", {
            key: "T", code: "KeyT", ctrlKey: true, shiftKey: true,
            bubbles: true, cancelable: true
        });
        // #138 — Anki's shortcut matcher still compares event.which, which is
        // zero on a synthetic KeyboardEvent unless it is supplied explicitly.
        Object.defineProperty(focusTagsEvent, "which", { value: 84 });
        Object.defineProperty(focusTagsEvent, "keyCode", { value: 84 });
        document.dispatchEvent(focusTagsEvent);
        })();
    """)


def cs_editor_setupShortcuts(self):
    _live_editors.add(self)
    _remove_owned_shortcuts(self, "_cs_editor_shortcuts")
    dupes = []
    # if a third element is provided, enable shortcut even when no field is selected
    cuts = [
        (config_scuts["editor card layout"], self.onCardLayout, True),
        (config_scuts["editor bold"], self.toggleBold),
        (config_scuts["editor italic"], self.toggleItalic),
        (config_scuts["editor underline"], self.toggleUnderline),
        (config_scuts["editor superscript"], self.toggleSuper),
        (config_scuts["editor subscript"], self.toggleSub),
        (config_scuts["editor remove format"], self.removeFormat),
        (config_scuts["editor foreground"], self.onForeground),
        (config_scuts["editor change col"], self.onChangeCol),
        (config_scuts["editor cloze"], self.onCloze),
        (config_scuts["editor cloze alt"], self.onCloze),
        (config_scuts["editor cloze forced increment"], self.cs_onStdCloze),
        (config_scuts["editor cloze no increment"], self.cs_onAltCloze),
        (config_scuts["editor add media"], self.onAddMedia),
        (config_scuts["editor record sound"], self.onRecSound),
        (config_scuts["editor insert latex"], self.insertLatex),
        (config_scuts["editor insert latex equation"], self.insertLatexEqn),
        (config_scuts["editor insert latex math environment"], self.insertLatexMathEnv),
        (config_scuts["editor insert mathjax inline"], self.insertMathjaxInline),
        (config_scuts["editor insert mathjax block"], self.insertMathjaxBlock),
        (config_scuts["editor focus tags"], self.cs_focus_tags, True),
        (config_scuts["editor _extras"]["paste custom text"],
         lambda text=config_scuts["Ω custom paste text"]: self.customPaste(text)),
    ]
    # if functions.get_version() < 45:
    #     cuts += [
    #             (config_scuts["editor html edit"], self.onHtmlEdit),]
    # else:
    cuts += [
        (config_scuts["editor html edit"], lambda:
        self.web.eval(
            "{const currentField = getCurrentField(); if (currentField) { currentField.toggleHtmlEdit(); }}"
        )),
        (config_scuts["editor toggle sticky current"], self.csToggleStickyCurrent),
        (config_scuts["editor toggle sticky all"], self.csToggleStickyAll),
    ]

    for scut in config_scuts["editor _duplicates"]:
        if self.sToF(scut):
            dupes.append((config_scuts["editor _duplicates"][scut],) + self.sToF(scut))
    cuts += dupes
    for label in config_scuts["editor _pastes"]:
        if label in config_scuts["Ω custom paste extra texts"]:
            scut = config_scuts["editor _pastes"][label]
            temp = config_scuts["Ω custom paste extra texts"][label]
            cuts.append((scut, lambda text=temp: self.customPaste(text)))
    # There is a try-except clause to handle 2.1.0 version, which does not have this shortcut
    with contextlib.suppress(AttributeError):
        cuts.append((config_scuts["editor insert mathjax chemistry"], self.insertMathjaxChemistry))
    gui_hooks.editor_did_init_shortcuts(cuts, self)
    for row in cuts:
        if len(row) == 2:
            keys, fn = row
            fn = self._addFocusCheck(fn)
        else:
            keys, fn, _ = row
        scut = QShortcut(QKeySequence(keys), self.widget, activated=fn)
        self._cs_editor_shortcuts.append(scut)


# Wrapper function to add another shortcut to change note type
# Not with the other custom shortcut editor functions because
# the Anki functionality handling card type is not
# in the Editor itself
def cs_editorChangeNoteType(self):
    NOTE_TYPE_STR = "editor change note type"
    new_scuts = {config_scuts[NOTE_TYPE_STR]}
    for act, key in config_scuts["editor _duplicates"].items():
        if functions.normalizeShortcutName(act) == NOTE_TYPE_STR:
            new_scuts.add(key)
    for scut in new_scuts:
        # if functions.get_version() >= 41:
        QShortcut(QKeySequence(scut), self._widget, activated=self.on_activated)
        # elif functions.get_version() >= 36:
        #     QShortcut(QKeySequence(scut), self.widget, activated=self.on_activated)
        # else:
        #     QShortcut(QKeySequence(scut), self.widget, activated=self.onModelChange)


def cs_editorNotetypeChooser(self, show_label: bool):
    NOTE_TYPE_STR = "editor change note type"
    new_scuts = {config_scuts[NOTE_TYPE_STR]}
    for act, key in config_scuts["editor _duplicates"].items():
        if functions.normalizeShortcutName(act) == NOTE_TYPE_STR:
            new_scuts.add(key)
    for scut in new_scuts:
        # Since the hard-coded shortcut for this is Ctrl+N,
        # Don't destroy the existing shortcut
        # (has the side effect of leaving Ctrl+N assigned at all times)
        if scut == "Ctrl+N":
            continue
        qconnect(QShortcut(QKeySequence(scut), self._widget).activated,
                 self.on_button_activated
                 )


def cs_editorUpdateStickyPins(self, stickies, model):
    stickiesStr = ""

    # Hack: the svelte interface exposes a function "setSticky" which manually sets the sticky displays of all the pins
    # Manually create a set of stickies in order to set the sticky pins to the right display value
    stickiesStr += "["
    firstInput = True
    for sticky in stickies:
        if not firstInput:
            stickiesStr += ","
        firstInput = False
        stickiesStr += ("true" if sticky else "false")
    stickiesStr += "]"

    try:
        update_notetype_legacy(parent=self.mw, notetype=model).run_in_background(
            initiator=self
        )
        self.web.eval(f"setSticky({stickiesStr})")
    except Exception:
        pass


def cs_editorToggleSticky(self, index: int):
    model = self.note.note_type()
    flds = model["flds"]
    stickies = []
    flds[index]["sticky"] = not flds[index]["sticky"]
    for fld in flds:
        stickies.append(fld["sticky"])
    cs_editorUpdateStickyPins(self, stickies, model)


# Toggle sticky on all fields
# "Toggle" is interpreted as it is in Anki:
# If any sticky is on, turn everything off
# If all stickies are off, turn everything on
def cs_editorToggleStickyAll(self):
    model = self.note.note_type()
    flds = model["flds"]

    any_sticky = any([fld["sticky"] for fld in flds])
    stickies = []
    for fld in flds:
        if not any_sticky or fld["sticky"]:
            fld["sticky"] = not fld["sticky"]
        stickies.append(fld["sticky"])
    cs_editorUpdateStickyPins(self, stickies, model)


# Toggle sticky on the current field
def cs_editorToggleStickyCurrent(self):
    if self.currentField is not None:
        cs_editorToggleSticky(self, self.currentField)


# Intercepts the bridge functions normally used to toggle stickiness
def cs_captureBridgeToggleSticky(self, cmd, _old):
    # If we intercept a "toggle sticky all" command, then
    if cmd.startswith("toggleStickyAll") and config_scuts["editor toggle sticky all"] != "Shift+F9":
        model = self.note.note_type()
        return model["flds"]["sticky"]
    elif cmd.startswith("toggleSticky") and config_scuts["editor toggle sticky current"] != "F9":
        model = self.note.note_type()
        (_, num) = cmd.split(":", 1)
        idx = int(num)

        return model["flds"][idx]["sticky"]
    return _old(self, cmd)


# Wrapper function to change the shortcut to add a card
# Not with the other custom shortcut editor functions because
# the add card button is not within the Editor class
def cs_editorAddCard(self):
    _remove_owned_shortcuts(self, "_cs_add_shortcuts")
    ADD_CARD_STR = "editor confirm add card"
    self.addButton.setShortcut(QKeySequence(config_scuts[ADD_CARD_STR]))
    for act, key in config_scuts["editor _duplicates"].items():
        if functions.normalizeShortcutName(act) == ADD_CARD_STR:
            self._cs_add_shortcuts.append(QShortcut(QKeySequence(key), self, activated=self.addCards))


def cs_editorChangeDeck(self):
    _remove_owned_shortcuts(self, "_cs_deck_shortcuts")
    chooser = getattr(self.parentWindow, "deck_chooser", None)
    if chooser is not None:
        for shortcut in chooser._widget.findChildren(QShortcut):
            if shortcut.key().toString() == "Ctrl+D":
                shortcut.setEnabled(False)
    CHANGE_DECK_STR = "editor change deck"
    new_scuts = {config_scuts[CHANGE_DECK_STR]}
    for act, key in config_scuts["editor _duplicates"].items():
        if functions.normalizeShortcutName(act) == CHANGE_DECK_STR:
            new_scuts.add(key)
    for scut in new_scuts:
        shortcut = QShortcut(QKeySequence(scut), self.widget, activated=self.cs_changeDeck)
        self._cs_deck_shortcuts.append(shortcut)


# IMPLEMENTS Browser shortcuts
def _navigation_key_sequences(value):
    value = str(value or "")
    if not value or value.lower() == "<nop>":
        return []
    result = [QKeySequence(value)]
    if "shift" not in value.lower().split("+"):
        result.append(QKeySequence("Shift+" + value))
    return result


def cs_browser_setupShortcuts(self):
    _live_browsers.add(self)
    if not hasattr(self, "_lastSearchTxt"):
        self._lastSearchTxt = ""
    f = self.form
    with contextlib.suppress(AttributeError):
        f.previewButton.setShortcut(config_scuts["window_browser preview"])
    try:
        f.action_set_due_date.setShortcut(config_scuts["window_browser reschedule"])
    except AttributeError:
        f.actionReschedule.setShortcut(config_scuts["window_browser reschedule"])
    f.actionSelectAll.setShortcut(config_scuts["window_browser select all"])
    f.actionUndo.setShortcut(config_scuts["window_browser undo"])
    f.actionInvertSelection.setShortcut(config_scuts["window_browser invert selection"])
    f.actionFind.setShortcut(config_scuts["window_browser find"])
    f.actionNote.setShortcut(config_scuts["window_browser goto note"])
    f.actionNextCard.setShortcut(config_scuts["window_browser goto next note"])
    f.actionPreviousCard.setShortcut(config_scuts["window_browser goto previous note"])
    f.actionChangeModel.setShortcut(config_scuts["window_browser change note type"])
    f.actionGuide.setShortcut(config_scuts["window_browser guide"])
    f.actionFindReplace.setShortcut(config_scuts["window_browser find and replace"])
    try:
        f.actionTags.setShortcut(config_scuts["window_browser filter"])
    except AttributeError:
        f.actionSidebarFilter.setShortcut(config_scuts["window_browser filter"])
    f.actionCardList.setShortcut(config_scuts["window_browser goto card list"])
    f.actionReposition.setShortcut(config_scuts["window_browser reposition"])
    f.actionFirstCard.setShortcuts(_navigation_key_sequences(config_scuts["window_browser first card"]))
    f.actionLastCard.setShortcuts(_navigation_key_sequences(config_scuts["window_browser last card"]))
    # setupMenus also registers Shift+Home/End as standalone shortcuts.
    # The managed actions now own those variants, including rebinding.
    for name in ("pgUpCut", "pgDownCut"):
        old = getattr(self, name, None)
        if old is not None:
            old.setEnabled(False)
    f.actionClose.setShortcut(config_scuts["window_browser close"])
    f.action_Info.setShortcut(config_scuts["window_browser info"])
    f.actionAdd_Tags.setShortcut(config_scuts["window_browser add tag"])
    f.actionRemove_Tags.setShortcut(config_scuts["window_browser remove tag"])
    f.actionToggle_Suspend.setShortcut(config_scuts["window_browser suspend"])
    f.actionDelete.setShortcut(config_scuts["window_browser delete"])
    f.actionAdd.setShortcut(config_scuts["window_browser add note"])
    f.actionChange_Deck.setShortcut(config_scuts["window_browser change deck"])
    f.actionRed_Flag.setShortcut(config_scuts["window_browser flag_red"])
    try:
        f.actionOrange_Flag.setShortcut(config_scuts["window_browser flag_orange"])
    except AttributeError:
        f.actionPurple_Flag.setShortcut(config_scuts["window_browser flag_orange"])
    f.actionGreen_Flag.setShortcut(config_scuts["window_browser flag_green"])
    f.actionBlue_Flag.setShortcut(config_scuts["window_browser flag_blue"])
    for color, fallback in (("pink", "Ctrl+5"), ("turquoise", "Ctrl+6"), ("purple", "Ctrl+7")):
        action = getattr(f, "action" + color.title() + "_Flag", None)
        if action is not None:
            action.setShortcut(config_scuts.get("window_browser flag_" + color, fallback))
    f.actionSidebar.setShortcut(config_scuts["window_browser goto sidebar"])
    f.actionToggle_Mark.setShortcut(config_scuts["window_browser toggle mark"])
    f.actionClear_Unused_Tags.setShortcut(config_scuts["window_browser clear unused tags"])
    f.actionFindDuplicates.setShortcut(config_scuts["window_browser find duplicates"])
    f.actionSelectNotes.setShortcut(config_scuts["window_browser select notes"])
    f.actionManage_Note_Types.setShortcut(config_scuts["window_browser manage note types"])
    # Keep navigation registered even when remove-buttons detaches its menu actions.
    # QObject ownership alone does not associate a QAction with a window.
    for action in (f.actionFind, f.actionNote, f.actionCardList, f.actionSidebar,
                   f.actionFirstCard, f.actionLastCard):
        self.addAction(action)
    filter_action = getattr(f, "actionSidebarFilter", getattr(f, "actionTags", None))
    if filter_action is not None:
        self.addAction(filter_action)
    # Hidden menu actions are otherwise excluded from Qt's shortcut map.
    _remove_owned_shortcuts(self, "_cs_hidden_actions")
    filter_action = getattr(f, "actionSidebarFilter", getattr(f, "actionTags", None))
    for action in (f.actionFind, f.actionNote, f.actionCardList, f.actionSidebar, f.actionClose, filter_action):
        if action is None:
            continue
        sequence = action.shortcut()
        if not action.isVisible():
            action.setShortcut(QKeySequence())
            self._cs_hidden_actions.append(QShortcut(sequence, self, activated=action.trigger))


# Mimics the style of other Anki functions, analogue of customPaste
# Note that the saveNow function used earler takes the cursor to the end of the line,
# as it is meant to save work before entering a new window
def cs_editor_custom_paste(self, text):
    self._customPaste(text)


# Mimics the style of other Anki functions, analogue of _customPaste
def cs_uEditor_custom_paste(self, text):
    html = text
    if config_scuts["Ω custom paste end style"].upper() == "Y":
        html += "</span>\u200b"
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        html = str(BeautifulSoup(html, "html.parser"))
    self.doPaste(html, True, True)


# detects shortcut conflicts
# Gets all the shortcuts in a given object of the form {name: scut, ...} and names them
# Returns a dictionary of the form {scut: [labels of objects with that scut], ...}
def cs_getAllScuts(obj, strCont):
    res = {}
    for key in obj:
        if isinstance(obj[key], dict):
            rec = cs_getAllScuts(obj[key], key + " in " + strCont)
            for term in rec:
                if term in res:
                    res[term] += rec[term]
                else:
                    res[term] = rec[term]
        else:
            text_scut = obj[key].upper()
            if text_scut in res:
                res[text_scut].append(key + " in " + strCont)
            else:
                res[text_scut] = [key + " in " + strCont]
    return res


# Ignores the Add-on (Ω) options
def cs_conflictDetect():
    if config["Ω enable conflict warning"].upper() != "Y":
        return
    ext_list = {}
    for e in config:
        sub = e[0:(e.find(" "))]
        val = config[e]
        if sub == "Ω":
            continue
        if sub not in ext_list:
            ext_list[sub] = {}
        if isinstance(val, dict):
            scuts = cs_getAllScuts(val, e)
            for scut in scuts:
                if scut in ext_list[sub]:
                    ext_list[sub][scut] += scuts[scut]
                else:
                    ext_list[sub][scut] = scuts[scut]
        elif sub == "^":
            return None
        else:
            text_val = val.upper()
            if text_val in ext_list[sub]:
                ext_list[sub][text_val].append(e)
            else:
                ext_list[sub][text_val] = [e]
    conflictStr = CS_CONFLICTSTR
    conflict = False
    for key in ext_list:
        for k in ext_list[key]:
            if len(ext_list[key][k]) == 1:
                continue
            if k == "<NOP>":
                continue
            if not k:
                continue
            conflict = True
            conflictStr += ", ".join(ext_list[key][k])
            conflictStr += "\nshare '" + k + "' as a shortcut\n\n"
    if conflict:
        conflictStr += "\nThese shortcuts will not work.\n"
        conflictStr += "Please change them in the config.json."
        showWarning(conflictStr)


def cs_toolbarCenterLinks(self):
    try:
        links = [
            self.create_link(
                "decks",
                tr.actions_decks(),
                self._deckLinkHandler,
                tip=tr.actions_shortcut_key(val=config_scuts["main deckbrowser"]),
                id="decks",
            ),
            self.create_link(
                "add",
                tr.actions_add(),
                self._addLinkHandler,
                tip=tr.actions_shortcut_key(val=config_scuts["main add"]),
                id="add",
            ),
            self.create_link(
                "browse",
                tr.qt_misc_browse(),
                self._browseLinkHandler,
                tip=tr.actions_shortcut_key(val=config_scuts["main browse"]),
                id="browse",
            ),
            self.create_link(
                "stats",
                tr.qt_misc_stats(),
                # #138 — קישור הסטטיסטיקה פותח תמיד את המסך החדש גם כש-Shift לחוץ.
                _open_new_stats,
                tip=tr.actions_shortcut_key(val=config_scuts["main stats"]),
                id="stats",
            ),
        ]

        links.append(self._create_sync_link())

        gui_hooks.top_toolbar_did_init_links(links, self)

        return "\n".join(links)
    except AttributeError:
        pass
    try:
        links = [
            self.create_link(
                "decks",
                "Decks",
                self._deckLinkHandler,
                tip="קיצור קנעפל: {}".format(config_scuts["main deckbrowser"]),
                id="decks",
            ),
            self.create_link(
                "add",
                "Add",
                self._addLinkHandler,
                tip="קיצור קנעפל: {}".format(config_scuts["main add"]),
                id="add",
            ),
            self.create_link(
                "browse",
                "Browse",
                self._browseLinkHandler,
                tip="קיצור קנעפל: {}".format(config_scuts["main browse"]),
                id="browse",
            ),
            self.create_link(
                "stats",
                "Stats",
                # #138 — גם מסלול התאימות הישן אינו מעביר Shift ל-mw.onStats.
                _open_new_stats,
                tip="קיצור קנעפל: {}".format(config_scuts["main stats"]),
                id="stats",
            ),
        ]

        links.append(self._create_sync_link())

        gui_hooks.top_toolbar_did_init_links(links, self)

        return "\n".join(links)
    except AttributeError:
        links = [
            ["decks", "Decks", "Shortcut key: {}".format(config_scuts["main deckbrowser"])],
            ["add", "Add", "Shortcut key: {}".format(config_scuts["main add"])],
            ["browse", "Browse", "Shortcut key: {}".format(config_scuts["main browse"])],
            ["stats", "Stats", "Shortcut key: {}".format(config_scuts["main stats"])],
            ["sync", "Sync", "Shortcut key: {}".format(config_scuts["main sync"])],
        ]
        return self._linkHTML(links)


def cs_browser_basicFilter(self, txt):
    self.form.searchEdit.lineEdit().setText(txt)
    self.onSearchActivated()


def cs_browser_concatFilter(self, txt):
    cur = str(self.form.searchEdit.lineEdit().text())
    if cur and cur != self._searchPrompt:
        txt = cur + " " + txt
    self.form.searchEdit.lineEdit().setText(txt)
    self.onSearchActivated()


def cs_browser_orConcatFilter(self, txt):
    cur = str(self.form.searchEdit.lineEdit().text())
    if cur:
        txt = cur + " or " + txt
    self.form.searchEdit.lineEdit().setText(txt)
    self.onSearchActivated()


# Inserts the custom filter shortcuts upon browser startup
def cs_browser_setupEditor(self):
    # Operations may notify the browser while its editor is being constructed.
    if not hasattr(self, "_lastSearchTxt"):
        self._lastSearchTxt = ""
    if editor_mode_import:
        def add_preview_button(editor):
            editor._links["preview"] = lambda _editor: self.onTogglePreview()

        gui_hooks.editor_did_init.append(add_preview_button)
        self.editor = Editor(self.mw, self.form.fieldsArea, self, editor_mode=EditorMode.BROWSER, )
        gui_hooks.editor_did_init.remove(add_preview_button)
    self.csFilterScuts = {}
    self.csFilterFuncs = {}
    self.csCatFilterScuts = {}
    self.csCatFilterFuncs = {}
    self.csOCatFilterScuts = {}
    self.csOCatFilterFuncs = {}
    for filt in config_scuts["window_browser _filters"]:
        scut = config_scuts["window_browser _filters"][filt]
        if isinstance(scut, dict):
            continue
        self.csFilterFuncs[filt] = lambda txt=filt: cs_browser_basicFilter(self, txt)
        self.csFilterScuts[filt] = QShortcut(QKeySequence(scut), self)
        self.csFilterScuts[filt].activated.connect(self.csFilterFuncs[filt])
    if "_concat" in config_scuts["window_browser _filters"]:
        for filt in config_scuts["window_browser _filters"]["_concat"]:
            scut = config_scuts["window_browser _filters"]["_concat"][filt]
            self.csCatFilterFuncs[filt] = lambda txt=filt: cs_browser_concatFilter(self, txt)
            self.csCatFilterScuts[filt] = QShortcut(QKeySequence(scut), self)
            self.csCatFilterScuts[filt].activated.connect(self.csCatFilterFuncs[filt])
    if "_orConcat" in config_scuts["window_browser _filters"]:
        for filt in config_scuts["window_browser _filters"]["_orConcat"]:
            scut = config_scuts["window_browser _filters"]["_orConcat"][filt]
            self.csOCatFilterFuncs[filt] = lambda txt=filt: cs_browser_orConcatFilter(self, txt)
            self.csOCatFilterScuts[filt] = QShortcut(QKeySequence(scut), self)
            self.csOCatFilterScuts[filt].activated.connect(self.csOCatFilterFuncs[filt])


# Corresponds to _setup_tools in the SidebarToolbar class in Anki 2.1.45
sidebar_tool_names = [
    "window_browser sidebar search",
    "window_browser sidebar select"
]


def cs_sidebar_setup_tools(self):
    _live_sidebar_toolbars.add(self)
    from aqt.theme import theme_manager
    for row, tool in enumerate(self._tools):
        action = self.addAction(
            theme_manager.icon_from_resources(tool[1]), tool[2]()
        )
        action.setCheckable(True)
        # If we are aware of the row, set it in the tools
        # otherwise, use the default
        action.setShortcut(
            config_scuts[sidebar_tool_names[row]]
            if row < len(sidebar_tool_names) else
            f"Alt+{row + 1}"
        )
        self._action_group.addAction(action)
    # always start with first tool
    active = 0
    self._action_group.actions()[active].setChecked(True)
    self.sidebar.tool = self._tools[active][0]


def cs_injectCloseShortcut(scuts):
    def inject_shortcut(self):
        _live_add_windows.add(self)
        from aqt.utils import is_mac
        cutExistingShortcut = False
        for scut in (scuts() if callable(scuts) else scuts):
            if scut == "<default>":
                continue
            addedShortcut = False
            if is_mac and not cutExistingShortcut:
                for child in self.findChildren(QShortcut):
                    if child.key().toString() == 'Ctrl+W':
                        child.setKey(scut)
                        addedShortcut = cutExistingShortcut = True
            if not addedShortcut:
                shortcut = QShortcut(QKeySequence(scut), self)
                qconnect(shortcut.activated, self.close)
                self._closeShortcut = shortcut

    return inject_shortcut


# Functions that execute on startup
if config_scuts["Ω enable main"].upper() == 'Y':
    Toolbar._centerLinks = cs_toolbarCenterLinks
    cs_main_setupShortcuts()
if config_scuts["Ω enable editor"].upper() == 'Y':
    Editor.cs_changeDeck = functions.editor_changeDeck
    Editor.sToF = functions.editor_sToF
    Editor.cs_u_onAltCloze = lambda self: functions.cs_editor_generate_cloze(self, altModifier=True)
    Editor.cs_u_onStdCloze = lambda self: functions.cs_editor_generate_cloze(self, altModifier=False)
    Editor.cs_onAltCloze = functions.cs_editor_on_alt_cloze
    Editor.cs_onStdCloze = functions.cs_editor_on_std_cloze
    Editor.customPaste = cs_editor_custom_paste
    Editor._customPaste = cs_uEditor_custom_paste
    # #138 — קיצור התגיות משתמש במימוש תואם Svelte במקום onFocusTags השבור של Anki 25.09.
    Editor.cs_focus_tags = cs_editor_focus_tags
    Editor.setupShortcuts = cs_editor_setupShortcuts
    Editor.setupShortcuts = wrap(Editor.setupShortcuts, cs_editorChangeDeck)
    # if functions.get_version() >= 45:
    Editor.csToggleStickyCurrent = cs_editorToggleStickyCurrent
    Editor.csToggleStickyAll = cs_editorToggleStickyAll
    Editor.onBridgeCmd = wrap(Editor.onBridgeCmd, cs_captureBridgeToggleSticky, "around")
    if notetypechooser_import:
        NotetypeChooser._setup_ui = wrap(NotetypeChooser._setup_ui, cs_editorNotetypeChooser)
    ModelChooser.setupModels = wrap(ModelChooser.setupModels, cs_editorChangeNoteType)
    AddCards.setupButtons = wrap(AddCards.setupButtons, cs_editorAddCard)
    with contextlib.suppress(AttributeError, KeyError):
        gui_hooks.add_cards_did_init.append(cs_injectCloseShortcut(lambda: [config_scuts["editor add card close window"]]))
if config_scuts["Ω enable reviewer"].upper() == 'Y':
    Reviewer._shortcutKeys = wrap(Reviewer._shortcutKeys, cs_review_setupShortcuts, "around")
    Reviewer._contextMenu = wrap(Reviewer._contextMenu, cs_review_context_menu, "around")
    Reviewer.sToF = functions.review_sToF
    # #318 — תפריט "עוד" של המבחן בונה QAction עם Shift+A קשיח; מחליפים לקיצור המותאם
    def _fix_auto_advance_in_menu(reviewer, menu):
        aa_key = config_scuts.get("reviewer toggle auto advance", "")
        if not aa_key or aa_key == "<nop>":
            return
        from aqt.qt import QKeySequence
        for action in menu.actions():
            if action.shortcut().toString() in ("Shift+A", "Shift+a"):
                action.setShortcut(QKeySequence(aa_key))
            text = action.text()
            if "Shift+A" in text or "Shift+a" in text:
                action.setText(text.replace("Shift+A", aa_key).replace("Shift+a", aa_key))
    gui_hooks.reviewer_will_show_context_menu.append(_fix_auto_advance_in_menu)
if config_scuts["Ω enable m_toolbox"].upper() == 'Y':
    cs_mt_setupShortcuts()
# Hooks to setup shortcuts at the right time
if config_scuts["Ω enable window_browser"].upper() == 'Y':
    Browser.setupEditor = cs_browser_setupEditor
    gui_hooks.browser_menus_did_init.append(cs_browser_setupShortcuts)
    # if functions.get_version() >= 45:
    from aqt.browser import SidebarToolbar

    SidebarToolbar._setup_tools = cs_sidebar_setup_tools

# Fun fact: the stats window shortcut can also be customized (very slightly)
# Due to the added complexity of handling this relative to what is probably zero demand, this will remain unimplemented for the time being
# gui_hooks.stats_dialog_will_show.append(cs_injectCloseShortcut([config_scuts["stats close window"]]))
# The deck options window is another feature that probably won't be implemented unless requested
# gui_hooks.deck_options_did_load.append(cs_injectCloseShortcut([config_scuts["editor deck options close window"]]))

# Detects all conflicts, regardless of enable status
cs_conflictDetect()

# Redraws the toolbar with the new shortcuts
mw.toolbar.draw()

def _live_reload_addon_shortcuts():
    """Call reload functions in other addons after config is written to disk"""
    import sys
    # #138 — מודולי add-on עם מקף בשם עשויים להירשם תחת שם חבילה או תת-מודול; מאתרים אותם בצורה סלחנית לרענון live.
    def _reload_module(*module_names):
        candidates = []
        for module_name in module_names:
            module = sys.modules.get(module_name)
            if module:
                candidates.append(module)
        for loaded_name, module in list(sys.modules.items()):
            module_file = os.path.normcase(
                str(getattr(module, '__file__', '') or '')
            ).replace('\\', '/')
            # #138 — בסביבת פיתוח מודול יכול להיטען כנתיב מלא שמסתיים בשם התוסף, לא רק להתחיל בו.
            if any(
                loaded_name == module_name
                or loaded_name.startswith(module_name + ".")
                or loaded_name.endswith("." + module_name)
                or ("." + module_name + ".") in loaded_name
                for module_name in module_names
            ) or (
                any('/' + module_name.split('.')[0] + '/' in module_file
                    and module_file.endswith('/__init__.py') for module_name in module_names)
            ) or (
                any(module_name.endswith('font_style') for module_name in module_names)
                and '/font-size/' in module_file
                and module_file.endswith('/font_style.py')
            ):
                candidates.append(module)
        for module in candidates:
            if hasattr(module, '_reload_config'):
                module._reload_config()
                return True
        return False
    # bottom-bar: module-level variables (skip_shortcut, info_shortcut, undo_shortcut)
    # Anki registers addon modules under the folder name (e.g. 'bottom-bar.Bottom_Bar')
    with contextlib.suppress(Exception):
        bb = sys.modules.get('bottom-bar.Bottom_Bar')
        if bb and hasattr(bb, '_reload_config'):
            bb._reload_config()
    # refresh-browser: resets cached options so next access reads fresh from disk
    with contextlib.suppress(Exception):
        rb = sys.modules.get('refresh-browser.browser_refresh')
        if rb and hasattr(rb, '_reload_config'):
            rb._reload_config()
        else:
            rb_conf = sys.modules.get('refresh-browser.config')
            if rb_conf and hasattr(rb_conf, 'newConf'):
                rb_conf.newConf(None)
    # defer-cards: Config object caches config in self.config, call _loadConfig to reload
    with contextlib.suppress(Exception):
        # #138 — AnkiWeb modules use the numeric deployment directory.
        # Keep the source-directory alias for development installations.
        for module_name in ('149564514.defer_cards', 'defer-cards_149564514.defer_cards'):
            dc = sys.modules.get(module_name)
            if dc and hasattr(dc, 'conf'):
                dc.conf._loadConfig()
                break
    # rescheduler: gc() calls mw.addonManager.getConfig on every call — no action needed
    # #138 — edit-field-review/font-size מחזיקים QAction וכפתורי עורך פעילים; מרעננים אותם אחרי שמירה ב-shortcut-manager.
    with contextlib.suppress(Exception):
        _reload_module('edit-field-review.editbar')
    with contextlib.suppress(Exception):
        _reload_module('edit-field-review.reviewer')
    with contextlib.suppress(Exception):
        # #138 / סבב 9 — Anki does not guarantee one exact module name for an
        # add-on whose directory contains a dash.  Using the tolerant lookup
        # above makes Apply/OK replace the live quick-style shortcuts instead
        # of only changing config.json until the next restart.
        _reload_module('font-size.font_style', 'font_size.font_style')
    # #138 — remove-clozes מחזיק QShortcut על עורכים פתוחים; מרעננים אותו מיד אחרי Apply במקום לחכות לפתיחה מחדש.
    with contextlib.suppress(Exception):
        _reload_module('remove-clozes_1966460736')
    # #187 — pdf-viewer מחזיק QShortcut על עורכים פתוחים; מעדכנים אותו אחרי שמירת קיצור PDF.
    with contextlib.suppress(Exception):
        _reload_module('pdf-viewer')
    with contextlib.suppress(Exception):
        _reload_module('print-addon')
    with contextlib.suppress(Exception):
        _reload_module('external-editor_805891399.external_js_editor_for_field',
                       '805891399.external_js_editor_for_field')


def _refresh_active_reviewer_shortcuts():
    # #138 — כאשר Apply/OK נלחץ בזמן מבחן, בונים מחדש את קיצורי מצב review במקום לחכות לחזרה למסך הראשי.
    if config_scuts.get("Ω enable reviewer", "").upper() != 'Y':
        return
    if getattr(mw, "state", None) != "review":
        return
    reviewer = getattr(mw, "reviewer", None)
    if not reviewer:
        return
    old_shortcuts = list(getattr(mw, "stateShortcuts", []) or [])
    for shortcut in old_shortcuts:
        with contextlib.suppress(Exception):
            shortcut.setEnabled(False)
    mw.setStateShortcuts(reviewer._shortcutKeys())
    for shortcut in old_shortcuts:
        with contextlib.suppress(Exception):
            shortcut.deleteLater()


def refresh_shortcuts():
    """Function to reload config and update shortcuts without restart"""
    global config
    global config_scuts

    import traceback

    from aqt.utils import showInfo as _dbg
    _do_refresh_shortcuts()


def _do_refresh_shortcuts():
    global config
    global config_scuts

    # 1. טעינה מחדש של הקונפיגורציה מהקובץ
    config = complete_shortcut_config(mw.addonManager.getConfig(__name__))

    # 2. עיבוד מחדש של המקשים (תרגום מ-Json לאובייקטי QT)
    new_scuts = cs_traverseKeys(Qt_functions, config)

    # 3. עדכון המילון הקיים במקום (In-place update)
    # זה קריטי כי שאר חלקי התוסף מחזיקים הפניה ל-config_scuts המקורי
    config_scuts.clear()
    config_scuts.update(new_scuts)

    # 4. החלה מחדש על רכיבים שניתן לעדכן בזמן אמת

    # עדכון קיצורי החלון הראשי (D, S, A, B, T, Y)
    if config_scuts.get("Ω enable main", "").upper() == 'Y':
        for action, scut_obj in _main_scut_objects.items():
            scut_obj.setKey(config_scuts[action])

    # עדכון קיצורי חפיסות (צור/שנה שם/מחק וכו')
    from . import haf_h_sc as _haf_h_sc
    _haf_h_sc.refresh_haf_shortcuts()

    # עדכון תפריט הכלים (File, Edit, Tools...)
    if config_scuts["Ω enable m_toolbox"].upper() == 'Y':
        cs_mt_setupShortcuts()

    # עדכון סרגל הכלים העליון (הקישורים ל-Decks, Add, Browse)
    mw.toolbar.draw()

    # רענון תוספים אחרים שמשתמשים במשתני מודול-level
    _live_reload_addon_shortcuts()

    _refresh_active_reviewer_shortcuts()
    _refresh_open_editing_windows()


def _refresh_open_editing_windows():
    """Replace owned bindings; leave foreign shortcuts and editor state intact."""
    if config_scuts.get("Ω enable editor", "").upper() == "Y":
        for editor in list(_live_editors):
            try:
                editor.setupShortcuts()
            except RuntimeError:
                _live_editors.discard(editor)
        add_entry = aqt_dialogs._dialogs.get("AddCards")
        add_window = add_entry[1] if add_entry else None
        windows = set(_live_add_windows)
        if add_window is not None:
            windows.add(add_window)
        for window in windows:
            try:
                cs_editorAddCard(window)
                close_shortcut = getattr(window, "_closeShortcut", None)
                if close_shortcut is not None:
                    close_shortcut.setKey(QKeySequence(config_scuts["editor add card close window"]))
                else:
                    cs_injectCloseShortcut(lambda: [config_scuts["editor add card close window"]])(window)
            except RuntimeError:
                _live_add_windows.discard(window)
    if config_scuts.get("Ω enable window_browser", "").upper() == "Y":
        for browser in list(_live_browsers):
            try:
                cs_browser_setupShortcuts(browser)
            except RuntimeError:
                _live_browsers.discard(browser)
        for toolbar in list(_live_sidebar_toolbars):
            try:
                for action, key in zip(toolbar._action_group.actions(), sidebar_tool_names):
                    action.setShortcut(config_scuts[key])
            except RuntimeError:
                _live_sidebar_toolbars.discard(toolbar)
