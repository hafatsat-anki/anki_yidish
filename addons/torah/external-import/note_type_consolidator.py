import re
import time

from anki.models import NotetypeId
from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressDialog,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    qconnect,
)
from aqt.utils import askUser, showInfo, tooltip

AUTO_CONSOLIDATE_INTERVAL_SECONDS = 182 * 24 * 60 * 60
LAST_AUTO_RUN_KEY = "note_type_consolidation_last_auto_run"

_DUPLICATE_NOTETYPE_SUFFIXES = [
    re.compile(r"\s*\(\d+\)\s*$"),
    re.compile(r"[-_]\d+\s*$"),
    re.compile(r"[-_](?:copy|עותק|העתק|קאפיע)(?:[-_]\d+)?\s*$", re.IGNORECASE),
    re.compile(r"\s+(?:copy|עותק|העתק|קאפיע)(?:\s+\d+)?\s*$", re.IGNORECASE),
    re.compile(r"[-_][0-9a-f]{4,}\s*$", re.IGNORECASE),
    re.compile(r"\s*\++[0-9a-f]{4,}\s*$", re.IGNORECASE),
    re.compile(r"\s+[a-z][0-9a-f]{4,}\s*$", re.IGNORECASE),
    re.compile(r"\s+[0-9a-f]{4,}\s*$", re.IGNORECASE),
]


def _addon_module_name() -> str:
    return __name__.split(".", 1)[0]


def _addon_config() -> dict:
    try:
        return mw.addonManager.getConfig(_addon_module_name()) or {}
    except Exception:
        return {}


def _write_addon_config(config: dict) -> None:
    try:
        mw.addonManager.writeConfig(_addon_module_name(), config)
    except Exception as err:  # noqa: BLE001
        print(f"[external-import] note_type_consolidator config save failed: {err}")


def _duplicate_notetype_base_candidates(name: str) -> list[str]:
    candidates: list[str] = []
    current = name.strip()
    for _attempt in range(4):
        for pattern in _DUPLICATE_NOTETYPE_SUFFIXES:
            base = pattern.sub("", current).rstrip(" -_+")
            if base and base != current:
                if base not in candidates:
                    candidates.append(base)
                current = base
                break
        else:
            break
    return candidates


def _notetype_structure_signature(note_type: dict) -> tuple:
    fields = tuple(str(field.get("name", "")) for field in note_type.get("flds", []))
    template_names = tuple(str(template.get("name", "")) for template in note_type.get("tmpls", []))
    return note_type.get("type"), fields, template_names


def _find_duplicate_base_notetype(source_type: dict, by_name: dict[str, dict]) -> dict | None:
    source_name = str(source_type.get("name", ""))
    source_id = int(source_type.get("id", 0) or 0)
    matches: list[dict] = []
    for base_name in _duplicate_notetype_base_candidates(source_name):
        base_type = by_name.get(base_name)
        if base_type and int(base_type.get("id", 0) or 0) != source_id:
            matches.append(base_type)
    return matches[-1] if matches else None


def _group_duplicates_without_base(
        note_types: list[dict], by_name: dict[str, dict]
) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for note_type in note_types:
        name = str(note_type.get("name", ""))
        candidates = _duplicate_notetype_base_candidates(name)
        if not candidates:
            continue
        has_named_base = any(
            by_name.get(candidate)
            and int(by_name[candidate].get("id", 0) or 0) != int(note_type.get("id", 0) or 0)
            for candidate in candidates
        )
        if has_named_base:
            continue
        base_name = candidates[-1]
        groups.setdefault(base_name, []).append(note_type)
    return {name: items for name, items in groups.items() if len(items) >= 2}


