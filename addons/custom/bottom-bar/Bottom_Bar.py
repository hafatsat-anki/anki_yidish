#// auth_ Mohamad Janati
#// Copyright (c) 2019-2021 Mohamad Janati (freaking stupid, right? :|)
import contextlib
import json
import re
import time
from typing import Union, cast

import aqt
from anki.hooks import wrap
from anki.tags import MARKED_TAG
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.reviewer import Reviewer
from aqt.utils import downArrow, tr

from . import Card_Info
from .Skip import burySkipped, try_unburySkipped

#// getting config information
config = mw.addonManager.getConfig(__name__)
speedFocus_addOn = config['  Speed Focus Add-on']
skipMethod = config['  Skip Method']
skip_shortcut = config ['Button_ Shortcut_ Skip Button'].lower()
showSkipped_shortcut = config ['Button_ Shortcut_ Show Skipped Button'].lower()
info_shortcut = config['Button_ Shortcut_ Info Button'].lower()
undo_shortcut = config['Button_ Shortcut_ Undo Button'].lower()

info_label = config['Button Label_ Info']
skip_label = config['Button Label_ Skip']
undo_label = config['Button Label_ Undo']


# מקשי הקיצור של כפתורי שוב/קשה/טוב/קל, נטענים מתוסף מנהל קיצורי מקשים (shortcut-manager)
_answer_button_keys: dict[int, str] = {}
_answer_button_titles_enabled = False


def _load_answer_button_keys() -> None:
    global _answer_button_keys, _answer_button_titles_enabled
    sm_config = mw.addonManager.getConfig("shortcut-manager") or {}
    _answer_button_titles_enabled = str(sm_config.get("Ω enable reviewer", "")).upper() == 'Y'
    _answer_button_keys = {
        ease: sm_config.get(f"reviewer choice {ease}", str(ease))
        for ease in range(1, 5)
    }


_load_answer_button_keys()


def _reload_config() -> None:
    global config, speedFocus_addOn, skipMethod
    global skip_shortcut, showSkipped_shortcut, info_shortcut, undo_shortcut
    global info_label, skip_label, undo_label
    config = mw.addonManager.getConfig(__name__)
    if not config:
        return
    speedFocus_addOn = config['  Speed Focus Add-on']
    skipMethod = config['  Skip Method']
    skip_shortcut = config['Button_ Shortcut_ Skip Button'].lower()
    showSkipped_shortcut = config['Button_ Shortcut_ Show Skipped Button'].lower()
    info_shortcut = config['Button_ Shortcut_ Info Button'].lower()
    undo_shortcut = config['Button_ Shortcut_ Undo Button'].lower()
    info_label = config['Button Label_ Info']
    skip_label = config['Button Label_ Skip']
    undo_label = config['Button Label_ Undo']

    _load_answer_button_keys()

    global SF_bottomHTML
    if config['  Speed Focus Add-on']:
        SF_bottomHTML = """
var autoAnswerTimeout = 0;
var autoAgainTimeout = 0;
var autoAlertTimeout = 0;

var setAutoAnswer = function(ms) {
    clearTimeout(autoAnswerTimeout);
    autoAnswerTimeout = setTimeout(function () { pycmd('ans') }, ms);
}
var setAutoAgain = function(ms) {
    clearTimeout(autoAgainTimeout);
    autoAgainTimeout = setTimeout(function () { pycmd("ease1"); }, ms);
}
var setAutoAlert = function(ms) {
    clearTimeout(autoAlertTimeout);
    autoAlertTimeout = setTimeout(function () { pycmd("autoalert"); }, ms);
}"""
    else:
        SF_bottomHTML = ""


gui_hooks.profile_did_open.append(_reload_config)



#// adding shortcuts to _shortcutKeys function in anki
def _shortcutKeys_wrap(self, _old):
    original = _old(self)
    sched_ver = mw.col.sched.version
    if sched_ver > 2 or skipMethod == 1:
        original.append((skip_shortcut, lambda: burySkipped()))
        original.append((showSkipped_shortcut, lambda: try_unburySkipped()))
    else:
        original.append((skip_shortcut, lambda: self.nextCard()))
    original.extend([
    (info_shortcut, lambda: Card_Info._cs.toggle()),
    (undo_shortcut, lambda: mw.onUndo())
    ])
    return original


def inBrowser():
    current_deck = mw.col.decks.current()
    name =current_deck["name"]
    find= f'"deck:{name}"'
    if not mw.col.decks.is_filtered(current_deck["id"]):
        find += ' (rated:1 or is:due or is:new) -is:suspended'
    browser = aqt.dialogs.open("Browser", aqt.mw)
    browser.search_for(f"{find}")
    browser.update_history()

#add to context menu
def showSkipped_():
    try_unburySkipped()

def showContextMenu(r, m):
        a=m.addAction("ווייז איבערגעהיפטע קארטלעך")
        a.setShortcut(QKeySequence(showSkipped_shortcut))
        a.triggered.connect(showSkipped_)

gui_hooks.reviewer_will_show_context_menu.append(showContextMenu)

#// adding button links to link handler function
def linkHandler_wrap(reviewer, url):
    # sched_ver = mw.col.sched.version
    if url == "card_info":
        Card_Info._cs.toggle()
    elif url == "skip":
        burySkipped()
    elif url == "showSkipped":
        try_unburySkipped()
    elif url == "undo":
        mw.onUndo()
    elif url == "mark":
        mw.reviewer.onMark()
    elif url == "start_muted":
        mw.onUndo()
    elif url == "bury":
        mw.reviewer.onBuryNote()
    elif url == "replay":
        mw.reviewer.replayAudio()
    elif url == "show_text_box":
        mw.reviewer.show_text_box()
    elif url == "browse_review":
        inBrowser()
    else:
        Review_linkHandelr_Original(reviewer, url)

Review_linkHandelr_Original = Reviewer._linkHandler
Reviewer._linkHandler = linkHandler_wrap

