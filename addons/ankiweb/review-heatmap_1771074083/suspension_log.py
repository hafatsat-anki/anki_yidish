from __future__ import annotations

import contextlib
import json
import time
from pathlib import Path
from typing import Iterable

from anki.utils import ids2str
from aqt import gui_hooks, mw

from .times import daystart_epoch

LOG_VERSION = 2
MAX_LOG_DAYS = 400
LOG_FILENAME = "review_heatmap_suspension_log.json"

_initialized = False


def _path() -> Path | None:
    profile_folder = mw.pm.profileFolder()
    if not profile_folder:
        raise RuntimeError("מען קען נישט דערקענען דעם פראפיל טעקע פאר דער אפשטעל היסטאריע")
    return Path(profile_folder) / LOG_FILENAME


def _open_collection_db():
    # אישיו #421: עצם קיום mw.col אינו מבטיח שה-Collection עדיין פתוח.
    # מחזירים DB רק כאשר הגישה אליו מצליחה, כדי שלא תזלוג CollectionNotOpen.
    try:
        col = getattr(mw, "col", None)
        if col is None:
            return None
        return col.db
    except Exception:
        return None


def _today_epoch() -> int | None:
    # אישיו #421: אין לחשב day-epoch לפני פתיחת האוסף או אחרי סגירתו.
    db = _open_collection_db()
    if db is None:
        return None
    rollover = 4
    with contextlib.suppress(Exception):
        rollover = int(mw.col.conf.get("rollover", 4))
    try:
        return int(daystart_epoch(db, "now", is_timestamp=False, offset=rollover))
    except Exception:
        return None


