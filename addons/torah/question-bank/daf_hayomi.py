import contextlib
import json
from datetime import datetime, timedelta

from anki.utils import pointVersion
from aqt.gui_hooks import profile_did_open
# #243 — daf_hayomi_init משתמש ב-showText גם בתוצאת ייבוא וגם במסלול שגיאה.
from aqt.utils import askUser, showText
from _shared_libs.haf_notifications import show_failure
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QStandardItemModel

from .config import *
from .custom_importer import *
from .get_todays_daf import today_daf
from .import_templates import getOrCreateModels
from .repo_importer import repo_notetypes_names

# משתנים גלובליים
ask_before_import = gc("ask_before_import")
rab_name = gc("rab_name")
if not isinstance(rab_name, list):
    rab_name = []

last_day_imported = 0


class settings_dialog(QDialog):
    def __init__(self, parent=mw):
        super().__init__(parent)
        Dialog = self
        Dialog.setObjectName("Dialog")
        Dialog.resize(299, 388)
        Dialog.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.daf_on = QtWidgets.QCheckBox()
        self.daf_on.setObjectName("daf_on")
        self.gridLayout.addWidget(self.daf_on, 0, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout.addWidget(self.groupBox, 1, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.ask_before_import = QtWidgets.QCheckBox(self.groupBox_2)
        self.ask_before_import.setObjectName("ask_before_import")
        self.gridLayout_3.addWidget(self.ask_before_import, 0, 0, 1, 1)

        self.group_by_masechet = QtWidgets.QCheckBox(self.groupBox_2)
        self.group_by_masechet.setObjectName("group_by_masechet")
        self.gridLayout_3.addWidget(self.group_by_masechet, 3, 0, 1, 1)

        self.daf_allow_dupes = QtWidgets.QCheckBox(self.groupBox_2)
        self.daf_allow_dupes.setObjectName("daf_allow_dupes")
        self.gridLayout_3.addWidget(self.daf_allow_dupes, 1, 0, 1, 1)
        self.import_to_each_profile = QtWidgets.QCheckBox(self.groupBox_2)
        self.import_to_each_profile.setObjectName("import_to_each_profile")
        self.gridLayout_3.addWidget(self.import_to_each_profile, 2, 0, 1, 1)

        self.ListView = QtWidgets.QListView(self.groupBox_2)
        self.ListView.setObjectName("ListView")
        self.gridLayout_3.addWidget(self.ListView, 4, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_2, 2, 0, 1, 1)
        self.offset_label = QtWidgets.QLabel(self.groupBox_2)
        self.offset_label.setWordWrap(True)
        self.offset_label.setObjectName("offset_label")
        self.gridLayout.addWidget(self.offset_label, 5, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 1)
        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        self.rab_actions = []

        self.setup_ui()

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "דף היומי איינשטעלונגען"))
        self.daf_on.setText(_translate("Dialog", "לייגט אויטאמאטיש אריין שאלות לויטן דף היומי סדר"))
        self.groupBox.setTitle(_translate("Dialog", "שאלות פון:"))
        self.groupBox_2.setTitle(_translate("Dialog", "איינשטעלונגען"))
        self.ask_before_import.setText(_translate("Dialog", "פרעגט יעדן טאג איידער מען לייגט צו שאלות"))
        self.daf_allow_dupes.setText(_translate("Dialog", "אימפארטירט אויך שאלות וואס זענען שוין פריער אימפארטירט"))
        self.daf_allow_dupes.setToolTip("קען שאפן טאפלטע רשומות")
        self.group_by_masechet.setText(_translate("Dialog", "גרופירט לויט מסכת (אנשטאט לויטן רב)"))
        self.import_to_each_profile.setText(_translate("Dialog", "שטעלט איין פאר יעדן פראפיל באזונדער"))
        self.offset_label.setText(
            _translate("Dialog", "הערה: דער דף היומי טוישט זיך לויט דער צייט באשטימט אין מעניו > איינשטעלונגען > תזמון > קומענדיגער טאג."))

    def setup_ui(self):
        num = 0
        rab_names = []
        # #341: repo_struct.json נכתב ב-UTF-8 (ראו create_json_tree.py); קידוד ISO-8859-8 גרם
        # ל-UnicodeDecodeError בפתיחת חלון ההגדרות של הדף היומי. הושווה ל-repo_importer.py.
        with open(os.path.join(os.path.dirname(__file__), "repo_struct.json"), encoding='utf-8') as settings:
            conf = json.load(settings)["children"]
        for ch in conf:
            if ch["name"] == "שס":
                for rb in ch["children"]:
                    if not rb["name"].endswith("$") and rb["name"] != "שאלות מהלומדים":
                        rab_names.append(rb["name"])
                break
        for rab in rab_names:
            if not rab.endswith("$"):
                CheckBox = QtWidgets.QCheckBox(self.groupBox)
                from .learning_catalog import source_description
                label, detail = source_description("מאגר השאלות/שס/" + rab, rab)
                CheckBox.setText(rab)
                CheckBox.setToolTip(label + "\n" + detail)
                CheckBox.setProperty("source_name", rab)
                self.rab_actions.append(CheckBox)
                self.gridLayout_2.addWidget(CheckBox, num, 0, 1, 1)
                if rab in rab_name:
                    CheckBox.setChecked(True)
                num += 1
        self.model = QStandardItemModel()
        for profile in mw.pm.profiles():
            item = QtGui.QStandardItem(profile)
            item.setCheckable(True)
            checked = profile in gc("profiles")
            check = QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked
            item.setCheckState(check)
            self.model.appendRow(item)
        self.ListView.setModel(self.model)
        self.daf_on.setChecked(gc("daf_on"))
        self.ask_before_import.setChecked(gc("ask_before_import"))
        self.import_to_each_profile.setChecked(gc("import_to_each_profile"))
        self.daf_allow_dupes.setChecked(gc("daf_allow_dupes"))
        self.group_by_masechet.setChecked(gc("group_by_masechet") or False)

        self.ListView.setEnabled(self.import_to_each_profile.isChecked())
        self.groupBox.setEnabled(self.daf_on.isChecked())
        self.groupBox_2.setEnabled(self.daf_on.isChecked())
        self.import_to_each_profile.toggled.connect(lambda checked: self.ListView.setEnabled(
            False) if not checked else self.ListView.setEnabled(True))

        self.daf_on.toggled.connect(lambda checked: self.groupBox.setEnabled(
            False) if not checked else self.groupBox.setEnabled(True))

        self.daf_on.toggled.connect(lambda checked: self.groupBox_2.setEnabled(
            False) if not checked else self.groupBox_2.setEnabled(True))

    def save_settings(self) -> None:
        global ask_before_import
        global rab_name

        config = mw.addonManager.getConfig(__name__)
        config["daf_on"] = self.daf_on.isChecked()
        config["ask_before_import"] = self.ask_before_import.isChecked()
        ask_before_import = self.ask_before_import.isChecked()
        config["import_to_each_profile"] = self.import_to_each_profile.isChecked()
        config["daf_allow_dupes"] = self.daf_allow_dupes.isChecked()
        config["group_by_masechet"] = self.group_by_masechet.isChecked()

        for checkbox in self.rab_actions:
            text = checkbox.property("source_name") or checkbox.text()
            if checkbox.isChecked():
                if text in rab_name:
                    rab_name.pop(rab_name.index(text))
                rab_name.append(text)
            else:
                if text in rab_name:
                    rab_name.pop(rab_name.index(text))

        config["rab_name"] = rab_name
        i = 0
        profiles = []
        while self.model.item(i):
            text = self.model.item(i).text()
            if self.model.item(i).checkState() == QtCore.Qt.CheckState.Checked:
                if text in profiles:
                    profiles.pop(profiles.index(text))
                profiles.append(text)
            else:
                if text in profiles:
                    profiles.pop(profiles.index(text))
            i += 1
        config["profiles"] = profiles
        mw.addonManager.writeConfig(__name__, config)

    def accept(self) -> None:
        self.save_settings()
        if self.daf_on.isChecked():
            daf_hayomi_init()

        return super().accept()


