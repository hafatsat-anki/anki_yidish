
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

"""The two editor-format actions enabled by this distribution."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from aqt.editor import Editor, EditorWebView

class Formatter(Protocol):
    """
    Protocol for format functions.

    Format functions are called by the editor when the user clicks on a button
    in the editor toolbar. They are expected to perform the necessary
    modifications to the editor's content.

    NOTE: Functions need to use camelCase to preserve compatibility with existing
          add-on configurations. Any functions added in the future should continue
          to use camelCase for consistency.
    """

    __name__: str

    def __call__(self, editor: "Editor", editor_webview: "EditorWebView") -> None: ...


FORMATTERS: dict[str, Formatter] = {}


def register_formatter(formatter: Formatter) -> None:
    FORMATTERS[formatter.__name__] = formatter


@register_formatter
def strikeThrough(editor: "Editor", editor_webview: "EditorWebView"):
    editor_webview.eval("setFormat('strikeThrough')")


@register_formatter
def insertHorizontalRule(editor: "Editor", editor_webview: "EditorWebView"):
    editor_webview.eval("setFormat('insertHorizontalRule')")
