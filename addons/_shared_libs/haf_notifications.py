"""Visible, coalesced addon failure notices, delivered on Anki's UI thread."""

from __future__ import annotations

import sys
from threading import Lock

from aqt import gui_hooks, mw
from aqt.qt import QTimer
from aqt.utils import showWarning

from .haf_logging import get_logger

_logger = get_logger("failures")

_lock = Lock()
_seen: set[str] = set()
_pending: dict[str, str] = {}
_scheduled = False
_generation = 0


def _reset() -> None:
    global _generation, _scheduled
    with _lock:
        _generation += 1
        _seen.clear()
        _pending.clear()
        _scheduled = False


def _show_pending(generation: int) -> None:
    global _scheduled
    with _lock:
        if generation != _generation:
            return
        messages = list(dict.fromkeys(_pending.values()))
        _pending.clear()
    try:
        if messages:
            showWarning(
                "מען האט נישט געקענט פארענדיקן א טייל פון די פעולות:\n\n"
                + "\n\n".join(messages)
                + "\n\nאויב דער פראבלעם קומט נאכאמאל פאר, קענט איר שיקן א באריכט דורך דעם הילף-מעניו.",
                parent=mw,
                textFormat="plain",
            )
    finally:
        # Keep delivery serialized even while a modal dialog runs Qt's event loop.
        with _lock:
            again = generation == _generation and bool(_pending)
            if generation == _generation:
                _scheduled = again
        if again:
            QTimer.singleShot(0, lambda: _show_pending(generation))


def warn_once(key: str, message: str) -> None:
    """Report a failure without modal reentrancy or a dialog on every redraw."""
    global _scheduled
    _logger.warning(
        "%s: %s", key, message, exc_info=sys.exc_info()[0] is not None,
    )
    with _lock:
        if key in _seen:
            return
        _seen.add(key)
        _pending[key] = message
        if _scheduled:
            return
        _scheduled = True
        generation = _generation
    try:
        mw.taskman.run_on_main(
            lambda: QTimer.singleShot(0, lambda: _show_pending(generation))
        )
    except Exception:
        # Failed delivery must not suppress a future attempt.
        with _lock:
            _seen.discard(key)
            _pending.pop(key, None)
            _scheduled = False
        raise


def show_failure(message: str, error: BaseException | str | None = None, *, parent=None) -> None:
    """Show an actionable message; keep exception details in diagnostics."""
    exception = error if isinstance(error, BaseException) else None
    active_exception = sys.exc_info()
    exc_info = (type(exception), exception, exception.__traceback__) if exception else (
        active_exception if active_exception[0] is not None else None
    )
    _logger.error("%s%s", message, "\n" + error if isinstance(error, str) else "", exc_info=exc_info)
    showWarning(message, parent=parent or mw, textFormat="plain")


gui_hooks.profile_will_close.append(_reset)
# Do not reset on profile_did_open: importing this module from an earlier
# opening hook would otherwise discard its queued failure notice.
