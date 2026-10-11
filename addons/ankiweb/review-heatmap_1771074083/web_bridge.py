
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
JS <-> PY communication
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Union

import aqt
from aqt.deckbrowser import DeckBrowser
from aqt.main import AnkiQt
from aqt.overview import Overview
from aqt.qt import QWidget
from aqt.stats import DeckStats

from .config import heatmap_colors, heatmap_modes

if TYPE_CHECKING:
    from .libaddon.anki.configmanager import ConfigManager

HANDLED_TYPE = tuple[bool, Any]
SUPPORTED_CONTEXT_TYPES = Union[DeckBrowser, Overview, DeckStats]


class HeatmapBridge:

    _identifier: str = "revhm"
    _command_splitter: str = "_"
    _payload_splitter: str = ":"

    # TODO: new deck stats
    _supported_contexts: tuple[type[DeckBrowser], type[Overview], type[DeckStats]] = (
        DeckBrowser,
        Overview,
        DeckStats,
    )

    def __init__(self, mw: AnkiQt, config: "ConfigManager"):
        self._mw: AnkiQt = mw
        self._config: ConfigManager = config
        self._command_handler: _CommandHandler = _CommandHandler(mw, config)

    def register(self):
        from aqt.gui_hooks import webview_did_receive_js_message

        webview_did_receive_js_message.append(self.bridge)
        # TODO: NewDeckStats
        DeckStats._linkHandler = lambda context, url: self.bridge_legacy(context, url)  # type: ignore

    def bridge(self, handled: HANDLED_TYPE, message: str, context: Any) -> HANDLED_TYPE:
        if not message.startswith(self._identifier) or not any(isinstance(context, c) for c in self._supported_contexts):
            return handled

        ret = self._handle_message(message, context)

        return (True, ret)

    def bridge_legacy(
        self, context: SUPPORTED_CONTEXT_TYPES, url: str, _old=None
    ) -> Any:
        if not url.startswith(self._identifier):
            return None if not _old else _old(context, url)

        return self._handle_message(url, context)

    def _handle_message(self, message: str, context: SUPPORTED_CONTEXT_TYPES) -> Any:
        identifier, command_and_payload = message.split(self._command_splitter, 1)

        payload: str | None

        try:
            # TODO: handle no command
            command, payload = command_and_payload.split(self._payload_splitter, 1)
        except ValueError:
            command = command_and_payload
            payload = None

        # TODO: decode payload JSON

        return self._command_handler(command, payload, context)


COMMAND_HANDLER_TYPE = Callable[
    ["_CommandHandler", Any, SUPPORTED_CONTEXT_TYPES], Any | None
]

_command_handler_registry: dict[str, COMMAND_HANDLER_TYPE] = {}


def _register_command_handler(cmd: str):
    def decorator(method: COMMAND_HANDLER_TYPE):
        _command_handler_registry[cmd] = method

    return decorator


class _CommandHandler:

    _handler_registry: dict[str, COMMAND_HANDLER_TYPE]

    def __init__(self, mw: "AnkiQt", config: "ConfigManager"):
        self._mw: AnkiQt = mw
        self._config: ConfigManager = config

    def __call__(
        self,
        command: str,
        payload: Any,
        context: Union[DeckBrowser, Overview, DeckStats],
    ) -> Any:
        handler = _command_handler_registry.get(command)

        # TODO: handle no handler more expressively
        if not handler:
            return None

        return handler(self, payload, context)  # type: ignore

    @_register_command_handler("browse")
    def browse(self, search: str, context: SUPPORTED_CONTEXT_TYPES) -> None:
        import re
        ridtoday_match = re.match(r"^ridtoday:([0-9]+):([0-9]+)$", search)
        if ridtoday_match:
            self._browse_today(int(ridtoday_match[1]), int(ridtoday_match[2]))
            return
        browser = aqt.dialogs.open("Browser", self._mw)
        browser.form.searchEdit.lineEdit().setText(search)
        browser.onSearchActivated()

    def _browse_today(self, start_ms: int, end_ms: int) -> None:
        # #304 — schtoday מיושם ב-finder: נלמד + תוזמן מחדש (מבחן) + להיום + באיחור.
        # prop:rated לא כולל תזמון ידני (ease=0), לכן חיפוש נייטיבי לא מספיק.
        search = f"schtoday:{start_ms}:{end_ms}"
        browser = aqt.dialogs.open("Browser", self._mw)
        browser.form.searchEdit.lineEdit().setText(search)
        browser.onSearchActivated()

    @_register_command_handler("opts")
    def amount(self, payload: None, context: SUPPORTED_CONTEXT_TYPES) -> None:
        self._get_context_parent(context)
        self._config["synced"]["amount"] = True
        self._config.save()
        # invoke_options_dialog(parent=parent)

    @_register_command_handler("contrib")
    def percent(self, payload: Any, context: SUPPORTED_CONTEXT_TYPES) -> None:
        self._get_context_parent(context)
        self._config["synced"]["amount"] = False
        self._config.save()
        # invoke_contributions_dialog(parent=parent)

    @_register_command_handler("modeswitch")
    def cycle_hm_modes(self, payload: Any, context: SUPPORTED_CONTEXT_TYPES) -> None:
        modes = list(heatmap_modes.keys())
        cur_idx = modes.index(self._config["synced"]["mode"])
        new_idx = (cur_idx + 1) % len(modes)
        self._config["synced"]["mode"] = modes[new_idx]
        self._config.save()

    @_register_command_handler("themeswitch")
    def cycle_hm_themes(self, payload: Any, context: SUPPORTED_CONTEXT_TYPES) -> None:
        themes = list(heatmap_colors.keys())
        cur_idx = themes.index(self._config["synced"]["colors"])
        new_idx = (cur_idx + 1) % len(themes)
        self._config["synced"]["colors"] = themes[new_idx]
        self._config.save()


    # Helpers

    def _get_context_parent(self, context: SUPPORTED_CONTEXT_TYPES) -> QWidget:
        if not isinstance(context, QWidget):
            return self._mw
        return context
