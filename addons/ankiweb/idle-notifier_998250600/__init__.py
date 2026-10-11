# Copyright (C) 2020 Hyun Woo Park
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# הזכויות על השינוים בתוסף זה שמורות להפצת אנקי ואין לעשות בהם שימוש מסחרי

import base64
import mimetypes
import os

import aqt
from anki.hooks import wrap
from aqt import AnkiQt, gui_hooks, mw
from aqt.qt import *
from aqt.reviewer import Reviewer
from aqt.utils import showInfo

from .mobileSupport.modelModifier import registerMobileScript
from .utils import debugLog, uuid
from .utils.configrw import getConfig
from .utils.JSCallable import JSCallable
from .utils.resource import readResource, updateMedia

gui_hooks.profile_did_open.append(registerMobileScript)


@JSCallable
def isActiveWindowAnki():
    return aqt.mw.app.activeWindow() is not None


def afterInitWeb(self):
    js = readResource("js/main.min.js")
    self.web.settings().setAttribute(
        QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False
    )
    updateMedia("_at_resume.mp3", readResource("sfx/resume.mp3", binary=True), False)

    def cb2(res):
        if getConfig("idleAlarm"):
            self.web.eval("window._atInstance.enableIdleAlarm(true)")

        fname = getConfig("alarmFile")
        if fname:
            updateMedia(
                "_at_alert.mp3", readResource("sfx/alert.mp3", binary=True), False
            )
            if os.path.isfile(fname):
                with open(fname, "rb") as f:
                    content = f.read()
                mimetype = mimetypes.guess_type(fname)[0]

                if mimetype == "audio/mpeg":
                    updateMedia("_at_alert.mp3", content)
                    self.web.eval('window._atInstance.setAlarmSound("_at_alert.mp3")')
                else:
                    b64 = base64.b64encode(content).decode("ascii")
                    dataURI = f"data:{mimetype};base64,{b64}"
                    self.web.eval(f'window._atInstance.setAlarmSound("{dataURI}")')
            else:
                from _shared_libs.haf_logging import get_logger
                from _shared_libs.haf_notifications import warn_once
                get_logger("idle_notifier").warning("Configured alarm sound was not found: %s", fname)
                warn_once("idle-notifier:sound", "די אויסגעקליבענע קלאנג טעקע פאר דער הפסקה דערמאנונג איז נישט געפונען געווארן. קלייבט אויס אן אנדערע טעקע אין די איינשטעלונגען פונעם צוגאב.")
        else:
            updateMedia(
                "_at_alert.mp3", readResource("sfx/alert.mp3", binary=True), True
            )

    self.web.evalWithCallback(js, cb2)


def _answerCard1(self, oo, ooo) -> None:
    self.web.eval('window._idle.isIdle_();')

def _answerCard2(self) -> None:
    try:
        _answerCard1(self, "oo", "ooo")
    except Exception:
        from _shared_libs.haf_notifications import warn_once
        warn_once("idle-notifier:answer", "דערהיינטיגן דעם אומטעטיגן צושטאנד איז דורכגעפאלן. די הפסקה דערמאנונג קען נישט ארבעטן ריכטיג; עפנט איבער דעם לערנען עקראן.")

def disposeAnkiTime(self, _old):
    self.web.evalWithCallback(
        "if (window._atInstance) window._atInstance.dispose();", lambda res: _old(self)
    )


def AnkiTime_pref(self: aqt.preferences.Preferences):
    config = mw.addonManager.getConfig(__name__)
    self.form.alarm_toggle = QCheckBox(
        'הילף זיך קאנצענטרירן - שפילט א קלאנג נאך א מינוט אן טעטיגקייט', mw
    )
    self.form.alarm_toggle.setChecked(config['alarm_toggle'])
    self.form.verticalLayout_5.addWidget(self.form.alarm_toggle)
    qconnect(
        self.form.alarm_toggle.stateChanged,
        lambda state, confVal='alarm_toggle': menu_select(state, confVal)
    )
    qconnect(self.form.alarm_toggle.stateChanged, alert)


aqt.preferences.Preferences.setup_global = wrap(
    aqt.preferences.Preferences.setup_global, AnkiTime_pref, "after"
)


def alert():
    showInfo("כדי די ענדערונג זאל גילטיג ווערן, הייבט אן די פראגראם פון פריש.")


def menu_select(state, confVal):
    config = mw.addonManager.getConfig(__name__)
    config[confVal] = state
    mw.addonManager.writeConfig(__name__, config)


def on_anki_start(*args):
    config = mw.addonManager.getConfig(__name__)
    if config.get('alarm_toggle', False):
        Reviewer._initWeb = wrap(Reviewer._initWeb, afterInitWeb, "after")
        aqt.reviewer.Reviewer._showAnswer = wrap(
            aqt.reviewer.Reviewer._showAnswer, _answerCard2, "after"
        )
        gui_hooks.reviewer_did_answer_card.append(_answerCard1)
        AnkiQt.unloadProfileAndExit = wrap(
            AnkiQt.unloadProfileAndExit, disposeAnkiTime, "around"
        )
    mw.addonManager.writeConfig(__name__, config)


mw.addonManager.setConfigUpdatedAction(__name__, on_anki_start)
on_anki_start()
