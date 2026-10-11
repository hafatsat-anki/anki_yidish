import json
import re
from bisect import bisect_right
from copy import deepcopy
from pathlib import Path

from aqt.utils import showText, tooltip
from _shared_libs.haf_notifications import show_failure
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from .config import *
from .custom_importer import *
from .get_todays_daf import letters_to_num
from .import_templates import getOrCreateModels, repo_notetypes_names
from .prakim_and_simanim import *
from .rashi_parashot import RASHI_COLLECTION_NAME, RASHI_PARASHOT
from .search_match import _is_gematria_term, ordered_terms_match

path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "מאגר השאלות")
current_directory = str(Path(__file__).parent.resolve())

# --- קבוע חדש לשמירת טקסט החיפוש בזיכרון ---
SEARCH_TEXT_ROLE = Qt.ItemDataRole.UserRole + 10

_SEARCH_TOKEN_RE = re.compile(r"[\w\u0590-\u05ff]+", re.UNICODE)


def _join_search_path(*parts: str) -> str:
    cleaned = [str(part).strip().lower() for part in parts if str(part or "").strip()]
    return "::".join(cleaned)


def _chapter_key_from_display(display_name: str) -> str:
    tokens = _SEARCH_TOKEN_RE.findall((display_name or "").lower())
    if tokens and _is_gematria_term(tokens[-1]):
        return tokens[-1]
    return ""


# -------------------------------------------

class MultiTermProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_terms = []

    def setFilterText(self, text):
        # #193 — כל מילה הופכת לרצף תווים שצריך להופיע באותו סדר בטקסט; אותיות באמצע מותרות, היפוך אסור.
        self.filter_terms = [t.lower() for t in text.split() if t]
        self.invalidateFilter()



    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filter_terms:
            return True

        index = self.sourceModel().index(source_row, 0, source_parent)

        # --- אופטימיזציה: שליפה ישירה מהזיכרון במקום חישוב מחדש ---
        # אנו שולפים את הטקסט המלא שהכנו מראש בעת יצירת הפריט
        full_path_text = self.sourceModel().data(index, SEARCH_TEXT_ROLE)

        # במקרה נדיר שהמידע לא קיים, נשתמש בטקסט הרגיל
        if not full_path_text:
            full_path_text = str(self.sourceModel().data(index) or "").lower()
        # --------------------------------------------------------

        return ordered_terms_match(full_path_text, self.filter_terms)


def open_file(self) -> None:
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo_explain.pdf")
    if hasattr(mw, "open_pdf_file"):
        mw.open_pdf_file(pdf_path, parent=self)
    else:
        from aqt.utils import openLink
        openLink(pdf_path)


class repo_item(QtGui.QStandardItem):
    def __init__(self, name):
        super().__init__(name)
        self.path = ""
        self.paths = []


def _item_import_paths(item) -> list[str]:
    """מחזיר נתיב יחיד או את שני חצאי הפרק המוצגים כאפשרות אחת."""
    paths = list(getattr(item, "paths", []) or [])
    if paths:
        return paths
    path = getattr(item, "path", "")
    return [path] if path else []


