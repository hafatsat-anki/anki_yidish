
from aqt import gui_hooks, mw
from aqt.qt import QTimer
from aqt.utils import showInfo, showWarning
from _shared_libs.haf_notifications import show_failure

#// getting config information

skipped_cards = []


def _skip_config():
    config = mw.addonManager.getConfig(__name__) or {}
    skipped_by_profile = config.get('skipped_cards')
    if not isinstance(skipped_by_profile, dict):
        skipped_by_profile = {}
        config['skipped_cards'] = skipped_by_profile
    return config, skipped_by_profile


# #239 - defer reviewer reset until the current Browser/editor initialization stack has finished.
def _reset_after_current_event():
    QTimer.singleShot(0, mw.reset)


#// Bury and mark for unburying
def burySkipped():
    # #138 — Undo restores the card, but does not undo this Python list.
    # Skipping it again must not send duplicate IDs to Anki's scheduler.
    if mw.reviewer.card.id not in skipped_cards:
        skipped_cards.append(mw.reviewer.card.id)
    mw.checkpoint("Bury")
    config, skipped_by_profile = _skip_config()
    skipped_by_profile[mw.pm.name] = skipped_cards
    mw.addonManager.writeConfig(__name__, config)
    mw.col.sched.buryCards([mw.reviewer.card.id])
    _reset_after_current_event()

def try_unburySkipped():
    global skipped_cards
    if not skipped_cards:
        return
    try:
        # showInfo("try_unburySkipped")
        mw.col.sched.unbury_cards(list(dict.fromkeys(skipped_cards)))
    except Exception as exc:
        show_failure("מען קען נישט צוריקברענגען די איבערגעהיפטע קארטלעך. די ליסטע איז אפגעזיכערט; עפנט דעם פראפיל פון פריש און פרובירט נאכאמאל.", exc)
        return

    skipped_cards=[]
    config, skipped_by_profile = _skip_config()
    skipped_by_profile[mw.pm.name] = []
    mw.addonManager.writeConfig(__name__, config)
    _reset_after_current_event()

def try_unburySkipped_review_end():
    global skipped_cards
    if not skipped_cards:
        return
    try:
        # showInfo("try_unburySkipped_review_end")
        mw.col.sched.unbury_cards(list(dict.fromkeys(skipped_cards)))
    except Exception as exc:
        show_failure("מען קען נישט צוריקברענגען די איבערגעהיפטע קארטלעך. די ליסטע איז אפגעזיכערט; עפנט דעם פראפיל פון פריש און פרובירט נאכאמאל.", exc)
        return
    skipped_cards=[]
    config, skipped_by_profile = _skip_config()
    skipped_by_profile[mw.pm.name] = []
    mw.addonManager.writeConfig(__name__, config)

#// Unbury skipped cards upon exiting review screeen
gui_hooks.reviewer_will_end.append(try_unburySkipped_review_end)
gui_hooks.profile_will_close.append(try_unburySkipped_review_end)

#// Unbury skipped cards when exiting anki
def try_unbury_Skipped_on_restart(state, _oldstate):
    if state == "deckBrowser":
        config, skipped_by_profile = _skip_config()
        if mw.pm.name in skipped_by_profile:
            # showInfo("try_unbury_Skipped_on_restart")
            skipped_bured_conf = skipped_by_profile.get(mw.pm.name)
            if skipped_bured_conf:
                # for card in skipped_bured_conf:
                # Older sessions may have persisted duplicate card IDs.
                mw.col.sched.unbury_cards(list(dict.fromkeys(skipped_bured_conf)))
                skipped_by_profile[mw.pm.name] = []
                mw.addonManager.writeConfig(__name__, config)
            # mw.reset()

gui_hooks.state_will_change.append(try_unbury_Skipped_on_restart)

def test():
    _config, skipped_by_profile = _skip_config()
    showInfo("{}".format(skipped_by_profile.get(mw.pm.name)))

