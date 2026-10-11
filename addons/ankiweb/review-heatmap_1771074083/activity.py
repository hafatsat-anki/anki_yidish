import datetime
# #171/#179 — cache מתמשך נשמר כ-JSON בתיקיית הפרופיל.
import json
import logging
# #171/#179 — Path משמש למציאת קובץ ה-cache בתיקיית הפרופיל.
from pathlib import Path
# #179 v2 — time משמש לחישוב day-epoch של revlog חדשות בעדכון אינקרמנטלי.
import time

from aqt.utils import *

_heatmap_logger = logging.getLogger("haf.review_heatmap")
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Literal,
    NamedTuple,
    Union,
)

from anki.errors import NotFoundError
from anki.utils import ids2str
from aqt import mw

if TYPE_CHECKING:
    from anki.collection import Collection
    from anki.dbproxy import DBProxy

import contextlib

from .errors import CollectionError
from .libaddon.anki.configmanager import ConfigManager
from .special_days import special_days_for_range
from .times import daystart_epoch
from .types import DeckId

# limit max forecast to 200 years to protect against invalid due dates
MAX_FORECAST_DAYS = 73000


class ActivityType(Enum):
    reviews = 0


class StatsType(Enum):
    streak = 0
    percentage = 1
    cards = 2


class StatsEntry(NamedTuple):
    value: int
    type: StatsType = StatsType.streak


class StatsEntryStreak(StatsEntry):
    value: int
    type: StatsType = StatsType.streak


class StatsEntryPercentage(StatsEntry):
    value: int
    type: StatsType = StatsType.percentage


class StatsEntryCards(StatsEntry):
    value: int
    type: StatsType = StatsType.cards


class StatsReport(NamedTuple):
    streak_max: StatsEntryStreak
    streak_cur: StatsEntryStreak
    pct_days_active: StatsEntryPercentage
    activity_daily_avg: StatsEntryCards


class ActivityReport(NamedTuple):
    activity: dict[int, list[Union[int, float]]]
    start: int | None
    stop: int | None
    today: int
    offset: int
    stats: StatsReport
    holy_days: list[int] = []  # שניות-אפוק חצות מקומית לשבתות וחגים (עבור הJS)
    hatch_days: list[int] = []  # יום אסור במלאכה שגם היום שאחריו אסור במלאכה


class _ReportCacheEntry(NamedTuple):
    signature: tuple[object, ...]
    report: ActivityReport | None
    # #171/#179 — cache גם את מזהי התחזית כדי שחזרה מ-cache לא תשאיר נתוני תחזית מפריסה קודמת.
    forecast_card_ids: dict[int, set[int]]

# #171/#179 — גרסת cache וקיבולת מוגבלת מאפשרות החלפה בטוחה של מבנה JSON בעתיד.
PERSISTENT_CACHE_VERSION = 4
MAX_PERSISTENT_CACHE_ENTRIES = 24
PERSISTENT_CARD_INDEX_VERSION = 5