#// Speed focus remove conflicts
if speedFocus_addOn:
    SF_bottomHTML = """
var autoAnswerTimeout = 0;
var autoAgainTimeout = 0;
var autoAlertTimeout = 0;

var setAutoAnswer = function(ms) {
    clearTimeout(autoAnswerTimeout);
    autoAnswerTimeout = setTimeout(function () { pycmd('ans') }, ms);
}
var setAutoAgain = function(ms) {
    clearTimeout(autoAgainTimeout);
    autoAgainTimeout = setTimeout(function () { pycmd("ease1"); }, ms);
}
var setAutoAlert = function(ms) {
    clearTimeout(autoAlertTimeout);
    autoAlertTimeout = setTimeout(function () { pycmd("autoalert"); }, ms);
}"""
else:
    SF_bottomHTML = ""


def _update_mark_icon(self) -> None:
    self.bottom.web.eval(f"starclick({json.dumps(self.card.note().has_tag(MARKED_TAG))});")

#// Review Screen Bottombar HTML
def _bottomHTML(self):
    time_color = ""
    return f"""
    <style>
    button {{
        border-radius: 10px !important;
        }}
.buttonbar1 {{
border-radius: var(--border-radius-large);
  background-color: white;
  color: black;
  padding: 0px !important;
  min-width: 0px;
  position: absolute;
  top: -20px;
  min-height: 22px;
  width: 22px;
  box-shadow:none !important;
  display: block;
  border: 2px solid #ededed00 !important;
  }}

.buttonbar1:hover {{
  border: 2px solid #ededed !important;
}}

.nightMode .buttonbar1 {{
  background-color: rgb(44, 44, 44) !important;
  color: black !important;
  padding: 0px !important;
  min-width: 0px !important;
  position: absolute !important;
  top: -11px !important;
  height: 22px  !important;
  width: 22px  !important;
  display: block !important;
  border: 2px solid #ededed00 !important;
  }}

.nightMode .buttonbar1:hover {{
  border: 2px solid #ededed !important;
}}
.nightMode svg {{
  fill: white;
}}

/* #284 — מען היט דעם טאבעלע Anki אריגינעל; סעלעקטארן child בלויז, כדי נישט צו שטערן די ענטפער קנעפל טאבעלע אינעם מיטעלן צעל. */
#outer {{
    width: 100%;
    overflow: visible;
}}

#innertable {{
    position: relative;
    width: 100% !important;
    table-layout: auto;
    border-collapse: collapse;
}}

#innertable > tbody > tr > td,
#innertable > tr > td {{
    position: relative;
    vertical-align: top;
    white-space: nowrap;
}}


/* #284 — די זייטיגע כלים שוועבן איבער דער קנעפל שורה און נעמען נישט קיין צעל וואס רוקט רעדאקטירן/אינפארמאציע/איבערהיפן. */
#bottom-toolbar {{
    display: block !important;
    position: absolute !important;
    top: 0;
    right: 0;
    width: 0 !important;
    min-width: 0 !important;
    height: 0;
    padding: 0 !important;
    overflow: visible !important;
    z-index: 5;
    pointer-events: none;
}}

#bottom-toolbar .buttonbar1 {{
    z-index: 6;
    pointer-events: auto;
}}

#innertable #middle {{
    width: auto !important;
    text-align: center;
    padding: 0 8px;
}}

/* #284 — קנעפל "ווייז די ענטפער" און די ענטפער קנעפלעך בלייבן אין מיטן צעל, אן אז-CSS פונעם סרגל זאל איבערשרייבן די אינערליכע טאבעלעס פון Anki. */
#innertable #middle > button,
#innertable #middle #ansbut,
#innertable #middle > center,
#innertable #middle > table {{
    margin-left: auto !important;
    margin-right: auto !important;
}}

#innertable #middle table {{
    margin-inline: auto !important;
}}

#innertable > tbody > tr > td.stat button,
#innertable > tr > td.stat button {{
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: clamp(44px, 8vw, 96px);
    min-width: 44px !important;
}}

@media (max-width: 620px) {{
    #innertable > tbody > tr > td.stat button,
    #innertable > tr > td.stat button {{
        font-size: 10px !important;
        padding-left: 2px !important;
        padding-right: 2px !important;
    }}

    #innertable #middle > button {{
        min-width: 44px !important;
    }}
}}

</style>

<center id=outer>
    <table id=innertable width=100% cellspacing=0 cellpadding=0>
        <tr>

            <!--options bar-->

            <td id="bottom-toolbar" aria-label="קארטל כלים">
                <button type="button" class="buttonbar1" id="star" onclick="pycmd('mark');"
                    title="צייכן אן אדער נעם אוועק דעם סימון פון דער יעצטיגער רשומה" style="right: 0px;">
                    <svg xmlns="http://www.w3.org/2000/svg" height="26" width="26" viewBox="-4 0 25 25">
                        <path stroke="null" id="svg_1"
                            d="m6.07975,16.6688l3.92807,-2.46982l3.92807,2.49609l-1.05082,-4.67689l3.4527,-3.15296l-4.55356,-0.42039l-1.77639,-4.41415l-1.77639,4.38787l-4.55356,0.42039l3.4527,3.15296l-1.05082,4.67689zm-2.25176,3.28434l1.62627,-7.38319l-5.45426,-4.96591l7.20563,-0.65687l2.80219,-6.96279l2.80219,6.96279l7.20563,0.65687l-5.45426,4.96591l1.62627,7.38319l-6.17983,-3.91493l-6.17983,3.91493zm6.17983,-9.32751z" />
                    </svg>
                </button>

                <button type="button" class="buttonbar1" onclick="pycmd('resched');" title="נייער צייטפלאן"
                    style="right: 27px;">
                    <svg xmlns="http://www.w3.org/2000/svg" height="25" width="25" viewBox="-2 0 25 25">
                        <path
                            d="M12,5V1L7,6l5,5V7c3.31,0,6,2.69,6,6s-2.69,6-6,6s-6-2.69-6-6H4c0,4.42,3.58,8,8,8s8-3.58,8-8S16.42,5,12,5z" />
                    </svg>
                </button>

                <button type="button" class="buttonbar1" onclick="pycmd('bury');" title="לייג באזייטיג ביז מארגן (שטופ אפ די פראגע ביז מארגן)"
                    style="right: 55px;">
                    <svg  xmlns="http://www.w3.org/2000/svg" height="21" width="21"  viewBox="0 0 511.999 511.999" xml:space="preserve" fill="#000000">
                    <path d="M89.759,239.644l-45.647,45.647C-9.546,338.949-14.247,423.011,29.984,482.01 c58.999,44.231,143.059,39.529,196.719-14.129l45.648-45.647L89.759,239.644z"></path>
                    <path d="M29.984,482.011c58.999,44.231,143.059,39.529,196.719-14.129l45.648-45.647l-91.296-91.294 L29.984,482.011z"></path>
                    <path d="M395.163,147.262L113.67,428.754c-8.404,8.404-22.028,8.405-30.433,0.001l0,0 c-8.404-8.404-8.403-22.028,0.001-30.431l281.494-281.493L395.163,147.262z"></path>
                    <path d="M83.238,428.755c8.405,8.404,22.03,8.404,30.433-0.001l273.886-273.885l-15.217-15.216 L83.238,428.755z"></path>
                    <path d="M447.334,125.525c-16.807,16.807-44.056,16.807-60.863,0c-16.809-16.807-16.809-44.056,0-60.864 l-22.825-22.824c-29.413,29.413-29.413,77.099,0,106.511c29.413,29.413,77.099,29.413,106.511,0L447.334,125.525z"></path>
                    <path d="M386.47,125.525C386.469,125.524,386.469,125.524,386.47,125.525l-22.825,22.824l0,0 c29.413,29.413,77.099,29.413,106.511,0l-22.824-22.824C430.527,142.332,403.277,142.332,386.47,125.525z"></path>
                    <rect x="405.209" y="-6.187" transform="matrix(-0.7071 0.7071 -0.7071 -0.7071 794.1403 -169.1716)" width="53.795" height="172.146"></rect> <rect x="435.651" y="67.272" transform="matrix(-0.7071 0.7071 -0.7071 -0.7071 867.6194 -138.7625)" width="53.795" height="86.073"></rect>
                    </svg>
                </button>

                <button type="button" class="buttonbar1" onclick="pycmd('undo');" title="זאג אפ" style="right: 90px;">
                    <svg xmlns="http://www.w3.org/2000/svg" height="25" width="25" viewBox="-2 0 25 25">
                        <path
                            d="M18.4 10.6C16.55 8.99 14.15 8 11.5 8c-4.65 0-8.58 3.03-9.96 7.22L3.9 16c1.05-3.19 4.05-5.5 7.6-5.5 1.95 0 3.73.72 5.12 1.88L13 16h9V7l-3.6 3.6z" />
                    </svg>
                </button>

                <button type="button" class="buttonbar1" onclick="pycmd('replay');"
                    title="שפיל דעם קארטל אוידיא אדער ווידיא" style="right: 120px;">
                    <svg xmlns="http://www.w3.org/2000/svg" height="25" width="25" viewBox="-2 1 25 25">
                        <path
                            d="M12,2C6.48,2,2,6.48,2,12s4.48,10,10,10s10-4.48,10-10S17.52,2,12,2z M12,20c-4.41,0-8-3.59-8-8s3.59-8,8-8s8,3.59,8,8 S16.41,20,12,20z M9.5,16.5l7-4.5l-7-4.5V16.5z" />
                    </svg>
                </button>

                <!-- <button type="button" class="buttonbar1" onclick="pycmd('start_muted');" title="שאלט צייטווייליג אויס קלאנגען"
                    style="right: 150px;">
                    <svg xmlns="http://www.w3.org/2000/svg" height="25" width="25" viewBox="-4 0 25 25">
                        <path stroke="null" id="svg_1"
                            d="m12.21104,19.6367l0,-1.70862q2.57641,-0.77163 4.20991,-2.96252t1.6335,-4.97428q0,-2.78339 -1.62022,-4.98806q-1.62022,-2.20467 -4.22319,-2.94874l0,-1.70862q3.29355,0.77163 5.36531,3.45857q2.07175,2.68694 2.07175,6.18684t-2.07175,6.18684q-2.07175,2.68694 -5.36531,3.45857zm-11.68681,-6.31086l0,-6.614l4.24975,0l5.31218,-5.51167l0,17.63733l-5.31218,-5.51167l-4.24975,0zm11.15559,1.3228l0,-9.28716q1.46085,0.46849 2.32408,1.76373t0.86323,2.89362q0,1.57082 -0.87651,2.86607t-2.3108,1.76373zm-3.18731,-9.2596l-3.00138,2.9763l-3.37324,0l0,3.307l3.37324,0l3.00138,3.00386l0,-9.28716zm-2.49673,4.6298z" />
                    </svg>
                </button> -->

                 <button type="button" class="buttonbar1" onclick="pycmd('show_text_box');"
                    title="ווייז א קעסטל אריינצוטייפן די ענטפער" style="right: 150px;">
                    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
                    <path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h357l-80 80H200v560h560v-278l80-80v358q0 33-23.5 56.5T760-120H200Zm280-360ZM360-360v-170l367-367q12-12 27-18t30-6q16 0 30.5 6t26.5 18l56 57q11 12 17 26.5t6 29.5q0 15-5.5 29.5T897-728L530-360H360Zm481-424-56-56 56 56ZM440-440h56l232-232-28-28-29-28-231 231v57Zm260-260-29-28 29 28 28 28-28-28Z"/>
                    </svg>
                </button>


            </td>

            <!--end of options bar-->

            <td width=50 align=left valign=top id=edit class=stat>
                <button title="קיצור קנעפל: E" onclick="pycmd('edit');">
                    רעדאקטירן
                </button>

            </td>

            <td width=50 align=left valign=top id=info class=stat>
                <button title="קיצור קנעפל: {info_shortcut.upper()}" onclick="pycmd('card_info');" {info_label}>אינפארמאציע
                </button>
            </td>

            <td align=center valign=top id=middle>
            </td>

            <td width=50 align=right valign=top class=stat>
                <button title="קיצור קנעפל: {skip_shortcut.upper()}" onclick="pycmd('skip');" {skip_label}>איבערהיפן
                </button>
            </td>
            <td width=50 align=right valign=top class=stat> <button title="קיצור קנעפל: {undo_shortcut}"
                    onclick="pycmd('undo');" {undo_label}>מאך צוריק די<br>לעצטע פעולה / גיי צוריק<br>צו דער פריערדיגער פראגע</button> </td>
            <td width=50 align=right valign=top class=stat style='color: {time_color}'>
                                <span id=time class=stattxt style="    top: 26px !important; left: 34px;   position: fixed;"></span>
                <button onclick="pycmd('more');">
                    אפציעס <br> נאך {downArrow()}

                </button>
            </td>
        </tr>
    </table>
</center>
<script>
function starclick(star_checked) {{
    let notetypeelement = document.getElementById("star");
    if (star_checked == true) {{
        notetypeelement.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" height="27" width="26" viewBox="-2 3 25 25">
                        <path stroke="null" id="svg_1"
                            d="M5.825,22 L7.45,14.975 2,10.25 9.2,9.625 12,3 14.8,9.625 22,10.25 16.55,14.975 18.175,22 12,18.275Z" />
                    </svg>`;
      }} else {{
        notetypeelement.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" height="26" width="26" viewBox="-4 0 25 25">
                        <path stroke="null" id="svg_1"
                            d="m6.07975,16.6688l3.92807,-2.46982l3.92807,2.49609l-1.05082,-4.67689l3.4527,-3.15296l-4.55356,-0.42039l-1.77639,-4.41415l-1.77639,4.38787l-4.55356,0.42039l3.4527,3.15296l-1.05082,4.67689zm-2.25176,3.28434l1.62627,-7.38319l-5.45426,-4.96591l7.20563,-0.65687l2.80219,-6.96279l2.80219,6.96279l7.20563,0.65687l-5.45426,4.96591l1.62627,7.38319l-6.17983,-3.91493l-6.17983,3.91493zm6.17983,-9.32751z" />
                    </svg>`;
      }}
  }}
time = {self.card.time_taken() // 1000};
{SF_bottomHTML}

</script>
"""
#// מציג בטולטיפ של כפתורי שוב/קשה/טוב/קל את מקש הקיצור שהוגדר במנהל קיצורי המקשים
def _answerButtons_wrap(self, _old):
    html = _old(self)
    if not _answer_button_titles_enabled:
        return html

    def repl(m):
        ease = int(m.group(2))
        key = _answer_button_keys.get(ease, "")
        title = tr.actions_shortcut_key(val=key) if key and key != "<nop>" else ""
        return f'title="{title}"{m.group(1)}'

    return re.sub(r'title="[^"]*"(\s+data-ease="(\d)")', repl, html)


