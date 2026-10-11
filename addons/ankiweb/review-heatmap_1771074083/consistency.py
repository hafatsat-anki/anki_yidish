"""One-time post-update consistency check, isolated from rendering and caches."""
from __future__ import annotations

import copy
import logging

from .times import daystart_epoch

DUE_QUERY = "(is:due or is:learn) -is:suspended -is:buried"
PROFILE_VERSION_KEY = "review_heatmap_consistency_checked_version"
_logger = logging.getLogger("haf.review_heatmap.consistency")
_initialized = False
_running_collection = None


# אישיו #199: בדיקה חוזרת משתמשת בדוח הקיים ובשאילתה אחת, בלי לסרוק revlog מחדש.
def check_today_report(reporter, report) -> dict:
    # אישיו #199: טעינת שעון מונוטוני למדידת פרק הזמן.
    import time

    # אישיו #199: שמירת זמן ההתחלה למדידת עלות בדיקת היום.
    started = time.monotonic()
    # אישיו #199: קריאת נתוני היום מהדוח שכבר חושב לתצוגה.
    values = report.activity.get(reporter._today, ()) if report else ()
    # אישיו #199: זיהוי לימוד היום שהופך השוואת מתוזמנים לנותרים ללא ישירה.
    if values and ((values[1] or 0) > 0 or (values[2] or 0) > 0):
        # אישיו #199: החזרת הסיבה לכך שהשוואת היום אינה ישירה.
        return {"status": "studied_today", "note": "די מתוזמנים אנטהאלטן קארטלעך וואס זענען שוין פארענדיגט"}
    # אישיו #199: זיהוי חפיסות מוחרגות לפני השוואה לכל האוסף.
    if reporter._config["synced"].get("limdecks"):
        # אישיו #199: החזרת הסיבה לכך שהשוואת היום אינה ישירה.
        return {"status": "excluded_decks", "note": "א קאלענדאר מיט אויסנאמען קען מען נישט פארגלייכן מיט דער גאנצער זאמלונג"}
    # אישיו #199: ספירת כרטיסי היום באמצעות שאילתת Anki הרשמית.
    expected_ids = set(reporter._col.find_cards(DUE_QUERY))
    expected = len(expected_ids)
    # אישיו #199: חילוץ מספר המתוזמנים שמופיע בלוח השנה.
    actual = abs(int(values[0] or 0)) if values else 0
    # אישיו #199: קביעת תוצאת ההשוואה בין הלוח לשאילתה.
    result = {"status": "ok" if expected == actual else "mismatch",
              # אישיו #199: צירוף שתי הספירות לפלט האבחון.
              "expected": expected, "actual": actual,
              # אישיו #199: תיעוד משך הבדיקה במילישניות.
              "elapsed_ms": round((time.monotonic() - started) * 1000, 2)}
    # אישיו #199: בחירת דיווח אזהרה כאשר הספירות שונות.
    if result["status"] == "mismatch":
        # Reports retain today's peak even after the current schedule shrinks.
        # Only treat it as informational when the uninflated cached IDs match
        # Anki exactly; do not hide a count/ID discrepancy or re-read revlog.
        get_forecast_ids = getattr(reporter, "get_last_forecast_card_ids", None)
        if actual > expected and callable(get_forecast_ids):
            from aqt import mw

            stored = mw.pm.profile.get(reporter._PM_KEY_TODAY_SCH_MAX, {})
            if (
                stored.get("day") == reporter._today
                and stored.get("sch") == actual
                and set(get_forecast_ids().get(reporter._today, ())) == expected_ids
            ):
                result.update(status="retained_peak", raw_actual=expected,
                              note="דער געוויזענער צאל אנטהאלט אן אפגעזיכערט טעגליכן רעקארד; די יעצטיגע קארטל מזהים שטימען מיט אנקי")
                _logger.info("Today's heatmap retains an earlier daily peak: %r", result)
                return result
        # אישיו #199: רישום אי־התאמה בספירות לצורך אבחון.
        _logger.warning("Today's heatmap differs from Anki query: %r", result)
    # אישיו #199: בחירת המסלול החלופי כאשר התנאי הקודם אינו מתקיים.
    else:
        # אישיו #199: רישום הצלחת ההשוואה ומשך הבדיקה.
        _logger.info("Today's heatmap checked: %r", result)
    # אישיו #199: החזרת תוצאת בדיקת העקביות והזמן שנמדד.
    return result


