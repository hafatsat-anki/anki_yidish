# Copyright(C)| 2024 Carlos Duarte - Defer Cards
# Fork on     | Lovac42 code, in add-on "SlackersDelight" https://github.com/lovac42/SlackersDelight
# License     | GNU AGPL, version 3 ou posterior; http://www.gnu.org/licenses/agpl.html
# Source in   | https://github.com/cjdduarte/DeferCards

import collections
import json
import os
from codecs import open

from anki.hooks import runHook
from aqt import gui_hooks, mw
from aqt.qt import *


class Config:
    config = {}

    def __init__(self, addonName):
        self.addonName = addonName
        gui_hooks.profile_did_open.append(self._loadConfig)

    def set(self, key, value):
        self.config[key] = value

    def get(self, key, default=None):
        return self.config.get(key, default)

    def has(self, key):
        return self.config.get(key) is not None

    def _loadConfig(self):
        if getattr(mw.addonManager, "getConfig", None):
            mw.addonManager.setConfigUpdatedAction(__name__, self._updateConfig)
        self.config = self._readConfig()
        runHook(self.addonName + '.configLoaded')

    def _updateConfig(self, config):
        self.config = nestedUpdate(self.config, config)
        runHook(self.addonName + '.configUpdated')

    def _readConfig(self):
        conf = self.readFile('config.json')
        meta = self.readFile('meta.json')
        if meta:
            conf = nestedUpdate(conf, meta.get('config', {}))
        return conf

    def readFile(self, fname, jsn=True):
        moduleDir, _ = os.path.split(__file__)
        path = os.path.join(moduleDir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
            if jsn:
                return json.loads(data)
            return data


# From: https://stackoverflow.com/questions/3232943/
def nestedUpdate(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = nestedUpdate(d.get(k, {}), v)
        else:
            d[k] = v
    return d