#// replacing/wrapping functions
Reviewer._shortcutKeys = wrap(Reviewer._shortcutKeys, _shortcutKeys_wrap, 'around')
Reviewer._update_mark_icon = wrap(Reviewer._update_mark_icon, _update_mark_icon, 'after')
Reviewer._answerButtons = wrap(Reviewer._answerButtons, _answerButtons_wrap, 'around')
Reviewer._bottomHTML = _bottomHTML


#הסתרת הפלוס בין המספרים של השאלות שנשארו במסך מבחן
# TODO: להעביר לתוסף של מראה כפתורי תשובה

def _get_total_counts() -> tuple[int, int]:
    """ברענגט צוריק (total_new, total_rev) אן צו רעכענען די טעגליכע גרעניצן."""
    try:
        deck = mw.col.decks.current()
        if mw.col.decks.is_filtered(deck["id"]):
            return -1, -1
        all_dids = mw.col.decks.deck_and_child_ids(deck["id"])
        did_str = ",".join(str(d) for d in all_dids)
        today = mw.col.sched.today
        total_new = mw.col.db.scalar(
            f"select count() from cards where did in ({did_str}) and queue = 0"
        )
        total_rev = mw.col.db.scalar(
            f"select count() from cards where did in ({did_str}) and queue = 2 and due <= ?",
            today
        )
        return total_new, total_rev
    except Exception:
        return -1, -1


