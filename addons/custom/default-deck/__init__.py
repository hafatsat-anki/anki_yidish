import pathlib

from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.utils import askUser


def update_deck_prefs():
    for conf in mw.col.decks.all_config():
        conf["new"]["perDay"] = 9999
        conf["rev"]["perDay"] = 9999
        mw.col.decks.save(conf)
        mw.reset()

def check_or_ask_deck_prefs(*args):
    # profile_settings = mw.pm.profile
    profile_settings = mw.col.conf
    conf_key = "update_deck_prefs_first_time"
    if not mw.col.conf.get(conf_key):
        profile_settings[conf_key] = True
        if mw.col.card_count() > 0 and not askUser("אכטונג! אלס ברירת מחדל באגרעניצט דער פראגראם די טעגליכע חזרות צו 20 פראגעס פאר א פעקל. \nווילט איר אוועקנעמען די גרעניץ פון אלע פעקלעך? \n איר קענט שפעטער טוישן די איינשטעלונג אין די פעקל אפציעס.\nאין די פעקל אפציעס געהערט יעדער פעקל צו א גרופע איינשטעלונגען. א טויש אין דער גרופע האט אן השפעה אויף אלע פעקלעך אין איר."):  #למשתמש ותיק
            return
    else: #כבר בוצע עדכון בעבר
        return
    update_deck_prefs()
    mw.reset()

gui_hooks.profile_did_open.append(check_or_ask_deck_prefs)



def add_menu_action():
    if not hasattr(mw, "addon_col_menu"):
        return
    action = QAction("נעם אוועק די טעגליכע חזרה גרעניץ", mw)
    qconnect(action.triggered, lambda: update_deck_prefs())
    filename = str(pathlib.Path(__file__).parent.resolve())
    icon = QIcon(filename + "/slash-circle.svg")
    action.setIcon(icon)
    mw.addon_col_menu.addAction(action)

gui_hooks.main_window_did_init.append(add_menu_action)
