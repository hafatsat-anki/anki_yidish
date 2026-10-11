import contextlib
import re

from aqt.utils import showInfo, tooltip

with contextlib.suppress(ImportError):
    from aqt.utils import (
        HelpPage,
        tr,
    )
import contextlib

from aqt.qt import *

with contextlib.suppress(ImportError):
    from aqt.operations.card import set_card_deck



def cs_editor_on_alt_cloze(self):
    self.saveNow(self.cs_u_onAltCloze, keepFocus=True)

def cs_editor_on_std_cloze(self):
    self.saveNow(self.cs_u_onStdCloze, keepFocus=True)

def cs_editor_generate_cloze(self, altModifier = False):
        # check that the model is set up for cloze deletion
    if not re.search('{{(.*:)*cloze:',self.note.model()['tmpls'][0]['qfmt']):
        if self.addMode:
            tooltip("אכטונג: באהאלטענע אויסלאזונגען וועלן נישט ארבעטן ביז "
                "איר וועט איבערבייטן דעם סארט אויבן אויפן בלאט צו אן אויסלאזונג סארט.")
        else:
            showInfo("""\
כדי צו שאפן א באהאלטענע אויסלאזונג אין אן עקזיסטירנדער רשומה, דארף מען איר קודם איבערבייטן \
צו אן אויסלאזונג סארט דורכן רעדאקטירן > טויש דעם סארט רשומה.""")
            return
        # find the highest existing cloze
    highest = 0
    for _name, val in list(self.note.items()):
        m = re.findall(r"\{\{c(\d+)::", val)
        if m:
            highest = max(highest, sorted([int(x) for x in m])[-1])
        # reuse last?
    if not altModifier:
        highest += 1
    highest = max(1, highest)
    self.web.eval(f"wrap('{{{{c{highest}::','}}}}');")

#Converts json shortcuts into functions for the reviewer
#sToF: shortcutToFunction
def review_sToF(self,scut):

    #"reviewer" is retained for copy-pastability, may be removed later
    #"self.mw.onEditCurrent" is exactly how it was in reviewer.py, DO NOT CHANGE
    def method(*names):
        for name in names:
            fn = getattr(self, name, None)
            if fn:
                return fn
        return None

    def flag_func(index):
        if hasattr(self, "set_flag_func"):
            return self.set_flag_func(index)
        if hasattr(self, "setFlag"):
            return lambda: self.setFlag(index)
        return None

    sdict = {
        "reviewer edit current": self.mw.onEditCurrent,
        "reviewer flip card": method("onEnterKey"),
        "reviewer flip card 1": method("onEnterKey"),
        "reviewer flip card 2": method("onEnterKey"),
        "reviewer flip card 3": method("onEnterKey"),
        "reviewer options menu": method("onOptions"),
        "reviewer record voice": method("onRecordVoice"),
        "reviewer play recorded voice": method("onReplayRecorded"),
        "reviewer play recorded voice 1": method("onReplayRecorded"),
        "reviewer play recorded voice 2": method("onReplayRecorded"),
        "reviewer delete note": method("onDelete", "delete_current_note"),
        "reviewer suspend card": method("onSuspendCard", "suspend_current_card"),
        "reviewer suspend note": method("onSuspend", "suspend_current_note"),
        "reviewer bury card": method("onBuryCard", "bury_current_card"),
        "reviewer bury note": method("onBuryNote", "bury_current_note"),
        "reviewer mark card": method("onMark", "toggle_mark_on_current_note"),
        "reviewer set flag 1": flag_func(1),
        "reviewer set flag 2": flag_func(2),
        "reviewer set flag 3": flag_func(3),
        "reviewer set flag 4": flag_func(4),
        # #138 — expose every flag supported by Anki 25, not only the first four.
        "reviewer set flag 5": flag_func(5),
        "reviewer set flag 6": flag_func(6),
        "reviewer set flag 7": flag_func(7),
        "reviewer set flag 0": flag_func(0),
        "reviewer replay audio": method("replayAudio"),
        "reviewer replay audio 1": method("replayAudio"),
        "reviewer replay audio 2": method("replayAudio"),
        "reviewer choice 1": lambda: self._answerCard(1),
        "reviewer choice 2": lambda: self._answerCard(2),
        "reviewer choice 3": lambda: self._answerCard(3),
        "reviewer choice 4": lambda: self._answerCard(4),
    }
    sdict["reviewer pause audio"] = method("on_pause_audio")
    sdict["reviewer seek backward"] = method("on_seek_backward")
    sdict["reviewer seek forward"] = method("on_seek_forward")
    sdict["reviewer more options"] = method("showContextMenu")
    sdict["reviewer set due date"] = method("on_set_due")
    sdict["reviewer card info"] = method("on_card_info")
    sdict["reviewer previous card info"] = method("on_previous_card_info")

    if scut in sdict and sdict[scut]:
        return sdict[scut]
    return None