def compare_ids(expected: set[int], actual: set[int]) -> dict:
    return {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing": sorted(expected - actual),
        "extra": sorted(actual - expected),
        "matches": expected == actual,
    }


def build_consistency_payload(source) -> dict:
    # Isolate diagnostic state; do not call get_report(), save caches, or change
    # the persistent daily maximum. All DB calls below are reads.
    reporter = copy.copy(source)
    reporter._report_cache = {}
    before = reporter.cache_signature(False)
    reporter._today = daystart_epoch(reporter._db, "now", is_timestamp=False, offset=reporter._offset)
    today = reporter._today
    rows = reporter._load_revlog_rows(False)
    full_ids: dict[int, set[int]] = {}
    full = reporter._cards_done(revlog_rows=rows, scheduled_ids=full_ids, persist_today=False)
    _, due_days, due_ids = reporter._current_card_meta_and_due(False, today)
    ignored = reporter._ignored_scheduled_days_by_card()
    grouped = {}
    for row in rows:
        grouped.setdefault(int(row[1]), []).append(row)
    contributions = {}
    indexed_ids: dict[int, set[int]] = {}
    for cid in set(grouped) | set(due_days):
        activity = reporter._card_contribution_from_rows(grouped.get(cid, []), due_days.get(cid), today, ignored.get(cid))
        contributions[str(cid)] = {"activity": reporter._activity_to_json(activity)}
        for day, values in activity.items():
            if values[0]:
                indexed_ids.setdefault(day, set()).add(cid)
    indexed = reporter._report_from_card_index_payload(
        {"card_contribs": contributions}, None, due_days, due_ids, today, persist_today=False
    )
    mismatched_days = {
        str(day): compare_ids(full_ids.get(day, set()), indexed_ids.get(day, set()))
        for day in full_ids.keys() | indexed_ids.keys()
        if full_ids.get(day, set()) != indexed_ids.get(day, set())
    }
    full_activity = full.activity if full else {}
    index_activity = indexed[0].activity if indexed and indexed[0] else {}
    value_mismatches = [
        day for day in full_activity.keys() | index_activity.keys()
        if full_activity.get(day) != index_activity.get(day)
    ]
    values = full_activity.get(today, ())
    studied_today = bool(values and ((values[1] or 0) > 0 or (values[2] or 0) > 0))
    expected = set(reporter._col.find_cards(DUE_QUERY))
    current = compare_ids(expected, full_ids.get(today, set()))
    current["comparison_applicable"] = not studied_today
    current["query"] = DUE_QUERY
    current["note"] = "נאך היינטיגן לערנען: מתוזמנים אנטהאלטן אויך פארענדיגטע קארטלעך; דער סך פון חזרות ווייזט די איבעריגע. נייע קארטלעך זענען נישט אריינגערעכנט אינעם קאנטראל."
    from aqt import mw
    stored = mw.pm.profile.get(reporter._PM_KEY_TODAY_SCH_MAX, {})
    retained_max = int(stored.get("sch", 0)) if stored.get("day") == today else 0
    raw_scheduled = abs(int(values[0] or 0)) if values else 0
    retained_max_mismatch = not studied_today and retained_max > raw_scheduled
    changed = reporter.cache_signature(False) != before
    status = "changed_during_check" if changed else (
        "mismatch" if mismatched_days or value_mismatches or retained_max_mismatch or (not studied_today and not current["matches"])
        else "checked" if studied_today else "ok"
    )
    return {
        "status": status,
        "today": today,
        "current_due": current,
        "history_id_mismatches": mismatched_days,
        "history_value_mismatches": sorted(value_mismatches),
        "retained_daily_max": retained_max,
        "retained_max_exceeds_history": retained_max_mismatch,
        "writes_performed": False,
    }


