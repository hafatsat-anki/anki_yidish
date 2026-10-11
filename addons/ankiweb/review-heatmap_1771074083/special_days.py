"""Read the precomputed Israel calendar; no Hebrew calendar calculations at runtime."""

import datetime
import json
from bisect import bisect_left, bisect_right
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _calendar():
    data = json.loads(Path(__file__).with_name("special_days.json").read_text(encoding="utf-8"))
    return {
        key: tuple(datetime.date.fromisoformat(day) for day in data[key])
        for key in ("gold_days", "hatch_days", "no_break_days")
    }


def special_days_for_range(start_day_epoch: int, end_day_epoch: int):
    """Return local SVG timestamps and streak keys on the report's day grid.

    Dates outside the static file's coverage have no special-day marking.
    Regenerate the file with tools/build_heatmap_special_days.py to extend it.
    """
    first = datetime.date.fromtimestamp(start_day_epoch)
    last = datetime.date.fromtimestamp(end_day_epoch)
    calendar = _calendar()
    selected = {}
    for key, dates in calendar.items():
        selected[key] = dates[bisect_left(dates, first):bisect_right(dates, last)]

    def midnight(day):
        return int(datetime.datetime.combine(day, datetime.time.min).timestamp())

    gold = [midnight(day) for day in selected["gold_days"]]
    hatch = [midnight(day) for day in selected["hatch_days"]]
    # Match the existing 86400-second report grid, including local DST changes.
    no_break = set()
    for stamp in (midnight(day) for day in selected["no_break_days"]):
        steps = -((start_day_epoch - stamp) // 86400)
        day_epoch = start_day_epoch + steps * 86400
        if start_day_epoch <= day_epoch <= end_day_epoch:
            no_break.add(day_epoch)
    return gold, hatch, no_break