def _today_start_ms() -> int:
    cutoff = getattr(mw.col.sched, "day_cutoff", None)
    if cutoff:
        return int(cutoff - 86400) * 1000
    return int(time.time() - 86400) * 1000


# #361 — כרטיס שנענה ב"טוב"/"קשה" בחפיסה זמנית (מסוננת) יוצא ממנה מיד אם אינו עומד עוד
# בתנאי הסינון: did חוזר לחפיסת המקור ו-odid מתאפס. שאילתת cards.did/odid בזמן השאילתה
# (במקום בזמן המענה עצמו) מפספסת אותו, ולכן רק כרטיסי "שוב" (שנשארים בחפיסה) נספרו כאפורים.
# פתרון: קאש בזיכרון של card id שנענו היום מתוך החפיסה הנוכחית, מתמלא מיד ב-reviewer_did_answer_card
# ולכן לא תלוי במיקום החפיסה הנוכחי של הכרטיס.
_answered_today_cache: dict[int, set[int]] = {}
_answered_today_cache_date: Union[str, None] = None


def _answered_today_cache_key() -> Union[int, None]:
    try:
        return mw.col.decks.current()["id"]
    except Exception:
        return None


def _reset_answered_today_cache_if_new_day() -> None:
    global _answered_today_cache, _answered_today_cache_date
    today = str(mw.col.sched.today) if mw.col and mw.col.sched else ""
    if today != _answered_today_cache_date:
        _answered_today_cache = {}
        _answered_today_cache_date = today


def _record_answered_card(card_id: int, deck_id: int) -> None:
    _reset_answered_today_cache_if_new_day()
    _answered_today_cache.setdefault(deck_id, set()).add(card_id)


def _answered_today_count() -> int:
    try:
        _reset_answered_today_cache_if_new_day()
        deck = mw.col.decks.current()
        all_dids = mw.col.decks.deck_and_child_ids(deck["id"])
        did_str = ",".join(str(did) for did in all_dids)
        db_ids = mw.col.db.list(
            f"""
            select distinct r.cid
            from revlog r
            join cards c on c.id = r.cid
            where r.id >= ? and (c.did in ({did_str}) or c.odid in ({did_str}))
            """,
            _today_start_ms(),
        ) or []
        # איחוד אמיתי של מזהים (ולא max של ספירות): כרטיס שנענה לפני הפעלה מחדש נספר רק
        # ב-DB, וכרטיס שיצא מהחפיסה הזמנית נספר רק בקאש — שניהם צריכים להיכלל יחד.
        cached_ids = _answered_today_cache.get(deck["id"], set())
        return len(set(db_ids) | cached_ids)
    except Exception:
        return 0


