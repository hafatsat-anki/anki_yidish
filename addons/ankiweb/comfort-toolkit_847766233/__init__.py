# Copyright: hafatzat-anki 2023
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import aqt
from anki.errors import Interrupted, SyncError, SyncErrorKind
from anki.hooks import wrap
from aqt import mw, sync
from aqt.import_export import exporting
from aqt.utils import showWarning, tooltip


def getConfig(arg, default=""):
    config = mw.addonManager.getConfig(__name__)
    if config:
        return config.get(arg, default)
    else:
        return default


def handle_sync_error(mw: aqt.main.AnkiQt, err: Exception, _old) -> None:
    if isinstance(err, SyncError):
        if err.kind is SyncErrorKind.AUTH:
            mw.pm.clear_sync_auth()
    elif isinstance(err, Interrupted):
        # no message to show
        return
    if getConfig("sync_error_tooltip", True):
        tooltip(str(err))
    else:
        showWarning(str(err))

sync.handle_sync_error = wrap(sync.handle_sync_error, handle_sync_error, "around")


def setup(self, did):
    self.frm.legacy_support.setChecked(not getConfig("exporter-legacy_support_set_unchecked", True))

exporting.ExportDialog.setup = wrap(exporting.ExportDialog.setup, setup, "after")
