
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
Overarching control of heatmap rendering and state
"""

import contextlib
import json
from typing import TYPE_CHECKING, NamedTuple

from aqt import gui_hooks
from aqt.main import AnkiQt
from aqt.operations import QueryOp
from aqt.qt import QTimer

from .activity import ActivityReporter
from .errors import CollectionError
from .renderer import HeatmapRenderer, HeatmapView
from .web_bridge import HeatmapBridge

if TYPE_CHECKING:
    from anki.collection import Collection
    from .libaddon.anki.configmanager import ConfigManager


class _AsyncRenderResult(NamedTuple):
    report: object
    data_signature: tuple[object, ...]
    config_signature: tuple[object, ...]
    collection_identity: tuple[object, ...]
    deck_id: int


class HeatmapController:
    def __init__(self, mw: AnkiQt, config: "ConfigManager"):
        self._mw = mw
        self._config: ConfigManager = config

        self._bridge: HeatmapBridge | None = HeatmapBridge(self._mw, self._config)
        self._bridge.register()

        self._renderer: HeatmapRenderer | None = None
        self._async_render_counter = 0
        self._pending_renders: dict[tuple[object, ...], list[tuple[object, str]]] = {}
        self._deferred_deckbrowser_renders: dict[tuple[object, ...], object] = {}
        self._profile_generation = 0
        gui_hooks.state_did_change.append(self._on_state_changed)
        gui_hooks.profile_will_close.append(self._on_profile_will_close)

    def _on_profile_will_close(self) -> None:
        """סבב 9 — invalidate delayed work before Anki closes the collection."""
        self._profile_generation += 1
        self._pending_renders.clear()
        self._deferred_deckbrowser_renders.clear()

    def _on_state_changed(self, new_state: str, old_state: str) -> None:
        """Resume deck-browser work only after returning from another deck."""
        if new_state != "deckBrowser" or not self._deferred_deckbrowser_renders:
            return
        deferred = list(self._deferred_deckbrowser_renders.values())
        self._deferred_deckbrowser_renders.clear()
        for start_render in deferred:
            QTimer.singleShot(250, start_render)

    def render_for_view(
        self,
        view: HeatmapView,
        limhist: int | None = None,
        limfcst: int | None = None,
        current_deck_only: bool = False,
        async_context: object | None = None,
    ) -> str:
        col = self._mw.col
        if not col:
            raise CollectionError("Anki collection and/or database is not ready")

        self._ensure_renderer(col)
        if async_context is not None:
            cached_html, data_signature, config_signature = self._renderer.cache_state(
                view, limhist, limfcst, current_deck_only
            )
            if cached_html is not None:
                return cached_html
            token = self._next_async_token(view)
            self._schedule_async_render(
                async_context,
                token,
                view,
                limhist,
                limfcst,
                current_deck_only,
                data_signature,
                config_signature,
            )
            return self._renderer.render_loading(view, token)
        # showText(str(self._renderer.render(view, limhist, limfcst, current_deck_only)), copyBtn=True)

        return self._renderer.render(view, limhist, limfcst, current_deck_only)

    def _ensure_renderer(self, col: "Collection") -> None:
        if not self._renderer:
            reporter = ActivityReporter(col, self._config)
            self._renderer = HeatmapRenderer(self._mw, reporter, self._config)
            return
        self._renderer.set_collection(col)

    def _next_async_token(self, view: HeatmapView) -> str:
        self._async_render_counter += 1
        return f"rh-{view.name}-{self._async_render_counter}"

    def _schedule_async_render(
        self,
        async_context: object,
        token: str,
        view: HeatmapView,
        limhist: int | None,
        limfcst: int | None,
        current_deck_only: bool,
        data_signature: tuple[object, ...],
        config_signature: tuple[object, ...],
    ) -> None:
        col = self._mw.col
        if not col:
            return
        deck_id: int = int(col.decks.current()["id"])
        collection_identity = ActivityReporter._make_collection_identity(col)
        # Older tests and third-party wrappers can construct the controller
        # without running __init__. Generation zero is the initial profile.
        profile_generation = getattr(self, "_profile_generation", 0)
        # pending_key חייב להיות hashable; view+params+deck מספיקים לדה-דופליקציה.
        pending_key = (view.value, limhist, limfcst, current_deck_only, deck_id)
        targets = self._pending_renders.setdefault(pending_key, [])
        targets.append((async_context, token))
        if len(targets) > 1:
            return

        def render_in_background(background_col):
            reporter = ActivityReporter(background_col, self._config)
            background_signature = reporter.cache_signature(current_deck_only)
            report = reporter.get_report(
                limhist=limhist,
                limfcst=limfcst,
                current_deck_only=current_deck_only,
                cache_signature=background_signature,
            )
            # אישיו #199: פעם ביום בכל פתיחת פרופיל, ברקע ורק בדוח של כלל האוסף.
            check_key = (profile_generation, reporter._today)
            # אישיו #199: בדיקה רק לדוח כלל האוסף שטרם נבדק ביום ובפרופיל הנוכחיים.
            if not current_deck_only and getattr(self, "_today_check_key", None) != check_key:
                # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
                from .consistency import check_today_report
                # אישיו #199: השוואת דוח היום הקיים בלי לחשב שוב את היסטוריית החזרות.
                check_today_report(reporter, report)
                # אישיו #199: סימון שהבדיקה בוצעה כדי למנוע שאילתות חוזרות באותו יום.
                self._today_check_key = check_key
            return _AsyncRenderResult(
                report=report,
                data_signature=background_signature,
                config_signature=config_signature,
                collection_identity=ActivityReporter._make_collection_identity(background_col),
                deck_id=deck_id,
            )

        def on_success(result: _AsyncRenderResult) -> None:
            if profile_generation != self._profile_generation:
                return
            current_col = self._mw.col
            if not current_col:
                return
            if ActivityReporter._make_collection_identity(current_col) != result.collection_identity:
                return
            self._ensure_renderer(current_col)
            html = self._renderer.render_report(
                result.report,
                view,
                limhist,
                limfcst,
                current_deck_only,
                result.data_signature,
                result.config_signature,
                result.deck_id,
            )
            targets_to_update = self._pending_renders.pop(pending_key, [])
            for target_context, target_token in targets_to_update:
                self._replace_loading_html(target_context, target_token, html)

        render_started = False

        def start_render_if_still_visible() -> None:
            nonlocal render_started
            if render_started:
                return
            if profile_generation != getattr(self, "_profile_generation", 0) or not self._mw.col:
                self._pending_renders.pop(pending_key, None)
                self._deferred_deckbrowser_renders.pop(pending_key, None)
                return
            # #369 — QueryOp שקורא מהאוסף מחזיק את תור פעולות האוסף. לאחר סיום
            # סקירה נותנים קודם לניווט חפיסות לפעול. אם המשתמש עבר לחפיסה אחרת,
            # שומרים את העבודה וממשיכים אותה כשחוזרים למסך החפיסות.
            if view is HeatmapView.deckbrowser and self._mw.state != "deckBrowser":
                deferred = getattr(self, "_deferred_deckbrowser_renders", None)
                if deferred is None:
                    # Defensive compatibility for partially constructed controllers.
                    self._pending_renders.pop(pending_key, None)
                    return
                deferred[pending_key] = start_render_if_still_visible
                return
            self._deferred_deckbrowser_renders.pop(pending_key, None)
            render_started = True
            def on_failure(exc: Exception) -> None:
                self._pending_renders.pop(pending_key, None)
                if "CollectionNotOpen" not in type(exc).__name__ and profile_generation == self._profile_generation:
                    raise exc

            QueryOp(
                parent=self._mw,
                op=render_in_background,
                success=on_success,
            ).failure(on_failure).run_in_background()

        if view is HeatmapView.deckbrowser:
            QTimer.singleShot(1500, start_render_if_still_visible)
        else:
            start_render_if_still_visible()

    def _replace_loading_html(self, async_context: object, token: str, html: str) -> None:
        web = getattr(async_context, "web", None)
        if web is None:
            web = getattr(getattr(async_context, "form", None), "web", None)
        if web is None:
            return
        script = """
        (function() {
            var marker = document.querySelector('[data-rh-token=%s]');
            if (!marker) { return; }
            var container = marker.closest('.rh-container');
            if (!container) { return; }
            var template = document.createElement('template');
            template.innerHTML = %s;
            var scripts = Array.prototype.slice.call(template.content.querySelectorAll('script'));
            var replacement = template.content.querySelector('.rh-container');
            if (!replacement) { return; }
            scripts.forEach(function(oldScript) {
                if (oldScript.parentNode) {
                    oldScript.parentNode.removeChild(oldScript);
                }
            });
            container.replaceWith(replacement);

            function requiredGlobalLoaded(src) {
                if (src.indexOf('/d3.min.js') !== -1) {
                    return !!window.d3;
                }
                if (src.indexOf('/anki-review-heatmap.js') !== -1) {
                    return !!window.ReviewHeatmap;
                }
                return false;
            }

            function runInlineScripts() {
                scripts.forEach(function(oldScript) {
                    if (oldScript.src) { return; }
                    var runnable = document.createElement('script');
                    runnable.text = oldScript.textContent;
                    document.body.appendChild(runnable);
                    document.body.removeChild(runnable);
                });
            }

            var externalScripts = scripts.filter(function(oldScript) {
                return oldScript.src;
            });
            var index = 0;
            function loadNextExternal() {
                if (index >= externalScripts.length) {
                    runInlineScripts();
                    return;
                }
                var oldScript = externalScripts[index++];
                if (requiredGlobalLoaded(oldScript.src)) {
                    loadNextExternal();
                    return;
                }
                var runnable = document.createElement('script');
                runnable.src = oldScript.src;
                runnable.onload = loadNextExternal;
                runnable.onerror = loadNextExternal;
                document.head.appendChild(runnable);
            }
            loadNextExternal();
        })();
        """ % (json.dumps(token), json.dumps(html))
        with contextlib.suppress(Exception):
            web.eval(script)


def initialize_controller(mw: "AnkiQt", config: "ConfigManager") -> HeatmapController:
    controller = HeatmapController(mw, config)
    mw._review_heatmap = controller  # type: ignore
    return controller
