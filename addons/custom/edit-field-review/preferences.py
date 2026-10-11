import aqt
from aqt import mw
from aqt.utils import qconnect
from anki.hooks import wrap
from PyQt6.QtWidgets import QLabel, QComboBox, QHBoxLayout
from .ankiaddonconfig import ConfigManager

conf = ConfigManager()

def add_edit_field_review_preferences(self: aqt.preferences.Preferences):
    # #176 — אפשרות זו משפיעה על עריכה בזמן מבחן, ולכן מוצגת בטאב המבחן ולא בטאב המראה.
    section_label = QLabel('<b>רעדאקטירן פעלדער אינעם חזרה פענסטער</b>', mw)
    self.form.verticalLayout_5.addWidget(section_label)

    hlayout = QHBoxLayout()
    # #311 — תיאור ברור יותר להגדרת ירידת שורה בין שדות.
    label = QLabel("אפטיילונג צווישן פעלדער ביים רעדאקטירן אין א חזרה (צום ביישפיל: דער מקור אין א באזונדערער שורה פון דער פראגע):")
    self.form.edit_field_tag_combo = QComboBox(mw)
    self.form.edit_field_tag_combo.addItems(["א באזונדערע שורה פאר יעדן פעלד", "אלע פעלדער איינס נאכן אנדערן"])

    conf.load()
    current_tag = conf.get("tag", "div")
    if current_tag == "div":
        self.form.edit_field_tag_combo.setCurrentIndex(0)
    else:
        self.form.edit_field_tag_combo.setCurrentIndex(1)

    self.form.edit_field_tag_combo.setToolTip(
        "באזונדערע שורה = יעדער פעלד הייבט זיך אן אויף א נייער שורה (ברירת מחדל).\n"
        "אין איין רצף = די פעלדער ווערן געוויזן איינס נאכן אנדערן אן א נייע שורה."
    )
        
    hlayout.addWidget(label)
    hlayout.addWidget(self.form.edit_field_tag_combo)
    hlayout.addStretch()

    self.form.verticalLayout_5.addLayout(hlayout)
    
    def on_tag_change(index):
        new_tag = "div" if index == 0 else "span"
        conf.load()
        conf['tag'] = new_tag
        conf.save()
        
    qconnect(self.form.edit_field_tag_combo.currentIndexChanged, on_tag_change)

def init_preferences():
    aqt.preferences.Preferences.setup_global = wrap(aqt.preferences.Preferences.setup_global, add_edit_field_review_preferences, "after")
