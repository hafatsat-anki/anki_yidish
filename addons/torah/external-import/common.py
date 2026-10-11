# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from typing import TextIO

from aqt import gui_hooks, mw

from _shared_libs.haf_logging import get_logger

logger = get_logger("external_import")

ADDON_NAME = 'אימפארטירן איינציגע שאלות פון א טעקע'


class LogDebug:
    _logfile: TextIO | None = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        gui_hooks.profile_will_close.append(self.close)

    def write(self, msg: str) -> None:
        logger.debug(f'CroPro debug: {msg}')
        # if not config['enable_debug_log']:
        return

    def __call__(self, *args, **kwargs):
        return self.write(*args, **kwargs)

    def close(self):
        if self._logfile and not self._logfile.closed:
            self.write("closing debug log.")
            self._logfile = self._logfile.close()
