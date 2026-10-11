# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from anki.collection import ImportLogWithChanges
from anki.import_export_pb2 import ImportAnkiPackageRequest
from aqt.utils import showText
from aqt import gui_hooks, mw
from . import cropro, note_type_consolidator  # , settings_dialog

cropro.init()
note_type_consolidator.init()






def import_anki_package(
        self, request: ImportAnkiPackageRequest
) -> ImportLogWithChanges:
    from _shared_libs.haf_logging import get_logger
    get_logger("external_import").debug("Importing Anki package through backend")
    log = self._backend.import_anki_package_raw(request.SerializeToString())
    return ImportLogWithChanges.FromString(log)


#anki.collection.Collection.import_anki_package = wrap(anki.collection.Collection.import_anki_package, import_anki_package, "around")
CURRENT_VERSION = 1

def run_auto_consolidation_per_profile():
    profile = mw.pm.profile
    if profile.get("auto_consolidation_version", 0) >= CURRENT_VERSION:
        return
    from . import note_type_consolidator
    note_type_consolidator.run_auto_consolidation(
        manual=False,
        force=True,
    )

    profile["auto_consolidation_version"] = CURRENT_VERSION
    mw.pm.save()

gui_hooks.profile_did_open.append(run_auto_consolidation_per_profile)
