# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable

from aqt import mw
from aqt.qt import *
from aqt.utils import disable_help_button, restoreGeom, saveGeom

from .ajt_common.about_menu import tweak_window
from .common import ADDON_NAME
from .config import config, write_config
from .widgets import ItemBox, SpinBox


def fetch_toggleables() -> Iterable[str]:
    for key, value in config.items():
        if isinstance(value, bool):
            yield key


def make_checkboxes() -> dict[str, QCheckBox]:
    return {key: QCheckBox(key.replace('_', ' ').capitalize()) for key in fetch_toggleables()}


class CroProSettingsDialog(QDialog):
    name = 'איינשטעלונגען פאר אימפארטירן איינציגע שאלות'

    def __init__(self, main_form, current_col, *args, **kwargs) -> None:
        QDialog.__init__(self, *args, **kwargs)
        self.main_form = main_form
        self.current_col = current_col
        disable_help_button(self)
        self._setup_ui()
        tweak_window(self)
        restoreGeom(self, self.name, adjustSize=True)

    def _setup_ui(self) -> None:
        self.setMinimumWidth(300)
        self.setWindowTitle(f"אפציעס פאר{ADDON_NAME}")
        self.setLayout(self._make_layout())
        self.connect_widgets()
        self.add_tooltips()

    def _make_layout(self) -> QLayout:
        self.hidden_fields_box = ItemBox(parent=self, initial_values=config['hidden_fields'])
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.checkboxes = make_checkboxes()

        layout = QVBoxLayout()
        layout.addLayout(self._make_form())
        layout.addWidget(self.hidden_fields_box)
        for key, checkbox in self.checkboxes.items():
            layout.addWidget(checkbox)
            checkbox.setChecked(config.get(key))
            if key == "tag_exported_cards":
                checkbox.setText("לייגט צו א צעטל צו אימפארטירטע קארטלעך")
            elif key == "skip_duplicates":
                checkbox.setText("היפט איבער עקזיסטירנדע שאלות")
            elif key == "copy_tags":
                checkbox.setText("קאפירט אויך צעטלעך")
            elif key == "allow_empty_search":
                checkbox.setText("ווייזט שאלות פון דער טעקע אויך אן זוכן")
            elif key == "preview_on_right_side":
                checkbox.setText("ווייזט א פארויסקוק פון די שאלות")
            elif key == "hide_imported_in_session":
                checkbox.setText("באהאלט שאלות אימפארטירט אין דער יעצטיגער סעסיע")
            elif key == "mark_imported_in_session":
                checkbox.setText("צייכנט אן מיט א קאליר שאלות אימפארטירט אין דער יעצטיגער סעסיע")
        layout.addStretch()
        layout.addWidget(self.button_box)
        return layout

    def _make_form(self) -> QFormLayout:
        self.tag_edit = QLineEdit(config['exported_tag'])
        self.max_notes_edit = SpinBox(min_val=10, max_val=10_000, step=50, value=config['max_displayed_notes'])
        self.hidden_fields_edit = QLineEdit()
        self.hidden_fields_edit.setPlaceholderText("לייגט צו א פעלד")

        layout = QFormLayout()
        layout.addRow("העכסטער צאל שאלות צו ווייזן", self.max_notes_edit)
        layout.addRow("צעטל צוצולייגן צו די שאלות", self.tag_edit)
        layout.addRow("באהאלט פעלדער וואס שטימען מיט:", self.hidden_fields_edit)
        return layout

    def connect_widgets(self):
        qconnect(self.button_box.accepted, self.accept)
        qconnect(self.button_box.rejected, self.reject)
        qconnect(self.hidden_fields_edit.textChanged, lambda: self.hidden_fields_box.new_item(self.hidden_fields_edit))

    def add_tooltips(self) -> None:
        self.hidden_fields_edit.setToolTip(
            "באהאלט פעלדער מיט נעמען וואס שטימען מיט דער ליסטע אונטן.\n"
            "דרוקט דעם רווח קנעפל אדער א קאמא צוצולייגן."
        )

    def finished(self, result: int) -> None:
        saveGeom(self, self.name)
        return super().finished(result)

    def accept(self) -> None:
        config['max_displayed_notes'] = self.max_notes_edit.value()
        config['exported_tag'] = self.tag_edit.text()
        config['hidden_fields'] = self.hidden_fields_box.values()
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        write_config()
        from .cropro import MainDialog
        d = MainDialog(parent=mw, current_col=self.current_col)
        d.show()
        return super().accept()

    def reject(self) -> None:
        from .cropro import MainDialog
        d = MainDialog(parent=mw, current_col=self.current_col)
        d.show()
        return super().reject()