def _run_version_check() -> None:
    global _running_collection
    from aqt import mw
    from aqt.operations import QueryOp
    from .consts import ADDON
    from .activity import ActivityReporter

    controller = getattr(mw, "_review_heatmap", None)
    collection = getattr(mw, "col", None)
    if collection is None or controller is None:
        return
    if mw.pm.profile.get(PROFILE_VERSION_KEY) == ADDON.VERSION:
        return
    if _running_collection is collection:
        return
    _running_collection = collection

    def done(payload) -> None:
        global _running_collection
        _running_collection = None
        if mw.col is not collection:
            return
        mw.pm.profile[PROFILE_VERSION_KEY] = ADDON.VERSION
        mw.pm.save()
        if payload["status"] not in ("ok", "checked"):
            # The saved daily peak can outlive suspension, deletion or
            # rescheduling. On its own it does not prove a calculation error.
            # WARNING reaches Anki's stderr error dialog, so keep this case
            # informational while retaining the full diagnostic payload.
            retained_max_only = (
                payload["status"] == "mismatch"
                and payload["retained_max_exceeds_history"]
                and payload["current_due"]["comparison_applicable"]
                and payload["current_due"]["matches"]
                and not payload["history_id_mismatches"]
                and not payload["history_value_mismatches"]
            )
            if retained_max_only:
                _logger.info("One-time consistency check found a retained daily peak: %r", payload)
            else:
                _logger.warning("One-time consistency check found a mismatch: %r", payload)

    def failed(error) -> None:
        global _running_collection
        _running_collection = None
        _logger.error("One-time consistency check failed: %s", error)

    QueryOp(
        parent=mw,
        op=lambda col: build_consistency_payload(ActivityReporter(col, controller._config)),
        success=done,
    ).failure(failed).run_in_background()


def setup_version_consistency_check() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True
    from aqt import gui_hooks
    from aqt.qt import QTimer

    gui_hooks.profile_did_open.append(_run_version_check)
    QTimer.singleShot(0, _run_version_check)


# אישיו #199: הגדרת setup_consistency_action לביצוע התיקון או בדיקתו.
def setup_consistency_action() -> None:
    # אישיו #199: תיעוד מטרת הפעולה המשויכת לאישיו.
    """Register a manual diagnostic without doing any work until it is clicked."""
    # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
    from aqt import mw
    # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
    from aqt.qt import QAction

    # אישיו #199: בחירת תפריט המאגר עבור בדיקת העקביות הידנית.
    menu = mw.form.menuCol
    # אישיו #199: מזהה קבוע שמאפשר למנוע יצירת פעולה כפולה.
    name = "haf_heatmap_consistency"
    # אישיו #199: בדיקה שהפעולה אינה קיימת כבר בתפריט.
    if any(action.objectName() == name for action in menu.actions()):
        # אישיו #199: עצירת המסלול כשהתנאי הקודם מונע המשך תקין או פעולה כפולה.
        return
    # אישיו #199: יצירת פעולת התפריט לבדיקה לפי בקשת המשתמש.
    action = QAction("קאנטראל פון די חזרות רעקארדס", mw)
    # אישיו #199: קביעת המזהה לזיהוי התקנות חוזרות של הפעולה.
    action.setObjectName(name)

    # אישיו #199: הגדרת run לביצוע התיקון או בדיקתו.
    def run() -> None:
        # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
        import json
        # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
        from aqt.operations import QueryOp
        # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
        from aqt.utils import showText
        from _shared_libs.haf_notifications import show_failure
        # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
        from .activity import ActivityReporter

        # אישיו #199: איתור בקר לוח השנה של החלון הנוכחי.
        controller = getattr(mw, "_review_heatmap", None)
        # אישיו #199: מניעת התחלת בדיקה ללא אוסף או בקר פעיל.
        if mw.col is None or controller is None:
            # אישיו #199: עצירת המסלול כשהתנאי הקודם מונע המשך תקין או פעולה כפולה.
            return
        # אישיו #199: יצירת פעולת קריאה שתתבצע ברקע.
        QueryOp(
            # אישיו #199: שיוך פעולת הרקע לחלון הראשי.
            parent=mw,
            # אישיו #199: חישוב דוח העקביות באמצעות האוסף של פעולת הרקע.
            op=lambda col: build_consistency_payload(ActivityReporter(col, controller._config)),
            # אישיו #199: הצגת דוח הבדיקה בעברית לאחר הצלחה.
            success=lambda report: showText(json.dumps(report, ensure_ascii=False, indent=2)),
        # אישיו #199: הצגת כשל הבדיקה למשתמש והפעלתה ברקע.
        ).failure(lambda error: show_failure("מען קען נישט פארענדיגן דעם קאנטראל פון די חזרות רעקארדס. פרובירט נאכאמאל נאכן איבערעפענען דעם פראפיל.", error)).run_in_background()

    # אישיו #199: התחלת הבדיקה רק לאחר לחיצה על הפעולה.
    action.triggered.connect(run)
    # אישיו #199: הוספת פעולת הבדיקה לתפריט המאגר.
    menu.addAction(action)