def open_settings_dialog():
    from .daily_manager import open_daily_manager
    open_daily_manager("daf")


def today_with_offset(dlt: timedelta = timedelta(0)):
    scheduling = mw.col.conf.get("rollover", 4)
    delta = timedelta(hours=scheduling)
    d = datetime.now() - delta - dlt
    return str(d).split(" ")[0]


def import_daf():
    pages_to_import = []

    def add_file_path_to_import(mesekhta, daf):
        # #341: תיקון קידוד — ראו הערה ב-setup_ui
        with open(os.path.join(os.path.dirname(__file__), "repo_struct.json"), encoding='utf-8') as repo_json_file:
            repo_tree = json.load(repo_json_file)
        daf_path = "מאגר השאלות/שס"
        for rab in rab_name:
            for subject in repo_tree["children"]:
                if subject["name"] == "שס":
                    for folder in subject["children"]:
                        if folder["name"] == rab:
                            rab_path = daf_path + f"/{rab}"
                            for masechta in folder["children"]:
                                if mesekhta in masechta["name"]:
                                    masech_path = rab_path + f'/{masechta["name"]}'
                                    for page in masechta["children"]:
                                        if "_" + daf + ".txt" in page["name"]:
                                            # אישיו #371: צירוף המקור בסוף הרשימה לשמירת סדר המחברים.
                                            pages_to_import.append(masech_path + f'/{page["name"]}')

    allow_dupes = gc("daf_allow_dupes")
    group_by_masechet = gc("group_by_masechet") or False
    # #203 - daily daf imports should use the same per-chapter default as repository imports.
    separte_by_prakim = gc("repo_separte_by_prakim") or False

    # איסוף תאריכים שיובאו בפועל בסשן הזה כדי לעדכן את ההיסטוריה
    imported_dates = []

    # 1. בדיקת דפים חסרים (באיחור)
    missing_data = get_missing_dapim_data()  # מחזיר (date_obj, daf_string)
    selected_missing_strings = []

    if missing_data:
        missing_strings_only = [x[1] for x in missing_data]
        daf_select_dialog = dapim_from_last_import_date_dlg(missing_strings_only)

        # אם המשתמש בחר דפים או לחץ על "דלג וסמן כנקרא"
        if daf_select_dialog.exec():
            selected_missing_strings = daf_select_dialog.checked_items_list

            if daf_select_dialog.skipped_all:
                # מסמנים את הכל כאילו יובא כדי לקדם את התאריך
                for d_date, _d_str in missing_data:
                    imported_dates.append(d_date)
            else:
                # מסמנים רק מה שנבחר
                for d_date, d_str in missing_data:
                    if d_str in selected_missing_strings:
                        imported_dates.append(d_date)
        else:
            # המשתמש סגר את החלון (X) - לא עושים כלום
            pass

    # 2. בדיקת הדף של היום
    mesekhta_today, daf_today = today_daf()
    today_date_obj = datetime.strptime(today_with_offset(), '%Y-%m-%d').date()
    import_today = False

    # --- תיקון: בדיקה האם היום כבר יובא בעבר (גם אם יש חורים בהיסטוריה) ---
    profile_key = mw.pm.name if gc("import_to_each_profile") else "non_profile"

    # טעינת לוג החריגים
    imported_log_dict = gc("imported_dates_log") or {}
    if not isinstance(imported_log_dict, dict):
        imported_log_dict = {}
    current_log_strs = set(imported_log_dict.get(profile_key, []))

    # טעינת התאריך הרציף האחרון
    try:
        last_continuous_str = gc("last_day_imported")[profile_key]
        last_continuous_date = datetime.strptime(last_continuous_str, '%Y-%m-%d').date()
    except (KeyError, TypeError, ValueError):
        last_continuous_date = datetime.min.date()

    # היום נחשב כיובא אם הוא מופיע בלוג החריגים או שהוא קטן/שווה לתאריך הרציף האחרון
    is_today_already_done = (str(today_date_obj) in current_log_strs) or (today_date_obj <= last_continuous_date)

    if not is_today_already_done:
        if ask_before_import:
            if askUser(f"דער היינטיגער דף היומי איז {mesekhta_today} {daf_today}. האט איר עס שוין געלערנט? "):
                import_today = True
        else:
            import_today = True
    # --- סוף תיקון ---

    # --- הוספה לרשימת הייבוא בפועל ---

    # הוספת דפים חסרים שנבחרו
    # אישיו #371: שמירת סדר הדפים החסרים במקום להפוך אותו.
    for _d_date, d_str in missing_data:
        if d_str in selected_missing_strings:
            m_parts = d_str.split(" ")
            m_daf = m_parts[-1]
            m_name = " ".join(m_parts[:-1])
            add_file_path_to_import(m_name, m_daf)

    # Older selected pages precede today; authors retain their configured order.
    # אישיו #371: הוספת הדף של היום רק אחרי הדפים החסרים שנבחרו.
    if import_today:
        # אישיו #371: צירוף הדף הנוכחי לסוף רשימת הייבוא.
        add_file_path_to_import(mesekhta_today, daf_today)
        # אישיו #371: רישום התאריך הנוכחי בין הימים שנבחרו לייבוא.
        imported_dates.append(today_date_obj)

    # 3. בדיקת מודלים
    for n in repo_notetypes_names:
        getOrCreateModels(mw.col, n)

    # 4. ביצוע הייבוא
    global log
    log = ""
    if pages_to_import != []:
        mw.progress.start(label="אימפארטירט דעם דף היומי...", immediate=True)
        try:
            result = importFromFolder(pages_to_import,
                                      _col=mw.col,
                                      allow_dupes=allow_dupes,
                                      daf=True,
                                      separte_by_prakim=separte_by_prakim,
                                      group_by_masechet=group_by_masechet,
                                      progress_manager=mw.progress)
        finally:
            mw.progress.finish()
        if result:
            showText(result, type="html")

    # 5. עדכון היסטוריית הייבוא
    if imported_dates:
        update_import_history(imported_dates)

