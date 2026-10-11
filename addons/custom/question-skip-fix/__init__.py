"""Small, distribution-level safeguards for stale Reviewer state."""

import time

from aqt import gui_hooks, mw
from aqt.qt import QTimer
from aqt.utils import showWarning, tooltip
from _shared_libs.haf_notifications import show_failure


_shown_fingerprint: tuple[int, bool, int] | None = None
_refresh_queued = False


def refresh_reviewer_by_zoom(_card) -> None:
    """Keep the original question-transition repaint workaround."""
    mw.web.setZoomFactor(mw.web.zoomFactor() + 0.1)
    mw.web.setZoomFactor(mw.web.zoomFactor() - 0.1)


def _scheduler_fingerprint(col) -> tuple[int, bool, int]:
    return (int(col.sched.today), bool(col.get_config("fsrs", False)), id(col.sched))


def _remember_question_state(_card) -> None:
    global _shown_fingerprint
    try:
        _shown_fingerprint = _scheduler_fingerprint(mw.col)
    except Exception as exc:
        _shown_fingerprint = None
        show_failure("מען קען נישט קוקן דעם צייטפלאן מצב. עפנט דעם לערן עקראן פון פריש פארן נאכאמאל ענטפערן.", exc)


def _day_has_rolled_over(col, now: float | None = None) -> bool:
    try:
        cutoff = float(col.sched.day_cutoff)
    except Exception as exc:
        raise RuntimeError("די בדיקה פונעם טאג איבערגאנג איז נישט געלונגען") from exc
    return float(time.time() if now is None else now) >= cutoff


def _queue_safe_refresh() -> None:
    global _refresh_queued
    if _refresh_queued:
        return
    _refresh_queued = True

    def refresh() -> None:
        global _refresh_queued
        try:
            mw.reset()
            tooltip("דער צייטפלאן מצב האט זיך געטוישט. די פראגע איז זיכער אויפגעפרישט געווארן — מען קען ווידער ענטפערן.")
        finally:
            _refresh_queued = False

    QTimer.singleShot(0, refresh)


def _preflight_answer(reviewer, ease: int) -> None:
    sched = mw.col.sched
    sched.build_answer(
        card=reviewer.card,
        states=reviewer._v3.states,
        rating=reviewer._v3.rating_from_ease(ease),
    )


# #367/#370/#373/#374 — a day rollover, sleep/resume or scheduler switch can
# leave Anki's Reviewer snapshot stale. Cancel and refresh before collection writes.
# #376 — preflight catches the reported negative-timer ValueError safely.
def _guard_answer(handled: tuple[bool, int], reviewer, _card) -> tuple[bool, int]:
    proceed, ease = handled
    if not proceed:
        return handled
    try:
        stale = (
            _shown_fingerprint is None
            or _shown_fingerprint != _scheduler_fingerprint(mw.col)
            or _day_has_rolled_over(mw.col)
        )
    except Exception as exc:
        show_failure("מען קען נישט קוקן דעם צייטפלאן. די ענטפער איז נישט אפגעזיכערט; עפנט דעם לערן עקראן פון פריש און ענטפערט נאכאמאל.", exc)
        return False, ease
    if stale:
        _queue_safe_refresh()
        return False, ease
    try:
        _preflight_answer(reviewer, ease)
    except ValueError:
        _queue_safe_refresh()
        return False, ease
    except Exception as exc:
        show_failure("מען קען נישט צוגרייטן דעם קארטל צום ענטפערן. די ענטפער איז נישט אפגעזיכערט; עפנט דעם לערן עקראן פון פריש און ענטפערט נאכאמאל.", exc)
        return False, ease
    return True, ease


gui_hooks.reviewer_did_show_question.append(refresh_reviewer_by_zoom)
gui_hooks.reviewer_did_show_question.append(_remember_question_state)
gui_hooks.reviewer_will_answer_card.append(_guard_answer)
