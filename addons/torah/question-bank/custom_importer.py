import os.path
from collections.abc import Iterable
from typing import NamedTuple

from anki.collection import Collection, CsvMetadata, ImportCsvRequest
from anki.import_export_pb2 import ImportResponse
from anki.notes import Note
from anki.utils import join_fields, tmpdir
from aqt import mw
from aqt.qt import *

from _shared_libs.haf_logging import get_logger

from .archive_access import extract_targets
from .prakim_and_simanim import SUBJECT_TYPES, get_perek_or_siman

logger = get_logger("question_bank")

# #346 — הוסרה התלות ב-py7zr לצורך תאימות מק ולינוקס.
# py7zr דרשה 48 בינאריים מקומפלים ל-cp313-win_amd64 בתיקיית vendor/. במק
# ובלינוקס הייבוא נכשל ולכן התוסף כולו לא נטען. המאגר הומר ל-tar.xz ונקרא
# דרך archive_access, שמשתמש ב-tarfile+lzma שבספרייה הסטנדרטית.

addon_path = os.path.dirname(os.path.realpath(__file__))
path = os.path.join(addon_path, "מאגר השאלות")


def importFromFolder(files: list,
                     _col: Collection = None,
                     col_path: str = "",
                     daf: bool = False,
                     allow_dupes: int = 2,
                     matchscope: int = 0,
                     separte_by_prakim: bool = False,
                     group_by_masechet: bool = False,
                     progress_manager=None,
                     return_after_import: bool = False,
                     selected_rows: dict | None = None,
                     public_deck: str = "",
                     strict_errors: bool = False
                     ):
    path_to_extract = os.path.join(tmpdir(), "temp_extracted_files")
    repo_media_dit_path = os.path.join(tmpdir(), "temp_extracted_repo_media_files")

    if progress_manager:
        progress_manager.update(label="פאקט אויס טעקעס פונעם מאגר...")
        mw.app.processEvents()

    selective_files = [f.replace("\\", "/") for f in files]
    extract_targets(selective_files, path_to_extract)

    # מסלולי הלוח הציבורי: חותכים רק את העותק הזמני, לפי השורות שאושרו בתצוגה.
    if selected_rows is not None:
        from .public_learning import select_csv_rows
        for selected_file in selective_files:
            select_csv_rows(os.path.join(path_to_extract, selected_file), selected_rows[selected_file])

    log = ""
    found_notes = 0
    ids_log = []

    # --- סט לשמירת שמות החפיסות שנוצרו בריצה זו בלבד ---
    newly_created_deck_names = set()
    # ---------------------------------------------------

    total_files = len(files)
    for i, file_path in enumerate(files):
        file_path = file_path.replace("\\", "/")
        if progress_manager:
            filename_short = file_path.split("/")[-1]
            progress_manager.update(label=f"אימפארטירט: {filename_short}", value=i, max=total_files)
            mw.app.processEvents()

        if file_path.lower().endswith(".txt"):
            file_name = file_path.split("/")[-1]
            log += f"<b>אימפארטירט א טעקע: {file_name}</b><br>"

            # --- בניית שם החפיסה ---

            # 1. פירוק הנתיב לרכיבים
            parts = file_path.split("/")
            parts = parts[:-1]  # הסרת שם הקובץ

            # ניקוי התיקייה הראשית ושמות עם $
            if parts and parts[0] == "מאגר השאלות":
                parts.pop(0)
            parts = [p[:-1] if p.endswith("$") else p for p in parts]

            # שמירת עותק של החלקים בתצורה המקורית (רב->מסכת) עבור חישוב הפרק
            # הפונקציה get_perek_or_siman מצפה למבנה הרגיל
            parts_for_calc = parts.copy()

            # 2. לוגיקה לשינוי סדר החפיסות (אם נבחר) עבור יצירת החפיסה באנקי
            deck_parts = parts.copy()
            if group_by_masechet and "שס" in deck_parts:
                try:
                    shas_index = deck_parts.index("שס")
                    if shas_index + 2 < len(deck_parts):
                        # החלפה בין הרב למסכת
                        deck_parts[shas_index + 1], deck_parts[shas_index + 2] = deck_parts[shas_index + 2], deck_parts[
                            shas_index + 1]
                except ValueError:
                    pass

            # 3. בניית שמות חפיסה זמניים
            # שם החפיסה לצורך חישוב פרק (מבנה רגיל)
            temp_deck_name_for_calc = "::".join(parts_for_calc)
            if daf:
                temp_deck_name_for_calc = temp_deck_name_for_calc.replace("שס::", "הדף היומי::")
            if "הדף היומי::" in temp_deck_name_for_calc:
                temp_deck_name_for_calc = temp_deck_name_for_calc.replace("מאגר השאלות::", "", 1)

            # 4. חישוב הפרק באמצעות המבנה הרגיל
            # התיקון: שולחים לפונקציה את המבנה שהיא מכירה
            calc_list = temp_deck_name_for_calc.split("::")
            perek, subject_type = get_perek_or_siman(calc_list, file_path)

            # 5. הרכבת שם החפיסה הסופי (deck_parts כבר מכיל את ההחלפה אם נדרשה)
            final_deck_parts = deck_parts

            # טיפול בשינויי שמות לדף היומי גם עבור השם הסופי
            # נבצע זאת ע"י המרה למחרוזת וחזרה או מניפולציה על הרשימה
            # הדרך הפשוטה: נבנה מחרוזת בסיסית ונעשה את ההחלפות
            base_deck_name = "::".join(final_deck_parts)
            if daf:
                base_deck_name = base_deck_name.replace("שס::", "הדף היומי::")
            if "הדף היומי::" in base_deck_name:
                base_deck_name = base_deck_name.replace("מאגר השאלות::", "", 1)
            else:
                # אם זה לא דף יומי (כלומר שולחן ערוך, שס רגיל וכו'):
                # אנחנו רוצים שתמיד יהיה תחת "מאגר השאלות".
                # מכיוון שבשלב 1 הסרנו את "מאגר השאלות" מתוך parts, כעת base_deck_name לא מכיל אותו.
                # אז נוסיף אותו ידנית.
                if not base_deck_name.startswith("מאגר השאלות"):
                    base_deck_name = "מאגר השאלות::" + base_deck_name

            final_deck_list = base_deck_name.split("::")

            # 6. הוספת הפרק/סימן לחפיסה הסופית
            if separte_by_prakim:
                if perek != "":
                    final_deck_list.append(f"{perek}")
                if subject_type in (SUBJECT_TYPES.SHUA, SUBJECT_TYPES.MISHNAB):
                    siman_deck = file_name.replace('_', ' ').replace('סימן ', '').replace('.txt', '').split(" ")[0]
                    final_deck_list.append(f"{siman_deck}")

            deckName = "::".join(final_deck_list)
            real_deck_name = deckName.replace("%", " ")
            if public_deck:
                # יחידת הלימוד מעל המקור: אותה שאלה שומרת על השדות וזהות הייבוא.
                real_deck_name = public_deck + "::" + "::".join(parts).replace("%", " ")

            # --- זיהוי אלו חפיסות בנתיב הן חדשות (כדי שלא נמחק חפיסות ישנות בטעות) ---
            path_parts = real_deck_name.split("::")
            current_path_check = ""
            for part in path_parts:
                if current_path_check:
                    current_path_check += "::" + part
                else:
                    current_path_check = part

                # אם החפיסה לא קיימת עדיין, נוסיף אותה לרשימת "נוצרו עכשיו"
                if _col.decks.by_name(current_path_check) is None:
                    newly_created_deck_names.add(current_path_check)
            # -----------------------------------------------------------------------

            did = _col.decks.id(real_deck_name)
            _col.decks.save(_col.decks.get(did))

            file_log = None
            try:
                file_log: ImportResponse = import_csv_to_col(
                    os.path.join(path_to_extract, file_path), _col, did, allow_dupes,
                    matchscope, source_file_name=file_name
                )
            except Exception as e:
                if strict_errors:
                    raise
                if "ליידיג" in str(e):
                    log += "<span style='color:red'>טעות: א ליידיגע טעקע</span><br><br>"
                else:
                    log += f"<span style='color:red'>אימפארט טעות: {str(e)}</span><br><br>"

            # --- מחיקה רקורסיבית מבוקרת ---
            # נמחק רק אם החפיסה סומנה כ"חדשה" בריצה זו
            if real_deck_name in newly_created_deck_names:
                card_count = _col.db.scalar("select count() from cards where did=?", did)
                if card_count == 0:
                    _col.decks.remove([did])

                    # 2. בדיקה ומחיקה כלפי מעלה (הורים)
                    # אנו רצים בלולאה כל עוד יש אבא, ובודקים אם הוא נשאר ריק (ללא כרטיסים וללא ילדים אחרים)
                    current_check_name = real_deck_name
                    while "::" in current_check_name:
                        # קבלת שם האבא
                        parent_name = "::".join(current_check_name.split("::")[:-1])

                        # --- תנאי עצירה קריטי: אם האבא היה קיים לפני הייבוא - לא נוגעים בו! ---
                        if parent_name not in newly_created_deck_names:
                            break
                        # -------------------------------------------------------------------

                        parent_deck = _col.decks.by_name(parent_name)

                        if not parent_deck:
                            break  # האבא לא קיים, עוצרים

                        parent_id = parent_deck['id']

                        # בדיקה א': האם יש לאבא כרטיסים?
                        parent_cards = _col.db.scalar("select count() from cards where did=?", parent_id)
                        if parent_cards > 0:
                            break  # לאבא יש כרטיסים, לא מוחקים ועוצרים את הטיפוס

                        # בדיקה ב': האם יש לאבא ילדים *אחרים*?
                        # מכיוון שמחקנו את הילד הנוכחי, אנו בודקים אם נשארו עוד ילדים ששמם מתחיל בשם האבא
                        has_children = False

                        # --- תיקון השגיאה כאן: גישה למאפייני האובייקט במקום Unpacking ---
                        for deck_item in _col.decks.all_names_and_ids():
                            if deck_item.name.startswith(parent_name + "::"):
                                has_children = True
                                break

                        if has_children:
                            break  # נשארו ילדים אחרים, לא מוחקים ועוצרים

                        # אם הגענו לפה - האבא ריק מכרטיסים וריק מילדים -> מוחקים אותו
                        _col.decks.remove([parent_id])

                        # ממשיכים לבדוק את הסבא
                        current_check_name = parent_name
            # -------------------------------------------------------------------

            if file_log is not None:
                try:
                    file_log.ClearField("changes")
                    ids_containers = [file_log.log.new,
                                      file_log.log.updated,
                                      file_log.log.duplicate,
                                      file_log.log.conflicting,
                                      file_log.log.first_field_match,
                                      file_log.log.empty_first_field]
                    found_notes += file_log.log.found_notes
                    file_log.log.ClearField("dupe_resolution")
                    file_log.log.ClearField("found_notes")

                    for container in ids_containers:
                        for _id in container:
                            ids_log.append(_id.id.nid)
                except (AttributeError, IndexError):
                    pass

                if _col == mw.col:
                    log += str(file_log)

    if progress_manager:
        progress_manager.update(label="קאנטראלירט פעלנדיגע מידיא טעקעס...")
        mw.app.processEvents()

    missing_files = []
    for note_id in ids_log:
        if note_id == 0:
            continue
        missing_files.extend(files_in_note(_col.get_note(note_id)))

    if missing_files:
        files_path_in_zip = []
        for f in missing_files:
            f_path = "מאגר השאלות/media/" + f.name
            if f_path not in files_path_in_zip:
                files_path_in_zip.append(f_path)

        if progress_manager:
            progress_manager.update(label="פאקט אויס מידיא...")

        extract_targets(files_path_in_zip, repo_media_dit_path)
        for mis_f in missing_files:
            try:
                _col.media.add_file(os.path.join(repo_media_dit_path, "מאגר השאלות", "media", mis_f.name))
            except FileNotFoundError:
                logger.warning(f"file {mis_f.name} not found")

    if _col == mw.col:
        dupe_resolution = f"ביי אן עקזיסטירנדן קארטל: {'מאכן א קאפיע' if allow_dupes == 2 else 'נישט אימפארטירן'}\n"
        found_notes = f'רשומות געפונען אינגאנצן: {found_notes}\n' if found_notes != 0 else ""

        final_log = (f"""<h3>מיט הצלחה פארענדיגט!</h3>
{dupe_resolution}{found_notes}
<hr>
{log}""".replace("first_field_match {", "<br>טאפלט (עקזיסטירט): ")
                     .replace(" }\n", "<br>")
                     .replace("}\n", "<br>")
                     .replace("\n fields:", ",")
                     .replace(" fields:", " | פעלדער:")
                     .replace("log {", "<br>פרטים: ")
                     .replace("nid:", "ID:")
                     .replace("found_notes:", "געפונען:")
                     .replace("\n id {", "")
                     .replace("new {", "<br><span style='color:green'>ניי:</span> ")
                     .replace("empty_first_field {", "<br><span style='color:red'>ערשטע פעלד ליידיג:</span> ")
                     .replace("conflicting {", "<br><span style='color:orange'>קאנפליקט:</span> ")
                     .replace("updated {", "<br><span style='color:blue'>דערהיינטיגט:</span> ")
                     .replace("dupe_resolution", "צושטאנד")
                     .replace("DUPLICATE", "<span style='color:orange'>קאפיע געמאכט</span>")
                     .replace("PRESERVE", "<span style='color:gray'>איבערגעהיפט</span>")
                     )
        return final_log
    else:
        if return_after_import:
            return "imported"
        # טעינת GUIDים שיובאו בעבר דרך ייבוא חלקי (bookmark ספציפי לפיצ'ר זה)
        addon_id = mw.addonManager.addonFromModule(__name__)
        conf = mw.addonManager.getConfig(addon_id)
        done_guids = set(conf.get("partial_import_done_guids", []))

        # סינון פתקים שכבר יובאו בעבר דרך הייבוא החלקי
        temp_notes = _col.db.all("select id, guid from notes")
        notes_to_remove = [nid for nid, guid in temp_notes if guid in done_guids]
        if notes_to_remove:
            _col.remove_notes(notes_to_remove)

        if not _col.db.scalar("select count() from notes"):
            from aqt.utils import tooltip
            tooltip("אלע שאלות פון די אויסגעקליבענע טעקעס זענען שוין פריער אימפארטירט געווארן")
            return "נישטא קיין נייע שאלות צו אימפארטירן"

        # GUIDים הזמינים בחלון זה (לזיהוי מה ייובא בפועל)
        available_guids = {guid for _, guid in _col.db.all("select id, guid from notes")}
        # snapshot של mw.col לפני פתיחת CRoPro
        guids_before = set(mw.col.db.list("select guid from notes"))

        d = mw._cropro_main_dialog(parent=mw, temp_col=_col, temp_col_path=col_path)

        # עדכון ה-bookmark כשהמשתמש סוגר את חלון CRoPro
        def _on_cropro_finished():
            guids_after = set(mw.col.db.list("select guid from notes"))
            newly_imported = (guids_after - guids_before) & available_guids
            if newly_imported:
                cfg = mw.addonManager.getConfig(addon_id)
                existing = set(cfg.get("partial_import_done_guids", []))
                existing.update(newly_imported)
                cfg["partial_import_done_guids"] = list(existing)
                mw.addonManager.writeConfig(addon_id, cfg)

        d.finished.connect(_on_cropro_finished)
        d.show()
        return "דער אויסוואל פענצטער איז געעפנט"


