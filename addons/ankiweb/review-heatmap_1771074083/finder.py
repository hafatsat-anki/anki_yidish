
# Review Heatmap Add-on for Anki
#
# Copyright (C) 2016-2022  Aristotelis P. <https//glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the accompanied license file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License which
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Finder extensions
"""

import re
from typing import TYPE_CHECKING

from aqt import mw

if TYPE_CHECKING:
    from aqt.browser.table import SearchContext


# FIXME: No longer works in combination with other search specifiers
# e.g. deck:current, which we actually add in the overview view


def _find_cards_reviewed_between(start_date: int, end_date: int) -> list[int]:
    # select from cards instead of just selecting uniques from revlog
    # in order to exclude deleted cards.
    # #304 — type=4 נכלל רק אם יש לו זמן שמור ב-profile (חזרה אמיתית במבחן)
    # ואינו חלק מתזמון FSRS מסיבי (הפרש < 20ms בין רשומות).
    from .manual_review_timer import PM_KEY
    exam_times = mw.pm.profile.get(PM_KEY, {})

    type4_rows = mw.col.db.list(
        "SELECT id FROM revlog WHERE id BETWEEN ? AND ? AND type = 4 ORDER BY id",
        start_date, end_date,
    )
    fsrs_rids: set[int] = set()
    prev = 0
    for rid in type4_rows:
        if prev and rid - prev < 20:
            fsrs_rids.add(rid)
            fsrs_rids.add(prev)
        prev = rid

    real_type4_rids = [r for r in type4_rows
                       if r not in fsrs_rids and str(r) in exam_times]

    if real_type4_rids:
        placeholders = ",".join("?" * len(real_type4_rids))
        return mw.col.db.list(
            "SELECT id FROM cards WHERE id IN "
            "(SELECT cid FROM revlog WHERE id BETWEEN ? AND ? AND type != 4 AND coalesce(time, 0) != 0"
            f" UNION SELECT cid FROM revlog WHERE id IN ({placeholders}))",
            start_date, end_date, *real_type4_rids,
        )
    return mw.col.db.list(
        "SELECT id FROM cards WHERE id IN "
        "(SELECT cid FROM revlog WHERE id BETWEEN ? AND ? AND type != 4 AND coalesce(time, 0) != 0)",
        start_date, end_date,
    )


_re_rid = re.compile(r"^rid:([0-9]+):([0-9]+)$")
_re_schtoday = re.compile(r"^schtoday:([0-9]+):([0-9]+)$")


def find_schtoday(search: str) -> list[int] | None:
    # #304 — הקוביה של היום: נלמד + תוזמן מחדש (מבחן) + תאריך יעד להיום + באיחור.
    # prop:rated לא כולל תזמון ידני (ease=0), לכן נדרש איחוד ידני.
    match = _re_schtoday.match(search)
    if not match:
        return None

    start_date = int(match[1])
    end_date = int(match[2])

    due_ids = set(mw.col.find_cards("is:due -is:suspended"))
    reviewed_ids = set(_find_cards_reviewed_between(start_date, end_date))
    return list(due_ids | reviewed_ids)


def find_rid(search: str) -> list[int] | None:
    match = _re_rid.match(search)

    if not match:
        return None

    start_date = int(match[1])
    end_date = int(match[2])

    return _find_cards_reviewed_between(start_date, end_date)


def on_browser_will_search(search_context: "SearchContext"):
    search = search_context.search
    if search.startswith("rid:"):
        found_ids = find_rid(search)
    elif search.startswith("schtoday:"):
        found_ids = find_schtoday(search)
    else:
        return

    if found_ids is None:
        return

    if hasattr(search_context, "card_ids"):
        search_context.card_ids = found_ids  # type: ignore[attr-defined]
    else:
        search_context.ids = found_ids  # type: ignore[assignment]


# HOOKS
######################################################################


def initialize_finder():
    from aqt.gui_hooks import browser_will_search

    browser_will_search.append(on_browser_will_search)
