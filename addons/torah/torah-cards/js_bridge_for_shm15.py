from typing import Any

from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer

current_card = ""
seen_fields = []
hiden_fields = []


def show_hide_after_reload(card):
    """Shows the fields that were displayed before reloading"""
    global current_card, count
    # showInfo(str(card.id))
    card = card.id
    if card == current_card:
        for field in seen_fields:
            if field == "all":
                mw.web.eval("showall()")
            mw.web.eval(f"show('{field}')")
    else:
        seen_fields.clear()
        hiden_fields.clear()
    current_card = card


gui_hooks.reviewer_did_show_answer.append(show_hide_after_reload)


def clear_lists(*args):
    """Clears the lists when switching to another screen"""
    seen_fields.clear()
    hiden_fields.clear()


gui_hooks.state_will_change.append(clear_lists)
gui_hooks.filtered_deck_dialog_did_add_or_update_deck.append(clear_lists)


def handle_pycmd_message(
        handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    """Receives from the JS the names of the fields that are currently displayed or everything is displayed/hidden"""
    if not isinstance(context, Reviewer):
        return handled
    global seen_fields, hiden_fields
    if message.startswith("show!:"):
        hiden_fields.clear()
        seen_fields.append(message.replace("show!:", ""))
        return (True, None)
    elif message.startswith("hide!:"):
        seen_fields.clear()
        # השורה הבאה הכנה לאפשרות עתידית למקרה שיהיה צורך להסתיר שדות בטעינה מחדש. כרגע אוטומטית הכל מוסתר
        # hiden_fields.append(message.replace("hide!:", ""))
        return (True, None)
    return handled

gui_hooks.webview_did_receive_js_message.append(handle_pycmd_message)

# nt_name = "15 - שאלות ותשובות מרובות"
