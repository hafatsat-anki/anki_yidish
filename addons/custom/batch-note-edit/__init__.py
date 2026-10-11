# import standard libraries
from aqt import mw
from aqt.qt import *
from aqt.utils import askUser, tooltip


class TargetNoteTypeDialog(QDialog):
    def __init__(self, model_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("קלייבט אויס דעם ציל סארט רשומה")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFixedWidth(500)

        layout = QVBoxLayout()
        info_label = QLabel("קלייבט אויס דעם נייעם סארט רשומה פאר אלע אויסגעקליבענע רשומות:")
        layout.addWidget(info_label)

        self.combo = QComboBox()
        self.combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo.setMinimumContentsLength(20)
        self.combo.addItems(model_names)
        layout.addWidget(self.combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def selected_name(self):
        return self.combo.currentText()


# מחלקה לדיאלוג התאמת שדות
class FieldMappingDialog(QDialog):
    def __init__(self, source_model, target_model, parent=None):
        super().__init__(parent)
        self.source_model = source_model
        self.target_model = target_model
        self.field_map = {} # {source_idx: target_idx}
        self.setWindowTitle(f"פארבינדונג פון פעלדער: {source_model['name']} ← {target_model['name']}")
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setFixedWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # הסבר
        info_label = QLabel(f"<b>טוישט פון:</b> {self.source_model['name']}<br><b>צו:</b> {self.target_model['name']}<br><br>פארבינדט די אלטע פעלדער מיט די ציל פעלדער:")
        layout.addWidget(info_label)

        grid = QGridLayout()
        self.combos = []

        # שדות המקור והיעד
        src_fields = [f['name'] for f in self.source_model['flds']]
        tgt_fields = [f['name'] for f in self.target_model['flds']]

        # יצירת שורות לכל שדה ביעד
        # אנחנו עוברים על שדות היעד ומבקשים מהמשתמש לבחור שדה מקור עבורם
        for i, tgt_name in enumerate(tgt_fields):
            label = QLabel(f"ציל: <b>{tgt_name}</b> ")
            combo = QComboBox()
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(12)
            combo.addItem("-- איבערהיפן --", -1)

            # הוספת שדות המקור לאפשרויות
            for j, src_name in enumerate(src_fields):
                combo.addItem(src_name, j)

            # ניסיון ניחוש אוטומטי לפי שם השדה
            index = combo.findText(tgt_name)
            if index != -1:
                combo.setCurrentIndex(index)

            grid.addWidget(label, i, 0)
            grid.addWidget(combo, i, 1)
            self.combos.append((i, combo))

        layout.addLayout(grid)

        # כפתורים
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_mapping(self):
        # יצירת המילון שנדרש לאנקי: {source_index: target_index}
        mapping = {}
        for tgt_idx, combo in self.combos:
            src_idx = combo.currentData()
            if src_idx is not None and src_idx != -1:
                mapping[src_idx] = tgt_idx
        return mapping

def change_mixed_note_types(browser):
    # 1. קבלת הרשומות שנבחרו
    nids = browser.selectedNotes()
    if not nids:
        tooltip("קיין רשומות זענען נישט אויסגעקליבן געווארן.")
        return

    mw.checkpoint("Change Mixed Note Types")
    col = mw.col

    # 2. קיבוץ הרשומות לפי סוג המקור שלהן (Note Type ID)
    # קבוצות = { model_id: [nid1, nid2, ...] }
    groups = {}
    for nid in nids:
        note = col.get_note(nid)
        mid = note.mid
        if mid not in groups:
            groups[mid] = []
        groups[mid].append(nid)

    # 3. בחירת סוג רשומה חדש (היעד)
    # שימוש בדיאלוג פשוט לבחירת המודל
    models = sorted(col.models.all(), key=lambda m: m['name'])
    model_names = [m['name'] for m in models]

    target_dialog = TargetNoteTypeDialog(model_names, browser)
    if target_dialog.exec() != QDialog.DialogCode.Accepted:
        return

    target_name = target_dialog.selected_name()

    target_model = col.models.by_name(target_name)

    # משתנה למעקב אם בוצע שינוי
    changes_made = False

    # 4. מעבר על כל קבוצה וביצוע המרה
    for src_mid, group_nids in groups.items():
        src_model = col.models.get(src_mid)

        # אם סוג המקור זהה ליעד, אין מה לעשות (אלא אם רוצים לרענן, אבל נדלג)
        if src_mid == target_model['id']:
            continue

        # פתיחת דיאלוג להתאמת שדות עבור הקבוצה הנוכחית
        dialog = FieldMappingDialog(src_model, target_model, browser)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            # אם המשתמש ביטל עבור סוג אחד, האם לעצור הכל?
            # כאן נבחר לעצור כדי לא ליצור בלאגן, או שאפשר just continue
            res = askUser(f"די פארבינדונג איז אפגעזאגט געווארן פאר '{src_model['name']}'. אפשטעלן אלע טוישן וואס ווארטן?")
            if res:
                break
            continue

        field_map = dialog.get_mapping()

        # התאמת תבניות כרטיסים (Card Templates)
        # כדי לפשט, נעשה מיפוי 1 ל-1 לפי אינדקס (Card 1 -> Card 1)
        # אם יש פערים, כרטיסים עודפים ימחקו או יווצרו לפי הלוגיקה של אנקי
        card_map = {}
        src_tmpls = src_model['tmpls']
        tgt_tmpls = target_model['tmpls']
        for i in range(len(src_tmpls)):
            if i < len(tgt_tmpls):
                card_map[i] = i
            else:
                # אין תבנית תואמת ביעד (למשל המרה מ-Reverse ל-Basic)
                card_map[i] = None

        # ביצוע השינוי בפועל
        # הפונקציה change מקבלת: (source_model, nids, target_model, field_map, card_map)
        col.models.change(src_model, group_nids, target_model, field_map, card_map)
        changes_made = True

    # 5. סיום וריענון
    if changes_made:
        mw.reset()
        tooltip("די רשומות זענען מיט הצלחה איבערגעטוישט געווארן.")
    else:
        tooltip("קיין טוישן זענען נישט געמאכט געווארן.")

def setup_menu_item(browser):
    menu = browser.form.menu_Notes
    action = QAction("טויש דעם סארט רשומה (געמישטע אויסוואל)", browser)
    action.triggered.connect(lambda: change_mixed_note_types(browser))
    menu.addSeparator()
    menu.addAction(action)

    # הוספה גם לתפריט קליק ימני (Context Menu)
    browser.form.menu_Notes.addAction(action)

# רישום ה-Hook באתחול התפריטים בדפדפן
from aqt.gui_hooks import browser_menus_did_init

browser_menus_did_init.append(setup_menu_item)
