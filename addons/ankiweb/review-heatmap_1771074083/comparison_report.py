"""
Exact due comparison report for Review Heatmap.

The report compares the card IDs calculated by the heatmap forecast with
Anki's own search results for prop:due=N, then writes a JSON file with
card/revlog details for every disagreement.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from aqt import mw
from aqt.qt import QAction, QFileDialog
from aqt.utils import showInfo, showText

PAST_DAYS_TO_COMPARE: int = 1200
DAYS_TO_COMPARE: int = 365
REVLOG_LIMIT_PER_CARD: int = 50
PAST_BROWSER_DETAIL_LIMIT: int = 100

# "summary" opens the old text summary window. "save_as" opens a Save As dialog
# for the JSON report when differences are found.
COMPARISON_RESULT_WINDOW_MODE: str = "save_as"


def _reporter():
    controller = getattr(mw, "_review_heatmap", None)
    reporter = getattr(controller, "_reporter", None)
    if reporter is not None:
        return reporter
    renderer = getattr(controller, "_renderer", None)
    reporter = getattr(renderer, "_reporter", None)
    if reporter is not None:
        return reporter
    if controller is not None and mw.col:
        from .activity import ActivityReporter

        return ActivityReporter(mw.col, controller._config)
    raise RuntimeError("review-heatmap reporter is not initialized")


def _today_epoch() -> int:
    from .times import daystart_epoch

    reporter = _reporter()
    return daystart_epoch(reporter._db, "now", is_timestamp=False, offset=reporter._offset)


def _collection_creation_time() -> int | None:
    creation_time = getattr(mw.col, "crt", None)
    if creation_time:
        return int(creation_time)
    try:
        row = mw.col.db.first("select crt from col")
        if row and row[0]:
            return int(row[0])
    except Exception:
        pass
    return None


def _current_sched_day(today_epoch: int) -> int:
    try:
        return int(mw.col.sched.today)
    except Exception:
        pass
    creation_time = _collection_creation_time()
    if creation_time:
        return int((today_epoch - creation_time) // 86400)
    return 0


def _date_from_epoch(epoch: int) -> str:
    return datetime.datetime.fromtimestamp(epoch).date().isoformat()


def _datetime_from_revlog_id(revlog_id: int) -> dict[str, str]:
    stamp = revlog_id / 1000
    return {
        "local": datetime.datetime.fromtimestamp(stamp).isoformat(sep=" ", timespec="seconds"),
        "utc": datetime.datetime.utcfromtimestamp(stamp).isoformat(sep=" ", timespec="seconds") + "Z",
    }


def _report_dir() -> Path:
    profile_folder = Path(mw.pm.profileFolder()) if getattr(mw, "pm", None) else Path.home()
    path = profile_folder / "review_heatmap_due_comparison"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _anki_prop_due_card_ids(offset: int) -> set[int]:
    return {int(cid) for cid in mw.col.find_cards(f"prop:due={offset}")}


def _anki_prop_rated_card_ids(offset: int) -> set[int]:
    query_offset = offset if offset == 0 else -abs(offset)
    return {int(cid) for cid in mw.col.find_cards(f"prop:rated={query_offset}")}


def _rid_bounds_for_day(day_epoch: int, offset_hours: int) -> tuple[int, int]:
    import time as _time
    # day_epoch = UTC midnight of the local calendar date (as returned by daystart_epoch).
    # The heatmap assigns revlog entries using LOCAL midnight as day boundaries:
    #   heatmap_day = (ts + local_offset - offset_hours*3600) rounded to UTC midnight.
    # So the revlog window for day_epoch must start at local midnight of that date.
    # local midnight (in UTC) = day_epoch - local_offset + offset_hours*3600
    local_offset = _time.localtime(day_epoch).tm_gmtoff
    start = day_epoch - local_offset + offset_hours * 3600
    start_ms = int(start * 1000)
    return start_ms, start_ms + 86400 * 1000


def _anki_rid_card_ids(start_ms: int, end_ms: int) -> set[int]:
    from .finder import find_rid

    return {int(cid) for cid in (find_rid(f"rid:{start_ms}:{end_ms}") or [])}


def _revlog_rows_between(start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    rows = mw.col.db.all(
        "SELECT id, cid, usn, ease, ivl, lastIvl, factor, time, type "
        "FROM revlog WHERE id BETWEEN ? AND ? ORDER BY cid, id",
        start_ms,
        end_ms,
    )
    keys = ["id", "cid", "usn", "ease", "ivl", "lastIvl", "factor", "time", "type"]
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(zip(keys, row))
        item["id"] = int(item["id"])
        item["cid"] = int(item["cid"])
        item["review_datetime"] = _datetime_from_revlog_id(item["id"])
        result.append(item)
    return result


def _counts_by_card(rows: list[dict[str, Any]]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for row in rows:
        cid = int(row["cid"])
        counts[cid] = counts.get(cid, 0) + 1
    return counts


def _counts_by_revlog_type(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("type"))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _is_manual_or_fsrs_like_revlog_row(row: dict[str, Any]) -> bool:
    return int(row.get("type") or 0) == 4 or int(row.get("time") or 0) == 0


def _deleted_or_missing_card_count(card_ids: list[int]) -> int:
    count = 0
    for cid in card_ids:
        if mw.col.db.first("SELECT 1 FROM cards WHERE id = ?", cid) is None:
            count += 1
    return count


def _missing_card_details(card_ids: list[int]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for cid in card_ids[:PAST_BROWSER_DETAIL_LIMIT]:
        card = mw.col.db.first("SELECT id, queue, did, odid, due, ivl FROM cards WHERE id = ?", cid)
        details.append({
            "card_id": cid,
            "status": "deleted_or_missing_from_cards" if card is None else "present_in_cards",
            "card": None if card is None else {
                "id": int(card[0]),
                "queue": int(card[1]),
                "did": int(card[2]),
                "odid": int(card[3] or 0),
                "due": int(card[4]),
                "ivl": int(card[5]),
            },
        })
    return details


def _activity_values(entry: list[Any] | tuple[Any, ...] | None) -> dict[str, Any]:
    values = list(entry or [])
    while len(values) < 6:
        values.append(0)
    scheduled, first_reviews, answered, percent, cards, done = values[:6]
    return {
        "scheduled": abs(int(scheduled or 0)),
        "first_reviews": abs(int(first_reviews or 0)),
        "answered_reviews": abs(int(answered or 0)),
        "percent": percent or 0,
        "unique_cards": abs(int(cards or 0)),
        "completed_scheduled_cards": abs(int(done or 0)),
    }


def _heatmap_card_ids_by_offset(past_days: int, future_days: int) -> tuple[int, dict[int, set[int]]]:
    reporter = _reporter()
    today_epoch = _today_epoch()
    reporter.get_report(limfcst=future_days + 1)
    by_day = reporter.get_last_forecast_card_ids()
    by_offset: dict[int, set[int]] = {}
    for offset in range(-past_days, future_days + 1):
        day_epoch = today_epoch + offset * 86400
        by_offset[offset] = {int(cid) for cid in by_day.get(day_epoch, [])}
    return today_epoch, by_offset


def _deleted_cards_explain_browser_gap(
    real_revlog_unique_cards: int,
    browser_cards: int,
    missing_from_browser: int,
    deleted_or_missing_cards: int,
    browser_only: int,
) -> bool:
    # heatmap_unique_cards counts "first-ever review on this day" — a different metric
    # that can differ by 1 from real_revlog_unique_cards due to close_open_card markers.
    # Do not compare them here; only check that deleted cards explain the browser gap.
    return (
        browser_only == 0
        and missing_from_browser == deleted_or_missing_cards
        and real_revlog_unique_cards - browser_cards == deleted_or_missing_cards
    )


def _past_browser_comparison_days(
    report_activity: dict[int, list[Any]],
    today_epoch: int,
    past_days: int,
    offset_hours: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    days: list[dict[str, Any]] = []
    discrepancies: list[dict[str, Any]] = []

    for offset in range(-past_days, 0):  # offset=0 (today) is skipped: heatmap stores today in a special format when no reviews yet
        day_epoch = today_epoch + offset * 86400
        heatmap = _activity_values(report_activity.get(day_epoch))
        # #182/#208 — activity[2] is already the total answered event count; activity[1]
        # remains a first-review breakdown for tooltips and must not be added again.
        heatmap_review_events = heatmap["answered_reviews"]
        start_ms, end_ms = _rid_bounds_for_day(day_epoch, offset_hours)
        rid_ids = _anki_rid_card_ids(start_ms, end_ms)
        prop_rated_ids = _anki_prop_rated_card_ids(offset)
        revlog_rows = _revlog_rows_between(start_ms, end_ms)
        manual_or_fsrs_like_rows = [
            row for row in revlog_rows if _is_manual_or_fsrs_like_revlog_row(row)
        ]
        real_review_rows = [row for row in revlog_rows if not _is_manual_or_fsrs_like_revlog_row(row)]
        revlog_counts = _counts_by_card(revlog_rows)
        revlog_ids = set(revlog_counts)
        real_revlog_counts = _counts_by_card(real_review_rows)
        real_revlog_ids = set(real_revlog_counts)
        repeated_cards = {cid: count for cid, count in real_revlog_counts.items() if count > 1}
        missing_from_browser = sorted(real_revlog_ids - rid_ids)
        browser_only = sorted(rid_ids - real_revlog_ids)
        missing_card_details = _missing_card_details(missing_from_browser)
        deleted_or_missing_count = _deleted_or_missing_card_count(missing_from_browser)
        # Compare revlog unique cards vs browser unique cards (not heatmap["unique_cards"],
        # which counts "cards with first-ever review on this day" — a different metric).
        count_mismatch = len(real_revlog_ids) != len(rid_ids)
        event_mismatch = heatmap_review_events != len(real_review_rows)
        expected_percent = round(100 * heatmap["completed_scheduled_cards"] / heatmap["scheduled"], 1) if heatmap["scheduled"] else (100 if heatmap_review_events else 0)
        percent_mismatch = heatmap["percent"] != expected_percent
        completion_overflow = heatmap["completed_scheduled_cards"] > heatmap["scheduled"]
        deleted_explains_browser_gap = _deleted_cards_explain_browser_gap(
            len(real_revlog_ids),
            len(rid_ids),
            len(missing_from_browser),
            deleted_or_missing_count,
            len(browser_only),
        )
        developer_attention_reasons: list[str] = []
        if event_mismatch:
            developer_attention_reasons.append("heatmap_events_do_not_match_real_revlog_events")
        if count_mismatch and not deleted_explains_browser_gap:
            developer_attention_reasons.append("browser_card_count_mismatch_not_explained_by_deleted_cards")
        if browser_only:
            developer_attention_reasons.append("browser_returns_cards_without_real_review_rows")
        if percent_mismatch:
            developer_attention_reasons.append("heatmap_percent_is_not_completed_scheduled_over_scheduled")
        if completion_overflow:
            developer_attention_reasons.append("completed_scheduled_cards_exceeds_scheduled_cards")
        developer_attention_needed = bool(developer_attention_reasons)

        day_payload = {
            "offset": offset,
            "date": _date_from_epoch(day_epoch),
            "heatmap_scheduled_count": heatmap["scheduled"],
            "heatmap_answered_review_count": heatmap["answered_reviews"],
            "heatmap_first_review_count": heatmap["first_reviews"],
            "heatmap_total_review_events": heatmap_review_events,
            "heatmap_unique_card_count": heatmap["unique_cards"],
            "heatmap_completed_scheduled_card_count": heatmap["completed_scheduled_cards"],
            "heatmap_percent": heatmap["percent"],
            "expected_heatmap_percent": expected_percent,
            "browser_rid_query": f"rid:{start_ms}:{end_ms}",
            "browser_rid_card_count": len(rid_ids),
            "browser_prop_rated_query": f"prop:rated={offset if offset == 0 else -abs(offset)}",
            "browser_prop_rated_card_count": len(prop_rated_ids),
            "revlog_event_count": len(revlog_rows),
            "revlog_real_review_event_count": len(real_review_rows),
            "revlog_unique_card_count": len(revlog_ids),
            "revlog_real_review_unique_card_count": len(real_revlog_ids),
            "revlog_type_counts": _counts_by_revlog_type(revlog_rows),
            "cards_with_multiple_revlog_events_count": len(repeated_cards),
            "revlog_cards_missing_from_browser_count": len(missing_from_browser),
            "deleted_or_missing_cards_count": deleted_or_missing_count,
            "browser_cards_missing_from_revlog_count": len(browser_only),
            "manual_or_fsrs_like_revlog_count": len(manual_or_fsrs_like_rows),
            "count_mismatch": count_mismatch,
            "event_mismatch": event_mismatch,
            "percent_mismatch": percent_mismatch,
            "completion_overflow": completion_overflow,
            "deleted_cards_explain_browser_gap": deleted_explains_browser_gap,
            "developer_attention_needed": developer_attention_needed,
            "developer_attention_reasons": developer_attention_reasons,
            "note": (
                "Heatmap tooltip review counts are revlog events. Browser rid results are unique existing cards from real review rows, "
                "so deleted cards can reduce the browser count. Percent completion is completed_scheduled_cards / scheduled_cards. "
                "Manual/FSRS revlog rows are reported separately and should not open extra Browser cards."
            ),
        }
        days.append(day_payload)

        if count_mismatch or event_mismatch or missing_from_browser or browser_only or manual_or_fsrs_like_rows:
            discrepancies.append({
                **day_payload,
                "cards_with_multiple_revlog_events": [
                    {"card_id": cid, "revlog_event_count": count}
                    for cid, count in sorted(repeated_cards.items(), key=lambda item: (-item[1], item[0]))[:PAST_BROWSER_DETAIL_LIMIT]
                ],
                "revlog_cards_missing_from_browser": missing_from_browser[:PAST_BROWSER_DETAIL_LIMIT],
                "revlog_cards_missing_from_browser_details": missing_card_details,
                "browser_cards_missing_from_revlog": browser_only[:PAST_BROWSER_DETAIL_LIMIT],
                "manual_or_fsrs_like_revlog_rows": manual_or_fsrs_like_rows[:PAST_BROWSER_DETAIL_LIMIT],
            })

    return days, discrepancies


def _card_details(cid: int, today_epoch: int) -> dict[str, Any] | None:
    row = mw.col.db.first(
        "SELECT id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, "
        "lapses, left, odue, odid, flags, data FROM cards WHERE id = ?",
        cid,
    )
    if row is None:
        return None

    keys = [
        "id", "nid", "did", "ord", "mod", "usn", "type", "queue", "due", "ivl",
        "factor", "reps", "lapses", "left", "odue", "odid", "flags", "data",
    ]
    card = dict(zip(keys, row))
    try:
        base_day = _current_sched_day(today_epoch)
        effective_due = card["odue"] if int(card["odid"] or 0) != 0 and int(card["odue"] or 0) != 0 else card["due"]
        card["effective_due"] = effective_due
        card["effective_due_source"] = "odue" if effective_due != card["due"] else "due"
        if card["queue"] in (2, 3):
            card["due_offset_from_today"] = int(card["due"] - base_day)
            card["effective_due_offset_from_today"] = int(effective_due - base_day)
        elif card["queue"] in (1, 4):
            card["due_local_datetime"] = datetime.datetime.fromtimestamp(int(card["due"])).isoformat(
                sep=" ", timespec="seconds"
            )
            card["effective_due_local_datetime"] = datetime.datetime.fromtimestamp(int(effective_due)).isoformat(
                sep=" ", timespec="seconds"
            )
    except Exception:
        pass
    return card


def _revlog_for_card(cid: int) -> list[dict[str, Any]]:
    rows = mw.col.db.all(
        "SELECT id, cid, usn, ease, ivl, lastIvl, factor, time, type "
        "FROM revlog WHERE cid = ? ORDER BY id DESC LIMIT ?",
        cid,
        REVLOG_LIMIT_PER_CARD,
    )
    keys = ["id", "cid", "usn", "ease", "ivl", "lastIvl", "factor", "time", "type"]
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(zip(keys, row))
        item["review_datetime"] = _datetime_from_revlog_id(int(item["id"]))
        item["time_note"] = "time is answer duration in milliseconds, not the review date"
        result.append(item)
    return result


def build_comparison_payload(
    past_days: int = PAST_DAYS_TO_COMPARE,
    future_days: int = DAYS_TO_COMPARE,
) -> dict[str, Any]:
    if not hasattr(mw, "_review_heatmap"):
        raise RuntimeError("review-heatmap is not loaded")
    if not mw.col:
        raise RuntimeError("collection is not available")

    reporter = _reporter()
    today_epoch, heatmap_by_offset = _heatmap_card_ids_by_offset(past_days, future_days)
    report = reporter.get_report(limhist=past_days, limfcst=future_days + 1)
    past_browser_days, past_browser_discrepancies = _past_browser_comparison_days(
        report.activity if report else {}, today_epoch, past_days, reporter._offset
    )
    generated = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    days: list[dict[str, Any]] = []
    discrepancies: list[dict[str, Any]] = []

    for offset in range(-past_days, future_days + 1):
        day_epoch = today_epoch + offset * 86400
        heatmap_ids = heatmap_by_offset.get(offset, set())
        anki_ids = _anki_prop_due_card_ids(offset)
        only_heatmap = sorted(heatmap_ids - anki_ids)
        only_anki = sorted(anki_ids - heatmap_ids)
        same = sorted(heatmap_ids & anki_ids)

        days.append({
            "offset": offset,
            "date": _date_from_epoch(day_epoch),
            "heatmap_count": len(heatmap_ids),
            "anki_prop_due_count": len(anki_ids),
            "same_count": len(same),
            "only_heatmap_count": len(only_heatmap),
            "only_anki_count": len(only_anki),
            "only_heatmap": only_heatmap,
            "only_anki_prop_due": only_anki,
        })

        for side, ids in (("only_heatmap", only_heatmap), ("only_anki_prop_due", only_anki)):
            for cid in ids:
                discrepancies.append({
                    "offset": offset,
                    "date": _date_from_epoch(day_epoch),
                    "side": side,
                    "card_id": cid,
                    "card": _card_details(cid, today_epoch),
                    "revlog": _revlog_for_card(cid),
                })

    return {
        "generated_at_local": generated,
        "past_days_to_compare": past_days,
        "future_days_to_compare": future_days,
        "today_epoch_seconds": today_epoch,
        "today_date": _date_from_epoch(today_epoch),
        "algorithm": {
            "heatmap_side": "card IDs collected from current cards.due/odue state used by the heatmap forecast diagnostics",
            "anki_side": "mw.col.find_cards('prop:due=N') for every N, with N=0 meaning today",
            "range": f"offsets -{past_days}..{future_days}; negative offsets are past Anki days",
            "difference_rule": "only_heatmap and only_anki_prop_due are exported with card table data and revlog history",
            "past_browser_side": "past days also compare heatmap tooltip counts with the same rid:start:end finder used when clicking a past heatmap square",
            "past_browser_difference_rule": "tooltip review counts are events; Browser rid rows are unique existing card IDs, so duplicate reviews or deleted cards can explain lower Browser counts",
            "past_percent_rule": "heatmap_percent is completed_scheduled_cards / scheduled_cards; repeated reviews do not increase percent",
            "revlog_id": "milliseconds since Unix epoch; convert with datetime.fromtimestamp(id / 1000)",
            "revlog_time": "answer duration in milliseconds, not a date",
        },
        "days": days,
        "discrepancies": discrepancies,
        "past_browser_days": past_browser_days,
        "past_browser_discrepancies": past_browser_discrepancies,
    }


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _create_comparison_report(
    past_days: int = PAST_DAYS_TO_COMPARE,
    future_days: int = DAYS_TO_COMPARE,
) -> tuple[Path, dict[str, Any]]:
    payload = build_comparison_payload(past_days, future_days)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = _report_dir() / f"review_heatmap_due_comparison_{stamp}.json"
    _write_payload(path, payload)
    return path, payload


def write_comparison_report(
    past_days: int = PAST_DAYS_TO_COMPARE,
    future_days: int = DAYS_TO_COMPARE,
) -> Path:
    path, _payload = _create_comparison_report(past_days, future_days)
    return path


def _mismatch_days(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [day for day in payload["days"] if day["only_heatmap_count"] or day["only_anki_count"]]


def _past_mismatch_days(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [day for day in payload["past_browser_days"] if day.get("developer_attention_needed")]


def _past_explained_days(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        day for day in payload["past_browser_days"]
        if (day["count_mismatch"] or day["event_mismatch"])
        and not day.get("developer_attention_needed")
    ]


def _comparison_is_clean(payload: dict[str, Any]) -> bool:
    return not _mismatch_days(payload) and not _past_mismatch_days(payload)


def _comparison_summary(path: Path, payload: dict[str, Any]) -> str:
    mismatch_days = _mismatch_days(payload)
    past_mismatch_days = _past_mismatch_days(payload)
    past_explained_days = _past_explained_days(payload)
    past_browser_discrepancies = payload.get("past_browser_discrepancies", [])
    total_past_browser_cards_delta = sum(
        abs(day["heatmap_unique_card_count"] - day["browser_rid_card_count"])
        for day in past_mismatch_days
    )
    total_past_event_delta = sum(
        abs(day["heatmap_total_review_events"] - day["revlog_real_review_event_count"])
        for day in past_mismatch_days
    )
    lines = [
        "דער קאלענדאר קאנטראל באריכט איז אפגעזיכערט אין א באזונדערע טעקע:",
        str(path),
        "",
        f"טעג וואס מען האט קאנטראלירט: {payload['past_days_to_compare']} צוריק + היינט + {payload['future_days_to_compare']} פאראויס",
        f"צוקונפטיגע טעג וואס דארפן א קאנטראל: {len(mismatch_days)}",
        f"קארטלעך מיט א צוקונפטיגן חילוק: {len(payload['discrepancies'])}",
        f"פארגאנגענע טעג צו שיקן צום אנטוויקלער: {len(past_mismatch_days)}",
        f"פארגאנגענע טעג מיט בלויז אן ערקלערטן חילוק: {len(past_explained_days)}",
        f"אומדערקלערטע קארטלעך חילוקים קעגן דורכבלעטערן: {total_past_browser_cards_delta}",
        f"אומדערקלערטע חזרה געשעענישן חילוקים קעגן revlog: {total_past_event_delta}",
    ]
    if mismatch_days:
        lines.append("")
        lines.append("איבערבליק פון טעג מיט חילוקים:")
        for day in mismatch_days[:30]:
            lines.append(
                f"offset={day['offset']} date={day['date']} "
                f"heatmap={day['heatmap_count']} prop:due={day['anki_prop_due_count']} "
                f"only_heatmap={day['only_heatmap_count']} only_prop_due={day['only_anki_count']}"
            )
    if past_mismatch_days:
        lines.append("")
        lines.append("איבערבליק פון פארגאנגענע טעג וואס דארפן אן אנטוויקלער קאנטראל:")
        for day in past_mismatch_days[:30]:
            lines.append(
                f"offset={day['offset']} date={day['date']} "
                f"tooltip_reviews={day['heatmap_total_review_events']} "
                f"tooltip_cards={day['heatmap_unique_card_count']} "
                f"completed_scheduled={day['heatmap_completed_scheduled_card_count']} "
                f"percent={day['heatmap_percent']} expected_percent={day['expected_heatmap_percent']} "
                f"browser_rid_cards={day['browser_rid_card_count']} "
                f"revlog_events={day['revlog_event_count']} "
                f"multi_review_cards={day['cards_with_multiple_revlog_events_count']} "
                f"missing_from_browser={day['revlog_cards_missing_from_browser_count']} "
                f"manual_or_fsrs_like={day['manual_or_fsrs_like_revlog_count']} "
                f"reasons={','.join(day.get('developer_attention_reasons') or [])}"
            )
    if past_browser_discrepancies:
        lines.append("")
        lines.append("א קורצע ערקלערונג: דורכבלעטערן ווייזט בלויז עקזיסטירנדע איינמאליגע קארטלעך פון אמתע חזרות. אן אויסגעמעקט קארטל קען ערקלערן א חילוק קעגן דעם הילף טעקסט; מאנועלע/FSRS תזמון שורות ווערן באזונדער באריכטעט און דארפן נישט עפענען נאך קארטלעך.")
    return "\n".join(lines)


def generate_comparison_report() -> str:
    path, payload = _create_comparison_report()
    if _comparison_is_clean(payload):
        return "אלעס איז אין ארדענונג"
    return _comparison_summary(path, payload)


def _show_save_as_report(path: Path, payload: dict[str, Any]) -> None:
    target, _selected_filter = QFileDialog.getSaveFileName(
        mw,
        "אפזיכערן דעם קאלענדאר קאנטראל באריכט",
        str(path),
        "JSON (*.json);;All files (*.*)",
    )
    if target:
        target_path = Path(target)
        if target_path.suffix.lower() != ".json":
            target_path = target_path.with_suffix(".json")
        _write_payload(target_path, payload)
        showText(_comparison_summary(target_path, payload), copyBtn=True)
        return

    showText(_comparison_summary(path, payload), copyBtn=True)


def show_comparison_report() -> None:
    path, payload = _create_comparison_report()
    if _comparison_is_clean(payload):
        showInfo("אלעס איז אין ארדענונג")
        return
    if COMPARISON_RESULT_WINDOW_MODE == "save_as":
        _show_save_as_report(path, payload)
        return
    showText(_comparison_summary(path, payload), copyBtn=True)


def setup_menuCol_action() -> None:
    for action in mw.form.menuCol.actions():
        if hasattr(action, "text") and (
            "פארגלייכן דעם פארויסזאג" in action.text()
            or "קאלענדאר קאנטראל באריכט" in action.text()
        ):
            return

    action = QAction("קאלענדאר קאנטראל באריכט - אויב עפעס איז נישט אין ארדענונג, שיקט צום אנטוויקלער", mw)
    action.triggered.connect(show_comparison_report)
    mw.form.menuCol.addSeparator()
    mw.form.menuCol.addAction(action)
