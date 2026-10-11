
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
Heatmap and stats elements generation
"""

import json
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

from aqt.main import AnkiQt

from .activity import ActivityReport, ActivityReporter, StatsEntry, StatsType
from .config import heatmap_modes
from .libaddon.platform import PLATFORM
from .web_content import (
    CSS_DISABLE_HEATMAP,
    CSS_DISABLE_STATS,
    CSS_MODE_PREFIX,
    CSS_PLATFORM_PREFIX,
    CSS_THEME_PREFIX,
    CSS_VIEW_PREFIX,
    HTML_HEATMAP,
    HTML_INFO_NODATA,
    HTML_LOADING,
    HTML_MAIN_ELEMENT,
    HTML_STREAK,
)

if TYPE_CHECKING:
    from .libaddon.anki.configmanager import ConfigManager


# workaround for list comprehensions not working in class-scope
def _compress_levels(colors, indices):
    return [colors[i] for i in indices]  # type: ignore


class HeatmapView(Enum):
    deckbrowser = 0
    overview = 1
    stats = 2


class _StatsVisual(NamedTuple):
    levels: list[tuple[int, str]] | None
    unit: str | None


class _RenderCache(NamedTuple):
    html: str
    arguments: tuple[HeatmapView, int | None, int | None, bool]
    deck: int
    data_signature: tuple[object, ...]
    config_signature: tuple[object, ...]


class HeatmapRenderer:

    _css_colors: tuple[str, str, str, str, str, str, str, str, str, str, str] = (
        "rh-col0",
        "rh-col11",
        "rh-col12",
        "rh-col13",
        "rh-col14",
        "rh-col15",
        "rh-col16",
        "rh-col17",
        "rh-col18",
        "rh-col19",
        "rh-col20",
    )

    _stats_formatting: dict[StatsType, _StatsVisual] = {
        StatsType.streak: _StatsVisual(
            levels=list(
                zip(
                    (0, 14, 30, 90, 180, 365),
                    _compress_levels(_css_colors, (0, 2, 4, 6, 9, 10)), strict=False,
                )
            ),
            unit="טעג",
        ),
        StatsType.percentage: _StatsVisual(
            levels=list(zip((0, 25, 50, 60, 70, 80, 85, 90, 95, 99), _css_colors, strict=False)),
            unit=None,
        ),
        StatsType.cards: _StatsVisual(levels=None, unit="קארטלעך"),
    }

    _dynamic_legend_factors: tuple[float, ...] = (
        0.125,
        0.25,
        0.5,
        0.75,
        1.0,
        1.25,
        1.5,
        2.0,
        4.0,
    )

    def __init__(self, mw: AnkiQt, reporter: ActivityReporter, config: "ConfigManager"):
        self._mw: AnkiQt = mw
        self._config: ConfigManager = config
        self._reporter: ActivityReporter = reporter
        self._render_cache: _RenderCache | None = None

    # TODO: Consider caching on the render-level

    def render(
        self,
        view: HeatmapView,
        limhist: int | None = None,
        limfcst: int | None = None,
        current_deck_only: bool = False,
    ) -> str:
        cached_html, data_signature, config_signature = self.cache_state(
            view, limhist, limfcst, current_deck_only
        )
        if cached_html is not None:
            return cached_html

        report = self._reporter.get_report(
            limhist=limhist,
            limfcst=limfcst,
            current_deck_only=current_deck_only,
            cache_signature=data_signature,
        )
        return self.render_report(
            report,
            view,
            limhist,
            limfcst,
            current_deck_only,
            data_signature,
            config_signature,
            self._current_deck_id(),
        )

    def _current_deck_id(self) -> int:
        return int(self._mw.col.decks.current()["id"])

    def cache_state(
        self,
        view: HeatmapView,
        limhist: int | None = None,
        limfcst: int | None = None,
        current_deck_only: bool = False,
    ) -> tuple[str | None, tuple[object, ...], tuple[object, ...]]:
        data_signature = self._reporter.cache_signature(current_deck_only)
        config_signature = self._config_signature(view)
        if self._render_cache and self._cache_still_valid(
            view, limhist, limfcst, current_deck_only, data_signature, config_signature
        ):
            return self._render_cache.html, data_signature, config_signature
        return None, data_signature, config_signature

    def render_loading(self, view: HeatmapView, token: str) -> str:
        classes = self._get_css_classes(view)
        return HTML_MAIN_ELEMENT.format(
            content=HTML_LOADING.format(token=token), classes=" ".join(classes)
        )

    def render_report(
        self,
        report: ActivityReport | None,
        view: HeatmapView,
        limhist: int | None,
        limfcst: int | None,
        current_deck_only: bool,
        data_signature: tuple[object, ...],
        config_signature: tuple[object, ...],
        deck_id: int,
    ) -> str:
        if report is None:
            render = HTML_MAIN_ELEMENT.format(content=HTML_INFO_NODATA, classes="")
            self.cache_html(
                render, view, limhist, limfcst, current_deck_only, data_signature, config_signature, deck_id
            )
            return render

        prefs = self._config["profile"]

        dynamic_legend = self._dynamic_legend(report.stats.activity_daily_avg.value)
        stats_legend = self._stats_legend(dynamic_legend)
        heatmap_legend = self._heatmap_legend(dynamic_legend)

        classes = self._get_css_classes(view)

        if prefs["display"][view.name]:
            heatmap = self._generate_heatmap_elm(
                report, heatmap_legend, current_deck_only
            )
        else:
            heatmap = ""
            classes.append(CSS_DISABLE_HEATMAP)

        if prefs["display"][view.name] or prefs["statsvis"]:
            stats = self._generate_stats_elm(report, stats_legend)
        else:
            stats = ""
            classes.append(CSS_DISABLE_STATS)

        if not current_deck_only:
            self._save_current_perf(report)

        render = HTML_MAIN_ELEMENT.format(
            content=heatmap + stats, classes=" ".join(classes)
        )

        self._render_cache = _RenderCache(
            html=render,
            arguments=(view, limhist, limfcst, current_deck_only),
            deck=deck_id,
            data_signature=data_signature,
            config_signature=config_signature,
        )

        return render

    def cache_html(
        self,
        html: str,
        view: HeatmapView,
        limhist: int | None,
        limfcst: int | None,
        current_deck_only: bool,
        data_signature: tuple[object, ...],
        config_signature: tuple[object, ...],
        deck_id: int,
    ) -> None:
        self._render_cache = _RenderCache(
            html=html,
            arguments=(view, limhist, limfcst, current_deck_only),
            deck=deck_id,
            data_signature=data_signature,
            config_signature=config_signature,
        )

    def set_activity_reporter(self, reporter: ActivityReporter):
        self._reporter = reporter

    def set_collection(self, col) -> None:
        # #179 — כאשר עוברים פרופיל, הרנדרר הקיים מקבל אוסף חדש ומוחק HTML/cache ישנים.
        if not self._reporter.collection_matches(col):
            self._reporter.set_collection(col)
            self._render_cache = None

    def invalidate_cache(self):
        self._render_cache = None
        self._reporter.invalidate_cache()

    def _cache_still_valid(
        self,
        view,
        limhist,
        limfcst,
        current_deck_only,
        data_signature,
        config_signature,
    ) -> bool:
        # FIXME: for 2.1.28+
        cache = self._render_cache
        if not cache:
            return False
        return (
            data_signature == cache.data_signature
            and config_signature == cache.config_signature
            and (view, limhist, limfcst, current_deck_only) == cache.arguments  # type: ignore
            and (not current_deck_only or cache.deck == self._current_deck_id())
        )

    def _config_signature(self, view: HeatmapView) -> tuple[object, ...]:
        synced = self._config["synced"]
        profile = self._config["profile"]
        display = profile.get("display", {})
        return (
            synced.get("colors"),
            synced.get("mode"),
            synced.get("amount"),
            synced.get("limhist"),
            synced.get("limdate"),
            synced.get("limfcst"),
            tuple(synced.get("limdecks") or ()),
            display.get(view.name),
            profile.get("statsvis"),
        )

    def _get_css_classes(self, view: HeatmapView) -> list[str]:
        conf = self._config["synced"]
        classes = [
            f"{CSS_PLATFORM_PREFIX}-{PLATFORM}",
            f"{CSS_THEME_PREFIX}-{conf['colors']}",
            f"{CSS_MODE_PREFIX}-{conf['mode']}",
            f"{CSS_VIEW_PREFIX}-{view.name}",
        ]
        return classes

    def _generate_heatmap_elm(
        self, report: ActivityReport, dynamic_legend, current_deck_only: bool
    ) -> str:
        mode = heatmap_modes[self._config["synced"]["mode"]]

        # TODO: pass on "whole" to govern browser link "deck:current" addition
        options = {
            "domain": mode["domain"],
            "subdomain": mode["subDomain"],
            "range": mode["range"],
            "domLabForm": mode["domLabForm"],
            "start": report.start,
            "stop": report.stop,
            "today": report.today,
            "offset": report.offset,
            "legend": dynamic_legend,
            "whole": not current_deck_only,
            "amount": self.amount,
            "holy_days": report.holy_days,
            "hatch_days": report.hatch_days,
        }
        # showText(str(HTML_HEATMAP.format(
        #     options=json.dumps(options), data=json.dumps(report.activity))))
        return HTML_HEATMAP.format(
            options=json.dumps(options), data=json.dumps(report.activity)
        )

    def _generate_stats_elm(self, data: ActivityReport, dynamic_legend) -> str:
        dynamic_levels = self._get_dynamic_levels(dynamic_legend)
        stats_formatting = self._stats_formatting

        format_dict: dict[str, str] = {}
        stats_entry: StatsEntry

        for name, stats_entry in data.stats._asdict().items():
            stat_format = stats_formatting[stats_entry.type]

            value = stats_entry.value
            levels = stat_format.levels

            if levels is None:
                levels = dynamic_levels

            css_class = self._css_colors[0]
            for threshold, css_class in levels:  # noqa: B007
                if value <= threshold:
                    break

            unit = stat_format.unit
            label = self._maybe_pluralize(value, unit) if unit else str(value)

            format_dict["class_" + name] = css_class
            format_dict["text_" + name] = label

        return HTML_STREAK.format(**format_dict)

    def _get_dynamic_levels(self, dynamic_legend) -> list[tuple[int, str]]:
        return list(zip(dynamic_legend, self._css_colors, strict=False))

    @property
    def amount(self) -> bool:
        try:
            return self._config["synced"]["amount"]
        except (KeyError, TypeError):
            return True

    def _heatmap_legend(self, legend: list[float]) -> list[float]:
        # Inverted negative legend for future dates. Allows us to
        # implement different color schemes for past and future without
        # having to modify cal-heatmap:
        if self.amount:  # paint by amount
            return [-i for i in legend[::-1]] + [0.0] + legend
        else:  # paint by percent
            # return [-i for i in legend[::-1]] + [0.0] + [0.1,20.0,30.0,45.0,60.0,70.0, 80.0,90.0,99.0,100]
            return [-i for i in legend[::-1]] + [0.0] + [0.1,20.0,30.0,45.0,60.0,70.0, 80.0,90.0,99.0, 10000]

    def _stats_legend(self, legend: list[float]) -> list[float]:
        return [0.0] + legend

    def _dynamic_legend(self, average: int) -> list[float]:
        # set default average if average too low for informational levels
        avg = max(20, average)
        return [fct * avg for fct in self._dynamic_legend_factors]

    @staticmethod
    def _maybe_pluralize(count: float, term: str) -> str:
        return "{} {}{}".format(str(count), term, "")

    def _save_current_perf(self, activity_report: ActivityReport):
        """
        Store current performance in mw object

        TODO: Make data like this available through a proper API

        Just a quick hack that allows us to assess user performance from
        other distant parts of the code / other add-ons
        """
        self._mw._hmStreakMax = activity_report.stats.streak_max.value  # type: ignore
        self._mw._hmStreakCur = activity_report.stats.streak_cur.value  # type: ignore
        self._mw._hmActivityDailyAvg = activity_report.stats.activity_daily_avg.value  # type: ignore