def update_import_history(new_dates_list):
    """
    מעדכן את לוג התאריכים שיובאו ומבצע 'דחיסה' של התאריך האחרון
    כדי לא לשמור היסטוריה אין סופית.
    """
    # 1. טעינת המצב הקיים
    profile_key = mw.pm.name if gc("import_to_each_profile") else "non_profile"

    # טעינת התאריך האחרון הרציף (העוגן)
    try:
        last_continuous_date_str = gc("last_day_imported")[profile_key]
        last_continuous_date = datetime.strptime(last_continuous_date_str, '%Y-%m-%d').date()
    except (KeyError, TypeError, ValueError):
        last_continuous_date = datetime.now().date() - timedelta(days=1)

    # טעינת לוג החריגים (דפים שיובאו מעבר לתאריך הרציף)
    # מבנה: dictionary { "profile": ["2025-01-05", "2025-01-07"] }
    imported_log_dict = gc("imported_dates_log") or {}
    if not isinstance(imported_log_dict, dict):
        imported_log_dict = {}

    current_log_strs = imported_log_dict.get(profile_key, [])
    # המרה ל-set של dates לנוחות
    log_dates_set = {datetime.strptime(d, '%Y-%m-%d').date() for d in current_log_strs}

    # 2. הוספת התאריכים החדשים
    for d in new_dates_list:
        log_dates_set.add(d)

    # 3. דחיסה (Compaction): קידום העוגן כל עוד יש רצף
    # בודקים אם (last + 1) קיים בלוג. אם כן, מקדמים ומוחקים מהלוג.
    while True:
        next_day = last_continuous_date + timedelta(days=1)
        if next_day in log_dates_set:
            last_continuous_date = next_day
            log_dates_set.remove(next_day)
        else:
            break

    # 4. שמירה
    # שמירת התאריך הרציף החדש
    wc("last_day_imported", str(last_continuous_date), profile_key)

    # שמירת הלוג המעודכן (המרה חזרה למחרוזות)
    updated_log_list = sorted([str(d) for d in log_dates_set])
    imported_log_dict[profile_key] = updated_log_list

    # שימוש ב-wc לכתיבת כל המילון
    # הפונקציה wc ב-config.py תומכת בכתיבה למפתח ראשי
    # wc("imported_dates_log", imported_log_dict) - לא, ה-wc הנוכחי שלך תומך רק ב-key, val או key, val, second_key
    # נשתמש ישירות ב-writeConfig כדי להיות בטוחים
    conf = mw.addonManager.getConfig(__name__)
    conf["imported_dates_log"] = imported_log_dict
    mw.addonManager.writeConfig(__name__, conf)


