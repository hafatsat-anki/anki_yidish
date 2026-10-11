
from aqt import gui_hooks, mw

config = mw.addonManager.getConfig(__name__)

if config.get('REMOVE_TOOLTIP'):

    js = '$("button").removeAttr("title");'

    # title属性を削除してボタンのツールチップを出ないようにする
    def remove_tooltip(card=None):
        mw.reviewer.bottom.web.eval(js)

    gui_hooks.reviewer_did_show_question.append(remove_tooltip)
    gui_hooks.reviewer_did_show_answer.append(remove_tooltip)
