"""Speed up Anki 25.09 editor windows without replacing Anki's editor.

The add-on attacks two different delays:
1. Edit Current / Add Cards / Browser window creation: keep the expensive
   QWebEngine editor alive after a normal close and reuse it on reopen.
2. Browser row changes: move Note.fields_check() out of the synchronous
   Editor.loadNote() path and run the duplicate/cloze check after the note is
   already rendered.

Real collection/profile shutdown still performs Anki's original cleanup.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import aqt
from anki.notes import NoteFieldsCheckResult
from aqt import gui_hooks, mw
from aqt.editor import Editor, EditorMode
from aqt.qt import QTimer
from aqt.sound import av_player
from aqt.utils import saveGeom, saveSplitter, saveState

PREFIX = "[EditorPerformance]"
SUPPORTED_PREFIX = "25.09"

DEFAULT_CONFIG = {
    "cache_edit_current": True,
    "cache_add_cards": True,
    "cache_browser": True,
    "async_browser_fields_check": True,
    "prewarm_add_cards": True,
    "prewarm_edit_current": True,
    "prewarm_add_cards_delay_ms": 900,
    "prewarm_edit_current_delay_ms": 350,
}


def _config() -> dict[str, Any]:
    try:
        user = mw.addonManager.getConfig(__name__) or {}
    except Exception:
        user = {}
    return {**DEFAULT_CONFIG, **user}


CFG = _config()
_INSTALLED = False
_ADD_PREWARMED = False
_EDIT_PREWARMED = False
_DIALOG_OPEN_WRAPPER: Callable[..., Any] | None = None


def _log(message: str) -> None:
    print(f"{PREFIX} {message}")


def _hook_remove(hook: Any, callback: Callable[..., Any]) -> None:
    with contextlib.suppress(ValueError):
        hook.remove(callback)


def _hook_append_once(hook: Any, callback: Callable[..., Any]) -> None:
    # Anki 25.09 generated hook objects are not iterable. Their callbacks live
    # in the generated _hooks list, while the supported mutation API remains
    # append()/remove(). Inspect that list only for duplicate prevention.
    callbacks = getattr(hook, "_hooks", None)
    if callbacks is None or callback not in callbacks:
        hook.append(callback)


def _stop_editor_audio(mode: EditorMode) -> None:
    with contextlib.suppress(Exception):
        av_player.stop_and_clear_queue_if_caller(mode)


# ---------------------------------------------------------------------------
# Edit Current cache
# ---------------------------------------------------------------------------




def _edit_suspend(win: Any) -> None:
    _hook_remove(gui_hooks.operation_did_execute, win.on_operation_did_execute)
    win._editor_perf_hidden = True


def _edit_resume(win: Any) -> None:
    _hook_append_once(gui_hooks.operation_did_execute, win.on_operation_did_execute)
    win._editor_perf_hidden = False


def _install_edit_current_cache() -> None:
    if not CFG["cache_edit_current"]:
        return

    from aqt.editcurrent import EditCurrent

    original_cleanup = EditCurrent.cleanup
    original_reopen = EditCurrent.reopen
    original_close_with_callback = EditCurrent.closeWithCallback

    def cleanup(self: Any) -> None:
        global _EDIT_PREWARMED
        # cleanup() is a real destruction path (eg. note deleted / closeAll).
        _EDIT_PREWARMED = False
        self._editor_perf_real_close = True
        _edit_resume(self)
        original_cleanup(self)

    def close_event(self: Any, evt: Any) -> None:
        if getattr(self, "_editor_perf_real_close", False):
            evt.accept()
            return

        evt.ignore()
        if getattr(self, "_editor_perf_save_pending", False):
            return
        self._editor_perf_save_pending = True

        def after_save() -> None:
            self._editor_perf_save_pending = False
            if getattr(self, "_editor_perf_real_close", False):
                return
            _stop_editor_audio(EditorMode.EDIT_CURRENT)
            saveGeom(self, "editcurrent")
            _edit_suspend(self)
            self.hide()

        self.editor.call_after_note_saved(after_save)

    def reopen(self: Any, mw_arg: Any) -> None:
        self._editor_perf_real_close = False
        _edit_resume(self)
        original_reopen(self, mw_arg)
        self.show()
        self.activateWindow()
        self.raise_()

    def close_with_callback(self: Any, onsuccess: Callable[[], None]) -> None:
        self._editor_perf_real_close = True
        _edit_resume(self)
        original_close_with_callback(self, onsuccess)

    EditCurrent.cleanup = cleanup
    EditCurrent.closeEvent = close_event
    EditCurrent.reopen = reopen
    EditCurrent.closeWithCallback = close_with_callback


# ---------------------------------------------------------------------------
# Add Cards cache
# ---------------------------------------------------------------------------


def _add_suspend(win: Any) -> None:
    _hook_remove(gui_hooks.operation_did_execute, win.on_operation_did_execute)
    win._editor_perf_hidden = True


def _add_resume(win: Any) -> None:
    _hook_append_once(gui_hooks.operation_did_execute, win.on_operation_did_execute)
    win._editor_perf_hidden = False


def _install_add_cards_cache() -> None:
    if not CFG["cache_add_cards"]:
        return

    from aqt.addcards import AddCards

    original_close = AddCards._close
    original_reopen = AddCards.reopen
    original_close_with_callback = AddCards.closeWithCallback

    def close_cached(self: Any) -> None:
        global _ADD_PREWARMED
        if getattr(self, "_editor_perf_real_close", False):
            _ADD_PREWARMED = False
            _add_resume(self)
            original_close(self)
            return

        # ifCanClose() has already saved and, when needed, confirmed discard.
        # Prepare the next empty note while the window is hidden, so the next
        # open does not pay this cost and discarded text cannot reappear.
        try:
            self._load_new_note()
        except Exception as exc:
            _log(f"AddCards background reset failed: {exc!r}")

        _stop_editor_audio(EditorMode.ADD_CARDS)
        saveGeom(self, "add")
        _add_suspend(self)
        with contextlib.suppress(Exception):
            self.mw.maybeReset()
        self.hide()

    def reopen(self: Any, mw_arg: Any) -> None:
        self._editor_perf_real_close = False
        _add_resume(self)
        original_reopen(self, mw_arg)
        self.show()
        self.activateWindow()
        self.raise_()

    def close_with_callback(self: Any, cb: Callable[[], None]) -> None:
        self._editor_perf_real_close = True
        _add_resume(self)
        original_close_with_callback(self, cb)

    AddCards._close = close_cached
    AddCards.reopen = reopen
    AddCards.closeWithCallback = close_with_callback


# ---------------------------------------------------------------------------
# Browser cache
# ---------------------------------------------------------------------------


def _browser_suspended_hooks(win: Any) -> list[tuple[Any, Callable[..., Any]]]:
    # Keep collection_will_temporarily_close attached: it is a safety hook and
    # must still destroy a hidden Browser before the collection disappears.
    return [
        (gui_hooks.undo_state_did_change, win.on_undo_state_change),
        (gui_hooks.backend_will_block, win.table.on_backend_will_block),
        (gui_hooks.backend_did_block, win.table.on_backend_did_block),
        (gui_hooks.operation_did_execute, win.on_operation_did_execute),
        (gui_hooks.focus_did_change, win.on_focus_change),
        (gui_hooks.flag_label_did_change, win._update_flag_labels),
    ]


def _browser_suspend(win: Any) -> None:
    if getattr(win, "_editor_perf_hooks_suspended", False):
        return
    for hook, callback in _browser_suspended_hooks(win):
        _hook_remove(hook, callback)
    win._editor_perf_hooks_suspended = True


def _browser_resume(win: Any) -> None:
    if not getattr(win, "_editor_perf_hooks_suspended", False):
        return
    for hook, callback in _browser_suspended_hooks(win):
        _hook_append_once(hook, callback)
    win._editor_perf_hooks_suspended = False


def _install_browser_cache() -> None:
    if not CFG["cache_browser"]:
        return

    from aqt.browser.browser import Browser

    original_close_window = Browser._closeWindow
    original_reopen = Browser.reopen
    original_close_with_callback = Browser.closeWithCallback
    original_temporary_close = Browser._on_temporary_close

    def close_window(self: Any) -> None:
        if getattr(self, "_editor_perf_real_close", False):
            _browser_resume(self)
            original_close_window(self)
            return

        with contextlib.suppress(Exception):
            self._cleanup_preview()
        with contextlib.suppress(Exception):
            self._card_info.close()

        _stop_editor_audio(EditorMode.BROWSER)
        saveSplitter(self.form.splitter, "editor3")
        saveGeom(self, self._editor_state_key)
        saveState(self, self._editor_state_key)
        _browser_suspend(self)
        with contextlib.suppress(Exception):
            self.mw.maybeReset()
        self.hide()

    def reopen(self: Any, *args: Any, **kwargs: Any) -> None:
        self._editor_perf_real_close = False
        _browser_resume(self)
        self.setUpdatesEnabled(True)
        self.show()
        self.activateWindow()
        self.raise_()
        original_reopen(self, *args, **kwargs)

    def close_with_callback(self: Any, onsuccess: Callable[[], None]) -> None:
        self._editor_perf_real_close = True
        _browser_resume(self)
        original_close_with_callback(self, onsuccess)

    def temporary_close(self: Any, col: Any) -> None:
        # This is never a user close: the collection is about to disappear.
        self._editor_perf_real_close = True
        _browser_resume(self)
        original_temporary_close(self, col)

    Browser._closeWindow = close_window
    Browser.reopen = reopen
    Browser.closeWithCallback = close_with_callback
    Browser._on_temporary_close = temporary_close


# ---------------------------------------------------------------------------
# Browser row-change fast path
# ---------------------------------------------------------------------------


def _install_async_browser_fields_check() -> None:
    if not CFG["async_browser_fields_check"]:
        return

    original_load_note = Editor.loadNote

    def load_note(self: Editor, focusTo: int | None = None) -> None:
        if self.editorMode is not EditorMode.BROWSER or not self.note:
            original_load_note(self, focusTo)
            return

        note = self.note
        had_override = "fields_check" in note.__dict__
        previous_override = note.__dict__.get("fields_check")

        # Anki 25.09 blocks Browser navigation on note.fields_check(). Feed the
        # synchronous load a neutral result, then perform the real check after
        # editor_did_load_note, when fields are already visible.
        note.fields_check = lambda: NoteFieldsCheckResult.NORMAL  # type: ignore[method-assign]
        self._editor_perf_pending_fields_check_note = note
        try:
            original_load_note(self, focusTo)
        finally:
            if had_override:
                note.fields_check = previous_override  # type: ignore[method-assign]
            else:
                with contextlib.suppress(AttributeError):
                    delattr(note, "fields_check")

    Editor.loadNote = load_note

    def after_note_loaded(editor: Editor) -> None:
        if editor.editorMode is not EditorMode.BROWSER:
            return
        note = getattr(editor, "_editor_perf_pending_fields_check_note", None)
        if note is None:
            return
        editor._editor_perf_pending_fields_check_note = None
        if editor.note is note:
            editor._check_and_update_duplicate_display_async()

    gui_hooks.editor_did_load_note.append(after_note_loaded)


# ---------------------------------------------------------------------------
# DialogManager integration, including Multiple Windows add-on compatibility
# ---------------------------------------------------------------------------


def _dialog_name_for_instance(instance: Any) -> str | None:
    try:
        from aqt.addcards import AddCards
        from aqt.browser.browser import Browser
        from aqt.editcurrent import EditCurrent

        if isinstance(instance, AddCards):
            return "AddCards"
        if isinstance(instance, Browser):
            return "Browser"
        if isinstance(instance, EditCurrent):
            return "EditCurrent"
    except Exception:
        pass
    return None


def _find_hidden_multiwindow_instance(manager: Any, name: str) -> Any | None:
    # Arthur Milchior's Multiple Windows add-on stores multi instances here.
    # Reusing a hidden one first preserves multi-window behavior: if every
    # existing instance is visible, the original openMany() still creates a
    # new window.
    for instance in reversed(list(getattr(manager, "_openDialogs", []))):
        if not getattr(instance, "_editor_perf_hidden", False):
            continue
        if _dialog_name_for_instance(instance) == name:
            return instance
    return None


def _install_dialog_open_reuse() -> None:
    global _DIALOG_OPEN_WRAPPER
    manager_cls = type(aqt.dialogs)
    current_open = manager_cls.open

    # Another add-on may replace DialogManager.open after our module import.
    # Only skip if our wrapper is still the active method.
    if getattr(current_open, "_editor_perf_reuse_wrapper", False):
        return

    original_open = current_open

    def open_reusing_hidden(self: Any, name: str, *args: Any, **kwargs: Any) -> Any:
        if name in {"AddCards", "Browser", "EditCurrent"}:
            cached = _find_hidden_multiwindow_instance(self, name)
            if cached is not None:
                if hasattr(cached, "reopen"):
                    cached.reopen(*args, **kwargs)
                else:
                    cached.show()
                    cached.activateWindow()
                    cached.raise_()
                return cached

        # Stock DialogManager already reuses self._dialogs[name][1]. If the
        # Multiple Windows add-on is active, this delegates to its open/openMany
        # logic and only creates another window when no hidden cache is free.
        return original_open(self, name, *args, **kwargs)

    open_reusing_hidden._editor_perf_reuse_wrapper = True  # type: ignore[attr-defined]
    open_reusing_hidden._editor_perf_wrapped = original_open  # type: ignore[attr-defined]
    manager_cls.open = open_reusing_hidden
    _DIALOG_OPEN_WRAPPER = open_reusing_hidden


# ---------------------------------------------------------------------------
# Idle prewarm
# ---------------------------------------------------------------------------


def _construct_without_show(dialog_name: str, cls: type) -> Any | None:
    # Constructors call self.show(). During prewarm suppress only that call;
    # all normal init hooks still run, then DialogManager keeps the instance.
    had_own_show = "show" in cls.__dict__
    old_show = cls.__dict__.get("show")
    setattr(cls, "show", lambda self: None)
    try:
        return aqt.dialogs.open(dialog_name, mw)
    except Exception as exc:
        _log(f"prewarm {dialog_name} failed: {exc!r}")
        return None
    finally:
        if had_own_show:
            setattr(cls, "show", old_show)
        else:
            with contextlib.suppress(AttributeError):
                delattr(cls, "show")


def _prewarm_add_cards() -> None:
    global _ADD_PREWARMED
    if _ADD_PREWARMED or not CFG["prewarm_add_cards"] or not CFG["cache_add_cards"]:
        return
    if not getattr(mw, "col", None):
        return

    from aqt.addcards import AddCards

    existing = aqt.dialogs._dialogs.get("AddCards", [None, None])[1]
    if existing is not None:
        _ADD_PREWARMED = True
        return

    win = _construct_without_show("AddCards", AddCards)
    if win is not None:
        _add_suspend(win)
        win.hide()
        _ADD_PREWARMED = True


def _prewarm_edit_current() -> None:
    global _EDIT_PREWARMED
    if _EDIT_PREWARMED or not CFG["prewarm_edit_current"] or not CFG["cache_edit_current"]:
        return
    reviewer = getattr(mw, "reviewer", None)
    if not reviewer or not reviewer.card:
        return

    from aqt.editcurrent import EditCurrent

    existing = aqt.dialogs._dialogs.get("EditCurrent", [None, None])[1]
    if existing is not None:
        _EDIT_PREWARMED = True
        return

    win = _construct_without_show("EditCurrent", EditCurrent)
    if win is not None:
        _edit_suspend(win)
        win.hide()
        _EDIT_PREWARMED = True


def _schedule_add_prewarm() -> None:
    QTimer.singleShot(int(CFG["prewarm_add_cards_delay_ms"]), _prewarm_add_cards)


def _schedule_edit_prewarm(*_args: Any) -> None:
    QTimer.singleShot(int(CFG["prewarm_edit_current_delay_ms"]), _prewarm_edit_current)


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    version = str(getattr(aqt, "appVersion", ""))
    if not version.startswith(SUPPORTED_PREFIX):
        _log(f"disabled on Anki {version}; this build is intentionally limited to {SUPPORTED_PREFIX}.x")
        return

    _install_edit_current_cache()
    _install_add_cards_cache()
    _install_browser_cache()
    _install_async_browser_fields_check()
    _install_dialog_open_reuse()
    # Re-apply after all add-ons have loaded, in case Multiple Windows replaced
    # DialogManager.open after this module was imported.
    gui_hooks.profile_did_open.append(_install_dialog_open_reuse)

    if CFG["prewarm_add_cards"]:
        gui_hooks.profile_did_open.append(_schedule_add_prewarm)
    if CFG["prewarm_edit_current"]:
        gui_hooks.reviewer_did_show_question.append(_schedule_edit_prewarm)

    _INSTALLED = True
    _log("installed")


_install()