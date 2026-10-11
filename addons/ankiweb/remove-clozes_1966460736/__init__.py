
# Remove Clozes Add-on for Anki
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

# #138 — contextlib מנקה references לעורכים שנסגרו בזמן רענון live של הקיצור.
import contextlib
# #138 — דרוש לעדכון tooltip בטוח כאשר הקיצור מכיל תווים מיוחדים.
import json
from typing import TYPE_CHECKING, Any
# #138 — WeakKeyDictionary מונע החזקת חלונות Editor אחרי סגירה.
from weakref import WeakKeyDictionary

from aqt import mw
from aqt.editor import Editor
from aqt.gui_hooks import editor_did_init_buttons, webview_will_set_content
# #138 — נדרש Qt.ShortcutContext כדי שקיצור remove-clozes יעבוד כשהפוקוס בתוך עורך WebEngine.
from aqt.qt import QKeySequence, QShortcut, Qt

if TYPE_CHECKING:
    from aqt.webview import WebContent

def _module_addon_id() -> str:
    # #138 — מזהה התוסף נלקח דרך Anki כשאפשר, כדי ש-shortcut-manager ו-remove-clozes יקראו את אותו config.
    try:
        return mw.addonManager.addonFromModule(__name__)
    except Exception:
        return __name__.split(".")[0]


# #138 — שימוש במזהה התוסף מונע מצב שבו קיצור נשמר בתוסף אחד ונקרא ממודול אחר.
MODULE_ADDON = _module_addon_id()
# #138 — שומרים קיצורים לפי מופע Editor כדי שאפשר יהיה לעדכן אותם בזמן אמת בלי להחזיק חלונות מתים.
_editor_shortcuts = WeakKeyDictionary()


def _configured_hotkey(editor: "Editor") -> str:
    # #138 — shortcut-manager שומר את הקיצור הראשי תחת remove_cloze; קוראים ממנו כדי שהקיצור יתעדכן גם אם config התוסף לא נכתב ישירות.
    try:
        manager_config = editor.mw.addonManager.getConfig("shortcut-manager") or {}
        manager_hotkey = manager_config.get("remove_cloze")
        if manager_hotkey:
            hotkey = str(manager_hotkey).strip()
            return "" if hotkey.lower() == "<nop>" else hotkey
    except Exception:
        pass
    # #138 — Anki שומר קונפיג לפי מזהה התוסף ולא לפי שם מודול מיובא, אחרת shortcut-manager יכול לכתוב קיצור שלא נטען בפועל.
    config = editor.mw.addonManager.getConfig(MODULE_ADDON)
    hotkey = config.get("hotkey", "Ctrl+Alt+Shift+R") if config else "Ctrl+Alt+Shift+R"
    return "" if str(hotkey).strip().lower() == "<nop>" else str(hotkey).strip()


def _set_editor_shortcut(editor: "Editor", hotkey: str) -> None:
    shortcut = _editor_shortcuts.get(editor)
    # #138 — קיצור ריק או <nop> מכבה את ה-QShortcut במקום להשאיר את הקיצור הקודם פעיל.
    key_sequence = QKeySequence(hotkey) if hotkey else QKeySequence()
    if shortcut is None:
        shortcut = QShortcut(key_sequence, editor.widget)
        # #138 — WidgetWithChildrenShortcut תופס את הקיצור גם כאשר הפוקוס נמצא בתוך שדה העריכה של Anki.
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(lambda editor=editor: remove_clozes(editor))
        _editor_shortcuts[editor] = shortcut
    else:
        shortcut.setKey(key_sequence)
    shortcut.setEnabled(bool(hotkey))


def inject_editor_script(web_content: "WebContent", context: Any):
    if isinstance(context, Editor):
        hotkey = json.dumps(_configured_hotkey(context))
        # #138 — קיצור JS נטען לתוך WebView עצמו כדי שיעבוד גם כשהפוקוס נמצא בתוך שדה העריכה ולא מגיע ל-QShortcut.
        web_content.head += (
            f"""<script>window.RemoveClozesPendingHotkey = {hotkey};</script>"""
            f"""<script src="/_addons/{MODULE_ADDON}/web/editor.js"></script>"""
        )


def remove_clozes(editor: "Editor"):
    """Remove cloze markers and hints from selected text"""
    if not editor.web:
        return
    editor.web.eval("removeClozes();")


def add_remove_clozes_button(buttons, editor: "Editor"):
    hotkey = _configured_hotkey(editor)
    b = editor.addButton(
        None,
        "RemoveClozes",
        remove_clozes,
        f"נעמט אראפ די אויסלאז סימנים ({hotkey})",
        label="[.X.]",
        keys=None,
        id="RemoveClozes"
    )
    # #138 — שומרים את QShortcut שלנו כדי שאפשר יהיה לשנות אותו מיד אחרי Apply בלי לפתוח מחדש את חלון העורך.
    _set_editor_shortcut(editor, hotkey)
    buttons.append(b)
    return buttons


def _reload_config() -> None:
    # #138 — עדכון קיצורי remove-clozes לכל עורכים פתוחים לאחר שמירת shortcut-manager.
    dead = []
    for editor in list(_editor_shortcuts.keys()):
        try:
            hotkey = _configured_hotkey(editor)
            _set_editor_shortcut(editor, hotkey)
            if editor.web:
                # #138 — json.dumps מגן על tooltip של קיצור שמכיל תווים מיוחדים.
                title = json.dumps(f"נעמט אראפ די אויסלאז סימנים ({hotkey})")
                encoded_hotkey = json.dumps(hotkey)
                editor.web.eval(
                    "var btn=document.getElementById('RemoveClozes');"
                    f"if(btn) btn.title={title};"
                    # #138 — live reload מעדכן גם את מאזין ה-JS בתוך WebView פתוח, לא רק את QShortcut של Qt.
                    "if(window.RemoveClozesShortcut) "
                    f"window.RemoveClozesShortcut.setHotkey({encoded_hotkey});"
                    "else "
                    f"window.RemoveClozesPendingHotkey={encoded_hotkey};"
                )
        except RuntimeError:
            dead.append(editor)
    for editor in dead:
        with contextlib.suppress(Exception):
            del _editor_shortcuts[editor]


mw.addonManager.setWebExports(__name__, r"web.*")  # type: ignore
editor_did_init_buttons.append(add_remove_clozes_button)  # type: ignore
webview_will_set_content.append(inject_editor_script)