def auto_consolidate_duplicate_note_types(col) -> dict[str, int]:
    note_types = list(col.models.all())
    by_name = {str(note_type.get("name", "")): note_type for note_type in note_types}
    operations: list[tuple[dict, dict, list[int]]] = []
    skipped_signature: list[tuple[str, str]] = []

    for source_type in note_types:
        base_type = _find_duplicate_base_notetype(source_type, by_name)
        if not base_type:
            continue
        if _notetype_structure_signature(source_type) != _notetype_structure_signature(base_type):
            skipped_signature.append((str(source_type.get("name", "")), str(base_type.get("name", ""))))
            continue
        source_mid = int(source_type["id"])
        note_ids = [int(note_id) for note_id in col.db.list("SELECT id FROM notes WHERE mid = ?", source_mid)]
        operations.append((source_type, base_type, note_ids))

    handled_ids = {int(source_type.get("id", 0) or 0) for source_type, _base_type, _note_ids in operations}
    groups = _group_duplicates_without_base(
        [note_type for note_type in note_types if int(note_type.get("id", 0) or 0) not in handled_ids],
        by_name,
    )
    for _base_name, duplicates in groups.items():
        duplicates_sorted = sorted(duplicates, key=lambda note_type: int(note_type.get("id", 0) or 0))
        base_type = duplicates_sorted[0]
        base_signature = _notetype_structure_signature(base_type)
        for source_type in duplicates_sorted[1:]:
            if _notetype_structure_signature(source_type) != base_signature:
                skipped_signature.append((str(source_type.get("name", "")), str(base_type.get("name", ""))))
                continue
            source_mid = int(source_type["id"])
            note_ids = [int(note_id) for note_id in col.db.list("SELECT id FROM notes WHERE mid = ?", source_mid)]
            operations.append((source_type, base_type, note_ids))

    if not operations:
        return {"types": 0, "notes": 0, "deleted": 0, "skipped": len(skipped_signature)}

    mw.checkpoint("אויטאמאטיש פאראייניגן סארטן רשומות")
    merged_types = 0
    moved_notes = 0
    deleted_types = 0
    for source_type, base_type, note_ids in operations:
        source_mid = int(source_type["id"])
        target_mid = int(base_type["id"])
        for note_id in note_ids:
            note = col.get_note(note_id)
            note.mid = target_mid
            col.update_note(note)
            moved_notes += 1

        refreshed_source = col.models.get(NotetypeId(source_mid))
        if refreshed_source and col.models.use_count(refreshed_source) == 0:
            col.models.remove(NotetypeId(source_mid))
            deleted_types += 1
        merged_types += 1

    return {"types": merged_types, "notes": moved_notes, "deleted": deleted_types, "skipped": len(skipped_signature)}


def _result_message(result: dict[str, int], *, manual: bool) -> str | None:
    if result.get("types"):
        return (
            f"פאראייניגט: {result['types']} טאפלטע סארטן רשומות "
            f"({result['notes']} רשומות אריבערגעפירט, {result['deleted']} סארטן אראפגענומען)."
            + (f"\nאיבערגעהיפט: {result.get('skipped', 0)} סארטן צוליב א אנדערן מבנה." if result.get("skipped") else "")
        )
    if manual:
        skipped = result.get("skipped", 0)
        return "קיין טאפלטע סארטן רשומות זענען נישט געפונען געווארן צו פאראייניגן." + (
            f"\nאיבערגעהיפט: {skipped} סארטן צוליב א אנדערן מבנה." if skipped else ""
        )
    return None


def run_auto_consolidation(*, manual: bool = False, force: bool = False) -> dict[str, int] | None:
    if mw is None or mw.col is None:
        return None

    config = _addon_config()
    now = int(time.time())
    last_run = int(config.get(LAST_AUTO_RUN_KEY) or 0)
    if not force and now - last_run < AUTO_CONSOLIDATE_INTERVAL_SECONDS:
        return None

    result = auto_consolidate_duplicate_note_types(mw.col)
    config[LAST_AUTO_RUN_KEY] = now
    _write_addon_config(config)

    message = _result_message(result, manual=manual)
    if message:
        tooltip(message)
    return result


def _auto_consolidate_on_profile_open() -> None:
    try:
        run_auto_consolidation(manual=False, force=False)
    except Exception as err:  # noqa: BLE001
        print(f"[external-import] auto_consolidate_on_profile_open failed: {err}")