def get_missing_dapim_data():
    """
    מחזיר את כל הדפים שבין התאריך הרציף האחרון להיום,
    למעט דפים שכבר נמצאים בלוג הייבוא.
    """
    missing_data = []  # List of tuples (date, string)
    profile_key = mw.pm.name if gc("import_to_each_profile") else "non_profile"

    try:
        last_str = gc("last_day_imported")[profile_key]
        date_to_check = datetime.strptime(last_str, '%Y-%m-%d').date()
    except (KeyError, TypeError, ValueError):
        return []

    # טעינת הלוג
    imported_log_dict = gc("imported_dates_log") or {}
    if not isinstance(imported_log_dict, dict):
        imported_log_dict = {}
    current_log_strs = set(imported_log_dict.get(profile_key, []))

    today = datetime.today().date()

    # רצים מיום אחרי האחרון ועד אתמול (כולל)
    date_to_check += timedelta(days=1)

    while date_to_check < today:
        date_str_key = str(date_to_check)

        # אם התאריך לא נמצא בלוג -> הוא חסר
        if date_str_key not in current_log_strs:
            daf_str = " ".join(today_daf(date_to_check))
            missing_data.append((date_to_check, daf_str))

        date_to_check += timedelta(days=1)

    return missing_data


# ... (rest of the file remains same: get_dapim_from_last_import_date old, init functions) ...
def get_dapim_from_last_import_date():
    # פונקציית תמיכה לאחור אם יש קריאות ממקום אחר, אבל import_daf משתמשת בחדשה
    data = get_missing_dapim_data()
    if not data:
        return []
    strs = [x[1] for x in data]
    daf_select_dialog = dapim_from_last_import_date_dlg(strs)
    if daf_select_dialog.exec():
        return daf_select_dialog.checked_items_list
    return []


