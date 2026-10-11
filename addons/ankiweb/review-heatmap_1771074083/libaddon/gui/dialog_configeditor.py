# -*- coding: utf-8 -*-

# Libaddon for Anki
#
# Copyright (C) 2018-2019  Aristotelis P. <https//glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program.
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
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
anki20 compat: Add-on configuration editor
"""

import aqt
from aqt.qt import *
from aqt.utils import tooltip, showInfo

from anki.utils import json

from .._vendor import markdown2

from ..consts import ADDON
from ..platform import PATH_THIS_ADDON

from .dialog_htmlview import HTMLViewer


class ConfigEditor(QDialog):
    
    def __init__(self, config_manager, parent):
        super(ConfigEditor, self).__init__(parent=parent)
        self.mgr = config_manager
        self.form = aqt.forms.editaddon.Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowTitle("{} Configuration".format(ADDON.NAME))
        self.setupWidgets()
        self.updateText(self.mgr["local"])
        self.exec()
    
    def setupWidgets(self):
        button_box = self.form.buttonBox
        restore_btn = button_box.addButton(QDialogButtonBox.RestoreDefaults)
        help_btn = button_box.addButton(QDialogButtonBox.Help)
        help_btn.clicked.connect(self.onHelpRequested)
        restore_btn.clicked.connect(self.onRestoreDefaults)
    
    def updateText(self, conf):
        self.form.text.setPlainText(
            json.dumps(conf, ensure_ascii=False, sort_keys=True,
                       indent=4, separators=(',', ': ')))
    
    def onRestoreDefaults(self):
        default_conf = self.mgr.defaults["local"]
        self.updateText(default_conf)
        tooltip("די פעליקע ווערטן זענען צוריקגעשטעלט", parent=self)
        
    def onHelpRequested(self):
        docs_path = os.path.join(PATH_THIS_ADDON, "config.md")
        if not os.path.exists(docs_path):
            return False
        with open(docs_path, "r") as f:
            html = markdown2.markdown(f.read())
        dialog = HTMLViewer(html, title="הילף מיט די איינשטעלונגען פון {}".format(
            ADDON.NAME), parent=self)
        dialog.show()
    
    def accept(self):
        txt = self.form.text.toPlainText()
        error = None
        try:
            new_conf = json.loads(txt)
        except ValueError as e:
            new_conf = None
            error = repr(e)
            
        if new_conf and not isinstance(new_conf, dict):
            error = "דער הויפט אביעקט מוז זיין א ווערטערבוך."

        if error:
            showInfo("די איינשטעלונגען זעען אויס אומגילטיג. מאכט זיכער אז עס איז נישט דא "
                     "א שרייב טעות אדער א פארגעסענער קאנטראל סימן (למשל קאמאס, קלאמערן אאז\"וו). "
                     "די אריגינעלע טעות מעלדונג:\n\n{}"
                     "\n\nאויב איר זענט נישט זיכער וואס איז געשען, קענט איר אנהייבן פון פריש "
                     "מיט א קליק אויף 'שטעלט צוריק די פעליקע ווערטן' "
                     "אינעם איינשטעלונגען פענצטער.".format(error))
            return
        
        act = self.mgr.conf_updated_action
        if act:
            act(new_conf)
        
        super(ConfigEditor, self).accept()
