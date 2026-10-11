# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import mw

# #139 — ברירות מחדל לסימון/הסתרת שאלות שיובאו בסשן הנוכחי גם אם config ישן עדיין לא מכיל אותן.
DEFAULT_CONFIG = {
    "hide_imported_in_session": False,
    "mark_imported_in_session": True,
}


def get_config():
    return mw.addonManager.getConfig(__name__)


def write_config():
    return mw.addonManager.writeConfig(__name__, config)


config = get_config() or {}
for key, value in DEFAULT_CONFIG.items():
    config.setdefault(key, value)