def _answered_card_cache_hook(reviewer, card, ease) -> None:
    deck_key = _answered_today_cache_key()
    if deck_key is not None:
        _record_answered_card(card.id, deck_key)


gui_hooks.reviewer_did_answer_card.append(_answered_card_cache_hook)


def _new_card_today_weight(card) -> int:
    """Number of times a new card can occupy the queue before today's cutoff."""
    try:
        decks = mw.col.decks
        if hasattr(decks, "config_dict_for_deck_id"):
            deck_config = decks.config_dict_for_deck_id(card.did)
        else:
            deck_config = decks.config_for_did(card.did)
        new_config = deck_config.get("new", {}) if isinstance(deck_config, dict) else {}
        steps = new_config.get("delays") or new_config.get("learning_steps") or []
        remaining_minutes = max(
            0.0,
            (float(mw.col.sched.day_cutoff) - time.time()) / 60.0,
        )

        # #365 — כל צעד קצר מיום נחשב רק אם אפשר להגיע אליו בפועל לפני סוף
        # היום. לדוגמה, בצעדים 1 ו-10 דקות כשנותרו 5 דקות, נספר רק הצעד הראשון.
        elapsed = 0.0
        available_steps = 0
        for raw_delay in steps:
            delay = float(raw_delay)
            if delay >= 24 * 60:
                break
            elapsed += delay
            if elapsed > remaining_minutes:
                break
            available_steps += 1
        return max(1, available_steps)
    except Exception:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/custom/bottom-bar/Bottom_Bar.py:_new_card_today_weight', 'מען קען נישט אויסרעכענען די לערן שטאפלען. דער פארשריט סרגל ניצט צייטווייליג א וואג פון 1 פאר א נייע קארטל און קען זיין אומפינקטליך.')
        return 1


def _split_learning_counts(queued_learning: int, pending_learning: int) -> tuple[int, int]:
    """טיילט דעם אנקי לערן ציילער צווישן גרייטע קארטלעך און קארטלעך וואס ווארטן."""
    queued = max(0, int(queued_learning))
    pending = max(0, int(pending_learning))
    return max(0, queued - pending), pending


def _is_waiting_learning_card(
    card_id: int,
    current_card_id: int,
    queue: int,
    due: int,
    now: int,
    cutoff: int,
) -> bool:
    """גיט צוריק אמת נאר פאר א לערן קארטל וואס איז היינט נאך נישט גרייט צום ענטפערן."""
    return card_id != current_card_id and queue == 1 and now < due < cutoff