class NoteTypeConsolidatorDialog(QDialog):
    def __init__(self, parent=mw):
        super().__init__(parent)
        self.matching_types: list[dict[str, object]] = []
        self.all_note_types: list[dict] = []
        self.setWindowTitle("פאראייניגן סארטן רשומות")
        self.setMinimumSize(600, 500)
        self._build_ui()
        self.populate_note_types()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        instructions = QLabel(
            "דאס געצייג פאראייניגט ענליכע סארטן רשומות אין איין סארט רשומה.\n\n"
            "1. לייגט אריין א מוסטער פאר די סארטן רשומות, למשל AnkiDaf-\n"
            "2. קלייבט אויס א ציל סארט רשומה אדער שאפט א נייעם ציל\n"
            "3. ווייזט א פארויסקוק\n"
            "4. באשטעטיקט פאראייניגן און, אויב געוואונטשן, אויסמעקן ליידיגע סארטן"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("מוסטער צו זוכן:"))
        self.pattern_input = QLineEdit("AnkiDaf-")
        pattern_layout.addWidget(self.pattern_input)
        layout.addLayout(pattern_layout)

        preview_layout = QHBoxLayout()
        self.preview_btn = QPushButton("ווייזט פאסיגע סארטן רשומות")
        self.preview_btn.clicked.connect(self.preview_matches)
        preview_layout.addWidget(self.preview_btn)
        self.count_label = QLabel("")
        preview_layout.addWidget(self.count_label)
        layout.addLayout(preview_layout)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("זוכן:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_preview)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        preview_scroll = QScrollArea()
        preview_scroll.setMaximumHeight(200)
        preview_scroll.setWidgetResizable(True)
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        preview_scroll.setWidget(self.preview_widget)
        layout.addWidget(preview_scroll)

        target_layout = QVBoxLayout()
        target_layout.addWidget(QLabel("ציל סארט רשומה:"))
        target_search_layout = QHBoxLayout()
        target_search_layout.addWidget(QLabel("זוכן א ציל:"))
        self.target_search = QLineEdit()
        self.target_search.textChanged.connect(self.filter_target_types)
        target_search_layout.addWidget(self.target_search)
        target_layout.addLayout(target_search_layout)
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        target_layout.addWidget(self.target_combo)
        layout.addLayout(target_layout)

        new_type_layout = QHBoxLayout()
        self.create_new_checkbox = QCheckBox("שאפט א נייעם סארט רשומה:")
        self.new_type_name = QLineEdit("AnkiDaf-Base")
        self.new_type_name.setEnabled(False)
        self.create_new_checkbox.toggled.connect(self.new_type_name.setEnabled)
        self.create_new_checkbox.toggled.connect(lambda checked: self.target_combo.setEnabled(not checked))
        new_type_layout.addWidget(self.create_new_checkbox)
        new_type_layout.addWidget(self.new_type_name)
        layout.addLayout(new_type_layout)

        self.delete_old_checkbox = QCheckBox("מעקט אויס די אריגינעלע סארטן רשומות נאכן פאראייניגן")
        self.delete_old_checkbox.setChecked(True)
        layout.addWidget(self.delete_old_checkbox)

        button_layout = QHBoxLayout()
        self.consolidate_btn = QPushButton("פאראייניגט סארטן רשומות")
        self.consolidate_btn.clicked.connect(self.consolidate_note_types)
        button_layout.addWidget(self.consolidate_btn)
        cancel_btn = QPushButton("אפזאגן")
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def populate_note_types(self) -> None:
        self.target_combo.clear()
        self.all_note_types = list(mw.col.models.all())
        for note_type in self.all_note_types:
            self.target_combo.addItem(note_type["name"], note_type)

    def filter_target_types(self) -> None:
        search_text = self.target_search.text().lower()
        self.target_combo.clear()
        for note_type in self.all_note_types:
            if not search_text or search_text in note_type["name"].lower():
                self.target_combo.addItem(note_type["name"], note_type)

    def preview_matches(self) -> None:
        pattern = self.pattern_input.text().strip()
        if not pattern:
            showInfo("ביטע לייגט אריין א מוסטער", parent=self)
            return

        self.matching_types = []
        for note_type in mw.col.models.all():
            if pattern in note_type["name"]:
                note_count = mw.col.models.use_count(note_type)
                self.matching_types.append({"name": note_type["name"], "count": note_count, "model": note_type})

        self.matching_types.sort(key=lambda item: str(item["name"]))
        total_notes = sum(int(item["count"]) for item in self.matching_types)
        self.count_label.setText(f"געפונען: {len(self.matching_types)} סארטן רשומות, אינגאנצן {total_notes} רשומות")
        self.filter_preview()

    def filter_preview(self) -> None:
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        search_text = self.search_input.text().lower()
        displayed_count = 0
        for item in self.matching_types:
            if search_text and search_text not in str(item["name"]).lower():
                continue
            if displayed_count < 50:
                label = QLabel(f"• {item['name']} ({item['count']} רשומות)")
                label.setStyleSheet("padding: 2px;")
                self.preview_layout.addWidget(label)
            displayed_count += 1

        if displayed_count > 50:
            more_label = QLabel(f"... און נאך {displayed_count - 50} סארטן")
            more_label.setStyleSheet("color: gray; font-style: italic;")
            self.preview_layout.addWidget(more_label)
        elif displayed_count == 0:
            no_results = QLabel("קיין פאסיגע סארטן רשומות זענען נישט געפונען געווארן")
            no_results.setStyleSheet("color: red;")
            self.preview_layout.addWidget(no_results)

    def _target_note_type(self) -> dict | None:
        if not self.create_new_checkbox.isChecked():
            return self.target_combo.currentData()

        new_name = self.new_type_name.text().strip()
        if not new_name:
            showInfo("ביטע לייגט אריין א נאמען פארן נייעם סארט רשומה", parent=self)
            return None
        existing = mw.col.models.by_name(new_name)
        if existing:
            if askUser(f"סארט רשומה '{new_name}' עקזיסטירט שוין. נוצן עס אלס ציל?", parent=self):
                return existing
            return None
        if not self.matching_types:
            showInfo("קיין פאסיגע סארטן רשומות זענען נישט געפונען געווארן צו נוצן אלס מוסטער", parent=self)
            return None

        template_type = self.matching_types[0]["model"]
        new_type = mw.col.models.copy(template_type)
        new_type["name"] = new_name
        mw.col.models.add(new_type)
        return new_type

    def consolidate_note_types(self) -> None:
        if not self.matching_types:
            showInfo("ביטע ווייזט קודם א פארויסקוק", parent=self)
            return
        target_type = self._target_note_type()
        if not target_type:
            return

        target_mid = int(target_type["id"])
        types_to_consolidate = [
            item for item in self.matching_types
            if int(item["model"]["id"]) != target_mid
        ]
        if not types_to_consolidate:
            showInfo("נישטא קיין סארטן רשומות צו פאראייניגן", parent=self)
            return

        total_notes = sum(int(item["count"]) for item in types_to_consolidate)
        if not askUser(
            f"פאראייניגן {len(types_to_consolidate)} סארטן רשומות אין '{target_type['name']}'?\n"
            f"אינגאנצן {total_notes} רשומות ווערן אריבערגעפירט.",
            title="באשטעטיקן פאראייניגן",
            parent=self,
        ):
            return

        mw.checkpoint("פאראייניגן סארטן רשומות")
        progress = QProgressDialog("פאראייניגט רשומות...", "אפזאגן", 0, max(total_notes, 1), self)
        progress.show()
        consolidated_count = 0
        deleted_types: list[str] = []
        try:
            for item in types_to_consolidate:
                source_type = item["model"]
                source_mid = int(source_type["id"])
                note_ids = mw.col.db.list("SELECT id FROM notes WHERE mid = ?", source_mid)
                for note_id in note_ids:
                    if progress.wasCanceled():
                        return
                    note = mw.col.get_note(note_id)
                    note.mid = target_mid
                    mw.col.update_note(note)
                    consolidated_count += 1
                    progress.setValue(consolidated_count)
                    if consolidated_count % 50 == 0:
                        QApplication.processEvents()

                if self.delete_old_checkbox.isChecked():
                    note_type = mw.col.models.get(NotetypeId(source_mid))
                    if note_type and mw.col.models.use_count(note_type) == 0:
                        mw.col.models.remove(NotetypeId(source_mid))
                        deleted_types.append(str(source_type["name"]))
            progress.close()
            message = f"מיט הצלחה פארענדיגט!\n\n• {consolidated_count} רשומות פאראייניגט אין '{target_type['name']}'"
            if deleted_types:
                message += f"\n• {len(deleted_types)} ליידיגע סארטן רשומות אראפגענומען"
            showInfo(message, parent=self)
            self.close()
            mw.reset()
        except Exception as exc:
            progress.close()
            from _shared_libs.haf_notifications import show_failure
            show_failure("פאראייניגן די רשומות איז נישט פארענדיגט. א טייל רשומות קענען שוין זיין דערהיינטיגט; קאנטראלירט זיי איידער איר פרובירט נאכאמאל.", exc, parent=self)


def show_note_type_consolidator() -> None:
    dialog = NoteTypeConsolidatorDialog(mw)
    dialog.exec()


def _run_manual_auto_consolidation() -> None:
    run_auto_consolidation(manual=True, force=True)


def _add_menu_actions() -> None:
    if getattr(mw, "_external_import_note_type_consolidator_actions", None):
        return
    if not hasattr(mw, "addon_col_menu"):
        return
    root_menu = mw.addon_col_menu

    auto_action = QAction("קאנטראל פון טאפלטע סארטן רשומות", root_menu)
    qconnect(auto_action.triggered, _run_manual_auto_consolidation)
    root_menu.addAction(auto_action)


    mw._external_import_note_type_consolidator_actions = (auto_action)


def init() -> None:
    gui_hooks.profile_did_open.append(_add_menu_actions)
    gui_hooks.profile_did_open.append(_auto_consolidate_on_profile_open)