def each_profile_init():
    global last_day_imported
    if mw.pm.name in gc("profiles"):
        try:
            last_day_imported = str(gc("last_day_imported")[mw.pm.name])
        except (KeyError, TypeError):
            last_day_imported = 0
        daf_hayomi_init()


def non_profile_init():
    global last_day_imported
    try:
        last_day_imported = str(gc("last_day_imported")["non_profile"])
    except (KeyError, TypeError):
        last_day_imported = 0
    daf_hayomi_init()


def daf_hayomi_init():
    if gc("daf_on") and last_day_imported != today_with_offset():
        try:
            import_daf()
        except Exception as e:
            show_failure("דער דף היומי אימפארט איז נישט פארענדיגט. קאנטראלירט דעם פעקל איידער איר פרובירט נאכאמאל פונעם מאגר השאלות מעניו.", e)


def init_daf():
    if pointVersion() > 54:
        if gc("import_to_each_profile"):
            profile_did_open.append(each_profile_init)
            with contextlib.suppress(ValueError):
                profile_did_open.remove(non_profile_init)
        else:
            profile_did_open.append(non_profile_init)
            with contextlib.suppress(ValueError):
                profile_did_open.remove(each_profile_init)
    else:
        profile_did_open.append(non_profile_init)


init_daf()


