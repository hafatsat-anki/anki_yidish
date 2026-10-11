# Multiple Choice for Anki
#
# Copyright (C) 2018-2021  zjosua <https://github.com/zjosua>
#
# This file is based on __init__.py from Glutanimate's
# Cloze Overlapper Add-on for Anki
#
# Copyright (C)  2016-2019 Aristotelis P. <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program
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
import contextlib
from pathlib import Path

from anki.hooks import wrap
from aqt import gui_hooks, notetypechooser, studydeck, tr
from aqt.notetypechooser import NotetypeChooser
from aqt.qt import *
from PyQt6 import QtCore

from .config import *
from .js_bridge_for_shm15 import *
from .main_templates import *
from .notetype_creator import NotetypeCreatorDialog, show_notetype_creator
from .old_notetypes_updater import ask_before_update_old_notetypes
from .packaging import version


def delayedInit():
    """Setup add-on config and templates, update if necessary"""
    getSyncedConfig()
    getLocalConfig()
    getOrCreateModels()
    if version.parse(mw.col.get_config("mc_conf")['version']) < version.parse(default_conf_syncd['version']):
        updateSyncedConfig()
    if version.parse(mw.pm.profile['mc_conf'].get('version', 0)) < version.parse(default_conf_syncd['version']):
        updateLocalConfig()
    ask_before_update_old_notetypes()



gui_hooks.profile_did_open.append(delayedInit)


def _add_creator_to_models_dialog(buttons, dialog):
    def _open_creator():
        # #186 — אותה יצירה ויזואלית זמינה גם מתוך "נהל סוגי רשומות", ואז הרשימה מתרעננת במקום.
        if NotetypeCreatorDialog(dialog).exec():
            with contextlib.suppress(Exception):
                dialog.refresh_list()

    buttons.insert(1, ("שאפט א נייעם סארט רשומה", _open_creator))
    return buttons


gui_hooks.models_did_init_buttons.append(_add_creator_to_models_dialog)


#  add link to explain about notetypes
def __init__(self: studydeck.StudyDeck, mw, names, accept, title, help, current, cancel, parent, dyn, buttons, geomKey,
             callback, ) -> None:
    if title == tr.qt_misc_choose_note_type():
        label = QLabel(
            '''<a href="00.com"><span style=" text-decoration: underline; color:#0000ff;">קליקט דא פאר אן ערקלערונג פון די סארטן קארטלעך</span></a>''')
        label.linkActivated.connect(lambda: open_file(self))
        self.form.verticalLayout.insertWidget(0, label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        btn_create = QPushButton("+ נייער סארט", self)
        btn_create.clicked.connect(lambda: (self.reject(), NotetypeCreatorDialog(self).exec()))
        self.form.buttonBox.addButton(btn_create, QDialogButtonBox.ButtonRole.ActionRole)


current_directory = str(Path(__file__).parent.resolve())


def open_file(self) -> None:
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "record_types_explanation.pdf")
    if hasattr(mw, "open_pdf_file"):
        mw.open_pdf_file(pdf_path, parent=self)
    else:
        from aqt.utils import openLink
        openLink(pdf_path)

studydeck.StudyDeck.__init__ = wrap(studydeck.StudyDeck.__init__, __init__, "after")


# change text in add card window from "type" to "q type"
def translate_q_type(self: NotetypeChooser, show_label: bool):
    if show_label:
        self.label.setText("שאלה סארט:")


notetypechooser.NotetypeChooser._setup_ui = wrap(notetypechooser.NotetypeChooser._setup_ui, translate_q_type, "after")