def _remaining_(self) -> str:
    if not self.mw.col.conf["dueCounts"]:
        return ""

    counts: list[Union[int, str]]
    if v3 := self._v3:
        idx, counts_ = v3.counts()
        counts = cast(list[Union[int, str]], counts_)
    else:
        # v1/v2 scheduler
        counts = list(self.mw.col.sched.counts()) if self.hadCardQueue else list(self.mw.col.sched.counts(self.card))
        idx = self.mw.col.sched.countIdx(self.card)

    n, l, r = int(counts[0]), int(counts[1]), int(counts[2])
    config = mw.addonManager.getConfig(__name__) or {}
    show_over_limit = bool(config.get("Review_ Show Over Limit Counts", False))
    total_new, total_rev = _get_total_counts() if show_over_limit else (-1, -1)
    answered = _answered_today_count()

    extra_n = (total_new - n) if (total_new > 0 and total_new > n) else 0
    extra_r = (total_rev - r) if (total_rev > 0 and total_rev > r) else 0

    has_extra_new = extra_n > 0
    has_extra_rev = extra_r > 0

    n_label = f"({extra_n})" if has_extra_new and n == 0 else (f"<span dir='ltr'>({extra_n})&nbsp;{n}</span>" if has_extra_new else str(n))
    r_label = f"({extra_r})" if has_extra_rev and r == 0 else (f"<span dir='ltr'>({extra_r})&nbsp;{r}</span>" if has_extra_rev else str(r))

    new_weight = _new_card_today_weight(getattr(self, "card", None))
    # #365 / סבב 12 — מסווגים כל כרטיס learning פעם אחת בלבד.
    # שאילתת DB אחת מונעת find_cards/get_card בכל ציור ואת חלון "מעבד" בתחילת חזרה.
    pending_learning = 0
    due_learning = 0
    try:
        now_epoch = int(time.time())
        day_cutoff = int(mw.col.sched.day_cutoff)
        today = int(mw.col.sched.today)
        current_card = getattr(self, "card", None)
        current_card_id = int(getattr(current_card, "id", 0) or 0)
        current_deck = mw.col.decks.current()
        deck_ids = [int(did) for did in mw.col.decks.deck_and_child_ids(current_deck["id"])]
        placeholders = ",".join("?" for _ in deck_ids)
        sql = (
            f"SELECT id, queue, due FROM cards "
            f"WHERE queue IN (1, 3) AND "
            f"(did IN ({placeholders}) OR odid IN ({placeholders}))"
        )
        rows = mw.col.db.all(sql, *deck_ids, *deck_ids) if deck_ids else []
        seen = set()
        for cid, queue, due in rows:
            cid = int(cid)
            if cid in seen:
                continue
            seen.add(cid)
            queue = int(queue)
            due = int(due)
            if cid == current_card_id:
                due_learning += 1
            elif queue == 1:
                if due <= now_epoch:
                    due_learning += 1
                elif due < day_cutoff:
                    pending_learning += 1
            elif queue == 3 and due <= today:
                due_learning += 1
    except Exception as error:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/custom/bottom-bar/Bottom_Bar.py:_remaining_', 'מען קען נישט אפטיילן גרייטע לערן קארטלעך פון די וואס ווארטן. דער פארשריט סרגל ווייזט צייטווייליג אלע אלס גרייט.')
        logger.warning("bottom-bar #365 learning count fallback: %s", error)
        due_learning = max(0, l)
        pending_learning = 0

    labels = [n_label, str(due_learning), r_label]
    pending_label = str(pending_learning)
    if idx == 1 and due_learning == 0 and pending_learning > 0:
        pending_label = f"<u>{pending_label}</u>"
    else:
        labels[idx] = f"<u>{labels[idx]}</u>"

    # #365 — רוחב הכרטיסים החדשים כולל את מספר שלבי הלמידה הקצרים מיום
    # שעוד יכולים להתרחש לפני day_cutoff; אין עוד הכפלה קבועה ולא סופרים צעד
    # שזמנו חורג מסוף היום.
    # אנקי כבר כולל ב־l את כרטיסי הלמידה הממתינים. לאחר הפיצול כל כרטיס
    # נספר פעם אחת בלבד: באדום רציף או באדום מקווקו.
    total = max(1, answered + n * new_weight + due_learning + pending_learning + r)
    def pct_style(count, has_extra=False, weight=1):
        if count == 0:
            return "min-width:fit-content;max-width:fit-content;" if has_extra else ""
        return f"width:{count * weight * 100 / total}%;"
    # #167 — זה הסרגל שמעל "הצג תשובה": מקטע אפור לכרטיסים שכבר נענו, והוא לא מוצג כשהכמות 0.
    answered_html = ""
    if answered > 0:
        answered_html = (
            f'<div class="progress-bar answered-count" '
            f'style="width:{answered * 100 / total}%; background-color:#8f949b !important;">{answered}</div>'
        )
    new_s = pct_style(n, has_extra_new, new_weight)
    lrn_s = pct_style(due_learning)
    pending_lrn_s = pct_style(pending_learning)
    rev_s = pct_style(r, has_extra_rev)
    new_html = (
        f'<div class="progress-bar new-count" style="{new_s}">{labels[0]}</div>'
        if (n > 0 or has_extra_new) else ""
    )
    lrn_html = (
        f'<div class="progress-bar learn-count" style="{lrn_s}">{labels[1]}</div>'
        if due_learning > 0 else ""
    )
    pending_lrn_html = (
        f'<div class="progress-bar pending-learn-count" style="{pending_lrn_s}" '
        f'data-pending-tooltip="קארטלעך צום לערנען און איבערלערנען וואס ווארטן ביז עס קומט זייער חזרה צייט">'
        f'{pending_label}</div>' if pending_learning > 0 else ""
    )
    rev_html = (
        f'<div class="progress-bar review-count" style="{rev_s}">{labels[2]}</div>'
        if (r > 0 or has_extra_rev) else ""
    )
    return f"""
    <div class=remains style='cursor: pointer; z-index:2; padding-top:8px;' onclick='event.stopPropagation(); return pycmd("browse_review")' id="ad">
      <div class="counts-bar">
        {answered_html}{new_html}{lrn_html}{pending_lrn_html}{rev_html}
      </div>
    </div>
    <style>
       /* #365/#291 — דער געדיכטער קו און דינער ראם האלטן דעם נומער לייענבאר אויך אין העלן מצב. */
       .pending-learn-count {{
         /* #365/#291 — געדיכטער ווי די פריערדיגע ווערסיע: צוויי רויטע פיקסעלן און איין דורכזיכטיגער. */
         background:repeating-linear-gradient(135deg,#d93025 0 2px,transparent 2px 3px) !important;
         border:1px solid #d93025 !important; color:#fff !important;
        -webkit-text-stroke:0.35px #6d0d08; text-shadow:0 0 2px var(--canvas,#fff);
      }}
      .pending-learning-tooltip {{ position:fixed; z-index:99999; padding:6px 9px; border-radius:6px;
        background:var(--canvas-elevated,#303030); color:var(--fg,#fff); box-shadow:0 2px 8px #0005;
        font-size:12px; pointer-events:none; max-width:280px; text-align:right; direction:rtl; }}
    </style>
    <script>
      (() => {{
        const segment=document.querySelector('.pending-learn-count');
        if(!segment || segment.dataset.tooltipReady) return;
        segment.dataset.tooltipReady='1'; let timer,tip;
        const hide=()=>{{clearTimeout(timer); if(tip) tip.remove(); tip=null;}};
        segment.addEventListener('mouseenter',()=>{{timer=setTimeout(()=>{{
          tip=document.createElement('div'); tip.className='pending-learning-tooltip';
          tip.textContent=segment.dataset.pendingTooltip; document.body.appendChild(tip);
          const r=segment.getBoundingClientRect();
          tip.style.left=Math.max(8,r.left+r.width/2-tip.offsetWidth/2)+'px';
          tip.style.top=Math.max(8,r.top-tip.offsetHeight-8)+'px';
        }},2000);}});
        segment.addEventListener('mouseleave',hide);
      }})();
    </script>
"""

aqt.reviewer.Reviewer._remaining = wrap(aqt.reviewer.Reviewer._remaining, _remaining_)


def _refresh_remaining_bar_now() -> None:
    """Apply preference changes to an already-open review screen."""
    if mw.state != "review" or not getattr(mw, "reviewer", None):
        return
    with contextlib.suppress(Exception):
        html = _remaining_(mw.reviewer)
        mw.bottomWeb.eval(
            # #384 — IIFE prevents a second preferences change from redeclaring
            # the global `const old` and failing with a JavaScript SyntaxError.
            "(()=>{const old=document.querySelector('.remains');"
            f"if(old){{old.outerHTML={json.dumps(html)};}}}})();"
        )


def _add_over_limit_preference(self: aqt.preferences.Preferences) -> None:
    """#384 — the progress-bar preference belongs to bottom-bar itself."""
    current = mw.addonManager.getConfig(__name__) or {}
    checkbox = QCheckBox(
        'ווייז אויפן פארשריט סרגל אויך פראגעס איבער דער טעגליכער גרעניץ',
        mw,
    )
    checkbox.setChecked(bool(current.get('Review_ Show Over Limit Counts', False)))
    self.form.verticalLayout_5.addWidget(checkbox)

    def changed(state: int) -> None:
        updated = mw.addonManager.getConfig(__name__) or {}
        updated['Review_ Show Over Limit Counts'] = bool(state)
        mw.addonManager.writeConfig(__name__, updated)
        _reload_config()
        _refresh_remaining_bar_now()

    qconnect(checkbox.stateChanged, changed)
    self.form.progress_show_over_limit = checkbox