#Converts json shortcuts into functions for the reviewer
#sToF: shortcutToFunction
def editor_sToF(self,scut):
    sdict = {
            "editor card layout": (self.onCardLayout, True),
            "editor bold": (self.toggleBold,),
            "editor italic": (self.toggleItalic,),
            "editor underline": (self.toggleUnderline,),
            "editor superscript": (self.toggleSuper,),
            "editor subscript": (self.toggleSub,),
            "editor remove format": (self.removeFormat,),
            "editor foreground": (self.onForeground,),
            "editor change col": (self.onChangeCol,),
            "editor cloze": (self.cs_onStdCloze,),
            "editor cloze alt": (self.cs_onAltCloze,),
            "editor add media": (self.onAddMedia,),
            "editor record sound": (self.onRecSound,),
            "editor insert latex": (self.insertLatex,),
            "editor insert latex equation": (self.insertLatexEqn,),
            "editor insert latex math environment": (self.insertLatexMathEnv,),
            "editor insert mathjax inline": (self.insertMathjaxInline,),
            "editor insert mathjax block": (self.insertMathjaxBlock,),
            "editor html edit": (self.onHtmlEdit,),
            # #138 — Anki 25.09's legacy onFocusTags accesses a removed self.tags widget.
            "editor focus tags": (self.cs_focus_tags, True),
            "editor toggle sticky current": (self.csToggleStickyCurrent,),
            "editor toggle sticky all": (self.csToggleStickyAll,),
        }
    if get_version() >= 45:
        sdict.update({
            "editor html edit": (lambda:
                self.web.eval(
                    """{const currentField = getCurrentField(); if (currentField) { currentField.toggleHtmlEdit(); }}"""
                ), ),
            "editor block indent": (lambda:
                self.web.eval(
                    """ document.execCommand("indent"); """
                ), ),
            "editor block outdent": (lambda:
                self.web.eval(
                    """ document.execCommand("outdent") """
                ), ),
            "editor list insert unordered": (lambda:
                self.web.eval(
                    """ document.execCommand("insertUnorderedList"); """
                ), ),
            "editor list insert ordered": (lambda:
                self.web.eval(
                    """ document.execCommand("insertOrderedList"); """
                ), ),
                })

    scut = normalizeShortcutName(scut)
    if scut in sdict:
        return sdict[scut]
    return None

def editor_changeDeck(self):
        # AddCards has no card yet; use its asynchronous deck chooser.
        chooser = getattr(self.parentWindow, "deck_chooser", None)
        if chooser is not None:
            chooser.choose_deck()
            return
        if not self.card:
            return
        from aqt.studydeck import StudyDeck
        cid = self.card.id
        did = self.card.did
        current = self.mw.col.decks.get(did)["name"]
        def selected(ret):
            if ret.name:
                target = self.mw.col.decks.id(ret.name)
                set_card_deck(parent=self.widget, card_ids=[cid], deck_id=target).run_in_background()

        StudyDeck(
                self.mw,
                current=current,
                accept=tr.browsing_move_cards(),
                title=tr.browsing_change_deck(),
                help=HelpPage.BROWSING,
                parent=self.mw,
                callback=selected,
                )



#For reviewer shortcut assignments:
#Takes as input ls (the list of shortcuts, of the form (shortcut, function pointer))
#and replacements (a dict mapping function pointers to new shortcuts)
#Then, for every tuple in the list, if its function pointer has a replacement shortcut, replace it
#Changes the list in-place
def reviewer_find_and_replace_functions(ls, replacements):
    for i, val in enumerate(ls):
        func = val[1]
        if func in replacements:
            ls[i] = (replacements[func].pop(), func)
            if not replacements[func]:
                replacements.pop(func)

#For reviewer shortcut assignments:
#Takes as input ls (the list of shortcuts, of the form (shortcut, function pointer))
#and replacements (a dict mapping old shortcuts to new shortcuts)
#Then, for every tuple in the list, if its shortcut is in the list, replace it
#Changes the list in-place
#Prefer reviewer_find_and_replace_functions to this because functions are less fragile
def reviewer_find_and_replace_scuts(ls, replacements):
    for i, val in enumerate(ls):
        scut = val[0]
        if scut in replacements:
            ls[i] = (replacements.pop(scut), val[1])