class dapim_from_last_import_date_dlg(QDialog):
    def __init__(self, dapim: list):
        super().__init__(mw)
        self.setWindowTitle("צולייגן פעלנדיגע בלעטער")
        self.dapim = dapim
        self.skipped_all = False  # דגל חדש

        self._explanation = QLabel(
            "דא איז א ליסטע בלעטער זינט איר האט צום לעצטן מאל צוגעלייגט שאלות לויטן דף היומי.\nצייכנט אן די בלעטער וואס איר האט זינט דעמאלט געלערנט, צו לייגן זיי צו די חזרות.\nאכטונג! די גרעסטע תועלת פון חזרות איז נאענט צום לערנען. אויב עס איז שוין אדורך אסאך צייט, לערנט די בלעטער איבער איידער איר לייגט זיי צום חזרות סדר.\nאיר קענט אויך שפעטער צולייגן די שאלות מאנועל דורכן מאגר השאלות פענצטער.")
        self._explanation.setWordWrap(True)
        self.list_view = QListView(self)
        self.list_view.setMinimumSize(465, 200)
        self.select_all_btn = QPushButton("קלייבט אלעס אויס")
        self.select_all_btn.clicked.connect(self.select_all)
        self.deselect_all_btn = QPushButton("נעמט אראפ דעם אויסוואל פון אלעס")
        self.deselect_all_btn.clicked.connect(self.deselect_all)

        self.model = QtGui.QStandardItemModel(self.list_view)
        for line in self.dapim:
            self.item = QtGui.QStandardItem(line)
            self.item.setCheckable(True)
            self.item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.model.appendRow(self.item)

        for row_num in range(0, self.model.rowCount()):
            row = self.model.item(row_num)
            row.setEditable(False)

        self.list_view.setModel(self.model)
        self.list_view.clicked.connect(lambda item_index: self.on_item_clicked(item_index))
        self.list_view.doubleClicked.connect(lambda item_index: self.on_item_clicked(item_index))

        self.acceptButton = QPushButton("&אימפארטירט אויסגעקליבענע בלעטער")
        self.acceptButton.clicked.connect(self.checked_items_list_update)
        self.acceptButton.clicked.connect(self.accept)

        self.skipButton = QPushButton("היפט איבער און צייכנט אלעס אן אלס געליינט")
        self.skipButton.clicked.connect(self.skip_all)

        self.rejectButton = QPushButton("&אפזאגן (גארנישט טון)")
        self.rejectButton.clicked.connect(self.reject)

        self.buttonBox = QHBoxLayout()
        self.buttonBox.addWidget(self.deselect_all_btn)
        self.buttonBox.addWidget(self.select_all_btn)
        self.buttonBox.addStretch()
        self.buttonBox.addWidget(self.skipButton)
        self.buttonBox.addWidget(self.acceptButton)
        self.buttonBox.addWidget(self.rejectButton)

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.addWidget(self._explanation)
        self.verticalLayout.addWidget(self.list_view)
        self.verticalLayout.addLayout(self.buttonBox)
        self.setLayout(self.verticalLayout)
        self.checked_items_list = []
        self.show()

    def checked_items_list_update(self):
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                self.checked_items_list.append(item.text())

    def skip_all(self):
        self.checked_items_list = []
        self.skipped_all = True  # מסמן שדילגנו על הכל
        self.accept()

    def select_all(self):
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            item.setCheckState(QtCore.Qt.CheckState.Checked)

    def deselect_all(self):
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)

    def on_item_clicked(self, item_index: QModelIndex):
        item = self.list_view.model().item(item_index.row())
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        elif item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.Checked)
