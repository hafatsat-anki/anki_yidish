import aqt
from anki.hooks import wrap
from aqt import gui_hooks, mw
from aqt.qt import QMessageBox

from _shared_libs.haf_logging import get_logger

logger = get_logger("disable_updates")

CONFIG_KEY = "initialized"


# ─────────────────────────────
# בדיקת תאימות גרסה
# ─────────────────────────────
def _check_version_compatibility():
    try:
        from _shared_libs.haf_compat import check_compatibility
        report = check_compatibility()
        if not report.is_compatible:
            for warning in report.warnings:
                logger.warning(warning)
            from aqt.utils import showWarning
            showWarning(
                f"די אנקי ווערסיע {report.anki_version} "
                f"איז עלטער פונעם פארלאנגטן מינימום ({report.target_version}).\n"
                "עס קענען זיין פאראיינבארקייט פראבלעמען מיט טייל צוגאבן."
            )
        else:
            logger.info(
                f"Anki {report.anki_version} compatible "
                f"(target: {report.target_version})"
            )
    except Exception as e:
        logger.warning(f"Version check failed: {e}")


gui_hooks.profile_did_open.append(_check_version_compatibility)


# ─────────────────────────────
# ריצה חד־פעמית: כיבוי בדיקת עדכונים
# ─────────────────────────────
def run_once_disable_update_check():
    config = mw.addonManager.getConfig(__name__) or {}

    if config.get(CONFIG_KEY, False):
        return

    mw.pm.set_update_check(0)

    config[CONFIG_KEY] = True
    mw.addonManager.writeConfig(__name__, config)


gui_hooks.profile_did_open.append(run_once_disable_update_check)


# ─────────────────────────────
# WRAP לטקסט של לשונית General → Updates
# ─────────────────────────────
def wrap_update_text(self):
    warning = (
        "⚠️ ווארענונג:\n\n"
        "אויטאמאטישע דערהיינטיגונגען קענען ברענגען פאראיינבארקייט פראבלעמען "
        "מיט צוגאבן אין דער ווערסיע.\n\n"
        "ביי א פראבלעם איז ראטזאם צוריקצוגיין צו א פריערדיגער ווערסיע פון Anki."
    )

    cb = self.form.check_for_updates

    def on_state_changed(state):
        # רק אם מנסים לסמן וי
        if state == 2:
            res = QMessageBox.question(
                self,
                "באשטעטיגן דאס אויסשאלטן דערהיינטיגונגען",
                warning,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if res != QMessageBox.StandardButton.Ok:
                mw.pm.set_update_check(0)
                cb.setChecked(False)

    cb.stateChanged.connect(on_state_changed)

aqt.preferences.Preferences.setup_global = wrap(aqt.preferences.Preferences.setup_global, wrap_update_text, "after")
