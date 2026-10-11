
# Review Heatmap Add-on for Anki
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

"""
Initializes add-on components.
"""

from ._version import __version__  # noqa: F401


def initialize_addon():
    """Initializes add-on after performing a few checks

    Allows more fine-grained control over add-on execution, which can
    be helpful when implementing workarounds for Anki bugs (e.g. the module
    import bug present in all Anki 2.1 versions up to 2.1.14)
    """

    from _shared_libs.haf_logging import get_logger

    get_logger("review_heatmap")
    from .consts import ADDON
    from .libaddon.consts import set_addon_properties

    set_addon_properties(ADDON)


    from aqt import mw

    if not mw:
        # TODO: better handling
        return

    mw.addonManager.setWebExports(__name__, r"web.*")

    from .config import config as config_manager
    from .controller import initialize_controller
    from .finder import initialize_finder
    from .gui import initialize_qt_resources
    from .views import initialize_views

    initialize_qt_resources()
    config_manager.setConfigAction(lambda: True)

    controller = initialize_controller(mw, config_manager)
    initialize_views(controller)
    initialize_finder()

    # #199 — מפעיל לוג פרופיל קדימה בלבד לאירועי השהיה/הטמנה עבור חישוב פעילות.
    from .suspension_log import initialize_suspension_log
    initialize_suspension_log()

    # Run the consistency audit once per installed add-on version and profile.
    # אישיו #199: טעינת רכיב הדרוש לתיקון המתואר באישיו.
    from .consistency import setup_version_consistency_check
    setup_version_consistency_check()

    # #182 — דוח תקינות לוח השנה הוסר מהתפריט; נשאר זמין כאופציה שקטה (קרא ידנית ל-generate_comparison_report/show_comparison_report).
    # from .comparison_report import setup_menuCol_action
    # setup_menuCol_action()

    # #304 — טיימר לתזמון ידני: מעדכן time ב-revlog כשמשתמש עושה Set Due Date
    from .manual_review_timer import initialize_manual_review_timer
    initialize_manual_review_timer()

    # #182 — מצב אוטומטי: אם משתנה הסביבה HEATMAP_AUTO_COMPARE=1, התוסף מריץ
    # אוטומטית את דוח התקינות של הלוח שנה אחרי שהפרופיל נטען, שומר ל-JSON עם חותם זמן,
    # ואז סוגר את Anki. שימושי להרצת loop של בדיקות מבחוץ (סקריפט PowerShell/bash).
    import os as _os

    if _os.environ.get("HEATMAP_AUTO_COMPARE") == "1":
        from aqt import gui_hooks
        from aqt.qt import QTimer

        def _auto_compare_and_quit() -> None:
            try:
                import json
                from datetime import datetime
                from pathlib import Path
                from .comparison_report import (
                    DAYS_TO_COMPARE,
                    PAST_DAYS_TO_COMPARE,
                    _create_comparison_report,
                )

                past_days = int(_os.environ.get("HEATMAP_AUTO_COMPARE_PAST_DAYS") or PAST_DAYS_TO_COMPARE)
                future_days = int(_os.environ.get("HEATMAP_AUTO_COMPARE_FUTURE_DAYS") or DAYS_TO_COMPARE)
                report_path, payload = _create_comparison_report(past_days=past_days, future_days=future_days)
                # שומרים עותק נוסף עם חותם זמן כדי שלא ידרוס בין הרצות.
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                stamped = Path(report_path).with_name(
                    f"heatmap_auto_compare_{ts}.json"
                )
                stamped.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:  # noqa: BLE001
                # רושמים את השגיאה לקובץ נפרד כדי שלא נחמיץ אותה בלולאה.
                try:
                    from datetime import datetime
                    from pathlib import Path
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    err_path = Path(mw.pm.profileFolder()) / f"heatmap_auto_compare_ERROR_{ts}.log"
                    err_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
                except Exception:
                    pass
            finally:
                # סוגרים את Anki בצורה נקייה בכל מקרה.
                try:
                    mw.app.quit()
                    QTimer.singleShot(5000, lambda: mw.app.exit(0))
                except Exception:
                    import sys as _sys
                    _sys.exit(0)

        def _schedule_auto_compare() -> None:
            # ממתינים שנייה כדי שכל ההוקים של profile_did_open יסיימו להירשם.
            QTimer.singleShot(1000, _auto_compare_and_quit)

        # #182 — add-on init can run after profile_did_open, so schedule immediately
        # when a collection is already available instead of waiting for a hook that already fired.
        if mw.col:
            _schedule_auto_compare()
        else:
            gui_hooks.profile_did_open.append(_schedule_auto_compare)


initialize_addon()
