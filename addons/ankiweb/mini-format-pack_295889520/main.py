
# Mini Format Pack Add-on for Anki
#
# Copyright: (c) 2014-2018 Stefan van den Akker <neftas@protonmail.com>
#            (c) 2017-2018 Damien Elmes <http://ichi2.net/contact.html>
#            (c) 2018-2023 Glutanimate and contributors <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program.
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
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.


import os
from typing import TYPE_CHECKING

from aqt import mw
from aqt.editor import Editor
from aqt.gui_hooks import editor_did_init_buttons, editor_did_load_note, webview_will_set_content
from aqt.qt import Qt, QKeySequence, QShortcut, QTimer

from .anki import config_getter_factory
from .consts import addon_path
from .formatters import FORMATTERS
from .media_import import install_media_import_enhancement

if TYPE_CHECKING:
    assert mw is not None

# Config


get_config = config_getter_factory(mw.addonManager, __name__)

# #204/#240 — only the actions enabled by this distribution belong in the
# runtime. Old upstream formatters are intentionally not restored.
DEFAULT_ACTIONS = [
    {"name": "strikeThrough", "tooltip": "דורכגעשטראכן", "hotkey": "alt+shift+5"},
    {"name": "insertHorizontalRule", "tooltip": "לייגט צו א צעטיילנדיגער שטריך", "hotkey": "ctrl+shift+alt+_"},
]


def configured_actions():
    actions = get_config().get("actions")
    if not isinstance(actions, list):
        actions = []
    configured_by_name = {
        action.get("name"): action
        for action in actions
        if isinstance(action, dict) and action.get("name")
    }
    merged = []
    for default_action in DEFAULT_ACTIONS:
        merged.append(configured_by_name.get(default_action["name"], default_action))
    return merged


# UI element creation


# Hooks


def on_setup_buttons(buttons: list[str], editor: "Editor"):
    """Add buttons to Editor for Anki 2.1.x"""

    if editor.web is None:
        return

    actions = configured_actions()

    if not actions:
        return

    for action in actions:
        try:
            name = action["name"]
            tooltip = action["tooltip"]
            label = action.get("label", "")
            hotkey = action["hotkey"]
        except KeyError:
            print("Mini Format Pack: Action not configured properly:", action)
            continue

        formatter = FORMATTERS.get(name)

        if formatter is None or not callable(formatter):
            print("Mini Format Pack: Method not found:", name)
            continue

        def wrapper(editor=editor, formatter=formatter):
            if editor.web is None:
                print("Mini Format Pack: Editor webview not properly initialized")
                return
            formatter(editor, editor.web)

        icon_path = os.path.join(addon_path, "icons", f"{name}.png")
        if not os.path.exists(icon_path):
            icon_path = ""

        shortcut_hint = f" ({hotkey})" if hotkey else ""
        button = editor.addButton(
            icon_path,
            name,
            wrapper,
            tip=f"{tooltip}{shortcut_hint}",
            label="" if icon_path else label,
            # Issue #379: QShortcut construction can stall first WebView paint
            # on Windows. Register it after the editor has rendered instead.
            keys=None,
        )

        buttons.append(button)


editor_did_init_buttons.append(on_setup_buttons)


def register_shortcuts_after_first_paint(editor: "Editor"):
    """Install format shortcuts after WebEngine has displayed the editor."""
    # #379 — the hook itself is cheap and stable for tests/integrations; the
    # actual QShortcut construction is queued until control returns to Qt so
    # WebEngine gets its first paint first.
    QTimer.singleShot(0, lambda: _install_shortcuts(editor))


def _install_shortcuts(editor: "Editor") -> None:
    if getattr(editor, "_mini_format_shortcuts_ready", False):
        return

    shortcuts = []
    for action in configured_actions():
        formatter = FORMATTERS.get(action.get("name"))
        hotkey = action.get("hotkey")
        if not callable(formatter) or not hotkey:
            continue

        shortcut = QShortcut(QKeySequence(hotkey), editor.widget)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

        def trigger(formatter=formatter, editor=editor):
            if editor.web is not None:
                formatter(editor, editor.web)

        shortcut.activated.connect(trigger)
        shortcuts.append(shortcut)

    # Keep Python references for the lifetime of the editor.
    editor._mini_format_shortcuts = shortcuts
    editor._mini_format_shortcuts_ready = True


editor_did_load_note.append(register_shortcuts_after_first_paint)


def keep_wrapped_editor_toolbar_rtl(web_content, context) -> None:
    """Keep every wrapped editor-toolbar row anchored to the RTL start edge."""
    if not isinstance(context, Editor):
        return
    web_content.head += """
    <style id="haf-editor-toolbar-rtl">
      #toolbar, #toolbar > div, .toolbar, .toolbar > div,
      .editor-toolbar, .editor-toolbar > div, .formatting-toolbar,
      [class*="toolbar-buttons"], [class*="toolbar-row"] {
        direction: rtl !important;
        justify-content: flex-start !important;
        text-align: right !important;
      }
    </style>
    """


webview_will_set_content.append(keep_wrapped_editor_toolbar_rtl)

# #375 — enhance Anki's existing attach/import button; do not add another
# toolbar button for the same task.
install_media_import_enhancement()