class MyTree(QDialog):
    def __init__(self, parent=mw):
        super(self.__class__, self).__init__(parent)
        self.setWindowTitle("שאלות זאמלונג")
        self.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.gridLayout = QtWidgets.QVBoxLayout(self)
        self.gridLayout.setObjectName("gridLayout")

        self.explain_label = QLabel(
            '''<div style="text-align: center;"><a href="00.com"><span style=" text-decoration: underline; color:#0000ff;">קליקט דא פאר אן ערקלערונג פון די פארשידענע מאגרים</span></a></div>''')
        self.explain_label.linkActivated.connect(lambda: open_file(self))
        self.label = QtWidgets.QLabel(self)
        self.label.setText(
            "הערה: אן אנגעצייכנטע טעקע בלייבט אנגעצייכנט אויך נאכן טוישן דעם זוכן.\nביים צעטיילן אין פרקים, געהערט דער לעצטער בלאט פון א פרק צום קומענדיגן פרק.")

        self.filterEdit = QtWidgets.QLineEdit()
        self.filterEdit.setPlaceholderText("זוכן...")
        self._search_timer = QtCore.QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._applyFilter)
        self.filterEdit.textChanged.connect(self.onTextChanged)
        self.treeView = QtWidgets.QTreeView(self)
        self.treeView.setObjectName("treeView")
        self.treeView.header().setVisible(False)
        self.treeView.clicked.connect(self.on_tree_clicked)

        # Checkboxes
        self.separte_by_prakim_button = QtWidgets.QCheckBox(self)
        self.separte_by_prakim_button.setText(
            'טיילט דעם מאגר לויט פרקים/פרשיות אין ש"ס און חומש / ענינים אין שו"ע'
        )
        self.separte_by_prakim_button.setCheckable(True)
        self.separte_by_prakim_button.setChecked(gc("repo_separte_by_prakim"))

        # Group by Masechet
        self.group_by_masechet_button = QtWidgets.QCheckBox(self)
        self.group_by_masechet_button.setText('גרופירט לויט מסכת (אנשטאט לויטן רב)')
        self.group_by_masechet_button.setCheckable(True)
        self.group_by_masechet_button.toggled.connect(self.reload_tree_structure)

        self.allow_dupes = QtWidgets.QCheckBox(self)
        self.allow_dupes.setText("אימפארטירט אויך עקזיסטירנדע שאלות (קען שאפן טאפלטע רשומות)")
        self.allow_dupes.setCheckable(True)
        self.allow_dupes.setChecked(gc("repo_allow_dupes"))

        # Matchscope
        self.matchscope_row = QHBoxLayout()
        self.matchscope_row.setContentsMargins(0, 0, 0, 0)
        self.matchscope_row.setSpacing(3)
        self.matchscope_row.addSpacing(3)
        self.matchscope_label = QtWidgets.QLabel()
        self.matchscope_label.setText("א רשומה איז טאפלט ווען: ")
        self.matchscope_notetype = QtWidgets.QRadioButton()
        self.matchscope_notetype.setText("דער זעלבער סארט רשומה")
        self.matchscope_notetype.setCheckable(True)
        self.matchscope_notetype.setChecked(gc("matchscope_notetype"))
        self.matchscope_notetype_and_deck = QtWidgets.QRadioButton()
        self.matchscope_notetype_and_deck.setText("דער זעלבער פעקל און סארט רשומה")
        self.matchscope_notetype_and_deck.setCheckable(True)
        self.matchscope_notetype_and_deck.setChecked(gc("matchscope_notetype_and_deck"))
        self.matchscope_row.addWidget(self.matchscope_label)
        self.matchscope_row.addWidget(self.matchscope_notetype)
        self.matchscope_row.addWidget(self.matchscope_notetype_and_deck)
        self.matchscope_row.addSpacing(110)
        self.matchscope_box = QGroupBox()
        self.matchscope_box.setLayout(self.matchscope_row)

        # Shas/Daf
        self.shas_or_daf_row = QHBoxLayout()
        self.shas_or_daf_row.addSpacing(3)
        self.shas_or_daf_row.setSpacing(3)
        self.shas_or_daf_row.setContentsMargins(0, 0, 0, 0)
        self.shas_or_daf_label = QtWidgets.QLabel()
        self.shas_or_daf_label.setText('אימפארטירט שאלות פונעם ש"ס מאגר: ')
        self.import_to_shas_deck = QtWidgets.QRadioButton("צום ש\"ס פעקל")
        self.import_to_shas_deck.setCheckable(True)
        self.import_to_shas_deck.setChecked(gc("import_to_shas_deck"))
        self.import_to_daf_deck = QtWidgets.QRadioButton()
        self.import_to_daf_deck.setText("צום דף היומי פעקל")
        self.import_to_daf_deck.setChecked(gc("import_to_daf_deck"))
        self.shas_or_daf_row.addWidget(self.shas_or_daf_label)
        self.shas_or_daf_row.addWidget(self.import_to_shas_deck)
        self.shas_or_daf_row.addWidget(self.import_to_daf_deck)
        self.shas_or_daf_row.addSpacing(90)
        self.shas_or_daf_box = QGroupBox()
        self.shas_or_daf_box.setLayout(self.shas_or_daf_row)

        # Check notes
        self.check_notes_row = QHBoxLayout()
        self.check_notes_row.setSpacing(3)
        self.check_notes_row.addSpacing(3)
        self.check_notes_row.setContentsMargins(0, 0, 0, 0)
        self.all_notes = QtWidgets.QRadioButton()
        self.all_notes.setText("אימפארטירט אלע שאלות פון די אנגעצייכנטע טעקעס")
        self.check_notes = QtWidgets.QRadioButton()
        self.check_notes.setText("קלייבט אויס וועלכע שאלות איר ווילט אימפארטירן")
        self.all_notes.setChecked(gc("all_notes"))
        self.check_notes.setChecked(not gc("all_notes"))
        self.check_notes_row.addWidget(self.all_notes)
        self.check_notes_row.addWidget(self.check_notes)
        self.check_notes_box = QGroupBox()
        self.check_notes_box.setLayout(self.check_notes_row)

        self.labe2 = QtWidgets.QLabel(self)
        self.labe2.setText(
            '<div style="text-align: center;"><span style="color: rgb(255, 40, 40);">--דער מאגר איז בלויז פאר חזרות נאכן גוט לערנען דעם נושא--</span></div>' + '<div style="text-align: center;"><span style="color: rgb(255, 40, 40);">--די שאלות זענען נישט מגיה געווען און מען קען זיך נישט פארלאזן אויף זיי למעשה--</span></div>')

        # #146 — ריווח קומפקטי אך לא דחוס מחזיר לחלון הראשי קריאות בלי להוסיף צבעים שפוגעים במצב לילה.
        self.gridLayout.setContentsMargins(8, 6, 8, 6)
        self.gridLayout.setSpacing(5)
        self.setMinimumSize(520, 600)
        self.setStyleSheet("QGroupBox { margin-top: 4px; padding: 4px; } QCheckBox, QRadioButton, QLabel { margin: 1px; }")
        self.gridLayout.addWidget(self.explain_label)
        self.gridLayout.addWidget(self.label)
        self.gridLayout.addWidget(self.filterEdit)
        self.gridLayout.addWidget(self.treeView)
        self.gridLayout.addWidget(self.separte_by_prakim_button)
        self.gridLayout.addWidget(self.group_by_masechet_button)
        self.gridLayout.addWidget(self.allow_dupes)
        self.gridLayout.addWidget(self.matchscope_box)
        self.gridLayout.addWidget(self.shas_or_daf_box)
        self.gridLayout.addWidget(self.check_notes_box)
        self.gridLayout.addWidget(self.labe2)

        self.model = QStandardItemModel()
        self.model.itemChanged.connect(self.on_item_changed)

        self.proxyModel = MultiTermProxyModel(self)
        self.proxyModel.setRecursiveFilteringEnabled(True)
        self.proxyModel.setAutoAcceptChildRows(True)
        self.proxyModel.setFilterKeyColumn(0)
        self.proxyModel.setSourceModel(self.model)
        self.treeView.setModel(self.proxyModel)

        self.daf_dialog = QPushButton("&אויטאמאטיש אימפארטירן לויטן דף היומי")
        from .daf_hayomi import open_settings_dialog
        self.daf_dialog.clicked.connect(lambda: open_settings_dialog())
        self.daily_tracks_btn = QPushButton("טעגליכע הספקים")
        self.daily_tracks_btn.clicked.connect(lambda: _import_open_track_manager(self))
        self.public_tracks_btn = QPushButton("לערנען סדרים לויטן ציבור קאלענדאר")
        self.public_tracks_btn.clicked.connect(_import_open_public_tracks)
        self.show_log_checkbox = QtWidgets.QCheckBox("ווייזט א באריכט ביים ענדע")
        self.show_log_checkbox.setChecked(gc("show_import_log", True))
        self.acceptButton = QPushButton("&באשטעטיקן")
        self.acceptButton.clicked.connect(self.accept)
        self.rejectButton = QPushButton("&אפזאגן")
        self.rejectButton.clicked.connect(self.reject)

        self.quick_actions_row = QHBoxLayout()
        self.daf_dialog.hide()
        self.public_tracks_btn.hide()
        self.quick_actions_row.addWidget(self.daily_tracks_btn)

        self.button_box = QHBoxLayout()
        self.button_box.addStretch()
        self.button_box.addWidget(self.show_log_checkbox)
        self.button_box.addWidget(self.acceptButton)
        self.button_box.addWidget(self.rejectButton)

        self.gridLayout.addLayout(self.quick_actions_row)
        self.gridLayout.addLayout(self.button_box)
        self.filterEdit.setFocus()
        # #146 — רוחב התחלתי גדול יותר מונע שבירת שורות צפופה בשורות האפשרויות.
        self.resize(560, 640)
        self.pages_to_import = []
        self.onLoadSettings()

        self.separte_by_prakim_button.clicked.connect(self.separte_by_prakim_)

    def reorganize_by_masechet(self, conf):
        new_conf = []
        for subject in conf:
            if subject["name"] == "שס":
                new_shas = {"name": "שס", "type": "directory", "children": []}
                masechet_map = {}

                for rabbi in subject["children"]:
                    rabbi_name = rabbi["name"]
                    for masechet in rabbi["children"]:
                        masechet_name = masechet["name"]

                        files_with_original_path = []
                        for file_node in masechet["children"]:
                            new_file = deepcopy(file_node)
                            new_file["original_rel_path"] = f"{rabbi_name}/{masechet_name}/{new_file['name']}"
                            files_with_original_path.append(new_file)

                        new_rabbi_node = {
                            "name": rabbi_name,
                            "type": "directory",
                            "children": files_with_original_path
                        }

                        if masechet_name not in masechet_map:
                            masechet_map[masechet_name] = []
                        masechet_map[masechet_name].append(new_rabbi_node)

                for masechet_name, rabbis in masechet_map.items():
                    new_shas["children"].append({
                        "name": masechet_name,
                        "type": "directory",
                        "children": rabbis
                    })
                new_conf.append(new_shas)
            else:
                new_conf.append(subject)
        return new_conf

    def reload_tree_structure(self):
        # ניתוק ה-proxy וה-view במהלך הבנייה מחדש כדי שכל appendRow
        # לא יפעיל filterAcceptsRow כשיש פילטר פעיל.
        current_filter_text = self.filterEdit.text()
        self.treeView.setUpdatesEnabled(False)
        self.treeView.setModel(None)
        self.proxyModel.setSourceModel(None)
        try:
            self.model.clear()
            self.onLoadSettings()
        finally:
            self.proxyModel.setSourceModel(self.model)
            self.treeView.setModel(self.proxyModel)
            if current_filter_text:
                self.proxyModel.setFilterText(current_filter_text)
                self.treeView.expandAll()
            self._last_filter_text = current_filter_text
            self.treeView.setUpdatesEnabled(True)

    def separte_by_prakim_(self, first_run=False):
        if not self.separte_by_prakim_button.isChecked() and not first_run:
            self.reload_tree_structure()
            return

        is_grouped_by_masechet = self.group_by_masechet_button.isChecked()
        current_filter_text = self.filterEdit.text()

        # אם הפרוקסי כבר מנותק (קריאה מקוננת מתוך reload_tree_structure / onLoadSettings),
        # נמנע מ-detach/reattach כפול — ההורה ידאג לחיבור מחדש בסיום.
        already_detached = self.proxyModel.sourceModel() is None

        if not already_detached:
            self.treeView.setUpdatesEnabled(False)
            self.treeView.setModel(None)
            self.proxyModel.setSourceModel(None)
        try:
            self._separte_by_prakim_inner(is_grouped_by_masechet, first_run)
        finally:
            if not already_detached:
                self.proxyModel.setSourceModel(self.model)
                self.treeView.setModel(self.proxyModel)
                if current_filter_text:
                    self.proxyModel.setFilterText(current_filter_text)
                    self.treeView.expandAll()
                self._last_filter_text = current_filter_text
                self.treeView.setUpdatesEnabled(True)

    def _separte_by_prakim_inner(self, is_grouped_by_masechet, first_run):
        for row_num in range(0, self.model.rowCount()):
            item1 = self.model.item(row_num)

            if item1.text() == "שס":
                if is_grouped_by_masechet:
                    self.handle_prakim_grouped_by_masechet(item1, first_run)
                else:
                    self.handle_prakim_standard(item1, first_run)

            elif item1.text() in ("משנה ברורה", "שו''ע"):
                self.handle_prakim_standard(item1, first_run)

            elif item1.text() == "על התורה":
                self.handle_rashi_parashot(item1)

    @staticmethod
    def _rashi_segment_order(item):
        filename = item.path.replace("\\", "/").rsplit("/", 1)[-1]
        segment = filename.removesuffix(".txt").removeprefix("פרק ")
        chapter, _, verse = segment.partition("_")
        return letters_to_num(chapter), letters_to_num(verse or "א")

    def handle_rashi_parashot(self, torah_item):
        """מקבץ את מקטעי חומש רש״י תחת 54 פרשות בלי לשנות את נתיבי הקבצים."""
        collection_item = next(
            (
                torah_item.child(row)
                for row in range(torah_item.rowCount())
                if torah_item.child(row)
                and torah_item.child(row).text() == RASHI_COLLECTION_NAME
            ),
            None,
        )
        if collection_item is None:
            return

        for book_row in range(collection_item.rowCount()):
            book_item = collection_item.child(book_row)
            boundaries = RASHI_PARASHOT.get(book_item.text()) if book_item else None
            if not boundaries:
                continue

            current_rows = [
                book_item.takeRow(0) for _row in range(book_item.rowCount())
            ]
            current_rows.sort(key=lambda row: self._rashi_segment_order(row[0]))
            boundary_names = list(boundaries)
            boundary_orders = [
                self._rashi_segment_order_from_label(label)
                for label in boundaries.values()
            ]
            grouped_rows = {name: [] for name in boundary_names}

            for row in current_rows:
                segment_order = self._rashi_segment_order(row[0])
                boundary_index = bisect_right(boundary_orders, segment_order) - 1
                if boundary_index < 0:
                    boundary_index = 0
                grouped_rows[boundary_names[boundary_index]].append(row)

            book_search_text = book_item.data(SEARCH_TEXT_ROLE) or book_item.text()
            for parasha_name in boundary_names:
                rows = grouped_rows[parasha_name]
                if not rows:
                    continue
                parasha_item = repo_item(f"פרשת {parasha_name}")
                parasha_item.setEditable(False)
                parasha_item.setCheckable(True)
                parasha_item.setAutoTristate(False)
                parasha_search_text = _join_search_path(
                    book_search_text, parasha_item.text()
                )
                parasha_item.setData(parasha_search_text, SEARCH_TEXT_ROLE)
                for row in rows:
                    file_item = row[0]
                    file_item.setData(
                        _join_search_path(parasha_search_text, file_item.text()),
                        SEARCH_TEXT_ROLE,
                    )
                    parasha_item.appendRow(row)
                book_item.appendRow(parasha_item)
            book_item.childs_moved = True

    def handle_rashi_chapters(self, torah_item):
        """מציג פרק אחד גם כאשר גבול פרשה פיצל אותו לשני קובצי מקור."""
        collection_item = next(
            (
                torah_item.child(row)
                for row in range(torah_item.rowCount())
                if torah_item.child(row)
                and torah_item.child(row).text() == RASHI_COLLECTION_NAME
            ),
            None,
        )
        if collection_item is None:
            return

        for book_row in range(collection_item.rowCount()):
            book_item = collection_item.child(book_row)
            if book_item is None:
                continue
            rows = [book_item.takeRow(0) for _ in range(book_item.rowCount())]
            rows.sort(key=lambda row: self._rashi_segment_order(row[0]))
            grouped = {}
            for row in rows:
                chapter, _verse = self._rashi_segment_order(row[0])
                grouped.setdefault(chapter, []).append(row[0])

            book_search_text = book_item.data(SEARCH_TEXT_ROLE) or book_item.text()
            for chapter in sorted(grouped):
                source_items = grouped[chapter]
                chapter_text = (
                    source_items[0].path.replace("\\", "/").rsplit("/", 1)[-1]
                    .removesuffix(".txt").removeprefix("פרק ").split("_", 1)[0]
                )
                chapter_item = repo_item(f"פרק {chapter_text}")
                chapter_item.setEditable(False)
                chapter_item.setCheckable(True)
                chapter_item.setAutoTristate(False)
                chapter_item.paths = [item.path for item in source_items]
                chapter_item.setData(
                    _join_search_path(book_search_text, chapter_item.text()),
                    SEARCH_TEXT_ROLE,
                )
                book_item.appendRow(chapter_item)
            book_item.childs_moved = True

    @staticmethod
    def _rashi_segment_order_from_label(label):
        chapter, _, verse = label.partition("_")
        return letters_to_num(chapter), letters_to_num(verse or "א")

    def handle_prakim_standard(self, item1, first_run):
        for rav_num in range(0, item1.rowCount()):
            rav: QStandardItem = item1.child(rav_num)
            if rav:
                for masechet_num in range(0, rav.rowCount()):
                    masehet_item: QStandardItem = rav.child(masechet_num)
                    masechet_name = masehet_item.text()[2:].split(" (")[0] if "שס" in item1.text() else \
                        masehet_item.text().split(" (")[0]
                    self.process_masechet_prakim(masehet_item, item1.text(), first_run, masechet_name)

    def handle_prakim_grouped_by_masechet(self, item1, first_run):
        for masechet_num in range(0, item1.rowCount()):
            masehet_item: QStandardItem = item1.child(masechet_num)
            masechet_name = masehet_item.text().split(" (")[0]

            for rav_num in range(0, masehet_item.rowCount()):
                rav_item: QStandardItem = masehet_item.child(rav_num)
                self.process_masechet_prakim(rav_item, "שס", first_run, masechet_name)

    def process_masechet_prakim(self, masehet_item, root_name, first_run, masechet_name):
        data_source = None
        if root_name == "שס":
            if shas.get(masechet_name):
                data_source = shas.get(masechet_name)
        elif root_name == "שו''ע":
            if shua.get(masechet_name):
                data_source = shua.get(masechet_name)
        elif root_name == "משנה ברורה":
            data_source = shua['אורח חיים']

        if not data_source:
            return

        # --- שליפת טקסט החיפוש של ההורה (המסכת) ---
        parent_search_text = masehet_item.data(SEARCH_TEXT_ROLE)
        if not parent_search_text:
            # Fallback
            parent_search_text = masehet_item.text().lower()
        # -------------------------------------------

        masehet_item.childs_moved = True
        current_child_rows = []
        for perek_or_daf_num in range(0, masehet_item.rowCount()):
            if (row_child := masehet_item.child(perek_or_daf_num)) is not None:
                current_child_rows.append(row_child)

        def sort_by_daf(daf_item):
            txt = daf_item.text().strip()
            parts = txt.split()
            if not parts:
                return 0
            if root_name == "שו''ע":
                candidate = txt.replace("סימן ", "", 1).split()[0]
            elif root_name == "משנה ברורה":
                # #388 — Most rows are named "סימן א", but contributor archives
                # occasionally contain only the Hebrew number.  Such a title must
                # not prevent the entire repository window from opening.
                candidate = parts[1] if len(parts) > 1 else parts[0]
            else:  # Shas
                candidate = parts[-1]
            return letters_to_num(candidate)

        current_child_rows.sort(key=sort_by_daf, reverse=True)

        for perek, daf in reversed(data_source.items()):
            new_item = repo_item(perek)
            new_item.setEditable(False)
            new_item.setCheckable(True)
            new_item.setAutoTristate(False)
            new_item.path = ""

            # --- שמירת נתיב חיפוש לפרק ---
            new_item_search_text = _join_search_path(parent_search_text, perek)
            new_item.setData(new_item_search_text, SEARCH_TEXT_ROLE)
            # -----------------------------

            masehet_item.insertRow(0, new_item)

            daf_num = letters_to_num(daf)
            while True:
                if len(current_child_rows) > 0:
                    current_daf_num = sort_by_daf(current_child_rows[0])
                    if current_daf_num >= daf_num:
                        # takeRow מחזיר רשימה של פריטים [item_col0, item_col1...]
                        items_list = masehet_item.takeRow(current_child_rows.pop(0).row())
                        daf_item = items_list[0]  # הפריט האמיתי נמצא באינדקס 0

                        # --- עדכון נתיב חיפוש לדף שזז לתוך הפרק ---
                        # מכיוון שהוא זז תחת הפרק, צריך לעדכן לו את טקסט החיפוש שיכלול גם את הפרק
                        current_daf_text = daf_item.text().lower()
                        chapter_key = _chapter_key_from_display(current_daf_text)
                        if chapter_key:
                            daf_search_text = _join_search_path(
                                new_item_search_text, chapter_key, current_daf_text
                            )
                        else:
                            daf_search_text = _join_search_path(new_item_search_text, current_daf_text)
                        daf_item.setData(daf_search_text, SEARCH_TEXT_ROLE)
                        # ------------------------------------------

                        new_item.insertRow(0, items_list)
                    else:
                        break
                else:
                    break

            if new_item.rowCount() == 0:
                masehet_item.removeRow(new_item.row())

    @QtCore.pyqtSlot(str)
    def onTextChanged(self, text):
        self._search_timer.start(200)

    def _applyFilter(self):
        text = self.filterEdit.text()
        if getattr(self, "_last_filter_text", None) == text:
            return
        self._last_filter_text = text
        self.treeView.setUpdatesEnabled(False)
        try:
            self.proxyModel.setFilterText(text)
            if text != "":
                self.treeView.expandAll()
            else:
                self.treeView.collapseAll()
        finally:
            self.treeView.setUpdatesEnabled(True)

    # --- עדכון: הפונקציה מקבלת כעת גם parent_search_text כדי לשרשר אותו ---
    def create_tree(self, conf, current_path="מאגר השאלות", root_menu=None, parent_search_text=""):
        if isinstance(conf, list):
            for i in conf:
                self.create_tree(i, current_path=current_path, root_menu=root_menu,
                                 parent_search_text=parent_search_text)
        elif conf["type"] == "directory":
            name = conf["name"]
            if conf["name"].endswith("$"):
                name = conf["name"][:-1]

            display_name = name.replace("%", " ")
            item = repo_item(display_name)

            # --- חישוב ושמירת טקסט החיפוש ---
            current_search_text = _join_search_path(parent_search_text, display_name)
            item.setData(current_search_text, SEARCH_TEXT_ROLE)
            # -------------------------------

            item.setEditable(False)
            item.setCheckable(True)
            item.setAutoTristate(False)
            item.path = ""
            root_menu.appendRow(item)
            current_path = current_path + "/" + conf["name"]

            # מעבירים את ה-search_text לילדים
            self.create_tree(conf['children'], current_path=current_path, root_menu=item,
                             parent_search_text=current_search_text)

        elif conf['type'] == "file" and conf["name"][-4:] == ".txt":
            if "original_rel_path" in conf:
                file_path = f"מאגר השאלות/שס/{conf['original_rel_path']}"
            else:
                file_path = current_path + "/" + conf["name"]

            display_name = conf["name"][:-4].replace("_", " ")
            # גבול פרשה באמצע פרק מוצג במפורש: "פרק ו פסוק ט".
            rashi_segment = re.fullmatch(
                r"פרק ([^_]+)_([^_]+)", conf["name"][:-4]
            )
            if rashi_segment:
                display_name = (
                    f"פרק {rashi_segment.group(1)} פסוק {rashi_segment.group(2)}"
                )
            item = repo_item(display_name)

            # --- חישוב ושמירת טקסט החיפוש לקובץ ---
            chapter_key = _chapter_key_from_display(display_name)
            if chapter_key:
                current_search_text = _join_search_path(parent_search_text, chapter_key, display_name)
            else:
                current_search_text = _join_search_path(parent_search_text, display_name)
            item.setData(current_search_text, SEARCH_TEXT_ROLE)
            # --------------------------------------

            item.path = file_path
            item.setEditable(False)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            root_menu.appendRow(item)

    def onLoadSettings(self):
        with open(os.path.join(os.path.dirname(__file__), "repo_struct.json"), encoding='utf-8') as settings:
            conf = json.load(settings)["children"]

        # אותו סדר תוכני נשמר גם עבור repo_struct ישן שטרם נבנה מחדש.
        root_order = {
            "שס": 0, "משנה ברורה": 1, "שו''ע": 2, "משניות": 3,
            "תלמוד ירושלמי": 4, "על התורה": 5, "עניינים": 6,
        }
        conf.sort(key=lambda node: root_order.get(node.get("name", ""), 100))

        if self.group_by_masechet_button.isChecked():
            conf = self.reorganize_by_masechet(conf)

        self.create_tree(conf, root_menu=self.model)

        if self.separte_by_prakim_button.isChecked():
            self.separte_by_prakim_(first_run=True)
        else:
            torah_item = next(
                (
                    self.model.item(row)
                    for row in range(self.model.rowCount())
                    if self.model.item(row)
                    and self.model.item(row).text() == "על התורה"
                ),
                None,
            )
            if torah_item is not None:
                self.handle_rashi_chapters(torah_item)

    def on_item_changed(self, item):
        self.model.blockSignals(True)
        try:
            state = item.checkState()

            # פרק חומש מאוחד יכול לייצג שני קובצי מקור.
            for import_path in _item_import_paths(item):
                if state == Qt.CheckState.Checked:
                    if import_path not in self.pages_to_import:
                        self.pages_to_import.append(import_path)
                elif state == Qt.CheckState.Unchecked and import_path in self.pages_to_import:
                    self.pages_to_import.remove(import_path)

            # עדכון הילדים
            if item.hasChildren() and state != Qt.CheckState.PartiallyChecked:
                self.update_children(item, state)
                self.update_parent_state(item)

            # עדכון ההורים כלפי מעלה
            parent = item.parent()
            while parent:
                self.update_parent_state(parent)
                parent = parent.parent()

        finally:
            self.model.blockSignals(False)

    def update_children(self, parent, state):
        # בדיקה האם יש פילטר פעיל
        filter_text = self.filterEdit.text().strip().lower()
        has_filter = bool(filter_text)

        # פיצול מילות חיפוש אם יש
        filter_terms = filter_text.split() if has_filter else []

        for i in range(parent.rowCount()):
            child = parent.child(i)

            should_update = True
            if has_filter:
                # במקום לשאול את ה-Proxy (פעולה כבדה), בודקים את ה-Data ששמרנו
                # זה פעולת מחרוזת פשוטה ומהירה מאוד בזיכרון
                child_search_text = child.data(SEARCH_TEXT_ROLE)
                if not child_search_text:
                    child_search_text = ""

                # #193 — אותו מנוע חיפוש כמו התצוגה: מונחים לפי סדר, בלי התאמת אותיות שחוצה מילים.
                if not ordered_terms_match(child_search_text, filter_terms):
                    should_update = False

            if should_update and child.checkState() != state:
                child.setCheckState(state)
                if child.hasChildren():
                    self.update_children(child, state)
                for import_path in _item_import_paths(child):
                    if state == Qt.CheckState.Checked:
                        if import_path not in self.pages_to_import:
                            self.pages_to_import.append(import_path)
                    elif import_path in self.pages_to_import:
                        self.pages_to_import.remove(import_path)

    def update_parent_state(self, parent):
        checked_count = 0
        partial_count = 0
        count = parent.rowCount()

        for i in range(count):
            state = parent.child(i).checkState()
            if state == Qt.CheckState.Checked:
                checked_count += 1
            elif state == Qt.CheckState.PartiallyChecked:
                partial_count += 1

        if checked_count == count:
            new_state = Qt.CheckState.Checked
        elif checked_count == 0 and partial_count == 0:
            new_state = Qt.CheckState.Unchecked
        else:
            new_state = Qt.CheckState.PartiallyChecked

        if parent.checkState() != new_state:
            parent.setCheckState(new_state)

    def on_tree_clicked(self, index):
        if self.treeView.isExpanded(index):
            self.treeView.collapse(index)
        else:
            self.treeView.expand(index)

    def accept(self) -> None:
        if len(self.pages_to_import) == 0:
            return super().accept()

        config = mw.addonManager.getConfig(__name__)
        separte_by_prakim = self.separte_by_prakim_button.isChecked()
        allow_dupes = 2 if self.allow_dupes.isChecked() else 1
        matchscope = 0 if self.matchscope_notetype.isChecked() else 1
        daf = self.import_to_daf_deck.isChecked()
        group_by_masechet = self.group_by_masechet_button.isChecked()

        config["repo_allow_dupes"] = self.allow_dupes.isChecked()
        config["repo_separte_by_prakim"] = self.separte_by_prakim_button.isChecked()
        config["matchscope_notetype"] = self.matchscope_notetype.isChecked()
        config["matchscope_notetype_and_deck"] = self.matchscope_notetype_and_deck.isChecked()
        config["import_to_shas_deck"] = self.import_to_shas_deck.isChecked()
        config["import_to_daf_deck"] = self.import_to_daf_deck.isChecked()
        config["all_notes"] = self.all_notes.isChecked()
        config["show_import_log"] = self.show_log_checkbox.isChecked()
        mw.addonManager.writeConfig(__name__, config)

        mw.progress.start(label="גרייט צו די מאגר טעקעס...", immediate=True)

        try:
            if self.all_notes.isChecked():
                for n in repo_notetypes_names:
                    getOrCreateModels(mw.col, n)

                mw.progress.update("אימפארטירט טעקעס...")
                result = importFromFolder(self.pages_to_import,
                                          _col=mw.col,
                                          allow_dupes=allow_dupes,
                                          daf=daf,
                                          matchscope=matchscope,
                                          separte_by_prakim=separte_by_prakim,
                                          group_by_masechet=group_by_masechet,
                                          progress_manager=mw.progress)
                if result:
                    if self.show_log_checkbox.isChecked():
                        showText(result, type="html")
                    else:
                        if "ליידיג" in result:
                            # ישנם קבצים ריקים - נוסיף התראה למרות שלא הוצג הלוג המלא
                            tooltip("דער אימפארט איז פארענדיגט, אבער מען האט געפונען ליידיגע טעקעס. קאנטראלירט דעם רעקארד ביים קומענדיגן אימפארט.", period=4000)
                        else:
                            tooltip("דער אימפארט איז מיט הצלחה פארענדיגט")

            else:
                short_col_name = "temp_for_repo_import"
                name = os.path.join(tmpdir(), short_col_name)
                colpath = os.path.join(name, "collection.anki2")
                if not os.path.exists(name):
                    os.mkdir(name)

                try:
                    mw.temp_col = Collection(colpath)
                except Exception as e:
                    show_failure("מען קען נישט עפענען א פארויסקוק פארן אימפארט. עפנט אנקי איבער און פרובירט נאכאמאל.", e)
                    return

                mw.temp_col.decks.remove(d["id"] for d in mw.temp_col.decks.all())
                for n in repo_notetypes_names:
                    getOrCreateModels(mw.temp_col, n)

                mw.progress.update("לאדט א פארויסקוק...")
                importFromFolder(self.pages_to_import,
                                 mw.temp_col,
                                 col_path=colpath,
                                 allow_dupes=allow_dupes,
                                 daf=daf,
                                 matchscope=matchscope,
                                 separte_by_prakim=separte_by_prakim,
                                 group_by_masechet=group_by_masechet,
                                 progress_manager=mw.progress)

        finally:
            mw.progress.finish()
            self.pages_to_import = []

        return super().accept()


def openMyTree():
    MyTree().exec()


mw.form.menuCol.addSeparator()
action_open_settings_dialog = QAction()
action_open_settings_dialog.setText("שאלות זאמלונג")
action_open_settings_dialog.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "inventory_2.png")))
action_open_settings_dialog.triggered.connect(lambda: openMyTree())
mw.form.menuCol.addAction(action_open_settings_dialog)


def _import_open_track_manager(parent=None):
    from .daily_manager import open_daily_manager
    open_daily_manager("custom", parent=parent)


def _import_open_public_tracks():
    from .public_tracks import open_public_tracks
    open_public_tracks()
