# #304 — טיימר מותאם לתזמון ידני.
# כשמשתמש עושה תזמון ידני (מכל מקור — Set Due Date, rescheduler, וכו'),
# אנקי רושם ב-revlog רשומה עם type=4 ו-time=0.
# הטיימר שומר ב-mw.pm.profile את ה-revlog ID + זמן שחלף,
# כדי שה-heatmap יספור את החזרה כחזרה אמיתית.

from __future__ import annotations

import time

from aqt import gui_hooks, mw
from aqt.qt import QTimer

PM_KEY = "heatmap_exam_revlog_times"

_card_show_times: dict[int, float] = {}


def _on_question_shown(card) -> None:
    _card_show_times[card.id] = time.time()


def _scan_for_uncaptured() -> None:
    if not _card_show_times or not mw.col:
        return
    try:
        cids = list(_card_show_times.keys())
        placeholders = ",".join("?" * len(cids))
        rows = mw.col.db.all(
            f"SELECT id, cid FROM revlog WHERE cid IN ({placeholders}) AND type = 4 AND time = 0",
            *cids,
        )
        if not rows:
            return
        exam_times = mw.pm.profile.get(PM_KEY, {})
        changed = False
        for rid, cid in rows:
            rid_str = str(rid)
            if rid_str in exam_times:
                continue
            show_time = _card_show_times.get(cid)
            if not show_time:
                continue
            show_time_ms = int(show_time * 1000)
            if rid < show_time_ms:
                continue
            elapsed_ms = min(rid - show_time_ms, 600_000)
            if elapsed_ms <= 0:
                elapsed_ms = 1
            exam_times[rid_str] = elapsed_ms
            changed = True
        if changed:
            mw.pm.profile[PM_KEY] = exam_times
    except Exception:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/ankiweb/review-heatmap_1771074083/manual_review_timer.py:_scan_for_uncaptured', 'אפזיכערן די צייטן פון מאנועלע חזרות איז דורכגעפאלן. א טייל לערנען צייטן קענען פעלן אינעם קאלענדאר.')
        pass


def _on_operation_done(changes, handler) -> None:
    _scan_for_uncaptured()
    QTimer.singleShot(3000, _scan_for_uncaptured)


def initialize_manual_review_timer() -> None:
    gui_hooks.reviewer_did_show_question.append(_on_question_shown)
    gui_hooks.operation_did_execute.append(_on_operation_done)
