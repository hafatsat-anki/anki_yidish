
# Batch Editing Add-on for Anki
#
# Copyright (C) 2016-2023  Aristotelis P. <https://glutanimate.com/>
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

import os
import tempfile
from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from anki.config import Config
from aqt.qt import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QIcon,
    QKeySequence,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    Qt,
    QVBoxLayout,
)
from aqt.utils import askUser, getFile, showCritical, tooltip

from .collection import EditMode
from .operation import batch_edit_notes

if TYPE_CHECKING:
    from anki.collection import Collection
    from anki.notes import NoteId
    from aqt.browser.browser import Browser


class BatchEditDialog(QDialog):
    """Browser batch editing dialog"""

    def __init__(
        self, browser: "Browser", collection: "Collection", nids: Sequence["NoteId"]
    ):
        QDialog.__init__(self, parent=browser)
        self._browser = browser
        self._collection = collection
        self._nids = nids

        text_field_label = QLabel("אינהאלט צוצולייגן אדער צו פארבייטן מיט: (צייכנט אן קארטלעך אין דער ליסטע איידער איר עפנט דעם פענצטער)")
        image_button = QPushButton(self)
        image_button.clicked.connect(self.insert_media)
        image_button.setIcon(QIcon("batch-editing:icons/attach.svg"))
        image_button.setToolTip("בייגט צו א מידיא טעקע (למשל א בילד)")
        press_action = QAction(self)
        press_action.triggered.connect(image_button.animateClick)
        press_action.setShortcut(QKeySequence("Alt+i"))
        image_button.addAction(press_action)
        top_hbox = QHBoxLayout()
        top_hbox.addWidget(text_field_label)
        top_hbox.insertStretch(1, stretch=1)
        top_hbox.addWidget(image_button)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setTabChangesFocus(True)

        field_label = QLabel("צולייגן אדער פארבייטן אין דעם פעלד:")
        self.field_selector = QComboBox()
        fields = self.get_fields()
        if fields is None:
            showCritical("טעות: מען קען נישט דערקענען דעם סארט רשומה")
            self.close()
            return
        self.field_selector.addItems(fields)
        field_hbox = QHBoxLayout()
        field_hbox.addWidget(field_label)
        field_hbox.addWidget(self.field_selector)
        field_hbox.setAlignment(Qt.AlignmentFlag.AlignLeft)

        button_box = QDialogButtonBox(Qt.Orientation.Horizontal, self)
        add_after_button = cast(
            QPushButton,
            button_box.addButton("לייגט צו &נאכדעם", QDialogButtonBox.ButtonRole.ActionRole),
        )
        add_before_button = cast(
            QPushButton,
            button_box.addButton("לייגט צו &פארדעם", QDialogButtonBox.ButtonRole.ActionRole),
        )
        replace_button = cast(
            QPushButton,
            button_box.addButton("&פארבייטן", QDialogButtonBox.ButtonRole.ActionRole),
        )
        close_button = cast(
            QPushButton,
            button_box.addButton("&אפזאגן", QDialogButtonBox.ButtonRole.RejectRole),
        )
        add_after_button.setToolTip("לייגט צו פאר דעם אינהאלט פונעם אויסגעקליבענעם פעלד")
        add_before_button.setToolTip("לייגט צו נאך דעם אינהאלט פונעם אויסגעקליבענעם פעלד")
        replace_button.setToolTip("פארבייט דעם אינהאלט פונעם אויסגעקליבענעם פעלד")
        add_after_button.clicked.connect(lambda _: self.on_confirm(EditMode.ADD_AFTER))
        add_before_button.clicked.connect(
            lambda _: self.on_confirm(EditMode.ADD_BEFORE)
        )
        replace_button.clicked.connect(lambda _: self.on_confirm(EditMode.REPLACE))
        close_button.clicked.connect(self.close)

        self.checkbox_html = QCheckBox(self)
        self.checkbox_html.setText("לייגט אריין אלס HTML")
        self.checkbox_html.setChecked(False)
        shortcut = QShortcut(
            QKeySequence("Alt+H"),
            self,
        )
        shortcut.activated.connect(self.checkbox_html.toggle)

        bottom_hbox = QHBoxLayout()
        bottom_hbox.addWidget(self.checkbox_html)
        bottom_hbox.addWidget(button_box)

        vbox_main = QVBoxLayout()
        vbox_main.addLayout(top_hbox)
        vbox_main.addWidget(self.text_edit)
        vbox_main.addLayout(field_hbox)
        vbox_main.addLayout(bottom_hbox)
        self.setLayout(vbox_main)
        self.text_edit.setFocus()
        self.setMinimumWidth(540)
        self.setMinimumHeight(400)
        self.setWindowTitle("רשומות אויסגעקליבן צו רעדאקטירן אינאיינעם")

    def get_fields(self) -> list[str] | None:
        nid = self._nids[0]
        model = self._collection.get_note(nid).note_type()
        if model is None:
            return None
        fields = self._collection.models.field_names(model)
        return fields

    def insert_media(self):
        media_file = self.get_clipboard()
        if not media_file:
            media_file = self.choose_file()
        if not media_file:
            return
        if not (editor := self._browser.editor):
            return
        filename = self._collection.media.add_file(media_file)
        html = editor.fnameToLink(filename)
        html = self._browser.editor._addMedia(media_file, canDelete=True)
        # need to unescape images again:"
        if hasattr(self._collection.media, "escape_images"):
            html = self._collection.media.escape_images(html, unescape=True)
        else:
            html = self._collection.media.escapeImages(  # type: ignore[attr-defined]
                html, unescape=True
            )
        current = self.text_edit.toPlainText()
        fragments = []
        if current:  # avoid duplicate newlines
            fragments = [*current.strip("\n").split("\n"), html]
            new = "\n".join(fragments)
        else:
            new = html
        self.text_edit.setPlainText(new)

    def choose_file(self) -> str:
        key = (
            "Media "
            "(*.jpg *.png *.gif *.tiff *.svg *.tif *.jpeg "
            "*.mp3 *.ogg *.wav *.avi *.ogv *.mpg *.mpeg *.mov *.mp4 "
            "*.mkv *.ogx *.ogv *.oga *.flv *.swf *.flac)"
        )
        return cast(str, getFile(self, "Add Media", None, key, key="media"))

    def get_clipboard(self) -> str | None:
        if (
            not (clip := QApplication.clipboard())
            or not (mimedata := clip.mimeData())
            or not mimedata.imageData()
        ):
            return None

        if self._collection.get_config_bool(Config.Bool.PASTE_IMAGES_AS_PNG):
            suffix = ".png"
        else:
            suffix = ".jpg"
        handle, image_path = tempfile.mkstemp(suffix=suffix)
        clip.image().save(image_path)
        clip.clear()
        if os.stat(image_path).st_size == 0:
            return None
        return image_path

    def on_confirm(self, mode: EditMode):
        browser = self._browser
        note_ids = self._nids
        field_name = self.field_selector.currentText()
        text = self.text_edit.toPlainText()
        is_html = self.checkbox_html.isChecked()
        if mode == EditMode.REPLACE:
            q = (
                f"די פעולה וועט פארבייטן דעם אינהאלט פון <b>'{field_name}'</b> פעלד "
                f"אין <b>{len(note_ids)} אויסגעקליבענע רשומות</b>. אויספירן?"
            )
            if not askUser(q, parent=self):
                return

        def on_edits_complete(count: int):
            self.close()
            tooltip(f"{count} רשומות זענען <b>דערהיינטיגט</b>", parent=browser)

        batch_edit_notes(
            parent=self,
            mode=mode,
            note_ids=note_ids,
            field_name=field_name,
            html=text,
            is_html=is_html,
            on_complete=on_edits_complete,
        )