class ActivityReporter:
    # להקפיץ בכל שינוי בלוגיקת החישוב כדי לפסול cache ישן
    # History/special-day fixes must invalidate reports computed by older rules.
    _CALC_VERSION = 9

    def __init__(self, col: "Collection", config: ConfigManager):
        self._col: Collection
        self._db: DBProxy

        self._config: ConfigManager = config
        self._report_cache: dict[tuple[object, ...], _ReportCacheEntry] = {}
        self.set_collection(col)
        self._last_forecast_card_ids: dict[int, set[int]] = {}
        self._today = daystart_epoch(self._db, "now", is_timestamp=False, offset=self._offset)
        self._exam_revlog_times: dict[str, int] = self._load_exam_revlog_times()
    @staticmethod
    def _load_exam_revlog_times() -> dict[str, int]:
        from .manual_review_timer import PM_KEY
        try:
            return mw.pm.profile.get(PM_KEY, {})
        except Exception:
            from _shared_libs.haf_notifications import warn_once
            warn_once('addons/ankiweb/review-heatmap_1771074083/activity.py:_load_exam_revlog_times', 'מען קען נישט לייענען די צייטן פון מאנועלע חזרות. לערנען צייטן אינעם קאלענדאר קענען פעלן.')
            return {}

    def _exam_time_for(self, rid: int) -> int:
        return self._exam_revlog_times.get(str(rid), 0)

    _PM_KEY_TODAY_SCH_MAX = "heatmap_today_sch_max"

    def _persist_today_sch(self, today: int, sch: int) -> int:
        try:
            stored = mw.pm.profile.get(self._PM_KEY_TODAY_SCH_MAX, {})
            stored_day = stored.get("day")
            stored_sch = stored.get("sch", 0)
            if stored_day == today:
                best = max(sch, stored_sch)
            else:
                best = sch
            mw.pm.profile[self._PM_KEY_TODAY_SCH_MAX] = {"day": today, "sch": best}
            return best
        except Exception:
            from _shared_libs.haf_notifications import warn_once
            warn_once('addons/ankiweb/review-heatmap_1771074083/activity.py:_persist_today_sch', 'מען קען נישט אפזיכערן דעם טעגליכן קארטלעך רעקארד. דער פראצענט פארענדיגט אינעם קאלענדאר קען זיין אומגענוי.')
            return sch

    # Public API
    #########################################################################

    def get_report(
            self,
            limhist: int | None = None,
            limfcst: int | None = None,
            activity_type: ActivityType = ActivityType.reviews,
            current_deck_only: bool = False,
            cache_signature: tuple[object, ...] | None = None,
    ) -> ActivityReport | None:
        self._today = daystart_epoch(self._db, "now", is_timestamp=False, offset=self._offset)

        history_start, forecast_stop = self._get_time_limits(limhist, limfcst)
        cache_key = self._report_cache_key(
            history_start, forecast_stop, activity_type, current_deck_only
        )
        signature = cache_signature or self.cache_signature(current_deck_only)
        cached = self._report_cache.get(cache_key)
        if cached and cached.signature == signature:
            # #171/#179 — גם ב-cache בזיכרון מחזירים את מזהי התחזית התואמים לחתימה הנוכחית בלבד.
            self._last_forecast_card_ids = {day: set(cids) for day, cids in cached.forecast_card_ids.items()}
            self._log_cache_source("memory-hit", current_deck_only)
            return cached.report

        # #171/#179 — cache JSON בפרופיל מונע חישוב מלא של revlog בכל פתיחת מסך כאשר אין שינוי בכרטיסים/חזרות.
        persistent_cached = self._load_persistent_report(cache_key, signature)
        if persistent_cached is not None:
            activity_report, forecast_card_ids = persistent_cached
            self._last_forecast_card_ids = forecast_card_ids
            self._report_cache[cache_key] = _ReportCacheEntry(signature, activity_report, forecast_card_ids)
            self._log_cache_source("persistent-hit", current_deck_only)
            return activity_report

        indexed_cached = self._try_report_from_card_index(
            forecast_stop=forecast_stop,
            current_deck_only=current_deck_only,
        )
        if indexed_cached is not None:
            activity_report, forecast_card_ids = indexed_cached
            self._last_forecast_card_ids = forecast_card_ids
            self._report_cache[cache_key] = _ReportCacheEntry(signature, activity_report, forecast_card_ids)
            self._save_persistent_report(cache_key, signature, activity_report, forecast_card_ids)
            self._log_cache_source("card-index-hit", current_deck_only)
            return activity_report

        if activity_type == ActivityType.reviews:
            self._log_cache_source("full-recompute", current_deck_only)
            revlog_rows = self._load_revlog_rows(current_deck_only)
            activity_report = self._cards_done(
                start=history_start,
                stop=forecast_stop,
                current_deck_only=current_deck_only,
                revlog_rows=revlog_rows,
            )
        else:
            raise NotImplementedError(
                f"activity type {activity_type} not implemented"
            )

        # #171/#179 — לאחר חישוב אמיתי שומרים גם בזיכרון וגם בקובץ פרופיל עד שהחתימה מצביעה על שינוי רלוונטי.
        forecast_card_ids = {day: set(cids) for day, cids in self._last_forecast_card_ids.items()}
        self._report_cache[cache_key] = _ReportCacheEntry(signature, activity_report, forecast_card_ids)
        self._save_persistent_report(cache_key, signature, activity_report, forecast_card_ids)
        self._save_card_index_snapshot(
            activity_report, current_deck_only=current_deck_only, revlog_rows=revlog_rows
        )
        return activity_report

    def cache_signature(self, current_deck_only: bool = False) -> tuple[object, ...]:
        offset = self._offset
        self._today = daystart_epoch(self._db, "now", is_timestamp=False, offset=offset)
        dids = self.__get_active_deck_ids() if current_deck_only else []
        deck_key = tuple(dids)
        revlog_limit = self._revlog_limit(current_deck_only)
        revlog_row = self._db.first(
            f"select count(), coalesce(max(id), 0) from revlog {revlog_limit}"
        ) or (0, 0)

        cards_sql = (
            "select count(), coalesce(max(mod), 0), coalesce(max(usn), 0), "
            "coalesce(sum(queue), 0), coalesce(sum(due), 0), "
            "coalesce(sum(odue), 0), coalesce(sum(odid), 0), "
            "coalesce(sum(did), 0) from cards where queue != -1"
        )
        if current_deck_only:
            cards_sql += f" and (did in {ids2str(dids)} or (odid != 0 and odid in {ids2str(dids)}))"
        cards_row = self._db.first(cards_sql) or (0, 0, 0, 0, 0, 0, 0, 0)

        # #179 — מזהה האוסף נכנס לחתימה כדי ש-cache מפרופיל/אוסף אחר לא ייחשב תקף.
        # #199 — שינוי בלוג השהיה/הטמנה פוסל cache כדי שספירת פעילות תחושב מחדש.
        self._exam_revlog_times = self._load_exam_revlog_times()
        return (self._CALC_VERSION, self._collection_identity, self._today, offset, deck_key, tuple(revlog_row), tuple(cards_row), self._suspension_log_signature(), len(self._exam_revlog_times))

    def _log_cache_source(self, source: str, current_deck_only: bool) -> None:
        # #244 — לוג פנימי בלבד; אין print ל-stdout כדי לא להציף את קונסול המשתמש.
        _heatmap_logger.debug(f"review_heatmap_cache source={source} current_deck_only={current_deck_only}")

    def _suspension_log_signature(self) -> tuple[int, int, int]:
        try:
            from .suspension_log import log_signature

            return log_signature()
        except Exception:
            return (0, 0, 0)

    def _ignored_scheduled_days_by_card(self) -> dict[int, set[int]]:
        try:
            from .suspension_log import ignored_scheduled_days_by_card

            return ignored_scheduled_days_by_card()
        except Exception as err:
            _heatmap_logger.error("heatmap_suspension_log_load_error: %s", err)
            return {}

    def invalidate_cache(self):
        self._report_cache.clear()

    def _report_cache_key(
            self,
            history_start: int | None,
            forecast_stop: int | None,
            activity_type: ActivityType,
            current_deck_only: bool,
    ) -> tuple[object, ...]:
        synced_config = self._config["synced"]
        deck_key = tuple(self.__get_active_deck_ids()) if current_deck_only else ()
        return (
            activity_type.value,
            self._collection_identity,
            history_start,
            forecast_stop,
            current_deck_only,
            deck_key,
            self._today,
            self._offset,
            bool(synced_config.get("limresched")),
            tuple(synced_config.get("limdecks") or ()),
        )

    def _persistent_cache_path(self) -> Path | None:
        # #171/#179 — הקובץ נשמר בתיקיית הפרופיל של Anki, כך שכל פרופיל מקבל cache נפרד משלו.
        with contextlib.suppress(Exception):
            profile_folder = mw.pm.profileFolder()
            if profile_folder:
                return Path(profile_folder) / "review_heatmap_activity_cache.json"
        return None

    def _persistent_card_index_path(self) -> Path | None:
        with contextlib.suppress(Exception):
            profile_folder = mw.pm.profileFolder()
            if profile_folder:
                return Path(profile_folder) / "review_heatmap_card_index_cache.json"
        return None

    @staticmethod
    def _json_stable(value: object) -> object:
        if isinstance(value, tuple):
            return [ActivityReporter._json_stable(item) for item in value]
        if isinstance(value, list):
            return [ActivityReporter._json_stable(item) for item in value]
        if isinstance(value, dict):
            return {str(key): ActivityReporter._json_stable(val) for key, val in value.items()}
        return value

    @classmethod
    def _cache_id(cls, value: object) -> str:
        # #171/#179 — מפתח יציב ל-JSON מאפשר להשוות tuples של Python בלי להסתמך על repr תלוי גרסה.
        return json.dumps(cls._json_stable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _stats_to_json(stats: StatsReport) -> dict[str, int]:
        return {
            "streak_max": int(stats.streak_max.value),
            "streak_cur": int(stats.streak_cur.value),
            "pct_days_active": int(stats.pct_days_active.value),
            "activity_daily_avg": int(stats.activity_daily_avg.value),
        }

    @staticmethod
    def _stats_from_json(data: dict[str, object]) -> StatsReport:
        return StatsReport(
            streak_max=StatsEntryStreak(value=int(data.get("streak_max") or 0)),
            streak_cur=StatsEntryStreak(value=int(data.get("streak_cur") or 0)),
            pct_days_active=StatsEntryPercentage(value=int(data.get("pct_days_active") or 0)),
            activity_daily_avg=StatsEntryCards(value=int(data.get("activity_daily_avg") or 0)),
        )

    @classmethod
    def _report_to_json(cls, report: ActivityReport | None) -> dict[str, object] | None:
        if report is None:
            return None
        return {
            "activity": {str(day): list(values) for day, values in report.activity.items()},
            "start": report.start,
            "stop": report.stop,
            "today": report.today,
            "offset": report.offset,
            "stats": cls._stats_to_json(report.stats),
            "holy_days": list(report.holy_days or []),
            "hatch_days": list(report.hatch_days or []),
        }

    @classmethod
    def _report_from_json(cls, data: dict[str, object] | None) -> ActivityReport | None:
        if data is None:
            return None
        activity_raw = data.get("activity") or {}
        if not isinstance(activity_raw, dict):
            activity_raw = {}
        activity = {
            int(day): list(values)
            for day, values in activity_raw.items()
            if isinstance(values, list)
        }
        stats_raw = data.get("stats") or {}
        return ActivityReport(
            activity=activity,
            start=data.get("start"),
            stop=data.get("stop"),
            today=int(data.get("today") or 0),
            offset=int(data.get("offset") or 0),
            stats=cls._stats_from_json(stats_raw if isinstance(stats_raw, dict) else {}),
            holy_days=[int(day) for day in (data.get("holy_days") or [])],
            hatch_days=[int(day) for day in (data.get("hatch_days") or [])],
        )

    @staticmethod
    def _forecast_to_json(forecast_card_ids: dict[int, set[int]]) -> dict[str, list[int]]:
        return {str(day): sorted(int(cid) for cid in cids) for day, cids in forecast_card_ids.items()}

    @staticmethod
    def _forecast_from_json(data: dict[str, object] | None) -> dict[int, set[int]]:
        if not isinstance(data, dict):
            return {}
        return {int(day): {int(cid) for cid in cids} for day, cids in data.items() if isinstance(cids, list)}

    def _load_persistent_report(
            self,
            cache_key: tuple[object, ...],
            signature: tuple[object, ...],
    ) -> tuple[ActivityReport | None, dict[int, set[int]]] | None:
        path = self._persistent_cache_path()
        if not path or not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("version") != PERSISTENT_CACHE_VERSION:
                return None
            cache_id = self._cache_id(cache_key)
            signature_id = self._cache_id(signature)
            for entry in payload.get("entries") or []:
                if entry.get("cache_key") == cache_id and entry.get("signature") == signature_id:
                    # #171/#179 — רק חתימה זהה מוחזרת מהקובץ; שינוי revlog/cards יגרום חישוב מחדש ושכתוב cache.
                    return (
                        self._report_from_json(entry.get("report")),
                        self._forecast_from_json(entry.get("forecast_card_ids")),
                    )
        except Exception as err:
            _heatmap_logger.error("heatmap_persistent_cache_load_error: %s", err)
        return None

    def _save_persistent_report(
            self,
            cache_key: tuple[object, ...],
            signature: tuple[object, ...],
            report: ActivityReport | None,
            forecast_card_ids: dict[int, set[int]],
    ) -> None:
        path = self._persistent_cache_path()
        if not path:
            return
        try:
            cache_id = self._cache_id(cache_key)
            payload: dict[str, object] = {"version": PERSISTENT_CACHE_VERSION, "entries": []}
            if path.exists():
                with contextlib.suppress(Exception):
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                    if loaded.get("version") == PERSISTENT_CACHE_VERSION:
                        payload = loaded
            # #171/#179 — אם קובץ ה-cache נפגם חלקית, מדלגים על entries שאינם dict במקום להפיל את שמירת cache חדשה.
            old_entries = [entry for entry in (payload.get("entries") or []) if isinstance(entry, dict) and entry.get("cache_key") != cache_id]
            # #171/#179 — שומרים מספר קטן של חתימות אחרונות כדי לתמוך במעבר בין מצב כל החפיסות/חפיסה נוכחית בלי קובץ ענק.
            payload["entries"] = [
                {
                    "cache_key": cache_id,
                    "signature": self._cache_id(signature),
                    "report": self._report_to_json(report),
                    "forecast_card_ids": self._forecast_to_json(forecast_card_ids),
                },
                *old_entries[:MAX_PERSISTENT_CACHE_ENTRIES - 1],
            ]
            path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        except Exception as err:
            _heatmap_logger.error("heatmap_persistent_cache_save_error: %s", err)

    def _card_index_key(self, current_deck_only: bool) -> str:
        synced_config = self._config["synced"]
        deck_key = tuple(self.__get_active_deck_ids()) if current_deck_only else ()
        return self._cache_id((
            self._collection_identity,
            self._offset,
            current_deck_only,
            deck_key,
            bool(synced_config.get("limresched")),
            tuple(synced_config.get("limdecks") or ()),
            self._suspension_log_signature(),
        ))

    def _revlog_cid_limit(self, current_deck_only: bool, cids: list[int] | set[int]) -> str:
        cid_filter = f"cid in {ids2str(list(cids))}"
        base_limit = self._revlog_limit(current_deck_only)
        if base_limit:
            return f"{base_limit} and {cid_filter}"
        return f"where {cid_filter}"

    def _card_due_day_epoch(self, queue: int, due: int, today: int) -> int | None:
        current_days_from_crt = self._current_sched_day()
        if queue in (2, 3):
            return today + (int(due) - current_days_from_crt) * 86400
        if queue in (1, 4) and int(due) > 1_000_000_000:
            due_ts = int(due)
            due_adj = due_ts + time.localtime(due_ts).tm_gmtoff - self._offset * 3600
            return due_adj - due_adj % 86400
        return None

    def _current_card_meta_and_due(
            self,
            current_deck_only: bool,
            today: int,
    ) -> tuple[dict[int, list[int]], dict[int, int], dict[int, set[int]]]:
        cards_sql = "select id, queue, due, odue, odid, did, mod, usn from cards"
        if current_deck_only:
            dids = self.__get_active_deck_ids()
            cards_sql += f" where did in {ids2str(dids)} or (odid != 0 and odid in {ids2str(dids)})"

        cards_meta: dict[int, list[int]] = {}
        active_due_days: dict[int, int] = {}
        due_card_ids_by_day: dict[int, set[int]] = {}
        for cid, queue, due, odue, odid, did, mod, usn in self._db.all(cards_sql):
            cid = int(cid)
            queue = int(queue)
            due = int(due or 0)
            odue = int(odue or 0)
            odid = int(odid or 0)
            cards_meta[cid] = [queue, due, odue, odid, int(did or 0), int(mod or 0), int(usn or 0)]
            if queue == -1:
                continue
            effective_due = odue if odid != 0 and odue != 0 else due
            due_day = self._card_due_day_epoch(queue, effective_due, today)
            if due_day is not None:
                active_due_days[cid] = due_day
                due_card_ids_by_day.setdefault(due_day, set()).add(cid)
        return cards_meta, active_due_days, due_card_ids_by_day

    def _day_from_revlog_id(self, rid: int) -> int:
        ts = int(str(int(rid))[:10])
        adjusted = ts + time.localtime(ts).tm_gmtoff - self._offset * 3600
        return adjusted - adjusted % 86400

    @staticmethod
    def _completion_percentage(completed: int, scheduled: int) -> float:
        return max(0, min(100, round(100 * completed / scheduled, 1))) if scheduled else 0

    @staticmethod
    def _add_card_activity(
            activity: dict[int, list[int]],
            day: int,
            sch: int = 0,
            new: int = 0,
            ans: int = 0,
            cards: int = 0,
            done: int = 0,
    ) -> None:
        entry = activity.setdefault(int(day), [0, 0, 0, 0, 0])
        entry[0] += int(sch)
        entry[1] += int(new)
        entry[2] += int(ans)
        entry[3] += int(cards)
        entry[4] += int(done)

    def _card_contribution_from_rows(
            self,
            rows: list[tuple],
            due_day: int | None,
            today: int,
            ignored_days: set[int] | None = None,
    ) -> dict[int, list[int]]:
        activity: dict[int, list[int]] = {}
        ignored_days = ignored_days or set()
        is_active = due_day is not None
        last_rid_day = 0
        last_next_sch = 0
        saw_real_review = False
        scheduled_days: set[int] = set()
        done_days: set[int] = set()

        def add_scheduled_day(day: int, completed: bool = False) -> None:
            if day in ignored_days:
                return
            scheduled_days.add(day)
            if completed:
                done_days.add(day)

        def add_scheduled_interval(start_day: int, end_day: int, require_active: bool, completed_day: int | None = None) -> None:
            if start_day <= 0:
                return
            if require_active and not is_active:
                return
            for day in range(start_day, end_day + 86400, 86400):
                if day <= today:
                    add_scheduled_day(day, completed=day == completed_day)

        def close_open_card(next_sch: int) -> None:
            # Resolve the open schedule before checking the historical marker:
            # an initial learning step or reset may have cleared that marker.
            scheduled_day = due_day if is_active else next_sch
            if scheduled_day is None or scheduled_day <= 0:
                return
            if next_sch == 0 and last_rid_day > 0:
                # First introduction is not a scheduled review, but subsequent
                # overdue days must not disappear together with that first day.
                scheduled_day = max(scheduled_day, last_rid_day + 86400)
            if scheduled_day <= today:
                add_scheduled_interval(scheduled_day, today, require_active=True)

        for review in rows:
            rid = int(review[0])
            day = self._day_from_revlog_id(rid)
            ivl = int(review[4])
            time_ms = int(review[7])
            review_type = int(review[8])

            if review_type == 4 and ivl == 0 and last_next_sch > 0:
                add_scheduled_interval(last_next_sch, day, require_active=False)
                last_rid_day = 0
                last_next_sch = 0
                continue
            # #304 — תזמון ידני עם time > 0 (או זמן שמור בפרופיל) נספר כחזרה אמיתית
            if time_ms == 0 and not self._exam_time_for(rid):
                continue

            is_first_review = not saw_real_review
            if is_first_review:
                self._add_card_activity(activity, day, new=1, cards=1)
                saw_real_review = True
            else:
                self._add_card_activity(activity, day, ans=1)
                if last_rid_day != day:
                    self._add_card_activity(activity, day, cards=1)
                if last_next_sch > 0:
                    add_scheduled_interval(last_next_sch, day, require_active=False, completed_day=day)

            last_rid_day = day
            last_next_sch = day + ivl * 86400 if ivl > 0 else day
            if is_first_review and last_next_sch == day:
                last_next_sch = 0

        if saw_real_review:
            close_open_card(last_next_sch)
        elif is_active and due_day is not None and due_day <= today:
            # כרטיס פעיל שבאיחור אך ללא revlog (למשל פתק משוכפל) צריך גם
            # להיגלל ל"היום" כמו כרטיס שכן נסקר, כדי שהספירה תתאים לפרוגרסבר
            add_scheduled_interval(due_day, today, require_active=True)

        for day in scheduled_days:
            self._add_card_activity(activity, day, sch=1)
        for day in done_days:
            if day in scheduled_days:
                self._add_card_activity(activity, day, done=1)

        return activity

    @staticmethod
    def _activity_to_json(activity: dict[int, list[int]]) -> dict[str, list[int]]:
        return {str(day): [int(v) for v in values] for day, values in activity.items() if any(values)}

    @staticmethod
    def _activity_from_json(data: object) -> dict[int, list[int]]:
        if not isinstance(data, dict):
            return {}
        result: dict[int, list[int]] = {}
        for day, values in data.items():
            if isinstance(values, list):
                padded = [int(v or 0) for v in values[:5]]
                while len(padded) < 5:
                    padded.append(0)
                result[int(day)] = padded
        return result

    def _load_revlog_rows(self, current_deck_only: bool) -> list[tuple]:
        # One report-local snapshot, shared by the full calculation and index writer.
        # Explicit columns preserve the positional contract used by both consumers.
        return self._db.all(
            "select id, cid, usn, ease, ivl, lastIvl, factor, time, type from revlog "
            f"{self._revlog_limit(current_deck_only)} order by cid, id"
        )

    def _save_card_index_snapshot(
            self,
            report: ActivityReport | None,
            current_deck_only: bool,
            revlog_rows: list[tuple] | None = None,
    ) -> None:
        # אישיו #421: reporter של פרופיל קודם אינו נוגע ב-DB אחרי שהאוסף הוחלף או נסגר.
        if getattr(mw, "col", None) is not self._col:
            return
        path = self._persistent_card_index_path()
        if not path or report is None or not report.start:
            return
        try:
            today = self._today
            cards_meta, active_due_days, _due_ids = self._current_card_meta_and_due(current_deck_only, today)
            rows = revlog_rows if revlog_rows is not None else self._load_revlog_rows(current_deck_only)
            revlog_row = (len(rows), max((int(row[0]) for row in rows), default=0))
            rows_by_cid: dict[int, list[tuple]] = {}
            for row in rows:
                rows_by_cid.setdefault(int(row[1]), []).append(row)
            ignored_by_card = self._ignored_scheduled_days_by_card()

            card_contribs: dict[str, dict[str, object]] = {}
            for cid in sorted(set(cards_meta) | set(rows_by_cid)):
                cid_rows = rows_by_cid.get(cid, [])
                contribution = self._card_contribution_from_rows(
                    cid_rows, active_due_days.get(cid), today, ignored_by_card.get(cid)
                )
                card_contribs[str(cid)] = {
                    "activity": self._activity_to_json(contribution),
                    "has_revlog": bool(cid_rows),
                }

            payload = {
                "version": PERSISTENT_CARD_INDEX_VERSION,
                "key": self._card_index_key(current_deck_only),
                "today": today,
                "revlog_count": int(revlog_row[0] or 0),
                "revlog_max_id": int(revlog_row[1] or 0),
                "cards_meta": {str(cid): meta for cid, meta in cards_meta.items()},
                "card_contribs": card_contribs,
            }
            path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        except Exception as err:
            # אישיו #421: Anki עשוי לעטוף CollectionNotOpen בסוג חריגה כללי.
            if "CollectionNotOpen" not in f"{type(err).__name__}: {err}":
                _heatmap_logger.error("heatmap_card_index_save_error: %s", err)

    def _load_card_index_payload(self, current_deck_only: bool) -> dict[str, object] | None:
        path = self._persistent_card_index_path()
        if not path or not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("version") != PERSISTENT_CARD_INDEX_VERSION:
                return None
            if payload.get("key") != self._card_index_key(current_deck_only):
                return None
            return payload
        except Exception as err:
            _heatmap_logger.error("heatmap_card_index_load_error: %s", err)
            return None

    def _recompute_changed_card_contribs(
            self,
            card_contribs: dict[str, dict[str, object]],
            changed_cids: set[int],
            active_due_days: dict[int, int],
            today: int,
            current_deck_only: bool,
    ) -> None:
        if not changed_cids:
            return
        ignored_by_card = self._ignored_scheduled_days_by_card()
        # Bound IN clauses while keeping each card's complete history ordered by id.
        ordered_cids = sorted(changed_cids)
        for start in range(0, len(ordered_cids), 500):
            batch = ordered_cids[start:start + 500]
            rows = self._db.all(
                "select id, cid, usn, ease, ivl, lastIvl, factor, time, type from revlog "
                f"{self._revlog_cid_limit(current_deck_only, batch)} order by cid, id"
            )
            rows_by_cid: dict[int, list[tuple]] = {}
            for row in rows:
                rows_by_cid.setdefault(int(row[1]), []).append(row)
            for cid in batch:
                cid_rows = rows_by_cid.get(cid, [])
                contribution = self._card_contribution_from_rows(
                    cid_rows,
                    active_due_days.get(cid),
                    today,
                    ignored_by_card.get(cid),
                )
                card_contribs[str(cid)] = {
                    "activity": self._activity_to_json(contribution),
                    "has_revlog": bool(cid_rows),
                }

    def _extend_unchanged_cards_to_today(
            self,
            card_contribs: dict[str, dict[str, object]],
            unchanged_cids: set[int],
            active_due_days: dict[int, int],
            old_today: int,
            today: int,
    ) -> None:
        if today <= old_today:
            return
        ignored_by_card = self._ignored_scheduled_days_by_card()
        for cid in unchanged_cids:
            due_day = active_due_days.get(cid)
            if due_day is None or due_day > today:
                continue
            raw = card_contribs.setdefault(str(cid), {"activity": {}})
            activity = self._activity_from_json(raw.get("activity"))
            ignored_days = ignored_by_card.get(cid, set())
            for day in range(max(due_day, old_today + 86400), today + 86400, 86400):
                if day not in ignored_days:
                    self._add_card_activity(activity, day, sch=1)
            raw["activity"] = self._activity_to_json(activity)

    def _report_from_card_index_payload(
            self,
            payload: dict[str, object],
            forecast_stop: int | None,
            active_due_days: dict[int, int],
            due_card_ids_by_day: dict[int, set[int]],
            today: int,
            persist_today: bool = True,
    ) -> tuple[ActivityReport | None, dict[int, set[int]]] | None:
        card_contribs = payload.get("card_contribs")
        if not isinstance(card_contribs, dict):
            return None

        all_days: set[int] = set()
        aggregate: dict[int, dict[str, int]] = {}
        for raw in card_contribs.values():
            if not isinstance(raw, dict):
                continue
            activity = self._activity_from_json(raw.get("activity"))
            for day, values in activity.items():
                all_days.add(day)
                entry = aggregate.setdefault(day, {"sch": 0, "new": 0, "ans": 0, "precent": 0, "cards": 0, "done": 0})
                entry["sch"] += values[0]
                entry["new"] += values[1]
                entry["ans"] += values[2]
                entry["cards"] += values[3]
                entry["done"] += values[4]

        if not all_days and not active_due_days:
            self._last_forecast_card_ids = {}
            return None

        start_day_epoch = min(all_days) if all_days else today
        end_day_epoch = max(today, max(active_due_days.values(), default=today))
        if forecast_stop is not None:
            end_day_epoch = max(today, min(end_day_epoch, int(forecast_stop)))

        review_dates_log: dict[int, dict[str, int] | tuple] = {}
        for day in range(start_day_epoch, end_day_epoch + 86400 + 86400, 86400):
            review_dates_log[day] = {"sch": 0, "new": 0, "ans": 0, "precent": 0, "cards": 0, "done": 0}
        for day, values in aggregate.items():
            if day in review_dates_log and isinstance(review_dates_log[day], dict):
                review_dates_log[day].update(values)

        forecast_card_ids: dict[int, set[int]] = {}
        for due_day, cids in due_card_ids_by_day.items():
            if due_day < start_day_epoch or due_day > end_day_epoch:
                continue
            forecast_card_ids[due_day] = set(cids)
            if due_day > today and due_day in review_dates_log and isinstance(review_dates_log[due_day], dict):
                review_dates_log[due_day]["sch"] -= len(cids)

        holy_days_local_sec, hatch_days_local_sec, no_break_days = special_days_for_range(
            start_day_epoch, end_day_epoch
        )

        todays_revlog = review_dates_log.get(today, {})
        streak_max = 0
        current = 0
        days_learned = 0
        total_learned_cards = 0
        for day, raw in list(review_dates_log.items()):
            if not isinstance(raw, dict):
                continue
            if day <= today:
                sch = raw["sch"]
                if day == today and persist_today:
                    sch = self._persist_today_sch(today, sch)
                    raw["sch"] = sch
                # #208 - first reviews are real work today; count them in answered totals while keeping the separate breakdown.
                answered_total = raw["ans"] + raw["new"]
                done_total = min(raw["done"], sch) if sch > 0 else 0
                raw["done"] = done_total
                precent = self._completion_percentage(done_total, sch)
                raw["precent"] = max(0, min(100, precent))
                raw["ans"] = answered_total
                if answered_total > 0:
                    current += 1
                    days_learned += 1
                    total_learned_cards += answered_total
                    streak_max = max(streak_max, current)
                elif day not in no_break_days:
                    current = 0
                review_dates_log[day] = tuple(raw.values())
            else:
                sch_val = raw["sch"] if raw["sch"] < 0 else None
                review_dates_log[day] = (sch_val, None, sch_val, sch_val, None, None)

        if (
            isinstance(todays_revlog, dict)
            and todays_revlog.get("ans") == 0
            and todays_revlog.get("new") == 0
        ):
            sch_val = -int(todays_revlog.get("sch") or 0)
            value = sch_val if sch_val < 0 else None
            review_dates_log[today] = (value, None, value, value, None, None)

        avg_cur = int(round(max(total_learned_cards, 0) / max(days_learned, 1)))
        days_total = (today - start_day_epoch) / 86400 + 1
        pdays = 100 if days_total == 1 else int(round(max(days_learned, 1) / max(days_total, 1) * 100))

        report = ActivityReport(
            activity=review_dates_log,
            start=start_day_epoch * 1000 if start_day_epoch else None,
            stop=end_day_epoch * 1000 if end_day_epoch else None,
            today=today * 1000,
            offset=self._offset,
            stats=StatsReport(
                streak_max=StatsEntryStreak(value=streak_max),
                streak_cur=StatsEntryStreak(value=current),
                pct_days_active=StatsEntryPercentage(value=pdays),
                activity_daily_avg=StatsEntryCards(value=avg_cur),
            ),
            holy_days=holy_days_local_sec,
            hatch_days=hatch_days_local_sec,
        )
        return report, forecast_card_ids

    def _try_report_from_card_index(
            self,
            forecast_stop: int | None,
            current_deck_only: bool,
    ) -> tuple[ActivityReport | None, dict[int, set[int]]] | None:
        payload = self._load_card_index_payload(current_deck_only)
        if payload is None:
            return None
        try:
            today = self._today
            old_today = int(payload.get("today") or 0)
            if old_today <= 0 or today < old_today:
                return None

            cards_meta, active_due_days, due_card_ids_by_day = self._current_card_meta_and_due(current_deck_only, today)
            old_cards_meta_raw = payload.get("cards_meta") or {}
            if not isinstance(old_cards_meta_raw, dict):
                return None
            old_cards_meta = {int(cid): list(meta) for cid, meta in old_cards_meta_raw.items() if isinstance(meta, list)}
            changed_cids = {
                cid for cid, meta in cards_meta.items()
                if old_cards_meta.get(cid) != meta
            }
            changed_cids.update(set(old_cards_meta) - set(cards_meta))

            revlog_limit = self._revlog_limit(current_deck_only)
            revlog_row = self._db.first(
                f"select count(), coalesce(max(id), 0) from revlog {revlog_limit}"
            ) or (0, 0)
            new_revlog_count = int(revlog_row[0] or 0)
            new_revlog_max = int(revlog_row[1] or 0)
            old_revlog_count = int(payload.get("revlog_count") or 0)
            old_revlog_max = int(payload.get("revlog_max_id") or 0)
            if new_revlog_count < old_revlog_count or new_revlog_max < old_revlog_max:
                return None
            if new_revlog_max > old_revlog_max:
                new_rows_limit = self._revlog_limit(current_deck_only)
                where_prefix = "and" if new_rows_limit else "where"
                rows = self._db.all(
                    f"select distinct cid from revlog {new_rows_limit} {where_prefix} id > ?",
                    old_revlog_max,
                )
                changed_cids.update(int(row[0]) for row in rows)
            elif new_revlog_count != old_revlog_count:
                return None

            card_contribs = payload.get("card_contribs")
            if not isinstance(card_contribs, dict):
                return None
            self._recompute_changed_card_contribs(
                card_contribs, changed_cids, active_due_days, today, current_deck_only
            )
            unchanged_cids = set(cards_meta) - changed_cids
            self._extend_unchanged_cards_to_today(
                card_contribs, unchanged_cids, active_due_days, old_today, today
            )

            payload["today"] = today
            payload["revlog_count"] = new_revlog_count
            payload["revlog_max_id"] = new_revlog_max
            payload["cards_meta"] = {str(cid): meta for cid, meta in cards_meta.items()}
            payload["card_contribs"] = card_contribs

            result = self._report_from_card_index_payload(
                payload, forecast_stop, active_due_days, due_card_ids_by_day, today
            )
            if result is None:
                return None
            path = self._persistent_card_index_path()
            if path:
                path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            return result
        except Exception as err:
            # סבב 9 — a profile switch can close the old collection between
            # reading the JSON index and querying changed cards. This is a
            # normal cancellation, not a heatmap error worth showing/logging.
            if "CollectionNotOpen" not in type(err).__name__:
                _heatmap_logger.error("heatmap_card_index_update_error: %s", err)
            return None

    def set_collection(self, col: "Collection"):
        # NOTE: Binding the collection is dangerous if we ever persist ActivityReporter
        # across profile reloads, so allow outside callers to update the collection
        # if necessary

        if not col or not col.db:
            raise CollectionError("Anki collection and/or database is not ready")

        self._col = col
        self._db = col.db
        self._collection_identity = self._make_collection_identity(col)
        self._report_cache = {}

    @staticmethod
    def _make_collection_identity(col: "Collection") -> tuple[object, ...]:
        path = getattr(col, "path", None) or getattr(getattr(col, "db", None), "_path", None)
        crt = getattr(col, "crt", None)
        # #179 — חתימת cache מתמשך צריכה להיות יציבה בין הפעלות; נתיב האוסף וזמן היצירה מספיקים להפרדה בין פרופילים/אוספים.
        stable_identity = (str(path) if path else None, int(crt) if crt else None)
        if any(stable_identity):
            return stable_identity
        return (id(getattr(col, "db", None)),)

    def collection_matches(self, col: "Collection") -> bool:
        return self._collection_identity == self._make_collection_identity(col)

    def get_last_forecast_card_ids(self) -> dict[int, list[int]]:
        return {day: sorted(cids) for day, cids in self._last_forecast_card_ids.items()}

    # Activity calculations
    #########################################################################

    # Collection properties
    #########################################################################

    @property
    def _sched_ver(self) -> Literal[1, 2, 3]:
        try:
            if self._col.v3_scheduler():
                return 3
        except AttributeError:
            pass
        try:
            return self._col.sched_ver()
        except AttributeError:
            return self._col.schedVer()

    @property
    def _offset(self) -> int:
        """
        Return daily scheduling cutoff time in hours
        """
        if self._sched_ver >= 2:
            rollover = self._col.conf.get("rollover", 4)
            return rollover

        creation_time = self._collection_creation_time()
        if creation_time:
            start_date = datetime.datetime.fromtimestamp(creation_time)
            return start_date.hour
        return 4

    def _collection_creation_time(self) -> int | None:
        creation_time = getattr(self._col, "crt", None)
        if creation_time:
            return int(creation_time)
        with contextlib.suppress(Exception):
            row = self._db.first("select crt from col")
            if row and row[0]:
                return int(row[0])
        return None

    def _current_sched_day(self) -> int:
        with contextlib.suppress(Exception):
            return int(self._col.sched.today)
        creation_time = self._collection_creation_time()
        if creation_time:
            return int((self._today - creation_time) // 86400)
        return 0



    def _get_time_limits(
            self, limhist: int | None = None, limfcst: int | None = None
    ) -> tuple[int | None, int | None]:

        conf = self._config["synced"]

        history_start: int | None
        forecast_stop: int | None

        if limhist is not None:
            history_start = self._days_from_today(-limhist)
        else:
            history_start = self._get_conf_history_limit(
                conf["limhist"], conf["limdate"]
            )

        if limfcst is not None:
            forecast_stop = self._days_from_today(limfcst)
        else:
            forecast_stop = self._get_conf_forecast_limit(conf["limfcst"])

        return (history_start, forecast_stop)

    def _get_conf_history_limit(
            self, limit_days: int | None, limit_date: int | None
    ) -> int | None:

        if limit_days is None and limit_date is None:
            return None

        limit_days_date = self._days_from_today(-limit_days) if limit_days else 0

        limit_date = daystart_epoch(self._db, str(limit_date)) if limit_date else None

        # be defensive as col.crt can be absent in newer Anki builds
        creation_time = self._collection_creation_time()

        if (
                not limit_date
                or not creation_time
                or limit_date == daystart_epoch(self._db, creation_time)
        ):
            # ignore zero value or default value
            limit_date = 0
        else:
            limit_date = limit_date

        # choose most restricting limit
        return max(limit_days_date, limit_date) or None

    def _get_conf_forecast_limit(self, limit_days: int) -> int:
        limit_days = limit_days or MAX_FORECAST_DAYS
        return self._days_from_today(limit_days)

    def _days_from_today(self, days: int) -> int:
        return self._today + 86400 * days

    # Deck limits
    #########################################################################

    def _valid_decks(self, excluded: list[DeckId]) -> list[DeckId]:
        deck_manager = self._col.decks
        all_excluded = []

        for did in excluded:
            try:
                children = [d[1] for d in deck_manager.children(did)]
            except NotFoundError:  # 2.1.28+
                continue
            all_excluded.extend(children)

        all_excluded.extend(excluded)

        return [d["id"] for d in self._col.decks.all() if d["id"] not in all_excluded]


    def _revlog_limit(self, current_deck_only: bool) -> str:
        if not current_deck_only:
                return ""
        dids = self.__get_active_deck_ids()
        return f"where cid IN (SELECT id FROM cards WHERE did IN {ids2str(dids)})"

    def __get_active_deck_ids(self) -> list["DeckId"]:
        deck_manager = self._col.decks
        try:
            selected_deck = deck_manager.get_current_id()
        except AttributeError:
            selected_deck = deck_manager.selected()
        active_deck_ids = deck_manager.deck_and_child_ids(selected_deck)
        return active_deck_ids

    # Other settings affecting included revlog entries
    #########################################################################


    # Database queries for user activity
    #########################################################################

    def _cards_done(
            self,
            start: int | None = None,
            stop: int | None = None,
            current_deck_only: bool = False,
            revlog_rows: list[tuple] | None = None,
            scheduled_ids: dict[int, set[int]] | None = None,
            persist_today: bool = True,
    ) -> ActivityReport | None:
        """Aggregate the same per-card history rules used by incremental updates.

        Identifier capture is opt-in for manual diagnostics/tests, never retained
        in normal rendering. Diagnostics can also disable profile persistence.
        """
        today = self._today
        streak_max = current = days_learned = total_learned_cards = 0
        days_before_today = -1
        rows = revlog_rows if revlog_rows is not None else self._load_revlog_rows(current_deck_only)
        _, active_due_days, current_due_card_ids_by_day = self._current_card_meta_and_due(current_deck_only, today)
        rows_by_cid: dict[int, list[tuple]] = {}
        for row in rows:
            rows_by_cid.setdefault(int(row[1]), []).append(row)
        ignored_by_card = self._ignored_scheduled_days_by_card()
        aggregate: dict[int, list[int]] = {}
        for cid in set(rows_by_cid) | set(active_due_days):
            contribution = self._card_contribution_from_rows(
                rows_by_cid.get(cid, []), active_due_days.get(cid), today, ignored_by_card.get(cid)
            )
            for day, values in contribution.items():
                total = aggregate.setdefault(day, [0, 0, 0, 0, 0])
                for index, value in enumerate(values):
                    total[index] += value
                if scheduled_ids is not None and values[0]:
                    scheduled_ids.setdefault(day, set()).add(cid)

        if not aggregate and not active_due_days:
            self._last_forecast_card_ids = {}
            return None
        start_day_epoch = min(aggregate) if aggregate else today
        end_day_epoch = max(today, max(active_due_days.values(), default=today))
        if stop is not None:
            end_day_epoch = max(today, min(end_day_epoch, int(stop)))
        review_dates_log = {
            day: {"sch": 0, "new": 0, "ans": 0, "precent": 0, "cards": 0, "done": 0}
            for day in range(start_day_epoch, end_day_epoch + 2 * 86400, 86400)
        }
        for day, values in aggregate.items():
            if day in review_dates_log:
                for field, value in zip(("sch", "new", "ans", "cards", "done"), values):
                    review_dates_log[day][field] = value
        for due_day, cids in current_due_card_ids_by_day.items():
            if today < due_day <= end_day_epoch:
                review_dates_log[due_day]["sch"] = -len(cids)

        holy_days_local_sec, hatch_days_local_sec, no_break_days = special_days_for_range(
            start_day_epoch, end_day_epoch
        )

        # שומר את התחשיב של היום לאחרי הלולאה כיון שיש הבדל אם כבר נענו היום או שעוד לא.
        try:
            todays_revlog = review_dates_log[self._today]
        except KeyError:
            todays_revlog = {}
            _heatmap_logger.warning(
                "heatmap_today_key_missing: self._today=%s not in review_dates_log keys (start=%s end=%s)",
                self._today, start_day_epoch, end_day_epoch,
            )

        for _total_days, (key, _val) in enumerate(review_dates_log.items(), start=1):
            def safe_division(n, d):
                """זיכער צעטיילן מיט נול"""
                return n / d if d else 0


            # חישוב סטטיסטיקות לסרגל שמתחת ללוח שנה וחישוב האחוזי מענה לכל יום
            if key <= self._today:  # תאריכים שעברו או היום
                if key == self._today and persist_today:
                    review_dates_log[key]["sch"] = self._persist_today_sch(self._today, review_dates_log[key]["sch"])
                # התנאי הבא נועד לפתור באג שלפעמים התוכנה מתזמנת כרטיסים להופיע לפני התאריך שאליו הם תוזמנו בפועל כך שנוצר מצב של יותר מ100% מענה
                # #208 - חזרה ראשונה נספרת כחזרה שבוצעה, ונשארת גם בפירוט "מתוכן חזרה ראשונה".
                answered_total = review_dates_log[key]["ans"] + review_dates_log[key]["new"]
                done_total = min(review_dates_log[key]["done"], review_dates_log[key]["sch"]) if review_dates_log[key]["sch"] > 0 else 0
                review_dates_log[key]["done"] = done_total
                precent = self._completion_percentage(done_total, review_dates_log[key]["sch"])
                review_dates_log[key]["precent"] = max(0, min(100, precent))
                review_dates_log[key]["ans"] = answered_total
                if answered_total > 0:
                    current += 1
                    days_before_today += 1  # לא מפריע שגם שוה להיום נספר מכיון שמתחיל ב-1
                    days_learned += 1
                    total_learned_cards += answered_total
                    # מעדכן את הרצף המקסימלי
                    if current > streak_max:
                        streak_max = current
                else:  # יום שלא היתה בו חזרה מתאפס הרצף הנוכחי
                    # תיקון #57: יום קדוש ראשון מתוך שני ימים קדושים רצופים — לא שובר רצף
                    if key not in no_break_days:
                        current = 0
                # ממיר את הערכים של היום הספציפי ממילון לרשימה
                review_dates_log[key] = tuple(review_dates_log[key].values())
            else:  # תאריכים עתידיים
                log_sch_val = review_dates_log[key]["sch"]
                log_sch_val = log_sch_val if log_sch_val < 0 else None
                # תיקון #54: log_sch_val גם ב-ans (אינדקס 2) כדי שמצב 'לפי כמות' יציג תחזית
                review_dates_log[key] = (log_sch_val,
                                                 None,
                                                 log_sch_val,
                                                 log_sch_val,
                                                 None,
                                                 None)

        if todays_revlog.get("ans") == 0 and todays_revlog.get("new") == 0:
            log_sch_val = -todays_revlog["sch"]
            _val = log_sch_val if log_sch_val < 0 else None
            # תיקון #54: _val גם ב-ans כדי שמצב 'לפי כמות' יציג תחזית
            review_dates_log[self._today] = (_val,
                                             None,
                                             _val,
                                             _val,
                                             None,
                                             None)

                # Stats: average count on days with activity
        avg_cur = int(round(max(total_learned_cards, 0) / max(days_learned, 1)))

        # Stats: percentage of days with activity
        #
        # NOTE: days_total is based on first recorded revlog entry, i.e. it is
        # not the grand total of days since collection creation date / whatever
        # history limits the user might have set. This value seems more
        # desirable and motivating than the raw percentage of days learned
        # in the date inclusion period.

        days_total = (today - start_day_epoch) / 86400 + 1

        pdays = 100 if days_total == 1 else int(round(max(days_learned, 1) / max(days_total, 1) * 100))

        self._last_forecast_card_ids = current_due_card_ids_by_day

        return ActivityReport(
            activity=review_dates_log,
            start=start_day_epoch * 1000 if start_day_epoch else None,
            stop=end_day_epoch * 1000 if end_day_epoch else None,
            today=(today * 1000),
            offset=self._offset,
            stats=StatsReport(
                streak_max=StatsEntryStreak(value=streak_max),
                streak_cur=StatsEntryStreak(value=current),
                pct_days_active=StatsEntryPercentage(value=pdays),
                activity_daily_avg=StatsEntryCards(value=avg_cur),
            ),
            holy_days=holy_days_local_sec,
            hatch_days=hatch_days_local_sec,
        )