def _load() -> dict[str, object]:
    path = _path()
    if not path or not path.exists():
        return {"version": LOG_VERSION, "days": {}, "suspensions": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("version") == 1:
            # #199 — שדרוג לא מאבד ימי הטמנה/השהיה שכבר תועדו בגרסה הקודמת.
            payload = {
                "version": LOG_VERSION,
                "days": payload.get("days", {}),
                "suspensions": {},
            }
        elif payload.get("version") != LOG_VERSION:
            raise ValueError("די ווערסיע פון דער אפשטעל היסטאריע ווערט נישט געשטיצט")
        if not isinstance(payload.get("days"), dict):
            raise ValueError("דער מבנה פון די אפשטעל טעג איז אומגילטיג")
        payload.setdefault("suspensions", {})
        if not isinstance(payload["suspensions"], dict):
            raise ValueError("דער מבנה פון די אפשטעל צייטן איז אומגילטיג")
        for day, entry in payload["days"].items():
            int(day)
            if not isinstance(entry, dict) or not isinstance(entry.get("card_ids", []), list):
                raise ValueError("א טאג רשומה אין דער אפשטעל היסטאריע איז אומגילטיג")
            for cid in entry.get("card_ids", []):
                int(cid)
        for cid, intervals in payload["suspensions"].items():
            int(cid)
            if not isinstance(intervals, list):
                raise ValueError("די ליסטע פון אפשטעל צייטן איז אומגילטיג")
            for interval in intervals:
                if not isinstance(interval, dict):
                    raise ValueError("די אפשטעל צייט איז אומגילטיג")
                int(interval["start"])
                if interval.get("end") is not None:
                    int(interval["end"])
        return payload
    except Exception as exc:
        raise RuntimeError("מען קען נישט לייענען די אפשטעל היסטאריע. די עקזיסטירנדע טעקע ווערט נישט איבערגעשריבן.") from exc


def _save(payload: dict[str, object]) -> None:
    path = _path()
    if not path:
        return
    today = _today_epoch()
    # אישיו #421: כתיבת הלוג נדחית אם האוסף אינו פתוח; אין סיבה לגעת ב-DB
    # רק כדי לנקות קובץ cache בזמן מעבר פרופיל או סגירה.
    if today is None:
        return
    cutoff = today - MAX_LOG_DAYS * 86400
    days = payload.get("days")
    if isinstance(days, dict):
        for day in list(days):
            with contextlib.suppress(Exception):
                if int(day) < cutoff:
                    days.pop(day, None)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def log_signature() -> tuple[int, int, int]:
    path = _path()
    if not path or not path.exists():
        return (LOG_VERSION, 0, 0)
    stat = path.stat()
    return (LOG_VERSION, int(stat.st_mtime_ns), int(stat.st_size))


def _reconcile_suspension_intervals(
        payload: dict[str, object], suspended: set[int], today: int,
) -> bool:
    """Reconcile recorded intervals with observed state, without backdating.

    An active card proves an open interval ended by today; it does not prove
    which earlier day it ended. Keep the observation's provenance explicit.
    """
    intervals_by_card = payload.setdefault("suspensions", {})
    if not isinstance(intervals_by_card, dict):
        return False
    changed = False
    for cid_raw, intervals in intervals_by_card.items():
        try:
            cid = int(cid_raw)
        except (TypeError, ValueError):
            continue
        if cid in suspended or not isinstance(intervals, list):
            continue
        for interval in intervals:
            if isinstance(interval, dict) and not interval.get("end"):
                if int(interval.get("start", today)) <= today:
                    interval["end"] = today
                    interval["end_source"] = "observed_active_or_absent"
                    changed = True
    for cid in suspended:
        intervals = intervals_by_card.setdefault(str(cid), [])
        if isinstance(intervals, list) and not any(
            isinstance(interval, dict) and not interval.get("end") for interval in intervals
        ):
            # #199: due may precede suspension; preserve overdue history before
            # the first observed suspension instead of backdating the interval.
            intervals.append({
                "start": today,
                "start_source": "observed_suspended",
            })
            changed = True
    return changed


def ignored_scheduled_days_by_card() -> dict[int, set[int]]:
    # #199 — הימים האלה מוחרגים מספירת "מתוזמן ולא נלמד" בחישוב heatmap.
    payload = _load()
    # Read-time recovery also covers imports/syncs where a suspend hook was missed.
    # Only the in-memory log copy is reconciled here; report generation is read-only.
    db = _open_collection_db()
    observed_today = _today_epoch()
    if db is not None and observed_today is not None:
        suspended = {int(cid) for cid in db.list("select id from cards where queue = -1")}
        _reconcile_suspension_intervals(payload, suspended, observed_today)
    days = payload.get("days")
    result: dict[int, set[int]] = {}
    if not isinstance(days, dict):
        days = {}
    for day_raw, entry in days.items():
        try:
            day = int(day_raw)
        except Exception:
            continue
        if not isinstance(entry, dict):
            continue
        for cid in entry.get("card_ids") or []:
            with contextlib.suppress(Exception):
                result.setdefault(int(cid), set()).add(day)

    # #199 — השהיה מיוצגת כטווח [יום התחלה, יום חזרה לפעילות). כך כל יום
    # מוחרג בנפרד בלי לייצר אירוע מלאכותי מדי לילה; יום ההפעלה מחדש אינו מוחרג.
    suspensions = payload.get("suspensions")
    if isinstance(suspensions, dict):
        today = _today_epoch()
        # אישיו #421: cache קיים עדיין ניתן לקריאה בלי אוסף, אבל הרחבת טווחי
        # השהיה עד "היום" דורשת יום לימוד של Collection פתוח ולכן נדחית.
        if today is None:
            return result
        cutoff = today - MAX_LOG_DAYS * 86400
        for cid_raw, intervals in suspensions.items():
            with contextlib.suppress(Exception):
                cid = int(cid_raw)
                for interval in intervals or []:
                    start = max(int(interval["start"]), cutoff)
                    stop = int(interval.get("end") or (today + 86400))
                    for day in range(start, stop, 86400):
                        result.setdefault(cid, set()).add(day)
    return result


def _card_ids_for_note_ids(note_ids: Iterable[int]) -> list[int]:
    ids = [int(nid) for nid in note_ids if nid]
    if not ids:
        return []
    db = _open_collection_db()
    # אישיו #421: hooks מאוחרים בזמן סגירת פרופיל אינם ניגשים לאוסף שכבר נסגר.
    if db is None:
        return []
    return [int(cid) for cid in db.list(f"select id from cards where nid in {ids2str(ids)}")]


def _record(card_ids: Iterable[int], action: str) -> None:
    # #199 — לוג קדימה בלבד: לא משנים היסטוריה לפני שקיים קובץ האירועים.
    cids = sorted({int(cid) for cid in card_ids if cid})
    if not cids:
        return
    today = _today_epoch()
    if today is None:
        return
    payload = _load()
    days = payload.setdefault("days", {})
    if not isinstance(days, dict):
        payload["days"] = days = {}
    day = str(today)
    entry = days.setdefault(day, {"card_ids": [], "events": []})
    if not isinstance(entry, dict):
        entry = {"card_ids": [], "events": []}
        days[day] = entry
    card_ids_set = {int(cid) for cid in entry.get("card_ids") or []}
    card_ids_set.update(cids)
    entry["card_ids"] = sorted(card_ids_set)
    events = entry.setdefault("events", [])
    if isinstance(events, list):
        now = int(time.time())
        events.extend({"ts": now, "action": action, "card_id": cid} for cid in cids)
    _save(payload)


def _record_note(note_id: int, action: str) -> None:
    _record(_card_ids_for_note_ids([int(note_id)]), action)


def _set_suspended(card_ids: Iterable[int], suspended: bool) -> None:
    # #199 — פתיחה/סגירה של טווח השהיה; אין צורך ברשומה נפרדת לכל יום.
    cids = sorted({int(cid) for cid in card_ids if cid})
    if not cids:
        return
    today = _today_epoch()
    # אישיו #421: אין ליצור אירוע השהיה בלי Collection פתוח שמגדיר את יום הלימוד.
    if today is None:
        return
    payload = _load()
    suspensions = payload.setdefault("suspensions", {})
    if not isinstance(suspensions, dict):
        payload["suspensions"] = suspensions = {}
    for cid in cids:
        intervals = suspensions.setdefault(str(cid), [])
        if not isinstance(intervals, list):
            intervals = suspensions[str(cid)] = []
        open_interval = next((item for item in reversed(intervals) if not item.get("end")), None)
        if suspended and open_interval is None:
            intervals.append({"start": today})
        elif not suspended and open_interval is not None:
            open_interval["end"] = today
    _save(payload)




def _seed_existing_suspensions_unchecked() -> None:
    # Observe both suspension and resumption after the collection is available.
    db = _open_collection_db()
    today = _today_epoch()
    if db is None or today is None:
        return
    payload = _load()
    suspended = {int(cid) for cid in db.list("select id from cards where queue = -1")}
    if _reconcile_suspension_intervals(payload, suspended, today):
        _save(payload)


_seed_error_shown = False


def _seed_existing_suspensions() -> None:
    global _seed_error_shown
    try:
        _seed_existing_suspensions_unchecked()
        _seed_error_shown = False
    except Exception as exc:
        from _shared_libs.haf_logging import get_logger
        get_logger("review_heatmap.suspension").warning("Suspension history update failed", exc_info=True)
        # Keep the hook installed so a later operation can retry after repair.
        if not _seed_error_shown:
            from _shared_libs.haf_notifications import show_failure
            _seed_error_shown = True
            show_failure("מען קען נישט דערהיינטיגן די אפשטעל היסטאריע. די קאלענדאר דאטן קענען זיין פארעלטערט; אויב די פראבלעם קומט צוריק, שיקט א באריכט פונעם הילף מעניו.", exc)


def _on_card_operation(changes, handler) -> None:
    if getattr(changes, "card", False):
        _seed_existing_suspensions()


def initialize_suspension_log() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True

    # #199 — addon loading מתרחש לפני פתיחת האוסף; ה-hook הוא נקודת הזמן
    # הראשונה שבה mw.col וה-DB זמינים. הקריאה המיידית מכסה reload בתוך פרופיל פתוח.
    # Hook objects in recent Anki versions are append-only and not iterable.
    # _initialized already guarantees that this callback is registered once.
    gui_hooks.profile_did_open.append(_seed_existing_suspensions)
    _seed_existing_suspensions()
    gui_hooks.operation_did_execute.append(_on_card_operation)
    sync_hook = getattr(gui_hooks, "sync_did_finish", None)
    if sync_hook is not None:
        sync_hook.append(_seed_existing_suspensions)

    for hook_name, callback in (
        ("reviewer_will_bury_note", lambda nid: _record_note(nid, "bury_note")),
        ("reviewer_will_bury_card", lambda cid: _record([cid], "bury_card")),
    ):
        hook = getattr(gui_hooks, hook_name, None)
        if hook is not None:
            hook.append(callback)

    with contextlib.suppress(Exception):
        from aqt.browser.browser import Browser

        original_bury_selected_cards = Browser.bury_selected_cards

        def bury_selected_cards(self, checked: bool) -> None:
            if checked:
                _record(self.selected_cards(), "browser_bury_cards")
            return original_bury_selected_cards(self, checked)

        Browser.bury_selected_cards = bury_selected_cards
