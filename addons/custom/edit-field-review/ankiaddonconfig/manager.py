import copy
import json
from collections.abc import Iterator
from typing import Any

from aqt import mw

from ..yiddish_config import normalise_config_keys



class ConfigManager:
    def __init__(self) -> None:
        self._config: dict
        # #138 — קונפיג edit-field-review חייב להיטען לפי מזהה התוסף האמיתי, כדי לקרוא את מה ש-shortcut-manager כותב.
        try:
            addon_dir = mw.addonManager.addonFromModule(__name__)
        except Exception:
            addon_dir = __name__.split(".")[0]
        self.addon_dir = addon_dir
        try:
            self.addon_name = mw.addonManager.addon_meta(addon_dir).human_name()
        except AttributeError:
            self.addon_name = mw.addonManager.addonName(addon_dir)
        self._default = mw.addonManager.addonConfigDefaults(addon_dir)
        self.load()

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """#138 — Anki's getConfig does only a shallow merge; this recursively fills in
        keys the user hasn't stored so nested fields (e.g. command/enabled/arg inside
        special_formatting entries) survive after saving only the shortcut."""
        result = copy.deepcopy(base)
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = ConfigManager._deep_merge(result[k], v)
            else:
                result[k] = copy.deepcopy(v)
        return result

    @staticmethod
    def _version_tuple(config: dict) -> tuple[int, int]:
        version = config.get("version", {}) if isinstance(config, dict) else {}
        if not isinstance(version, dict):
            return (-1, -1)
        try:
            return (int(version.get("major", -1)), int(version.get("minor", -1)))
        except (TypeError, ValueError):
            return (-1, -1)

    def _apply_distribution_migrations(self, raw_config: dict) -> bool:
        if self._version_tuple(raw_config) >= (1, 0):
            return False
        if self._config.get("ctrl_click") is True:
            self._config["ctrl_click"] = False
        self._config["version"] = {"major": 1, "minor": 0}
        return True

    def load(self) -> None:
        "Loads config from disk"
        # getConfig already overlays package defaults, masking an absent migration
        # marker. addonMeta is the raw metadata API used by Anki's own getConfig.
        raw = mw.addonManager.addonMeta(self.addon_dir).get("config", {})
        if raw is None:
            print("[edit-field-review] Restoring null user configuration")
            raw = {}
        if not isinstance(raw, dict):
            raise ValueError("edit-field-review settings must be a dictionary")
        raw = normalise_config_keys(raw)
        # #138 — getConfig does a top-level merge only; do a proper deep merge so that
        # nested keys the user hasn't set (e.g. command/enabled/arg in special_formatting)
        # are filled in from defaults and not lost.
        self._config = self._deep_merge(self._default or {}, raw)
        if self._apply_distribution_migrations(raw or self._default or {}):
            self.save()

    def save(self) -> None:
        "Writes its config data to disk."
        mw.addonManager.writeConfig(self.addon_dir, self._config)

    def load_defaults(self) -> None:
        "call .save() afterwards to restore defaults."
        self._config = copy.deepcopy(self._default)

    def to_json(self) -> str:
        return json.dumps(self._config)

    def get_from_dict(self, dict_obj: dict, key: str) -> Any:
        "Raises KeyError if config doesn't exist"
        levels = key.split(".")
        return_val = dict_obj
        for level in levels:
            if isinstance(return_val, list):
                level = int(level)
            return_val = return_val[level]
        return return_val

    def copy(self) -> dict:
        return copy.deepcopy(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        "Returns default or None if config dones't exist"
        try:
            return self.get_from_dict(self._config, key)
        except KeyError:
            return default

    def get_default(self, key: str) -> Any:
        return self.get_from_dict(self._default, key)

    def set(self, key: str, value: Any) -> None:
        levels = key.split(".")
        conf_obj = self._config
        for i in range(len(levels) - 1):
            level = levels[i]
            if isinstance(conf_obj, list):
                level = int(level)
            try:
                conf_obj = conf_obj[level]
            except KeyError:
                conf_obj[level] = {}
                conf_obj = conf_obj[level]
        level = levels[-1]
        if isinstance(conf_obj, list):
            level = int(level)
        conf_obj[level] = value

    def pop(self, key: str) -> Any:
        levels = key.split(".")
        conf_obj = self._config
        for i in range(len(levels) - 1):
            level = levels[i]
            if isinstance(conf_obj, list):
                level = int(level)
            try:
                conf_obj = conf_obj[level]
            except KeyError:
                return None
        level = levels[-1]
        if isinstance(conf_obj, list):
            level = int(level)
        return conf_obj.pop(level)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        "This function only modifies the internal config data. Call conf.save() to actually write to disk"
        self.set(key, value)

    def __iter__(self) -> Iterator:
        return iter(self._config)

    def __delitem__(self, key: str) -> Any:
        self.pop(key)

    def __contains__(self, key: str) -> bool:
        try:
            self.get_from_dict(self._config, key)
            return True
        except KeyError:
            return False

    # Config Window




