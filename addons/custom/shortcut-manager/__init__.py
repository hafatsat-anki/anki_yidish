##התוסף של הקיצורי דרך המקורי
import aqt

#######
from aqt import mw
from aqt.qt import *

from . import Settings as Settings
from . import cs_functions as cs_functions
# #238/#212 - normalize legacy color shortcut rows so malformed config cannot crash editor setup.
from .color_shortcuts import iter_active_color_shortcuts
from . import custom_shortcuts as custom_shortcuts

config = mw.addonManager.getConfig(__name__)

################
#קיצורי מקשים לשינוי צבעים


from anki.hooks import wrap
from aqt import gui_hooks


def updateColour(editor, colour):
    editor.fcolour = colour
    editor.onColourChanged()
    editor._wrapWithColour(editor.fcolour)

def onSetupShortcuts(cuts, editor):
    # add colours
    fresh_config = mw.addonManager.getConfig(__name__)
    for code, key in iter_active_color_shortcuts((fresh_config or {}).get('keys')):
        cuts.append((key, lambda c=code: updateColour(editor, c)))

gui_hooks.editor_did_init_shortcuts.append(onSetupShortcuts)


from . import haf_h_sc as haf_h_sc


# הסתרת הגדרת קיצורי המקשים בחלון ההגדרות. כדי לרכז הכל בחלון קיצורי המקשים
def remove_reduce_motion(self: aqt.preferences.Preferences):
    self.form.preferences_answer_keys.setVisible(False)
    #self.form.hide_top_bar.deleteLater()

aqt.preferences.Preferences.setup_global = wrap(aqt.preferences.Preferences.setup_global, remove_reduce_motion, "after")
