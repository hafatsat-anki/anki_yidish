# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import os
from typing import NamedTuple

from anki.collection import Collection, ImportAnkiPackageRequest
from anki.notes import NoteId
from anki.utils import tmpdir
from aqt import mw
from aqt.import_export.importing import ApkgImporter  #, show_import_log, stringify_log

from _shared_libs.haf_logging import get_logger

logger = get_logger("external_import")


class ApkgImporter_(ApkgImporter):
    def __init__(self, col_name, temp_col):
        super().__init__()
        self.col_name =col_name
        self.temp_col : Collection = temp_col

    def do_import_(self) -> None:
        if isinstance(self.col_name, str):
            self.current_col = self.col_name

            request = ImportAnkiPackageRequest(package_path = self.current_col)
            self.temp_col.import_anki_package(request)
            self.temp_col.db.modified_in_python = True
            # self.temp_col.save()
            self.temp_col.close( downgrade=False)
            # print(self.temp_col.import_anki_package(self.current_col))



class NameId(NamedTuple):
    name: str
    id: int

    @classmethod
    def none_type(cls) -> 'NameId':
        # !
        # return cls('None (create new if needed)', -1)
        return cls('אן ענדערונג', -1)


def sorted_decks_and_ids(col: Collection) -> list[NameId]:
    return sorted(NameId(deck.name, deck.id) for deck in col.decks.all_names_and_ids())




class CollectionManager:
    """This class keeps other collections (profiles) open and can switch between them."""

    def __init__(self):
        self._opened_cols: dict[str, Collection] = {}
        self._current_name: str | None = None

    @property
    def name(self) -> str | None:
        if not self.is_opened:
            raise RuntimeError("Collection vanished or was never opened.")
        return self._current_name

    @property
    def col(self):
        return self._opened_cols[self.name]

    @property
    def media_dir(self):
        return self.col.media.dir()

    @staticmethod
    def col_name_and_id() -> NameId:
        return NameId("די גאנצע זאמלונג", -1)


    @property
    def is_opened(self) -> bool:
        # return (self._current_name is not None) and (self._current_name in self._opened_cols)
        return True

    def close(self):
        if self.is_opened:
            self._current_name = None

    def close_all(self):
        for col in self._opened_cols.values():
            col.close()
        self._current_name = None
        self._opened_cols.clear()

    def open(self, col_name: str, temp_col = None) -> None:
        if not col_name.endswith("collection.anki2"):
            parts = col_name.replace("\\", "/").split("/")
            short_col_name = parts[-4] + parts[-3] + parts[-2] + parts[-1]
            name = os.path.join(tmpdir(), short_col_name)
            colpath = os.path.join(name, "collection.anki2")
            if col_name not in self._opened_cols:
                if not os.path.exists(name):
                    os.mkdir(name)
                    ApkgImporter_(col_name, Collection(colpath)).do_import_()
                # else: התיקייה כבר קיימת מייבוא קודם, צלח לפתיחת האוסף הקיים
            self._opened_cols[col_name] = Collection(colpath)
        else:  #מהמאגר שאלות
            colpath = col_name
            self._opened_cols[col_name] = temp_col
        self.file = colpath
        self._current_name = col_name


    def deck_names_and_ids(self) -> list[NameId]:
        return sorted_decks_and_ids(self.col)

    def find_notes(self, deck: NameId, filter_text: str):
        if deck == self.col_name_and_id():
            query = filter_text if filter_text.strip() else "deck:*"
            result = self.col.find_notes(query=query)
            return result
        else:
            query = f'"deck:{deck.name}" {filter_text}'
            result = self.col.find_notes(query=query)
            return result

    def get_note(self, note_id: NoteId):
        return self.col.get_note(note_id)