def import_csv_to_col(path, _col, did, allow_dupes, matchscope, source_file_name=None):
    metadata: CsvMetadata = _col.get_csv_metadata(path, None)
    metadata.deck_id = did
    metadata.dupe_resolution = allow_dupes
    metadata.match_scope = matchscope
    metadata.tags_column = metadata.tags_column + 1
    metadata.global_tags.append("מאגר")

    if source_file_name and _col != mw.col:
        metadata.global_tags.append(source_file_name.replace(".txt", ""))

    request = ImportCsvRequest(path=path, metadata=metadata)
    log = _col.import_csv(request)

    if _col == mw.col:
        mw.reset()
    return log


class NameId(NamedTuple):
    name: str
    id: int

    @classmethod
    def none_type(cls) -> 'NameId':
        return cls('None (create new if needed)', -1)


def sorted_decks_and_ids(col: Collection) -> list[NameId]:
    return sorted(NameId(deck.name, deck.id) for deck in col.decks.all_names_and_ids())


class FileInfo(NamedTuple):
    name: str
    path: str


def files_in_note(note: Note) -> Iterable[FileInfo]:
    for file_ref in note.col.media.files_in_str(note.mid, join_fields(note.fields)):
        if not os.path.exists(file_path := os.path.join(note.col.media.dir(), file_ref)):
            yield FileInfo(file_ref, file_path)
