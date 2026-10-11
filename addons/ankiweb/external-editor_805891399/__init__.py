# license: see license.txt

import json
import os

from aqt import gui_hooks, mw


def tinyloader():
    from . import external_js_editor_for_field


def maybe_reset_config():
    """Complete legacy settings without resetting choices made in the editor."""
    old_config = mw.addonManager.getConfig(__name__)
    if old_config is None:
        old_config = {}
    if not isinstance(old_config, dict):
        raise ValueError("External editor settings must be a dictionary")
    marker = old_config.get("auto_reset_number", 0)
    if not isinstance(marker, int) or isinstance(marker, bool) or marker < 0:
        raise ValueError("External editor migration marker must be a non-negative integer")
    if marker < 2:
        addon_path = os.path.dirname(__file__)
        json_file_path = os.path.join(addon_path, "config.json")
        with open(json_file_path, encoding="utf8") as f:
            new_default_config = json.load(f)
        completed = {**new_default_config, **old_config}
        completed["auto_reset_number"] = 2
        mw.addonManager.writeConfig(__name__, completed)


gui_hooks.profile_did_open.append(tinyloader)
gui_hooks.profile_did_open.append(maybe_reset_config)