aqt.preferences.Preferences.setup_global = wrap(
    aqt.preferences.Preferences.setup_global,
    _add_over_limit_preference,
    "after",
)


# #353 — בשלוש הלחיצות הראשונות (אי פעם) על כפתור "קשה" מוצגת הודעה מעוצבת באמצע המסך,
# שדורשת לחיצה על "הבנתי" כדי להיסגר. מסבירה שקשה לא "שומר" על הכרטיס אלא רק מגדיל את
# המרווח בפחות מאשר שוב, ושהמנגנון לומד מהרגלי המשתמש. המונה נשמר בקונפיג כדי שההודעה לא
# תופיע יותר משלוש פעמים, ואפשר גם לבטל אותה לחלוטין דרך תיבת סימון בתוך ההודעה עצמה.
class _HardHintDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.dont_show_again = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        # #353 — כיוון RTL לכל הדיאלוג, כדי שגם הצ'קבוקס, הכפתור והטקסט ייושרו לימין.
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        from aqt.theme import theme_manager
        if theme_manager.night_mode:
            bg, fg, border, accent = "#2b2b2b", "#f0f0f0", "#5a5a5a", "#ffb74d"
        else:
            bg, fg, border, accent = "#fffdf5", "#333333", "#e0c96e", "#bf720f"

        card = QWidget(self)
        card.setObjectName("card")
        card.setStyleSheet(f"""
            #card {{
                background: {bg};
                border: 1.5px solid {border};
                border-radius: 16px;
            }}
            QLabel {{ color: {fg}; }}
        """)

        # #353 — צביעת שמות הכפתורים עצמם (לא כל מופע של "קשה" כתואר) לזיהוי חזותי מהיר.
        hard_btn = '<b style="color:#2e7d32;">שווער</b>'
        good_btn = '<b style="color:#4caf50;">גוט</b>'
        again_btn = '<b style="color:#c62828;">נאכאמאל</b>'

        # #353 — מנוע ה-rich-text של Qt לא מכבד text-align ב-CSS על div; משתמשים במאפיין
        # align של תגית p, שהוא הדרך הנתמכת ליישור בלוקים ב-QLabel.
        title = QLabel(
            f'<p align="right" dir="rtl">'
            f'<span style="font-size:22px;">💡</span> '
            f'<b style="font-size:17px; color:{accent};">א מינוט פארן ווייטערגיין...</b>'
            f'</p>'
        )
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setAlignment(Qt.AlignmentFlag.AlignRight)

        body = QLabel(
            '<p align="right" dir="rtl">'
            f"אויב איר האט נישט געדענקט די ענטפער — א דרוק אויף {hard_btn} אנשטאט {again_btn} שאדט אייער געדענקען דעם חומר.<br><br>"

            f"{hard_btn}, פונקט ווי {good_btn}, <b>פארגרעסערט</b> דעם מרווח ביז דער קומענדיגער חזרה — נאר ווייניגער. "
            f"צום ביישפיל: אויב דער פריערדיגער מרווח איז געווען א חודש, {hard_btn} וועט אים פארגרעסערן צו א חודש מיט א וואך. "
            "אויב איר האט נישט געדענקט ביים קורצן מרווח, איז נישט דא קיין סיבה אז א לענגערער מרווח זאל אייך העלפן געדענקען — "
            "דער קארטל וועט פשוט צוריקקומען נאכאמאל פארגעסן, נאך אן איבעריגע לאנגע ווארט.<br><br>"

            f"{again_btn}, שטעלט אבער נישט דעם קארטל צוריק ווי א נייע קארטל — עס גיט נאר א פאר קורצע חזרות "
            "וואס פרישן טאקע אויף דעם זכרון, און נאכדעם גייט דער קארטל צוריק צום געווענליכן צייטפלאן.<br><br>"

            f"{hard_btn} איז נאר פאר ווען איר האט זיך דערמאנט אין דער ריכטיגער ענטפער, אבער עס האט געדויערט אדער איר זענט נישט געווען זיכער.<br><br> "

            "דערצו שטערט דער געוואוינהייט דעם נייעם צייטפלאן מאטאר: ער דארף זיך לערנען פון אייערע חזרות "
            f"ווען עס איז אייך טאקע שווער צו געדענקען, אבער ווען מען דריקט {hard_btn} אנשטאט {again_btn} ער \"מיינט\" אז איר האט געוואוסט — "
            "און דער קאמפיוטער קען נישט אליין וויסן אז דאס איז נישט ריכטיג.<br><br>"

            f"אויב אפילו מיטן נוצן פון{again_btn} איז א קארטל שווער צו געדענקען, "
            "זאלט איר אים איבערארבעטן אז עס זאל זיין גרינגער צו געדענקען, אדער טרעפן אן אנדערן וועג אים צו געדענקען."
            '</p>'
        )
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignmentFlag.AlignRight)
        body.setStyleSheet("font-size: 14px; line-height: 1.6;")

        # #353 — הבעיה במסכים קטנים הייתה לאורך (גובה), לא לרוחב: הדיאלוג חסר גובה
        # קבוע/מקסימלי, כך שהטקסט הארוך דחף אותו לגובה שחורג מגובה המסך הזמין.
        # עוטפים את הטקסט בגלילה, אבל הגובה המקסימלי שלה הוא כל השטח הפנוי במסך
        # (פחות מקום קבוע לכותרת/תיבת סימון/כפתור ומרווח קטן מלמעלה ולמטה) — כדי
        # שהגלילה תופיע רק כשבאמת אין ברירה, לא סתם כי קבענו אחוז שרירותי קטן מדי.
        body_scroll = QScrollArea()
        body_scroll.setWidget(body)
        body_scroll.setWidgetResizable(True)
        body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        body_scroll.setStyleSheet("background: transparent;")
        body_scroll.viewport().setStyleSheet("background: transparent;")
        # #353 — עדיפות ל-screen של mw עצמו (parent) ולא של הדיאלוג עצמו: הדיאלוג עדיין
        # לא מוצג בשלב הזה ועלול להחזיר מסך ברירת מחדל/שגוי דרך self.screen().
        # ויתרנו על החיתוך מול mw.frameGeometry(): בפועל הוא צימצם את השטח הרבה מעבר
        # למצופה (כאילו חלון אנקי עצמו קטן בהרבה מהמסך, גם כשהוא ממוקסם) — סימן
        # שהוא לא שיקף אמינה את השטח האמיתי הזמין. נשארים עם availableGeometry של
        # המסך בלבד (כבר מוציא את שורת המשימות מעצמו), עם מרווח מינימלי.
        screen = (parent.screen() if parent is not None else None) or self.screen()
        screen_avail = screen.availableGeometry() if screen else None
        available_h = screen_avail.height() if screen_avail else 800
        # שטח שמור לשאר רכיבי הדיאלוג (כותרת, תיבת סימון, כפתור, מרווחים ושוליים)
        # ולמרווח נשימה קטן מקצה המסך מלמעלה ומלמטה — צומצם למינימום כדי לשאוף ל-0 גלילה.
        # הערך כולל: כותרת (~35), צ'קבוקס (~25), כפתור (~35), spacing+margins של הכרטיס
        # (~45), ומרווח נשימה מהמסך (~20).
        reserved_for_chrome_and_screen_margin = 160
        self._body_scroll = body_scroll
        self._body_label = body
        self._body_allowed_max = max(200, available_h - reserved_for_chrome_and_screen_margin)
        self._bounds_rect = screen_avail

        dont_show_checkbox = QCheckBox("דערמאן מיך מער נישט דעראן")
        dont_show_checkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        def _on_toggled(checked: bool) -> None:
            self.dont_show_again = checked

        dont_show_checkbox.toggled.connect(_on_toggled)

        ok_button = QPushButton("איך האב פארשטאנען")
        ok_button.setDefault(True)
        ok_button.setFixedWidth(120)
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background: {accent}; color: white; border: none;
                border-radius: 8px; padding: 8px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background: {border}; }}
        """)
        ok_button.clicked.connect(self.accept)

        card_layout = QVBoxLayout(card)
        # #353 — מרווחים אנכיים צומצמו (20->12) כדי לפנות עוד קצת שטח לטקסט ולהקטין
        # את הסיכוי לגלילה מיותרת.
        card_layout.setContentsMargins(24, 12, 24, 12)
        card_layout.setSpacing(10)
        card_layout.addWidget(title)
        card_layout.addWidget(body_scroll)
        card_layout.addWidget(dont_show_checkbox, alignment=Qt.AlignmentFlag.AlignRight)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(ok_button)
        card_layout.addLayout(button_row)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(card)
        # #353 — רוחב קבוע 420px זלג מעבר לגבולות המסך בחלונות/מסכים קטנים מ-420px.
        # הרוחב מוגבל כעת לחלון ההורה (עם שוליים), ולעולם לא יעלה על 420px.
        body.setWordWrap(True)
        max_w = 420
        with contextlib.suppress(Exception):
            parent_w = parent.width() if parent is not None else 0
            if parent_w:
                max_w = max(260, min(420, parent_w - 40))
        self.setFixedWidth(max_w)

        # #353 — הליבה של התיקון: setMaximumHeight על QScrollArea לא גורם לו לגדול —
        # ל-QScrollArea יש sizeHint צנוע משלו, ושם הדיאלוג נתקע (זו הסיבה שהופיעה
        # גלילה גם במסך גדול, ושכל שינויי התקרה הקודמים "לא שינו כלום"). קובעים לו
        # גובה *בפועל*: גובה הטקסט המלא ברוחב הנתון (heightForWidth — תלוי גלישת
        # שורות), חסום בתקרה של שטח המסך. גלילה תופיע רק אם הטקסט באמת גבוה מהמסך.
        inner_w = max_w - 48 - 16  # שולי הכרטיס (24+24) + רזרבה לפס גלילה אנכי
        content_h = self._body_label.heightForWidth(inner_w)
        if content_h <= 0:
            content_h = self._body_label.sizeHint().height()
        self._body_scroll.setFixedHeight(min(content_h + 8, self._body_allowed_max))

    def showEvent(self, evt) -> None:
        # #353 — Qt ממקם דיאלוגים ללא מיקום מפורש במרכז ה-parent כברירת מחדל, אבל זה
        # לא מבטיח שהם נשארים בתוך גבולות המסך/חלון אנקי אם הדיאלוג גדול יחסית אליהם.
        # אחרי שהגודל הסופי כבר ידוע (בשלב ההצגה), מציבים אותו מחדש בתוך התחום שחושב
        # למעלה (self._bounds_rect — חיתוך של שטח המסך הזמין וגבולות חלון אנקי) אם חורג.
        super().showEvent(evt)
        bounds = getattr(self, "_bounds_rect", None)
        if bounds is None or not bounds.isValid():
            return
        geo = self.geometry()
        x = min(max(geo.x(), bounds.x()), bounds.x() + bounds.width() - geo.width())
        y = min(max(geo.y(), bounds.y()), bounds.y() + bounds.height() - geo.height())
        if (x, y) != (geo.x(), geo.y()):
            self.move(x, y)


def _hard_button_hint(reviewer, card, ease) -> None:
    if ease != 2:
        return
    conf = mw.addonManager.getConfig(__name__) or {}
    if not conf.get("Hard Hint_ Enabled", True):
        return
    shown = int(conf.get("Hard Hint_ Times Shown", 0) or 0)
    max_times = int(conf.get("Hard Hint_ Max Times", 3) or 0)
    if shown >= max_times:
        return
    conf["Hard Hint_ Times Shown"] = shown + 1
    mw.addonManager.writeConfig(__name__, conf)

    dialog = _HardHintDialog(mw)
    dialog.exec()
    if dialog.dont_show_again:
        conf = mw.addonManager.getConfig(__name__) or {}
        conf["Hard Hint_ Enabled"] = False
        mw.addonManager.writeConfig(__name__, conf)


gui_hooks.reviewer_did_answer_card.append(_hard_button_hint)
