import html
import time

import aqt.main
from anki.decks import DeckCollapseScope, DeckId, DeckTreeNode
from anki.hooks import wrap
from anki.utils import pointVersion
from aqt import gui_hooks
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar, RenderDeckNodeContext
from aqt.operations.deck import add_deck_dialog, reparent_decks, set_current_deck
from aqt.utils import *
from PyQt6.QtGui import QActionGroup
from PyQt6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QSpinBox

from _shared_libs.gimatria_sort import gimatria_sort_key
from _shared_libs.haf_logging import get_logger
from _shared_libs.haf_notifications import show_failure

from .config import *
from .html_s import *
from .sql_querys import *
from .utils import *

logger = get_logger("modern_theme")

DECK_NAME_TODAY = "%^$$מבחן_היום_או_באיחור$$^%"

addon = mw.addonManager.addonFromModule(__name__)
base = "/_addons/" + addon
def last_overdue_alert():
    return get_config()["last_overdue_alert"]
def alert_overdue():
    return get_config()["alert_overdue"]
in_search = False
search_str = ""
search_len = 0

current_epoch = 0
start_of_anki_epoche_day = 0
next_anki_day_start = 0
days_from_crt = 0

FORECAST_CALC_DAYS = 14    # כמה ימים קדימה לחשב ממוצע ולשלוף נתונים
FORECAST_DISPLAY_DAYS = 7  # כמה ימים קדימה להציג בהתראה
# #183 — cache קטן לממוצע revlog מונע סריקה חוזרת של כל ההיסטוריה בכל רינדור של המסך הראשי.
_revlog_avg_time_cache: tuple[tuple[int, int, int], float] | None = None

# #128 — מחרוזות החיפוש של הסטטיסטיקות הגדולות הן מקור האמת גם לספירה וגם ללחיצה.
STATS_FILTER_TODAY = "(prop:due=0 or (is:learn is:due)) -is:suspended -is:buried"
# #330 — הוספת -is:learn כדי להוציא כרטיסי relearn (type=3,queue=1) שכבר נספרים ב"להיום" דרך is:learn is:due
STATS_FILTER_OVERDUE = "is:review is:due -prop:due=0 -is:learn -is:suspended -is:buried"
STATS_FILTER_NEW = "is:new -is:suspended -is:buried"
# #330 — is:learn (בלי is:due) כדי לכלול כרטיסי למידה בהשהיית צעד (למשל 10 דק') בסך הכל.
#         הוסר rated:1 (#326) כי כרטיס review שנענה יוצא מ-is:due אוטומטית; ה-rated גרם לפער מול TODAY+OVERDUE.
STATS_FILTER_ALL_DUE = "(is:due or is:learn) -is:suspended -is:buried"
STATS_FILTER_ALL_DUE_WITH_NEW = "(is:due or is:learn or is:new) -is:suspended -is:buried"
FILTER_ORDER_OPTIONS = [
    (0, "די עלטסטע"),
    (1, "צופעליג"),
    (2, "לויט וואקסנדיגע צייט מרווחים"),
    (3, "לויט קלענער ווערנדיגע צייט מרווחים"),
    (4, "די מערסטע טעותים"),
    (5, "צולייג סדר"),
    (6, "געפלאנטער דאטום"),
    (7, "לעצטנס צוגעלייגט"),
    (8, "לויט וואקסנדיגער מעגליכקייט צו דערמאנען"),
    (9, "לויט קלענער ווערנדיגער מעגליכקייט צו דערמאנען"),
]

all_decks_stats: {int: dict} = {}
sub_decks_html = {}
# #396 — מטמון זמני לסכום learning עתידי של חפיסה ותתי-החפיסות שלה.
_pending_learning_render_cache: dict[int, int] = {}


# #128 — הסטטיסטיקות הגדולות נספרות דרך אותם חיפושים שהקליקים שלהן מפעילים, בכל המאגר וללא מגבלות יומיות של עץ החפיסות.
def _stats_filter_count(filter_string: str, fallback: int = 0) -> int:
    try:
        return retlen(filter_string)
    except Exception as e:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/custom/modern-theme/deck_browser.py:_stats_filter_count', 'דאס ציילן די סטאטיסטיק איז נישט געלונגען. די נומערן אויפן הויפט עקראן זענען נישט פארלעסליך ביז א ריכטיגן אויפפריש.')
        logger.error(f"modern-theme #128 stats count failed for {filter_string!r}: {e}")
        return fallback


def _stats_all_due_filter(include_new: bool) -> str:
    return STATS_FILTER_ALL_DUE_WITH_NEW if include_new else STATS_FILTER_ALL_DUE


def _answer_time_clauses() -> tuple[list[str], list[int], int]:
    # #183 — אותו סינון maxTaken משמש גם לזמן היום וגם לממוצע revlog כדי לא לספור זמני מענה חריגים.
    try:
        max_taken = int(mw.col.conf.get("maxTaken") or 0)
    except Exception:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/custom/modern-theme/deck_browser.py:_answer_time_clauses', 'מען קען נישט לייענען די ענטפער צייט גרעניץ. די געוויזענע לערן צייטן און שאצונג קענען זיין אומריכטיג.')
        max_taken = 0

    clauses = ["time > 0", "type != 4"]
    params = []
    if max_taken > 0:
        clauses.append("time < ?")
        params.append(max_taken * 1000)
    return clauses, params, max_taken


# #183 — הפרוגרס בר ו"זמן לימוד" נשארים מבוססי החזרות שנעשו היום בלבד.
def _today_answer_time_stats() -> tuple[int, int]:
    clauses, params, _max_taken = _answer_time_clauses()
    today_clause = f"id >= {start_of_anki_epoche_day}000"
    time_clauses = [today_clause, *clauses]
    # #330 — ספירת חזרות בלי סינון; כל רשומת revlog מהיום נספרת (כולל תזמונים ידניים type=4).
    count_clauses = [today_clause]

    try:
        time_row = mw.col.db.first(
            "SELECT coalesce(sum(time), 0) FROM revlog WHERE "
            + " AND ".join(time_clauses),
            *params,
        ) or (0,)
        count_row = mw.col.db.first(
            "SELECT count(id) FROM revlog WHERE "
            + " AND ".join(count_clauses),
        ) or (0,)
        return int(time_row[0] or 0), int(count_row[0] or 0)
    except Exception as e:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/custom/modern-theme/deck_browser.py:_today_answer_time_stats', 'דאס אויסרעכענען די צייט און חזרות פאר היינט איז נישט געלונגען. די געוויזענע נולן מיינען נישט אז איר האט היינט נישט געלערנט.')
        logger.error(f"modern-theme #183 today answer time stats failed: {e}")
        return 0, 0


# #183 — רק צפי הזמן משתמש בממוצע כל ה-revlog, וגם הוא מחושב מחדש רק כשה-revlog השתנה.
def _revlog_average_time_ms() -> float:
    global _revlog_avg_time_cache
    clauses, params, max_taken = _answer_time_clauses()
    where_sql = " AND ".join(clauses)
    try:
        sig_row = mw.col.db.first(
            "SELECT count(id), coalesce(max(id), 0) FROM revlog WHERE " + where_sql,
            *params,
        ) or (0, 0)
        signature = (int(sig_row[0] or 0), int(sig_row[1] or 0), max_taken)
        if _revlog_avg_time_cache and _revlog_avg_time_cache[0] == signature:
            return _revlog_avg_time_cache[1]
        avg_row = mw.col.db.first(
            "SELECT coalesce(avg(time), 0) FROM revlog WHERE " + where_sql,
            *params,
        ) or (0,)
        avg_time = float(avg_row[0] or 0) or 12000
        _revlog_avg_time_cache = (signature, avg_time)
        return avg_time
    except Exception as e:
        from _shared_libs.haf_notifications import warn_once
        warn_once('addons/custom/modern-theme/deck_browser.py:_revlog_average_time_ms', 'דאס אויסרעכענען די דורכשניטליכע ענטפער צייט איז נישט געלונגען. די לערן שאצונג איז צייטווייליג באזירט אויף 12 סעקונדעס פאר א חזרה, אנשטאט אייער געשיכטע.')
        logger.error(f"modern-theme #183 revlog average time failed: {e}")
        return 12000

# ── Tutorial ──────────────────────────────────────────────────────────────────
_tut_step: int = 0
# 0=כבוי 1=צור-חפיסה 2=הוסף-שאלה(row) 3=AddCards-window 4=לחץ-ללמוד(row)
# 5=הצג-תשובה(reviewer) 6=כפתורי-תשובה(reviewer) 7=סיור-נאובר
_tut_did:  int = 0   # DID של החפיסה שנוצרה
_tut_nav_idx: int = 0  # אינדקס נוכחי בסיור הנאובר

_TUT_STYLE = """<style id="tut-style">
@keyframes tut-glow {
  0%,100%{box-shadow:0 0 0 0 rgba(39,174,96,0),0 0 6px 1px rgba(39,174,96,.4);}
  50%    {box-shadow:0 0 0 5px rgba(39,174,96,.35),0 0 18px 3px rgba(39,174,96,.65);}
}
#tut-frame{
  position:fixed;border:3px solid #27ae60;border-radius:9px;
  z-index:9998;pointer-events:none;animation:tut-glow 1.4s ease-in-out infinite;
}
#tut-tip{
  position:fixed;z-index:99999;pointer-events:none;
  background:#1a1a2e;color:#fff;border-radius:14px;
  padding:12px 22px;font-size:15px;font-family:SecularOne-Regular,sans-serif;
  direction:rtl;text-align:center;
  box-shadow:0 6px 28px rgba(0,0,0,.75);max-width:300px;line-height:1.7;
}
#tut-skip{
  position:fixed;bottom:22px;left:50%;transform:translateX(-50%);
  z-index:99999;cursor:pointer;pointer-events:auto;
  background:rgba(255,255,255,.13);color:#eee;
  border:1px solid rgba(255,255,255,.25);border-radius:20px;
  padding:7px 22px;font-size:13px;font-family:SecularOne-Regular,sans-serif;
}
</style>"""


def _tut_sel_msg():
    if _tut_step == 1:
        return "#btn-add-deck", "דריקט אויף <b>שאף א פעקל</b><br>כדי צו שאפן א לערן נושא"
    if _tut_step == 2:
        sel = (f"div.deck[data-deck-id='{_tut_did}'] .deck-buttons-col"
               if _tut_did else ".deck-buttons-col")
        return sel, "&#127881; זייער גוט!<br>דריקט אויף <b>&#128221; לייג צו א פראגע</b><br>אין דער פעקל שורה &#9658;"
    if _tut_step == 4:
        sel = (f"div.deck[data-deck-id='{_tut_did}'] .accordion-button"
               if _tut_did else "div.deck .accordion-button")
        return sel, "&#127891; אויסגעצייכנט!<br>דריקט אויף <b>דעם פעקל נאמען</b><br>כדי אנהייבן צו לערנען &#9660;"
    return None


def _tut_spotlight_js() -> str:
    """ברענגט צוריק JS ריין (אן א טאג script) פארן אויסלייכטן."""
    info = _tut_sel_msg()
    if not info:
        return ""
    sel, msg = info
    return f"""(function(){{
  function go(){{
  var sel="{sel}", PAD=16;
  ['tut-b0','tut-b1','tut-b2','tut-b3','tut-frame','tut-tip','tut-skip']
    .forEach(function(id){{var e=document.getElementById(id);if(e)e.remove();}});
  var el=document.querySelector(sel);
  if(!el){{setTimeout(go,200);return;}}
  var r0=el.getBoundingClientRect();
  if(r0.width===0&&r0.height===0){{setTimeout(go,200);return;}}
  var fr=document.createElement('div');fr.id='tut-frame';document.body.appendChild(fr);
  var tip=document.createElement('div');tip.id='tut-tip';
  tip.innerHTML={repr(msg)};document.body.appendChild(tip);
  var sk=document.createElement('button');sk.id='tut-skip';
  sk.textContent='\u2715  \u05d3\u05dc\u05d2 \u05e2\u05dc \u05d4\u05de\u05d3\u05e8\u05d9\u05da';
  sk.onclick=function(){{pycmd('tut_close');}};document.body.appendChild(sk);
  var bars=[];
  for(var i=0;i<4;i++){{
    var b=document.createElement('div');b.id='tut-b'+i;
    b.style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);';
    document.body.appendChild(b);bars.push(b);
  }}
  function update(){{
    var r=el.getBoundingClientRect();
    var W=window.innerWidth,H=window.innerHeight;
    var x1=Math.max(0,r.left-PAD),y1=Math.max(0,r.top-PAD);
    var x2=Math.min(W,r.right+PAD),y2=Math.min(H,r.bottom+PAD);
    bars[0].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:0;left:0;right:0;height:'+y1+'px';
    bars[1].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:'+y2+'px;left:0;right:0;bottom:0';
    bars[2].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:'+y1+'px;height:'+(y2-y1)+'px;left:0;width:'+x1+'px';
    bars[3].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:'+y1+'px;height:'+(y2-y1)+'px;left:'+x2+'px;right:0';
    fr.style.top=y1+'px';fr.style.left=x1+'px';
    fr.style.width=(x2-x1)+'px';fr.style.height=(y2-y1)+'px';
    var tr=tip.getBoundingClientRect();
    var ty=r.bottom+18;
    if(ty+tr.height>H-12)ty=r.top-tr.height-18;
    tip.style.top=Math.max(6,ty)+'px';
    tip.style.left=Math.max(6,r.left+r.width/2-tr.width/2)+'px';
  }}
  update();
  window.addEventListener('resize',update);
  window.addEventListener('scroll',update,true);
  }}
  setTimeout(go,150);
}})();"""


def _tut_make_script() -> str:
    js = _tut_spotlight_js()
    if not js:
        return ""
    return f'<script id="tut-script">{js}</script>'



def _tut_clear_web(web):
    web.eval("""
['tut-b0','tut-b1','tut-b2','tut-b3','tut-frame','tut-tip','tut-skip','tut-style','tut-script','tut-nav-next']
  .forEach(function(id){var e=document.getElementById(id);if(e)e.remove();});
""")


def _tut_clear_qt():
    try:
        from aqt import dialogs
        from PyQt6.QtWidgets import QLabel, QPushButton
        pair = dialogs._dialogs.get("AddCards")
        if pair and pair[1]:
            win = pair[1]
            for btn in win.findChildren(QPushButton):
                if btn.property("tut_hl"):
                    btn.setStyleSheet("")
                    btn.setProperty("tut_hl", False)
            for lbl in win.findChildren(QLabel):
                if lbl.property("tut_lbl"):
                    lbl.deleteLater()
    except Exception:
        pass


def _tut_setup_add_cards(add_cards_win=None):
    """לייגט צו banner און צייכנט אויס דעם צולייג קנעפל אינעם פראגע צולייג פענסטער - Qt."""
    if _tut_step != 3:
        return
    try:
        from aqt import dialogs, mw
        from PyQt6.QtWidgets import QPushButton, QLabel, QVBoxLayout
        from PyQt6.QtCore import Qt, QObject, QEvent, QTimer

        if add_cards_win is not None:
            win = add_cards_win
        else:
            pair = dialogs._dialogs.get("AddCards")
            if not (pair and pair[1]):
                return
            win = pair[1]

        cw = getattr(win, 'centralWidget', lambda: None)()
        if cw:
            pass

        # avoid double-setup if both hook and timer fire
        for existing in win.findChildren(QLabel):
            if existing.property("tut_lbl"):
                return

        # banner instruction at top
        lbl = QLabel("✏️  שרייבט <b>פראגע</b> ו<b>ענטפער</b>, דריקט דערנאך <b>לייג צו</b>")
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setProperty("tut_lbl", True)
        lbl.setStyleSheet(
            "background:#1a1a2e;color:#fff;border-radius:8px;"
            "padding:8px 14px;font-size:14px;margin:4px 2px;direction:rtl;"
        )
        # QMainWindow.layout() returns internal QMainWindowLayout — useless.
        # Always prefer centralWidget().layout() for QMainWindow subclasses.
        _layout = None
        if cw and cw.layout():
            _layout = cw.layout()
        elif win.layout():
            _layout = win.layout()

        if _layout:
            _layout.insertWidget(0, lbl)
        else:
            # fallback: set banner as a child and show manually at the top
            lbl.setParent(win)
            lbl.setGeometry(10, 5, win.width() - 20, 40)
            lbl.show()

        # highlight Add button
        found_btn = False
        for btn in win.findChildren(QPushButton):
            txt = btn.text().replace("&", "")
            if txt in ("Add", "לייג צו", "Add Cards", "לייג צו\u200e"):
                btn.setStyleSheet(
                    "QPushButton{border:3px solid #27ae60;border-radius:8px;"
                    "background:#e8f8f0;color:#1a5c35;font-weight:bold;padding:4px 14px;}"
                    "QPushButton:hover{background:#c5f0d8;}"
                )
                btn.setProperty("tut_hl", True)
                found_btn = True
                break
        if not found_btn:
            pass

        # event filter: כשסוגרים את החלון ו-_tut_step==4, רענן את מסך הבית
        class _TutCloseFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.Close and _tut_step == 4:
                    QTimer.singleShot(120, mw.deckBrowser.show)
                return False

        flt = _TutCloseFilter(win)
        win.installEventFilter(flt)

        # tooltip בפתיחת החלון
        from aqt.utils import tooltip
        tooltip(
            "<div style='direction:rtl;text-align:center;font-size:15px;line-height:1.8;'>"
            "✏️ <b>שרייבט א פראגע און אן ענטפער</b><br>"
            "און דריקט דערנאך אויפן קנעפל <b>לייג צו</b>."
            "</div>",
            period=5000,
        )
    except Exception:
        pass



def _tut_auto_review():
    global _tut_step, _tut_did
    if _tut_step != 4:
        return
    try:
        from aqt import mw
        # הדף נטען — מריץ שוב את הספוטלייט דרך eval (layout כבר סגור)
        js = _tut_spotlight_js()
        if js:
            css = _TUT_STYLE.split(">", 1)[1].rsplit("</style>", 1)[0]
            inject = (
                f"(function(){{"
                f"var s=document.getElementById('tut-style');"
                f"if(!s){{s=document.createElement('style');s.id='tut-style';document.head.appendChild(s);}}"
                f"s.textContent={repr(css)};"
                f"}})();"
            )
            mw.deckBrowser.web.eval(inject)
            mw.deckBrowser.web.eval(js)
    except Exception as e:
        pass


def _tut_on_show_question(card):
    """Step 5: לאז בלינקען דעם 'ווייז די ענטפער' קנעפל איןreviewer."""
    global _tut_step
    if _tut_step == 4:
        _tut_step = 5
        _tut_clear_web(mw.deckBrowser.web)
    if _tut_step != 5:
        return
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(300, _tut_inject_show_answer)


def _tut_inject_show_answer():
    if _tut_step != 5:
        return
    # Button glow in bottom bar
    btn_js = """
(function(){
  var style = document.getElementById('tut-rev-style');
  if (!style) { style = document.createElement('style'); style.id = 'tut-rev-style'; document.head.appendChild(style); }
  style.textContent = `
    @keyframes tut-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(39,174,96,0);} 50%{box-shadow:0 0 0 8px rgba(39,174,96,.5);} }
    #ansbut { animation: tut-pulse 1.4s ease-in-out infinite !important; border: 2px solid #27ae60 !important; border-radius: 8px !important; }
  `;
})();
"""
    # Tooltip in main reviewer web (no height clip)
    tip_js = """
(function(){
  var style = document.getElementById('tut-rev-tip-style');
  if (!style) { style = document.createElement('style'); style.id = 'tut-rev-tip-style'; document.head.appendChild(style); }
  style.textContent = `
    #tut-rev-tip { position:fixed; bottom:18px; left:50%; transform:translateX(-50%); z-index:99999;
      background:#1a1a2e; color:#fff; border-radius:14px; padding:12px 22px; font-size:15px;
      font-family:SecularOne-Regular,sans-serif; direction:rtl; text-align:center;
      box-shadow:0 6px 28px rgba(0,0,0,.75); max-width:320px; line-height:1.7; pointer-events:none; }
  `;
  var tip = document.getElementById('tut-rev-tip');
  if (!tip) { tip = document.createElement('div'); tip.id = 'tut-rev-tip'; document.body.appendChild(tip); }
  tip.innerHTML = '&#128270; <b>\u05e7\u05e8\u05d0 \u05d0\u05ea \u05d4\u05e9\u05d0\u05dc\u05d4</b><br>\u05d5\u05dc\u05d7\u05e5 \u05e2\u05dc <b>\u05d4\u05e6\u05d2 \u05ea\u05e9\u05d5\u05d1\u05d4</b>';
})();
"""
    try:
        mw.reviewer.bottom.web.eval(btn_js)
        mw.reviewer.web.eval(tip_js)
    except Exception:
        pass


def _tut_on_show_answer(card):
    """Step 6: לאז בלינקען די ענטפער קנעפלעך מיט א ווארענונג."""
    global _tut_step
    if _tut_step != 5:
        return
    _tut_step = 6
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(300, _tut_inject_answer_buttons)


def _tut_inject_answer_buttons():
    if _tut_step != 6:
        return
    # Button styling in bottom bar
    btn_js = """
(function(){
  var style = document.getElementById('tut-rev-style');
  if (!style) { style = document.createElement('style'); style.id = 'tut-rev-style'; document.head.appendChild(style); }
  style.textContent = `
    @keyframes tut-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(39,174,96,0);} 50%{box-shadow:0 0 0 8px rgba(39,174,96,.5);} }
    button[data-ease] { animation: tut-pulse 1.4s ease-in-out infinite !important; border-radius: 8px !important; }
    button[data-ease="1"] { border: 2px solid #e74c3c !important; }
    button[data-ease="2"] { border: 2px solid #f39c12 !important; }
    button[data-ease="3"] { border: 2px solid #27ae60 !important; box-shadow: 0 0 12px rgba(39,174,96,.6) !important; }
    button[data-ease="4"] { border: 2px solid #3498db !important; }
  `;
})();
"""
    # Tooltip in main reviewer web
    tip_js = """
(function(){
  var style = document.getElementById('tut-rev-tip-style');
  if (!style) { style = document.createElement('style'); style.id = 'tut-rev-tip-style'; document.head.appendChild(style); }
  style.textContent = `
    #tut-rev-tip { position:fixed; bottom:18px; left:50%; transform:translateX(-50%); z-index:99999;
      background:#1a1a2e; color:#fff; border-radius:14px; padding:12px 22px; font-size:15px;
      font-family:SecularOne-Regular,sans-serif; direction:rtl; text-align:center;
      box-shadow:0 6px 28px rgba(0,0,0,.75); max-width:380px; line-height:1.7; pointer-events:none; }
  `;
  var el = document.getElementById('tut-rev-tip');
  if (!el) { el = document.createElement('div'); el.id = 'tut-rev-tip'; document.body.appendChild(el); }
  el.innerHTML = '&#128161; <b>\u05d0\u05dd \u05dc\u05d0 \u05d9\u05d3\u05e2\u05ea</b> \u05d0\u05ea \u05d4\u05ea\u05e9\u05d5\u05d1\u05d4 \u2014 \u05dc\u05d7\u05e5 \u05e2\u05dc <b style="color:#e74c3c">\u05e9\u05d5\u05d1</b>.<br>\u05d0\u05dd \u05d9\u05d3\u05e2\u05ea \u2014 \u05dc\u05d7\u05e5 \u05e2\u05dc <b style="color:#27ae60">\u05d8\u05d5\u05d1</b>.<br>&#128197; <span style="font-size: 13px;">\u05de\u05e2\u05dc \u05d4\u05db\u05e4\u05ea\u05d5\u05e8\u05d9\u05dd \u05de\u05d5\u05e4\u05d9\u05e2 \u05ea\u05d0\u05e8\u05d9\u05da \u05d4\u05d7\u05d6\u05e8\u05d4 \u05d4\u05d1\u05d0\u05d4, \u05d5\u05db\u05db\u05dc \u05e9\u05ea\u05d3\u05e2 \u05d9\u05d5\u05ea\u05e8 \u05d8\u05d5\u05d1 \u05d4\u05e4\u05e2\u05e8 \u05d4\u05d5\u05dc\u05da \u05d5\u05d2\u05d3\u05dc.</span>';
})();
"""
    try:
        mw.reviewer.bottom.web.eval(btn_js)
        mw.reviewer.web.eval(tip_js)
    except Exception:
        pass


def _tut_on_answer_card(reviewer, card, ease):
    """נאכן ענטפערן → איבערגיין צום אויבערשטן סרגל טור."""
    global _tut_step, _tut_did, _tut_nav_idx
    if _tut_step != 6:
        return
    # נקה reviewer
    try:
        mw.reviewer.bottom.web.eval("var s=document.getElementById('tut-rev-style'); if(s)s.remove();")
        mw.reviewer.web.eval("""
          var s=document.getElementById('tut-rev-tip-style'); if(s)s.remove();
          var t=document.getElementById('tut-rev-tip'); if(t)t.remove();
        """)
    except Exception:
        pass
    _tut_step = 7
    _tut_nav_idx = 0
    from aqt.utils import tooltip
    tooltip(
        "<div style='direction:rtl;text-align:center;font-size:15px;line-height:1.9;'>"
        "✨ <b>זייער פיין!</b><br>יעצט לאמיר זיך באקענען מיטן אויבערשטן סרגל."
        "</div>",
        period=3500,
    )
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(400, lambda: mw.moveToState("deckBrowser"))


# ── Navbar Tour (step 7) ──────────────────────────────────────────────────────
_NAV_ITEMS = [
    ("#btn-add-deck", "📚 וואס איז א פעקל?", "פעקל = לערן נושא.<br>שאפט א באזונדערן פעקל פאר יעדן נושא (גמרא, משניות, הלכה...)."),
    ("div.deck", "📅 ווי לערנט מען למעשה?", "עפנט יעדן טאג דעם פראגראם און דריקט אויפן פעקל נאמען,<br>אנקי וועט ווייזן נאר וואס איז שוין צייט צו לערנען."),
    ("[data-tt='nav-menu']", "מעניו", "דא געפינען זיך אלע איינשטעלונגען:<br><b>טעקע</b>, <b>רעדאקטירן</b>, <b>כלים</b> און נאך."),
    ("[data-tt='nav-home']", "הויפט עקראן", "צוריק צום הויפט עקראן<br>מיט אלע פעקלעך און סטאטיסטיק."),
    ("[data-tt='nav-browse']", "בלעטערט דורך קארטלעך", "זוכט, רעדאקטירט און פירט אלע<br>אייערע פראגעס און ענטפערס."),
    ("[data-tt='nav-filter']", "פילטערט פראגעס", "שאף א געפילטערטן פעקל<br>פארן לערנען גענוי לויט באשטימטע תנאים."),
    ("[data-tt='nav-stats']", "סטאטיסטיק", "קוקט אין גראפן און נומערן<br>ווי אייער לערנען גייט פאראויס."),
    ("[data-tt='nav-help']", "הילף", "אויספירליכע מדריכים, עצות<br>און נוצליכע לינקס. <b>ראטזאם!</b>"),
]


def _tut_nav_spotlight():
    """Step 7: א טור אינעם אויבערשטן סרגל — ווייזט spotlight אויפן יעצטיגן פריט מיטן קנעפל 'ווייטער'."""
    global _tut_step, _tut_nav_idx
    if _tut_step != 7:
        return
    if _tut_nav_idx >= len(_NAV_ITEMS):
        # סיום הסיור → פתח תפריט עזרה
        _tut_step = 0
        _tut_clear_web(mw.deckBrowser.web)
        from aqt.utils import tooltip
        tooltip(
            "<div style='direction:rtl;text-align:center;font-size:15px;line-height:1.9;'>"
            "✨ <b>איר האט פארענדיגט דעם מדריך!</b><br>"
            "עפנט דעם מעניו <b>הילף</b> פאר נאך מדריכים."
            "</div>",
            period=5000,
        )
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: mw.form.menuHelp.exec())
        return

    sel, title, desc = _NAV_ITEMS[_tut_nav_idx]
    msg = f"<b>{title}</b><br>{desc}"
    nxt_label = "ווייטער \u25b6" if _tut_nav_idx < len(_NAV_ITEMS) - 1 else "פארענדיגן \u2714"
    js = f"""(function(){{
  var sel="{sel}", PAD=8;
  ['tut-b0','tut-b1','tut-b2','tut-b3','tut-frame','tut-tip','tut-skip','tut-nav-next']
    .forEach(function(id){{var e=document.getElementById(id);if(e)e.remove();}});
  var el=document.querySelector(sel);
  if(!el)return;
  var fr=document.createElement('div');fr.id='tut-frame';document.body.appendChild(fr);
  var tip=document.createElement('div');tip.id='tut-tip';
  tip.innerHTML={repr(msg)};document.body.appendChild(tip);
  var sk=document.createElement('button');sk.id='tut-skip';
  sk.textContent='\\u2715  \u05d3\u05dc\u05d2 \u05e2\u05dc \u05d4\u05de\u05d3\u05e8\u05d9\u05da';
  sk.onclick=function(){{pycmd('tut_close');}};document.body.appendChild(sk);
  var nxt=document.createElement('button');nxt.id='tut-nav-next';
  nxt.textContent={repr(nxt_label)};
  nxt.style.cssText='position:fixed;z-index:99999;cursor:pointer;pointer-events:auto;background:#27ae60;color:#fff;border:none;border-radius:20px;padding:8px 28px;font-size:15px;font-family:SecularOne-Regular,sans-serif;box-shadow:0 4px 14px rgba(39,174,96,.45);transform:translateX(-50%);';
  nxt.onclick=function(){{pycmd('tut_nav_next');}};document.body.appendChild(nxt);
  var bars=[];
  for(var i=0;i<4;i++){{var b=document.createElement('div');b.id='tut-b'+i;
    b.style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);';
    document.body.appendChild(b);bars.push(b);}}
  function update(){{
    var r=el.getBoundingClientRect(),W=window.innerWidth,H=window.innerHeight;
    var x1=Math.max(0,r.left-PAD),y1=Math.max(0,r.top-PAD);
    var x2=Math.min(W,r.right+PAD),y2=Math.min(H,r.bottom+PAD);
    bars[0].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:0;left:0;right:0;height:'+y1+'px';
    bars[1].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:'+y2+'px;left:0;right:0;bottom:0';
    bars[2].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:'+y1+'px;height:'+(y2-y1)+'px;left:0;width:'+x1+'px';
    bars[3].style.cssText='position:fixed;z-index:9997;pointer-events:none;background:rgba(0,0,0,.76);top:'+y1+'px;height:'+(y2-y1)+'px;left:'+x2+'px;right:0';
    fr.style.top=y1+'px';fr.style.left=x1+'px';
    fr.style.width=(x2-x1)+'px';fr.style.height=(y2-y1)+'px';
    var tr=tip.getBoundingClientRect();
    var ty=r.bottom+18;if(ty+tr.height>H-80)ty=r.top-tr.height-18;
    tip.style.top=Math.max(6,ty)+'px';
    tip.style.left=Math.max(6,r.left+r.width/2-tr.width/2)+'px';
    nxt.style.top=(tip.getBoundingClientRect().bottom + 10)+'px';
    nxt.style.left=(tip.getBoundingClientRect().left + tr.width/2)+'px';
  }}
  update();
}})();"""
    css = _TUT_STYLE.split(">", 1)[1].rsplit("</style>", 1)[0]
    inject_css = (
        f"(function(){{"
        f"var s=document.getElementById('tut-style');"
        f"if(!s){{s=document.createElement('style');s.id='tut-style';document.head.appendChild(s);}}"
        f"s.textContent={repr(css)};"
        f"}})();"
    )
    mw.deckBrowser.web.eval(inject_css)
    mw.deckBrowser.web.eval(js)


# ── END tutorial ───────────────────────────────────────────────────────────────

_body = nav() + f"""
 <style>
 /* --- Global Variables & Night Mode --- */
 body.night {{

background: linear-gradient(20deg, rgba(0, 0, 0, 0.55), rgba(79, 71, 73, 0.82)), url('{base}/user_files/assets/background.jpg') !important;
 }}

 body {{
     /* לייגט דעם פארב איבערגאנג און הינטערגרונט בילד גלייך אויפן גוף */
     background: linear-gradient(20deg, rgba(250, 241, 232, 0.55), rgba(249, 218, 186, 0.82)), url('{base}/user_files/assets/background.jpg') !important;
 }}

 </style>
""" + """
<!-- Floating Tooltip Container -->
<div id="global_tooltip"></div>

<div class="d-flex" style="min-height: 100vh; width: 100%%;">
    <!-- main container -->
    <!-- #282 — container-fluid מיט gap האלט דעם סטאטיסטיק שפאלט לינקס, אן אים צו שטופן אונטער אדער אינעם פעקל שפאלט. -->
    <div class="mx-0 container-fluid  d-flex flex-sm-nowrap flex-wrap gap-3">
        <!-- decks container -->
        %(tree)s
        <!-- end decks container -->
        <!-- סטאטיסטיק שפאלט -->
        %(stats)s
        <!--סוף פונעם סטאטיסטיק שפאלט -->
    </div>
</div>

<script>
let row;
let parent;
let child;

// א הילף פונקציע פאר קלוגן גלילה
function smartScroll(element) {
    if (!element) return;

    // #280 — scrollIntoView גליט אויך דעם דאקומענט-WebView און נישט נאר די פעקל ליסטע.
    // די פריערדיגע פאררעכטונג האט צוגעלייגט 130px margin דערפאר האט זי אמאל גערוקט די שורה צו ווייט אראפ.
    // מען גליט יעצט נאר דעם פעקל האלטער, פונקט וויפיל מען דארף כדי די שורה זאל זיך ווייזן.
    const scroller = element.closest('.deck-tree-container');
    if (scroller) {
        const itemRect = element.getBoundingClientRect();
        const viewportRect = scroller.getBoundingClientRect();
        const gap = 6;
        if (itemRect.top < viewportRect.top + gap) {
            scroller.scrollBy({top: itemRect.top - viewportRect.top - gap, behavior: "smooth"});
        } else if (itemRect.bottom > viewportRect.bottom - gap) {
            scroller.scrollBy({top: itemRect.bottom - viewportRect.bottom + gap, behavior: "smooth"});
        }
        return;
    }

    // א זיכערער אנדערער וועג אויב דער פארמאט-HTML וועט זיך שפעטער טוישן און מען דערקענט נישט קיין פעקל האלטער.
    const itemRect = element.getBoundingClientRect();
    if (itemRect.top < 0) {
        window.scrollBy({top: itemRect.top - 6, behavior: "smooth"});
    } else if (itemRect.bottom > window.innerHeight) {
        window.scrollBy({top: itemRect.bottom - window.innerHeight + 6, behavior: "smooth"});
    }
}

function scrollToCurrent() {
 if (typeof autoScrollEnabled !== 'undefined' && autoScrollEnabled) {
     var element = document.querySelector(".current");
     maybeSmartScroll(element, true);
 }
}

let lastAutoScrollDeck = null;
let lastAutoScrollAt = 0;

function maybeSmartScroll(element, force = false) {
    if (!element) return;
    const now = Date.now();
    var dk = element.closest('[data-deck-id]');
    const deckKey = dk ? dk.dataset.deckId : "";
    if (!force) {
        // Prevent repeated pull when current deck sits near viewport edge.
        if (deckKey === lastAutoScrollDeck && (now - lastAutoScrollAt) < 1200) {
            return;
        }
    }
    lastAutoScrollDeck = deckKey;
    lastAutoScrollAt = now;
    smartScroll(element);
}

// Observer to watch for class changes (keyboard navigation)
var observer = new MutationObserver(function(mutations) {
 mutations.forEach(function(mutation) {
 if (mutation.attributeName === "class") {
     var target = mutation.target;
     var oldClass = mutation.oldValue || "";
     // Scroll only when element becomes current, not on every class mutation.
     if (target.classList.contains("current") && !oldClass.includes("current")) {
         maybeSmartScroll(target);
     }
 }
 });
});

// Initialize observer on all potential deck buttons
function attachObserver() {
 observer.disconnect();
 document.querySelectorAll('.accordion-button').forEach(function(el) {
 observer.observe(el, { attributes: true, attributeOldValue: true, attributeFilter: ["class"] });
 });
 scrollToCurrent();
}

// --- Tooltip JS Logic (lazy — data-tooltip attribute) ---
$(document).ready(function() {
 const tooltipDiv = document.getElementById('global_tooltip');

 $(document).on('mouseenter', '.tooltip_bar', function(e) {
     var text = $(this).attr('data-tooltip') || $(this).find('.tooltiptext').html();
     if (text) {
         tooltipDiv.innerHTML = text;
         tooltipDiv.style.display = 'block';
     }
 }).on('mousemove', '.tooltip_bar', function(e) {
     tooltipDiv.style.left = (e.pageX + 15) + 'px';
     tooltipDiv.style.top = (e.pageY + 15) + 'px';
     if (e.pageX + 300 > window.innerWidth) {
         tooltipDiv.style.left = (e.pageX - 30) + 'px';
     }
 }).on('mouseleave', '.tooltip_bar', function() {
     tooltipDiv.style.display = 'none';
 });
});

// Trigger startup actions
setTimeout(attachObserver, 200);
</script>
  """


def update_times():
    global current_epoch, start_of_anki_epoche_day, next_anki_day_start, days_from_crt
    current_epoch = int(time.time())
    start_of_anki_epoche_day = get_beginning_of_current_day_epoch()
    next_anki_day_start = start_of_anki_epoche_day + 86400
    days_from_crt = mw.col.sched.today


def update_decks_stats():
    global all_decks_stats
    # ניקוי מלא לפני כל רענון — מונע השארת נתונים של חפיסות שנעלמו/השתנו.
    all_decks_stats = {}
    # 1. Get general stats
    sql_query = decks_stats_query.format(
        days_from_crt=days_from_crt,
        current_epoch_1200=current_epoch + 1200,
        next_anki_day_start=next_anki_day_start,
        next_anki_day_start_86400=next_anki_day_start + 86400,
        days_from_crt_1=days_from_crt + 1,
        start_of_anki_epoche_day=start_of_anki_epoche_day
    )
    db_decks_stats = mw.col.db.all(sql_query)

    # #396 — סופרים בנפרד כרטיסי learning שזמנם טרם הגיע היום.
    # GROUP BY יחיד מונע שאילתה נפרדת לכל שורת חפיסה.
    pending_rows = mw.col.db.all(
        """
        SELECT did, count(*)
        FROM cards
        WHERE queue = 1 AND due > ? AND due < ?
        GROUP BY did
        """,
        current_epoch,
        next_anki_day_start,
    )
    pending_map = {int(did): int(count or 0) for did, count in pending_rows}

    # 2. Get actual reviews and time (Items 100 & 8)
    time_sql = time_and_reps_query.format(start_of_anki_epoche_day=start_of_anki_epoche_day)
    db_time_stats = mw.col.db.all(time_sql)
    time_map = {row[0]: {'reps': row[1], 'time': row[2]} for row in db_time_stats}

    for deck in db_decks_stats:
        did = deck[0]
        stats = {}
        stats["overdue"] = deck[1] or 0
        stats["total_cards"] = deck[2] or 0
        stats["tomorrow"] = deck[3] or 0
        stats["today"] = deck[4] or 0
        stats["suspended"] = deck[5] or 0
        # Item 104: Buried
        stats["buried"] = deck[6] or 0
        # אינדקס 7 הוא מספר החדשים בשאילתת הסטטיסטיקות.
        stats["new"] = deck[7] or 0
        stats["pending_learning"] = pending_map.get(int(did), 0)

        # Item 100: Use actual reps instead of answered cards
        t_stats = time_map.get(did, {'reps': 0, 'time': 0})
        stats["answered"] = t_stats['reps']  # Real Repetitions
        stats["time_ms"] = t_stats['time']  # Time in ms

        all_decks_stats[did] = stats
    mw.ffff = {}
    for key, items in all_decks_stats.items():
        mw.ffff[mw.col.decks.get(key)["name"]] = items


_FORECAST_HEB_DAYS = ["זונטאג", "מאנטאג", "דינסטאג", "מיטוואך", "דאנערשטאג", "פרייטאג", "שבת"]


def get_forecast_alert(days_from_crt: int) -> str:
    """ברענגט צוריק HTML פון טעג ווען מען ערווארט א גרויסן עול (אדער '' אויב עס איז נישט דא)."""
    # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
    cfg = get_config()
    if not cfg.get("forecast_enabled", True):
        return ""
    threshold_pct = cfg.get("forecast_threshold_percent", 150)
    min_cards = cfg.get("forecast_min_cards", 30)

    sql = forecast_query.format(days_from_crt=days_from_crt, forecast_calc_days=FORECAST_CALC_DAYS)
    rows = mw.col.db.all(sql)  # [(days_ahead, cnt), ...]
    if not rows:
        return ""

    total_cards = sum(r[1] for r in rows)
    average = total_cards / FORECAST_CALC_DAYS

    today = datetime.date.fromtimestamp(start_of_anki_epoche_day)
    overloaded = []
    for days_ahead, cnt in rows:
        if days_ahead > FORECAST_DISPLAY_DAYS:
            continue
        if cnt < min_cards:
            continue
        if average > 0 and cnt < average * (threshold_pct / 100):
            continue
        day_date = today + datetime.timedelta(days=int(days_ahead))
        heb_idx = (day_date.weekday() + 1) % 7  # weekday(): 0=Mon, 6=Sun → Sun=0 בעברית
        day_name = _FORECAST_HEB_DAYS[heb_idx]
        overloaded.append((int(days_ahead), day_name, cnt))

    if not overloaded:
        return ""

    parts = []
    for days_ahead, day_name, cnt in overloaded:
        parts.append(
            f'<span class="forecast-day statscursor" '
            f'onclick=\'pycmd("forecast_early_review:{days_ahead}")\' '
            f'style="cursor:pointer; text-decoration:underline dotted;">'
            f'{day_name}({cnt})</span>'
        )

    return (
        '<div class="mt-1" style="font-size:0.9rem; color: var(--bs-warning-text-emphasis, #856404);">'
        '⚠ טעג מיט א גרויסן עול: ' + ' '.join(parts) +
        '</div>'
    )


def renderStats(self, _old):
    # כלל הכרטיסים לפי סוג
    # שייך להיום ולעוגה
    update_times()
    sql = stats_query.format(
        tommorow_days_from_crt=days_from_crt + 1,
        next_anki_day_start=next_anki_day_start,
        days_from_crt=days_from_crt,
        current_epoch_1200=current_epoch + 1200,
        start_of_anki_epoche_day=start_of_anki_epoche_day
    )
    # showText(sql, copyBtn=True)
    res = mw.col.db.first(sql)
    new = res[0] or 0
    learn = res[1] or 0
    review = res[2] or 0
    buried = res[3] or 0
    suspended = res[4] or 0
    young = res[5] or 0
    mature = res[6] or 0
    due = res[7] or 0
    overdue = res[8] or 0
    added = res[9] or 0
    #tomorrow_mature = res[10] or 0
    tomorrow_total = res[11] or 0  # Item 114

    # total = new+learn+review

    # #183 — זמן שנלמד ופרוגרס בר נשארים לפי היום בלבד; רק הצפי משתמש בממוצע כלל ה-revlog.
    total_time_ms, total_reps = _today_answer_time_stats()
    total_time_mins = int(total_time_ms / 60000)


    # #128 — כל מספר בסטטיסטיקות הגדולות נספר באותה נוסחת חיפוש של הלחיצה עליו; learning נכלל בתוך "להיום" ולא מוצג כפס נפרד.
    # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
    config = get_config() or {}
    include_new_in_all = bool(config.get("filter_include_new", False))
    all_due_filter = _stats_all_due_filter(include_new_in_all)

    bar_due = _stats_filter_count(STATS_FILTER_TODAY, due + learn)
    bar_overdue = _stats_filter_count(STATS_FILTER_OVERDUE, overdue)
    bar_new = _stats_filter_count(STATS_FILTER_NEW, new)
    total_due_today = _stats_filter_count(
        all_due_filter,
        bar_due + bar_overdue + (bar_new if include_new_in_all else 0),
    )
    pending_learning_total = max(
        0,
        total_due_today - bar_due - bar_overdue - (bar_new if include_new_in_all else 0),
    )
    bar_learn = pending_learning_total
    # אישיו #394: הסימון המקווקו של learning עתידי שייך לשורות החפיסות בלבד;
    # לכן הוא אינו תופס מקום ואינו מצויר בתוך סרגל הסיכום של היום.
    visible_due_total = bar_due + bar_overdue + bar_new


    # Calc expected time (Item 8)
    # avg time per card * remaining scheduler cards.
    # Usually avg is around 10-15 sec/card if not available.
    # #183 — ממוצע כלל ה-revlog משפיע רק על צפי הסיום, לא על ספירת הנלמדו היום בפרוגרס בר.
    avg_time_per_rep = _revlog_average_time_ms()
    expected_cards = total_due_today
    expected_time_ms = expected_cards * avg_time_per_rep
    expected_time_mins = int(expected_time_ms / 60000)

    beyond_cap_rev = 0
    # #183 — total_reps הוא נתון היום בלבד, ולכן הוא בטוח לשימוש בפרוגרס בר בלי להכניס את כלל ה-revlog.
    studied_rescheduled = total_reps  # Use actual reps

    total_for_bar = visible_due_total + studied_rescheduled + beyond_cap_rev
    _p = safe_division(100, total_for_bar)

    def progress_width(count):
        if count == 0:
            return "max-width: 0% !important; min-width: 0% !important;"
        else:
            return f"width:{count * _p}%"

    new_p = progress_width(bar_new)
    due_p = progress_width(bar_due)
    overdue_p = progress_width(bar_overdue)
    studied_rescheduled_p = progress_width(studied_rescheduled)
    beyond_cap_rev_p = progress_width(beyond_cap_rev)

    tomorrow_bar = ""
    # Item 114: Check total tomorrow cards, not just mature
    if visible_due_total == 0 and tomorrow_total > 0:
        tomorrow_bar = f"""
        <div class="progress-bar bg-info" style="width: 100%">
        <span class="inner inner-center tooltip_bar" onclick='pycmd("review_tomorrow_check")' data-tt="db-tomorrow" data-tooltip-pos="top">
        {tomorrow_total} פאר מארגן
        </span>
        </div>
        """

    # Item 8: Restored original structure, tooltip will be positioned by CSS
    time_stat_str = f"""<span class='display-1 mt-1 ms-0 tooltip_bar' style="font-size: 1rem;">
    <span class="tooltip_bar" style="display: inline-block;" data-tt="db-time" data-n-avg="{int(avg_time_per_rep / 1000)}" data-n-exp="{expected_cards}" data-tooltip-pos="bottom">
    לערן צייט: {total_time_mins} מינ׳' | געשאצטע ענדע: {expected_time_mins} מינ׳'
    </span>
    </span>"""

    # Hide calendar if empty
    stats_second_row = stats_conatiner_second_row
    # בעיה 10: מסתירים את מסגרת לוח-השנה כשאין נתוני revlog, אין סטטיסטיקות, או מצב compact
    try:
        revlog_count = mw.col.db.scalar("SELECT count() FROM revlog LIMIT 1") or 0
    except Exception:
        revlog_count = 1
    if (
        revlog_count == 0
        or (visible_due_total + total_reps + suspended + buried) == 0
        # #127: תוקן ברירת מחדל מ-True ל-False — כדי שלוח השנה יוצג כאשר הקונפיג ריק
        # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
        or get_config().get("compact_mode", False)
    ):
        stats_second_row = stats_second_row.replace(
            '<div class="col p-1 mb-1  align-hetmap-center stats_row" style="overflow: visible;">',
            '<div class="col p-1 mb-1  align-hetmap-center stats_row" style="overflow: visible; display:none;">',
            1,
        )

    forecast_html = get_forecast_alert(days_from_crt)

    # #274 — review הוא סך כל החזרות, ו-young/mature הן החלוקה שלו; לא סופרים אותו שוב במכנה של העוגה.
    total_vals = sum([new, learn, buried, suspended, young, mature])
    third_row = stats_conatiner_third_row if total_vals > 0 else ""

    stats_continer = (stats_conatiner_first_row.format(
        total=total_due_today,
        added=added,
        studied_rescheduled_p=studied_rescheduled_p,
        studied_rescheduled=studied_rescheduled if studied_rescheduled != 0 else "",
        due_p=due_p,
        due=bar_due if bar_due != 0 else "",
        overdue_p=overdue_p,
        overdue=bar_overdue if bar_overdue != 0 else "",
        new_p=new_p,
        new=bar_new if bar_new != 0 else "",
        beyond_cap_rev_p=beyond_cap_rev_p,
        beyond_cap_rev=beyond_cap_rev if beyond_cap_rev != 0 else "",
        time_stats=time_stat_str,
        tomorrow_bar=tomorrow_bar,
        forecast_alert=forecast_html
    )
                      + stats_second_row
                      + third_row)
    stats_script = stats_js.format(mature=mature,
                                   mature_percent=round(safe_division(mature, total_vals) * 100, 2),
                                   young=young,
                                   young_percent=round(safe_division(young, total_vals) * 100, 2),
                                   new=new,
                                   new_percent=round(safe_division(new, total_vals) * 100, 2),
                                   learn=learn,
                                   learn_percent=round(safe_division(learn, total_vals) * 100, 2),
                                   suspended=suspended,
                                   suspended_percent=round(safe_division(suspended, total_vals) * 100, 2),
                                   buried=buried,
                                   buried_percent=round(safe_division(buried, total_vals) * 100, 2)
                                   )

    return _old(self) + stats_continer + stats_script


def renderDeckTree(self, top: DeckTreeNode, _old) -> str:
    update_times()
    update_decks_stats()
    global in_search, _pending_learning_render_cache
    _pending_learning_render_cache = {}

    # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
    config = get_config()
    auto_scroll = "true" if config.get("auto_scroll", False) else "false"

    # --- Night Mode Check ---
    night_mode_script = ""
    if theme_manager.night_mode:
        night_mode_script = "<script>document.body.classList.add('night');</script>"

    grayscale_script = ""
    if config.get("grayscale_mode", False):
        grayscale_script = "<script>document.body.classList.add('modern-grayscale');</script>"

    scroll_script = f"<script>var autoScrollEnabled = {auto_scroll};</script>"

    # --- Compact Mode Logic ---
    compact_mode = config.get("compact_mode", False)
    compact_scale = config.get("compact_scale", 100)
    scale_decimal = compact_scale / 100.0

    compact_inject = ""
    col_class = "col-12 modern-deck-tree-wrap"

    if compact_mode:
        # #170 — גם במצב דחוס נשאיר class ייעודי כדי שכללי הפריסה לא יישברו כשהסטטיסטיקות יורדות מתחת לחפיסות.
        col_class = "col-12 modern-deck-tree-wrap"
        compact_inject = f"""
        <style>
        :root {{
            --compact-font-size: {scale_decimal}rem;
        }}
        </style>
        """

    buf = scroll_script + grayscale_script + night_mode_script + compact_inject + deck_tree_top.format(col_class=col_class)

    if in_search:
        buf += reset_search_button

    # --------------------------------------------------------------------------------------
    # FIX: search_row must be added ALWAYS, otherwise the HTML tags from deck_tree_top
    # won't be closed properly, resulting in "None" or broken UI.
    # --------------------------------------------------------------------------------------
    buf += search_row

    ctx = RenderDeckNodeContext(current_deck_id=self.mw.col.conf["curDeck"])

    buf += '<div class="deck-tree-container">'

    if top.children[0].name == "ברירת מחדל" and retlen("") == 0:
        buf += deck_browser_new_user
    else:
        update_times()

        for child in _gimatria_sorted_children(top.children):
            buf += self._render_deck_node(child, ctx)[0]

    buf += "</div>"
    buf += deck_tree_buttom

    if in_search and search_len == 0:
        showInfo(f'קיין פעקלעך זענען נישט געפונען געווארן לויט דער זוכעניש "{search_str}"')
        mw.moveToState("deckBrowser")
    in_search = False

    if _tut_step in (1, 2, 4):
        buf += _TUT_STYLE + _tut_make_script()

    if _tut_step == 4:
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(350, _tut_auto_review)

    if _tut_step == 7:
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, _tut_nav_spotlight)

    if _tut_step == 7:
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, _tut_nav_spotlight)

    # ── TUT DEBUG ──────────────────────────────────────────────
    try:
        _n_decks   = len([d for d in self.mw.col.decks.all()
                          if not self.mw.col.decks.is_filtered(d['id'])
                          and d['name'] not in ('Default', 'ברירת מחדל')])
        _n_cards   = self.mw.col.db.scalar("SELECT count() FROM cards WHERE queue >= 0")
        _n_revlog  = self.mw.col.db.scalar("SELECT count() FROM revlog")
    except Exception as _e:
        pass
    # ───────────────────────────────────────────────────────────

    return buf


# #362 — מיון חפיסות לפי גימטריא (טו/טז): עץ החפיסות מגיע מה-backend ממוין לקסיקוגרפית,
# מה שממקם "טו"/"טז" לפני "יא".."יד". ממיינים מחדש את הילדים לפי מפתח הגימטריא המשותף.
# ההגדרה (הפעלה/כיבוי) משותפת עם תוסף hebrew-date — צ'קבוקס בטאב מראה שבהעדפות.
def _gimatria_sort_decks_enabled() -> bool:
    try:
        config = aqt.mw.addonManager.getConfig("hebrew-date") or {}
        return bool(config.get("gimatria_sort_enabled", True))
    except Exception:
        return True


def _gimatria_sorted_children(children):
    if not _gimatria_sort_decks_enabled():
        return children
    try:
        return sorted(children, key=lambda child: gimatria_sort_key(child.name))
    except Exception:
        return children


def render_deck_node(self, node: DeckTreeNode, ctx: RenderDeckNodeContext, _old) -> str:
    return renderdecknode(node, ctx, "")


def renderdecknode(node: DeckTreeNode, ctx: RenderDeckNodeContext, parent_name="") -> (
    str, int, int, int, int, int, int, int, int):
    global in_search, search_str, search_len

    stats: dict = all_decks_stats.get(node.deck_id)
    if stats:
        overdue = stats["overdue"]
        all_deck_cards = stats["total_cards"]
        tomorrow = stats["tomorrow"]
        today = stats["today"]
        suspended = stats["suspended"]
        studied_rescheduled = stats["answered"]
        new_c = stats["new"]
        buried = stats.get("buried", 0)
        pending_learning = stats.get("pending_learning", 0)
    else:
        # אין סטטיסטיקות לחפיסה: מתחילים מכל הספירות באפס.
        overdue, all_deck_cards, tomorrow, today, suspended, studied_rescheduled, new_c, buried = 0, 0, 0, 0, 0, 0, 0, 0
        pending_learning = 0

    full_deck_name = (parent_name + "\x1f" + node.name) if parent_name else node.name
    childs_buf = ""
    for child in _gimatria_sorted_children(node.children):
        c_buf, child_overdue, child_all_deck_cards, child_tomorrow, child_today, child_suspended, child_studied_rescheduled, child_new_c, child_buried = renderdecknode(
            child, ctx, full_deck_name)
        if not in_search:
            childs_buf += c_buf
        overdue += child_overdue
        all_deck_cards += child_all_deck_cards
        tomorrow += child_tomorrow
        today += child_today
        suspended += child_suspended
        studied_rescheduled += child_studied_rescheduled
        new_c += child_new_c
        buried += child_buried
        pending_learning += _pending_learning_render_cache.get(int(child.deck_id), 0)
    _pending_learning_render_cache[int(node.deck_id)] = pending_learning
    # name, collapse, icon
    prefix = "collapsed" if node.collapsed and not in_search else ""

    indent = "&nbsp;" if in_search else "&nbsp;" * 6 * (node.level - 1)

    klass = "current" if node.deck_id == ctx.current_deck_id else ""

    if parent_name != "":
        parent_name += ""
    if in_search:
        if search_str not in node.name:
            buf = ""
            for child in node.children:
                buf += renderdecknode(child, ctx, full_deck_name)[0]
            return buf, overdue, all_deck_cards, tomorrow, today, suspended, studied_rescheduled, new_c, buried
        else:
            search_len += 1

    total = studied_rescheduled + node.new_count + node.review_count + node.learn_count
    total = safe_division(100, total)
    total_due_limited = node.new_count + node.review_count + node.learn_count  # limited by deck options

    # באג: today כולל כרטיסים שכבר נענו + כרטיסי למידה חדשים.
    # חיסור studied_rescheduled מונע ספירת כרטיסים שכבר נלמדו כ"מעבר למגבלה".
    _remaining_today = max(0, today + overdue - studied_rescheduled)
    due_unlimited = max(0, _remaining_today - node.learn_count - node.review_count)
    # #123: accordion-header מקבל class current בנפרד מ-accordion-button,
    # מה שגורם לשתי שורות אפורות. מסירים את klass מ-accordion-header
    # ומשאירים אותו רק על accordion-button שם הוא נדרש לגלילה אוטומטית.
    # #85 — data-deck-id פעם אחת בלבד על div.deck; כל JS גוזר משם via closest('[data-deck-id]').
    # #85b — accordion-header מוזג ל-div.deck (flex+wrap); חוסך div עטיפה.
    buf = f"""
        <div class="deck" data-deck-id="{node.deck_id}" data-deck-name="{html.escape(node.name)}">
        <div
            class="accordion-button collapsed button {klass} deck"
            onclick="return onDeckClick(event,this)"
            oncontextmenu="return pycmd('opts:'+this.closest('[data-deck-id]').dataset.deckId)">
        """

    # deck link
    if node.children and not in_search:
        collapse = (f"""<a
            class="collapse-button {prefix}"
            onclick='event.stopPropagation();this.classList.toggle("collapsed"); return pycmd(\"collapse:{node.deck_id} \")'
            ></a>""")
    else:
        # #85b — non-collapse-button היה אלמנט ריק ללא CSS/JS; הוסר.
        collapse = ""

    # #85b — extraclass "filtered" הוסר (לא מוגדר בשום CSS/JS); def_img נשמר לאייקון.
    if node.filtered:
        def_img = "CustomStudySession"
    else:
        def_img = "default"

    if in_search:
        parent_display = parent_name.replace("\x1f", " &#x276F; ") if parent_name else ""
        highlighted_name = html.escape(node.name).replace(search_str,
                                       f"""<span style="background-color: rgba(99, 113, 165, 0.5);">{search_str}</span>""")
        if parent_display:
            search_name = f"""<span style="display:inline-flex;flex-direction:column;vertical-align:middle;"><span style="color:gray;font-size:0.7em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2;">{parent_display}</span><span style="line-height:1.2;">{highlighted_name}</span></span>"""
        else:
            search_name = highlighted_name
    else:
        search_name = html.escape(node.name)
    # #385/#291 — שם החפיסה וה-checkbox הם flex items מפורשים; ה-checkbox נשאר
    # בקצה הימני ובמרכז הגובה גם כשמצב הבחירה מופעל.
    buf += f"""
    <div class="deck-name-col col-5">
            <input type="checkbox"
                class="deck-select-cb form-check-input"
                onclick="event.stopPropagation();">
            <span class="deck-name-content">
            {indent}<img src="{base}/user_files/assets/deck_icons/{def_img}.png"
            alt=""
            class="rounded img-fluid deck_img">
            {collapse}
            {search_name}
            </span>
    """

    if all_deck_cards and all_deck_cards > 0:
        # #132 — כשיש מושהים או מוטמנים, עיגול הספירה מקבל class במקום צבע inline כדי שמצב כהה יוכל לצבוע אותו נכון.
        side_count = suspended + buried
        side_count_class = " side-count" if side_count > 0 else ""

        # #85b — הוסר col class (ההורה כבר לא flex-row אז col חסר משמעות).
        buf += f"""<span class='count totaldeck-count tooltip_bar{side_count_class}' data-tt="db-count" data-n="{all_deck_cards}" data-n-s="{suspended}" data-n-b="{buried}" data-tooltip-pos="top">
            {all_deck_cards}
                </span>"""

    buf += """
    </div>"""

    # #85b — progress_bar_part מחזיר מחרוזת ריקה כשהספירה 0, במקום div בלתי נראה.
    def progress_width(count):
        if count == 0:
            return ""
        return f"width:{count * total}%"

    studied_rescheduled_precent = progress_width(studied_rescheduled)
    new_precent = progress_width(node.new_count)
    review_precent = progress_width(node.review_count)
    due_learning = max(0, int(node.learn_count) - pending_learning)
    learn_precent = progress_width(due_learning)
    pending_learning_precent = progress_width(pending_learning)

    if all_deck_cards == 0:
        icon_html = empty_icon
        icon_type = "empty"
        icon_n = 0
    elif total_due_limited == 0:  # הושלם
        # 104. Check if completed but has buried cards
        if buried > 0:
            icon_html = finished_but_buried_icon(buried)
            icon_type = "buried"
            icon_n = buried
        else:
            icon_html = finished_icon
            icon_type = "done"
            icon_n = 0
    elif node.filtered:
        icon_html = filtered_icon
        icon_type = "filtered"
        icon_n = 0
    elif overdue:
        icon_html = overdue_icon(overdue)
        icon_type = "overdue"
        icon_n = overdue
    else:
        icon_html = due_icon
        icon_type = "due"
        icon_n = 0
    buf += f'<div class="deck-icon-col col-1 tooltip_bar" data-tt="db-icon" data-n-type="{icon_type}" data-n="{icon_n}" data-tooltip-pos="top-right">'
    buf += icon_html
    buf += "</div>"
    # deck progress
    buf += """    <div class="deck-progress-col col-3">
                <div class="progress deck-progress">
    """

    def progress_bar_part(background, style, label, num, extras=None, display=None):
        # #85b — דילוג על progress bars ריקים (width 0): בלתי נראים ובלתי ניתנים להובר.
        if not style:
            return ""
        data_num = num if num != 0 and num != "" else ""
        shown = display if display is not None else (data_num if data_num != "" else "")
        extra_attrs = ""
        if extras:
            for i, (ecount, elabel) in enumerate(extras, 1):
                extra_attrs += f' data-n-e{i}="{ecount}" data-n-e{i}l="{elabel}"'
        return f"""
        <div class="progress-bar db-pb {background} tooltip_bar" style="{style}"
             data-tt="db-pb" data-n-label="{label}" data-n="{data_num}"{extra_attrs} data-tooltip-pos="top">
        {shown}
        </div>
        """

    _overflow_ann = ""
    if sum([node.new_count, node.review_count, node.learn_count]) > 0:
        buf += progress_bar_part("bg-secondary", studied_rescheduled_precent, "חזרות וואס מען האט היינט געמאכט",
                                 studied_rescheduled if studied_rescheduled != 0 else "")

        new_beyond = new_c - node.new_count
        has_review_bar = node.review_count > 0

        _new_extras = [(new_beyond, "איבער דער טעגליכער גרעניץ")] if new_beyond > 0 else None
        if new_beyond > 0 and not has_review_bar:
            _suffix = " " + str(node.new_count) if node.new_count > 0 else ""
            _new_display = '<span style="color:rgb(13 40 253);font-weight:bold">('+ str(new_beyond) +')</span>' + _suffix
        else:
            _new_display = str(node.new_count) if node.new_count > 0 else ""
        buf += progress_bar_part("bg-new", new_precent, "נייע קארטלעך",
                                 node.new_count if node.new_count != 0 else "",
                                 extras=_new_extras, display=_new_display)

        buf += progress_bar_part("bg-learn", learn_precent, "ביים לערנען — עס איז שוין צייט",
                                 due_learning if due_learning != 0 else "")
        buf += progress_bar_part("pending-learning-segment", pending_learning_precent,
                                 "ביים לערנען — די חזרה צייט איז נאך נישט געקומען",
                                 pending_learning if pending_learning != 0 else "")

        _rev_extras = []
        if due_unlimited > 0:
            _rev_extras.append((due_unlimited, "איבער דער טעגליכער גרעניץ"))
        if new_beyond > 0:
            _rev_extras.append((new_beyond, "נייע איבער דער גרעניץ"))

        # Review bar: overflow | review count | new-overflow
        _rev_parts = []
        if new_beyond > 0 and has_review_bar:
            _rev_parts.append('<span style="color:rgb(13 40 253);font-weight:bold">('+ str(new_beyond) +')</span>')
        if due_unlimited > 0:
            _rev_parts.append('<span style="color:#fff;font-weight:bold">('+ str(due_unlimited) +')</span>')
        if node.review_count > 0:
            _rev_parts.append(str(node.review_count))
        _rev_display = " ".join(_rev_parts) if _rev_parts else ""
        _rev_data_n = node.review_count if node.review_count > 0 else ""
        buf += progress_bar_part("bg-review", review_precent, "קארטלעך פאר חזרה",
                                 _rev_data_n,
                                 extras=_rev_extras or None, display=_rev_display)

    elif studied_rescheduled > 0:
        if tomorrow > 0 and not node.filtered:
            buf += progress_bar_part("bg-secondary", "width:50%", "חזרות וואס מען האט היינט געמאכט",
                                     studied_rescheduled if studied_rescheduled != 0 else "")
            buf += progress_bar_part("bg-info", "width:50%", "וויפיל פראגעס זענען געפלאנט פאר מארגן (אן נייע און די וואס מען לערנט נאך)",
                                     tomorrow if tomorrow != 0 else "")
        else:
            buf += progress_bar_part("bg-secondary", "width:100%", "חזרות וואס מען האט היינט געמאכט",
                                     studied_rescheduled if studied_rescheduled != 0 else "")
    elif tomorrow > 0 and not node.filtered:
        buf += progress_bar_part("bg-info", "width:100%", "וויפיל פראגעס זענען געפלאנט פאר מארגן (אן נייע און די וואס מען לערנט נאך)",
                                 tomorrow if tomorrow != 0 else "")

    buf += "  </div>\n"  # close .progress
    if _overflow_ann:
        buf += f'<div style="text-align:center;line-height:1.3;margin-top:1px">{_overflow_ann}</div>\n'
    buf += "                </div>\n"  # close .col-3
    buf += deck_row_buttons_only
    buf += """
              </div>
              """  # closes accordion-button div

    all_childs_buf = f'<div id="collapse{node.deck_id}" class="deck-children" style="transform:scaleY(0);">{childs_buf}</div>'

    if not node.collapsed or in_search:
        buf += all_childs_buf.replace('transform:scaleY(0);', 'transform:scaleY(1);', 1)

    sub_decks_html[node.deck_id] = all_childs_buf

    buf += """</div>"""
    return buf, overdue, all_deck_cards, tomorrow, today, suspended, studied_rescheduled, new_c, buried

    # return buf


# hide menubar
def _show_menubar(*args) -> None:
    mw.form.menubar.setMaximumSize(0, 0)
    mw.form.menubar.setMinimumSize(0, 0)


def open_stats_on_all_decks():
    stats_dialog: aqt.stats.NewDeckStats = aqt.dialogs.open("NewDeckStats", mw)
    stats_dialog.form.web.eval("""setTimeout(() => {
                                document.querySelector("label>input[value='2']").click();},1000)""")


# 4. Context Menu Logic
def on_stat_context(arg):
    m = QMenu(mw)
    # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
    config = get_config()

    # Option to include new cards in Today's Review
    opt_new = QAction("נעם מיט נייע קארטלעך אין דער חזרה", m)
    opt_new.setCheckable(True)
    opt_new.setChecked(config.get("filter_include_new", False))
    opt_new.triggered.connect(lambda: save_conf(opt_new.isChecked(), "filter_include_new"))
    m.addAction(opt_new)

    # Sort order submenu
    order_menu = m.addMenu("ווייז סדר")
    order_group = QActionGroup(order_menu)
    order_group.setExclusive(True)
    current_order = config.get("filter_order", 1)
    for val, label in FILTER_ORDER_OPTIONS:
        act = QAction(label, order_menu)
        act.setCheckable(True)
        act.setChecked(val == current_order)
        order_group.addAction(act)
        order_menu.addAction(act)
        act.triggered.connect(lambda checked, v=val: save_conf(v, "filter_order"))

    # Option to review ahead (tomorrow) without young
    opt_ahead = QAction("חזר פריער די קארטלעך פון מארגן (אן יונגע)", m)
    opt_ahead.triggered.connect(lambda: create_temp_filtered_deck("is:due prop:due=1 -prop:ivl<21"))
    m.addAction(opt_ahead)

    m.exec(QCursor.pos())


def _copy_deck_recursive(col, src_did: DeckId, new_parent_name: str, structure_only: bool = False) -> int:
    """Copy a deck (and all its sub-decks and notes) under new_parent_name.
    פראבלעם 11: structure_only=True שאפט נאר דעם פעקל בוים, אן צו קאפירן די פראגעס.
    Returns the number of notes copied."""
    col.decks.flush()  # make sure we have a fresh view
    src_deck = col.decks.get(src_did, default=False)
    if not src_deck:
        return 0

    # Build new deck name: parent_name + "::" + short_name_of_src
    src_full_name = src_deck["name"]
    short_name = src_full_name.split("::")[-1]
    if new_parent_name:
        new_deck_name = new_parent_name + "::" + short_name
    else:
        new_deck_name = short_name

    # Ensure unique name
    base_new_name = new_deck_name
    counter = 2
    while col.decks.id_for_name(new_deck_name):
        new_deck_name = base_new_name + f" ({counter})"
        counter += 1

    new_did = DeckId(col.decks.id(new_deck_name, create=True))

    # Copy notes that belong directly to this deck (not children) — מדלגים אם רק מבנה
    copied = 0
    if not structure_only:
        note_ids = col.find_notes(f"did:{src_did}")
        for nid in note_ids:
            src_note = col.get_note(nid)
            new_note = col.new_note(src_note.note_type())
            new_note.fields = list(src_note.fields)
            new_note.tags = list(src_note.tags)
            col.add_note(new_note, new_did)
            copied += 1

    # Recurse into sub-decks (children returns direct + indirect; filter direct only)
    all_children = col.decks.children(src_did)  # list of (name, id)
    # keep only direct children: name has exactly one more "::" segment than src_full_name
    src_depth = src_full_name.count("::")
    direct_children = [(n, DeckId(i)) for n, i in all_children
                       if n.count("::") == src_depth + 1]
    for _, child_did in direct_children:
        copied += _copy_deck_recursive(col, child_did, new_deck_name, structure_only=structure_only)

    return copied


def _is_ancestor_or_self(col, possible_ancestor_id: DeckId, deck_id: DeckId) -> bool:
    """קוקט צי possible_ancestor_id איז גלייך צו-deck_id אדער אן אויבערשטער פעקל פון אים (גייט ארויף אינעם בוים)"""
    if possible_ancestor_id == deck_id:
        return True
    try:
        children_ids = {DeckId(i) for _, i in col.decks.children(possible_ancestor_id)}
        return deck_id in children_ids
    except Exception:
        return False


def _handle_deck_paste(browser: DeckBrowser, arg: str) -> None:
    """arg format: action:target_id:source_id1,source_id2,..."""
    parts = arg.split(":", 2)
    if len(parts) != 3:
        showInfo("א טעות אין די אריינלייג פאראמעטערן")
        return
    action, target_id_str, source_ids_str = parts
    try:
        target_id = DeckId(int(target_id_str))
        source_ids = [DeckId(int(x)) for x in source_ids_str.split(",") if x.strip()]
    except ValueError:
        showInfo("טעות: אומגילטיגע פעקל אידענטיפיקאטארן")
        return

    if not source_ids:
        showInfo("קיין פעקלעך זענען נישט אויסגעקליבן געווארן")
        return

    col = browser.mw.col

    # בעיה 11: מניעת העתקה/הזזה של חפיסה לתוך עצמה או תת-חפיסה שלה
    invalid = [sid for sid in source_ids if _is_ancestor_or_self(col, sid, target_id)]
    if invalid:
        showInfo("מען קען נישט אריינלייגן א פעקל אין זיך אליין אדער אין אן אייגענעם אונטערפעקל")
        return

    if action == "cut":
        reparent_decks(parent=browser.mw, deck_ids=source_ids, new_parent=target_id).run_in_background()
        showInfo(f"{len(source_ids)} די פעקלעך זענען מיט הצלחה אריבערגעפירט געווארן")
    elif action == "copy_structure":
        # בעיה 11: העתקת מבנה החפיסות בלבד - יוצרים את אותו עץ חפיסות אצל היעד, ללא העתקת שאלות.
        target_deck = col.decks.get(target_id, default=False)
        target_name = target_deck["name"] if target_deck else ""
        for src_did in source_ids:
            _copy_deck_recursive(col, src_did, target_name, structure_only=True)
        col.save()
        browser.mw.reset()
        showInfo(f"{len(source_ids)} די פעקלעך זענען קאפירט געווארן (נאר דער סטרוקטור)")
    else:
        # "copy" — duplicate decks with their notes under target_id
        target_deck = col.decks.get(target_id, default=False)
        target_name = target_deck["name"] if target_deck else ""
        total_copied = 0
        for src_did in source_ids:
            total_copied += _copy_deck_recursive(col, src_did, target_name)
        col.save()
        browser.mw.reset()
        showInfo(f"{len(source_ids)} די פעקלעך זענען מיט הצלחה קאפירט געווארן ({total_copied} קארטלעך)")

    browser.web.eval("exitSelectMode()")


# בעיה 11: מחיקת חפיסות מסומנות עם הודעת אזהרה לפני ביצוע
def _handle_deck_delete_selected(browser: DeckBrowser, arg: str) -> None:
    """arg format: deck_id1,deck_id2,..."""
    try:
        source_ids = [DeckId(int(x)) for x in arg.split(",") if x.strip()]
    except ValueError:
        showInfo("טעות: אומגילטיגע פעקל אידענטיפיקאטארן")
        return
    if not source_ids:
        showInfo("קיין פעקלעך זענען נישט אויסגעקליבן געווארן")
        return

    col = browser.mw.col
    # סופרים כרטיסים בכל החפיסות (כולל תתי-חפיסות) כדי להציג מספר אמיתי באזהרה
    deck_names = []
    total_cards = 0
    for did in source_ids:
        deck = col.decks.get(did, default=False)
        if not deck:
            continue
        deck_names.append(deck["name"])
        # כולל תתי-חפיסות
        try:
            dids = [did] + [DeckId(i) for _, i in col.decks.children(did)]
            total_cards += col.db.scalar(
                f"select count() from cards where did in ({','.join('?' * len(dids))})",
                *dids,
            ) or 0
        except Exception:
            pass

    names_preview = "\n• ".join(deck_names[:10])
    if len(deck_names) > 10:
        names_preview += f"\n... און נאך {len(deck_names) - 10} פעקלעך"

    msg = (
        f"אויסמעקן {len(source_ids)} אנגעצייכנטע פעקלעך?\n\n"
        f"• {names_preview}\n\n"
        f"דאס אויסמעקן וועט אוועקנעמען {total_cards} קארטלעך צוזאמען מיט די אונטערפעקלעך.\n"
        f"מען קען די פעולה נישט צוריקדרייען!"
    )
    if not askUser(msg, defaultno=True, title="באשטעטיגן דאס אויסמעקן פעקלעך"):
        browser.web.eval("exitSelectMode()")
        return

    from aqt.operations.deck import remove_decks
    # remove_decks דורש deck_name — משתמשים בשמות החפיסות שכבר אספנו
    combined_name = ", ".join(deck_names)
    remove_decks(parent=browser.mw, deck_ids=source_ids, deck_name=combined_name).run_in_background()
    browser.web.eval("exitSelectMode()")


def linkHandler(self: DeckBrowser, url: str, _old) -> Any:
    mw.hide_menubar()
    mw.form.menubar.setMaximumSize(0, 0)
    # print(url)
    arg = ""
    if ":" in url:
        (cmd, arg) = url.split(":", 1)
    else:
        cmd = url

    global _tut_active, _tut_step, _tut_did, _tut_did, _tut_nav_idx, _tut_nav_idx

    if cmd == "stat_context":
        on_stat_context(arg)
        return

    if cmd == "tut_start":
        _tut_active = True
        _tut_step = 1
        _tut_did = 0
        self.show()
        return

    if cmd == "tut_close":
        _tut_active = False
        _tut_step = 0
        _tut_did = 0
        _tut_nav_idx = 0
        _tut_clear_web(self.web)
        _tut_clear_qt()
        try:
            mw.reviewer.bottom.web.eval("var s=document.getElementById('tut-rev-style'); if(s)s.remove();")
            mw.reviewer.web.eval("""
              var s=document.getElementById('tut-rev-tip-style'); if(s)s.remove();
              var t=document.getElementById('tut-rev-tip'); if(t)t.remove();
            """)
        except Exception:
            pass
        return

    if cmd == "tut_nav_next":
        _tut_nav_idx += 1
        _tut_nav_spotlight()
        return

    if cmd == "collapse":
        # self._collapse(DeckId(int(arg)))
        did = int(arg)
        if pointVersion() > 231001:
            node = self.mw.col.decks.find_deck_in_tree(self._render_data.tree, did)
        else:
            node = self.mw.col.decks.find_deck_in_tree(self._dueTree, did)
        # for child in node.children:
        if node:
            node.collapsed = not node.collapsed
            mw.col.decks.set_collapsed(deck_id=did, collapsed=node.collapsed, scope=DeckCollapseScope.REVIEWER)
        if not mw.pm.reduce_motion():
            if node.collapsed:
                self.web.eval(f'''
                row = document.getElementById("collapse{arg[:-1]}");
                if (row) {{
                    row.style.transform = "scaleY(0)";
                    setTimeout(() => {{
                        if (row && row.parentElement) row.remove();
                    }}, "100");
                }}''')
            else:
                ctx = RenderDeckNodeContext(current_deck_id=self.mw.col.conf["curDeck"])
                self._render_deck_node(node, ctx)
                self.web.eval(f"""
                row = document.querySelector('.deck[data-deck-id="{arg.strip()}"] > .accordion-button');
                parent = row.parentElement;
                parent.insertAdjacentHTML('afterend', `{sub_decks_html[int(arg)].replace('transform:scaleY(0);', 'transform:scaleY(1);', 1)}`);
                var newChild = document.getElementById("collapse{arg[:-1]}");
                if (newChild) window.getComputedStyle(newChild).transform;
                // פראבלעם 8: ווען מען עפנט אונטערפעקלעך, האבן די קנעפלעך (צולייגן א פראגע / דורכבלעטערן וכדומה) זיך נישט געוויזן
                // ווייל fill_deck_btns() ווערט אויפגערופן נאר איינמאל ביים סוף פון-deck tree. מען רופט עס נאכאמאל אויפן נייעם אונטערבוים.
                if (typeof fill_deck_btns === 'function' && newChild) {{ fill_deck_btns(newChild); }}
                // #85b — מען האט אוועקגענומען טויטן קאוד פון jQuery UI draggable/droppable destroy + drag_drop() וואס איז נישט פאראן.
                setTimeout(() => {{
                    if (newChild) newChild.style.transform = "scaleY(1)";
                    attachObserver();
                }}, "1");
            """)
        else:
            if node.collapsed:
                self.web.eval(f"""
                row = document.getElementById("collapse{arg[:-1]}");
                if (row && row.parentElement) row.remove();
                """)
            else:
                ctx = RenderDeckNodeContext(current_deck_id=self.mw.col.conf["curDeck"])
                self._render_deck_node(node, ctx)
                self.web.eval(f"""
                row = document.querySelector('.deck[data-deck-id="{arg.strip()}"] > .accordion-button');
                parent = row.parentElement;
                parent.insertAdjacentHTML('afterend', `{sub_decks_html[int(arg)].replace('transform:scaleY(0);', 'transform:scaleY(1);', 1)}`);
                var newChild = document.getElementById("collapse{arg[:-1]}");
                if (newChild) window.getComputedStyle(newChild).transform;
                // פראבלעם 8: ווען מען עפנט אונטערפעקלעך, האבן די קנעפלעך (צולייגן א פראגע / דורכבלעטערן וכדומה) זיך נישט געוויזן
                // ווייל fill_deck_btns() ווערט אויפגערופן נאר איינמאל ביים סוף פון-deck tree. מען רופט עס נאכאמאל אויפן נייעם אונטערבוים.
                if (typeof fill_deck_btns === 'function' && newChild) {{ fill_deck_btns(newChild); }}
                // #85b — מען האט אוועקגענומען טויטן קאוד פון jQuery UI draggable/droppable destroy + drag_drop().
                setTimeout(() => {{
                    attachObserver();
                }}, "1");
                """)
    elif cmd == "Stats":
        open_stats_on_all_decks()
        # mw.onStats()  # סטטיסטיקות
    elif cmd == "select":
        set_current_deck(parent=self.mw, deck_id=DeckId(int(arg))).run_in_background()
    ############
    elif cmd == "filtoday":
        alert_if_too_much_overdue(STATS_FILTER_OVERDUE)
        create_temp_filtered_deck(STATS_FILTER_TODAY)
    elif cmd == "filoverdue":
        create_temp_filtered_deck(STATS_FILTER_OVERDUE)
    elif cmd == "filall":
        # 103. Check config
        # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
        config = get_config()
        include_new = config.get("filter_include_new", False)
        create_temp_filtered_deck(_stats_all_due_filter(bool(include_new)))
    elif cmd == "filall_with_new":
        create_temp_filtered_deck(STATS_FILTER_ALL_DUE_WITH_NEW)
    elif cmd == "rev_new":
        create_temp_filtered_deck(STATS_FILTER_NEW)
    elif cmd == "review_ahead_mature":
        if askUser("זענט איר זיכער אז איר ווילט פריער חזרן בוגר קארטלעך וואס זענען געפלאנט פאר מארגן?"):
            create_temp_filtered_deck("prop:due=1 prop:ivl>=21")
    # Item 114: Check logic for tomorrow
    elif cmd == "review_tomorrow_check":
        # Check mature cards count for tomorrow directly from DB to be safe
        update_times()
        mature_sql = f"SELECT count() FROM cards WHERE queue IN (2, 3) AND due = {days_from_crt + 1} AND ivl >= 21"
        mature_tomorrow = mw.col.db.scalar(mature_sql)

        if mature_tomorrow > 0:
            if askUser("זענט איר זיכער אז איר ווילט פריער חזרן בוגר קארטלעך וואס זענען געפלאנט פאר מארגן?"):
                create_temp_filtered_deck("prop:due=1 prop:ivl>=21")
        else:
            showInfo(
                "עס איז נישט ראטזאם פריער צו חזרן יונגע קארטלעך. זיי זענען נאך אין די ערשטע איבערלערן שטאפלען, און עס איז וויכטיג צו היטן זייערע אריגינעלע מרווחים.\n\nאויב איר ווילט זיי דאך חזרן, קענט איר דאס טון דורך שאפן א 'געפילטערטן פעקל' (Custom Study).")

        ############
    elif cmd == "menuCol":
        mw.form.menuCol.exec(QCursor.pos())
    elif cmd == "deckBrowser":
        mw.moveToState("deckBrowser")
    elif cmd == "add_deck":
        if _tut_step == 1:
            _tut_step = 2
            def _capture_did():
                global _tut_did
                if _tut_did == 0:
                    reg = [d for d in mw.col.decks.all()
                           if not mw.col.decks.is_filtered(d['id'])
                           and d['name'] not in ('Default', 'ברירת מחדל')]
                    if reg:
                        _tut_did = max(d['id'] for d in reg)
            from PyQt6.QtCore import QTimer as _QT
            _QT.singleShot(700, _capture_did)
        if op := add_deck_dialog(parent=mw):
            op.run_in_background()
    elif cmd == "FilteredDialog":
        aqt.dialogs.open("FilteredDeckConfigDialog", aqt.mw)
    elif cmd == "AddCard":
        mw.onAddCard()
    elif cmd == "onBrowse":
        mw.onBrowse()
    elif cmd == "menu_Help":
        mw.form.menuHelp.exec(QCursor.pos())  ############
    elif cmd == "browser_search":
        inBrowser(str(arg))
    elif cmd == "search_decks":
        in_deck_search(str(arg))
    ################
    elif cmd == "Add_deck_Card":
        if _tut_step == 2:
            _tut_step = 3
            _tut_did = int(arg)
        AddCard(DeckId(int(arg)))
        if _tut_step == 3:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(150, _tut_setup_add_cards)
    elif cmd == "browser_deck":
        deck = aqt.mw.col.decks.get(int(arg))
        deckName = deck['name']
        browser = aqt.dialogs.open("Browser", aqt.mw)
        browser.search_for(f"\"deck:{deckName}\"")
    elif cmd == "add_sub_deck":
        on_create(DeckId(int(arg)))
    ################
    elif cmd == "manual":
        files_map = {
            "explanation": "explanation.pdf",
            "write": "tutor1write.pdf",
            "full": "tutor3long.pdf",
            "maagar": "tutor_maagar.pdf"
        }
        if hasattr(mw, "open_pdf_file"):
            mw.open_pdf_file(files_map[arg])

        ################
    elif cmd == "v2upgradeinfo":
        showInfo("""
צייטפלאן מאטאר V3 איז דער מאטאר וואס באשטימט דעם סדר פון אנקי חזרות.<br />
        """, textFormat="rich", title="צייטפלאן מאטאר V3")
    elif cmd == "open":
        # סבב 9 — use Anki's official collection operation and only navigate
        # after it completes. The former synchronous legacy select()+immediate
        # onOverview path could leave the first deck selected in the session as
        # the persisted curDeck when Anki was closed/crashed soon afterwards.
        set_current_deck(
            parent=self.mw,
            deck_id=DeckId(int(arg)),
        ).success(lambda _changes: mw.onOverview()).run_in_background()
    elif cmd == "deck_paste":
        _handle_deck_paste(self, arg)
    elif cmd == "deck_select_error":
        showInfo(arg)
    elif cmd == "deck_delete_selected":
        # בעיה 11: מחיקת חפיסות מסומנות עם אישור משתמש
        _handle_deck_delete_selected(self, arg)
    elif cmd == "drag":
        parts = arg.split(",", 1)
        if len(parts) == 2:
            try:
                source_id = DeckId(int(parts[0]))
                target_id = DeckId(int(parts[1])) if parts[1].strip() else DeckId(0)
                reparent_decks(parent=self.mw, deck_ids=[source_id], new_parent=target_id).run_in_background()
            except ValueError:
                pass
    elif cmd == "forecast_early_review":
        days_ahead = int(arg)
        update_times()
        target_day = days_from_crt + days_ahead
        total_day = mw.col.db.scalar(
            f"SELECT COUNT(*) FROM cards WHERE queue IN (2,3) AND due = {target_day}"
        ) or 0
        early_count = mw.col.db.scalar(
            f"SELECT COUNT(*) FROM cards WHERE queue IN (2,3) AND due = {target_day} AND ivl >= 30"
        ) or 0
        target_date = datetime.date.fromtimestamp(start_of_anki_epoche_day) + datetime.timedelta(days=days_ahead)
        heb_idx = (target_date.weekday() + 1) % 7
        day_name = _FORECAST_HEB_DAYS[heb_idx]
        if early_count > 0:
            msg = (
                f"אום {day_name} (אין {days_ahead} טעג) ערווארט מען {total_day} קארטלעך פאר חזרה.\n\n"
                f"מען קען יעצט חזרן {early_count} קארטלעך מיט א מרווח פון מער ווי א חודש, כדי צו פארקלענערן דעם עול."
            )
            box = QMessageBox(mw)
            box.setWindowTitle("דערווארטער עול — פריערדיגע חזרה")
            box.setText(msg)
            btn_yes = box.addButton("חזר יעצט", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("אפזאגן", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() == btn_yes:
                filter_str = f"prop:due={days_ahead} prop:ivl>=30 -is:suspended -is:buried"
                create_temp_filtered_deck(filter_str)
        else:
            showInfo(
                f"אום {day_name} (אין {days_ahead} טעג) ערווארט מען {total_day} קארטלעך פאר חזרה.\n\n"
                f"אין דעם טאג זענען נישט דא קארטלעך מיט א מרווח פון מער ווי א חודש וואס מען קען פריער חזרן."
            )
    else:
        return _old(self, url)


def _v1_upgrade_message_wrapper(self, required: bool, _old) -> str:
    if not required:
        return _old(self, required)
    return """
<center>
<div class="callout">
    <div>
      אייער זאמלונג איז אפגעזיכערט מיט אן אלטן צייטפלאן מאטאר (V2). צייטפלאן מאטאר V3 איז די יעצטיגע ראטזאמע ווערסיע — זי פארבעסערט דעם חזרה אלגאריטם און איז נויטיג כדי דער צוגאב זאל ריכטיג ארבעטן.<br>
      ⚠️ <strong>אן א דערהיינטיגונג וועט דער פראגראם נישט ריכטיג ארבעטן.</strong> נוצן דעם צייטפלאן מאטאר V2 איז נאר מעגליך אין אלטע ווערסיעס פון Anki.<br>
      ✅ <strong>עס איז ראטזאם צו דריקן אויף "דערהיינטיגונג"</strong> — די פעולה איז אינגאנצן זיכער און וועט נישט אויסמעקן קיין שום דאטן.
    </div>
    <div>
      <button onclick='pycmd("v2upgrade")'>דערהיינטיגונג</button>
      <button onclick='pycmd("v2upgradeinfo")'>לערנט מער</button>
    </div>
</div>
</center>
"""


def updateRenderingMethods():
    DeckBrowser._body = _body
    DeckBrowser._renderDeckTree = wrap(DeckBrowser._renderDeckTree, renderDeckTree, 'around')
    DeckBrowser._render_deck_node = wrap(DeckBrowser._render_deck_node, render_deck_node, 'around')
    DeckBrowser._v1_upgrade_message = wrap(DeckBrowser._v1_upgrade_message, _v1_upgrade_message_wrapper, 'around')

    # עטיפה מותנית לסטטיסטיקות - אם מצב דחוס דלוק, מוחקים לוח שנה ומעגלים פינות
    def renderStatsWrapper(self, _old):
        # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
        config = get_config()
        if config.get("compact_mode", False):
            compact_js = """<script>
        document.body.classList.add('compact-mode');
        </script>"""
            return renderStats(self, _old) + compact_js
        return renderStats(self, _old)

    DeckBrowser._renderStats = wrap(DeckBrowser._renderStats, renderStatsWrapper, 'around')
    mw.show_menubar = wrap(mw.show_menubar, _show_menubar, 'after')
    # <<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>
    DeckBrowser._linkHandler = wrap(DeckBrowser._linkHandler, linkHandler, 'around')
    DeckBrowser._drawButtons = wrap(DeckBrowser._drawButtons, drawButtons, 'around')


# helpers
# מחיקת הסרגל העליון
def drawButtons(self, _old):
    self.bottom.web.stdHtml("""<style>
#outer{{
 height:0px;
}}
 </style>
      <script>
document.body.style.margin=0
</script>""", css=[], js=[], context=DeckBrowserBottomBar(self), )
    self.bottom.web.setFixedHeight(0)


mw.toolbar.web.setVisible(False)


def in_deck_search(find):
    if retlen("") == 0:
        showInfo(
            " עס זענען יעצט נישט דא קיין פראגעס אין דער זאמלונג. \n קוקט אין די מדריכים אינעם מעניו \"הילף\" פאר אינפארמאציע ווי צו נוצן דעם פראגראם גוט און ווירקזאם. \nפאר בירורים און פראגעס קען מען זיך ווענדן צום טעכנישן הילף אימעיל: anki4tora@gmail.com\nמיט הצלחה!")
        return
    global in_search, search_str, search_len
    search_len = 0
    in_search = True
    search_str = find
    mw.moveToState("deckBrowser")

    # search_str = ""
    # search_len = 0


def create_temp_filtered_deck(_filter_string):
    if retlen(_filter_string) > 0:
        if (old_f_deck := mw.col.decks.id_for_name(DECK_NAME_TODAY)) is not None:
            mw.col.decks.remove([old_f_deck])
        f_deck_id = mw.col.decks.new_filtered(DECK_NAME_TODAY)
        f_deck = mw.col.decks.current()
        f_deck['resched'] = True
        f_deck['delays'] = None
        # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
        config = get_config()
        order = config.get("filter_order", 1)
        f_deck['terms'] = [[_filter_string, 10000, order]]
        mw.col.decks.save(f_deck)
        mw.col.sched.rebuild_filtered_deck(f_deck_id)
        try:
            # #339: כניסה ישירה למבחן בלי מסך סקירה מחייבת startTimebox(), אחרת
            # check_timebox נופל על AttributeError: _startTime כשמוגדרת מגבלת זמן להיום.
            mw.col.startTimebox()
            mw.moveToState("review")
        except Exception as e:
            show_failure("דער לערן עקראן האט זיך נישט געעפנט. גייט צוריק צום פעקל עקראן און פרובירט דארט צו עפענען דעם פעקל.", e)
    else:
        # #128 — הודעות ריקות משוות לקבועים כדי לא להיפרד מנוסחת החיפוש של הסטטיסטיקות.
        if _filter_string == STATS_FILTER_TODAY:
            showInfo("איר האט פארענדיגט די חזרה פון די קארטלעך געפלאנט פאר היינט.")
        elif _filter_string == STATS_FILTER_OVERDUE:
            showInfo("עס זענען נישט דא קיין פארשפעטיגטע קארטלעך.")
        elif _filter_string == STATS_FILTER_ALL_DUE:
            showInfo("איר האט פארענדיגט די חזרה פון אלע קארטלעך וואס זענען געפלאנט געווען ביז יעצט.")
        else:
            pass


def save_conf(state, confVal):
    # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
    config = get_config()
    config[confVal] = state
    mw.addonManager.writeConfig(__name__, config)

# #188 — ריענון טיימר גלובלי מנוטרל ב-__init__.py (QTimer interception).
def too_much_overdue_alert_set(self: aqt.preferences.Preferences):
    # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
    config = get_config()

    # העדפת הבאנר בטאב הראשון, בהתאם למיקום שביקש המשתמש.
    from aqt.qt import QScrollArea
    first_page = self.form.tabWidget.widget(0)
    if isinstance(first_page, QScrollArea):
        first_page = first_page.widget()
    self.form.show_beta_banner = QCheckBox('ווייז דעם פרואוו ווערסיע באנער אויפן הויפט עקראן', first_page)
    self.form.show_beta_banner.setChecked(bool(config.get('show_beta_banner', True)))
    first_page.layout().addWidget(self.form.show_beta_banner)

    def on_beta_banner_toggle(checked):
        save_conf(checked, 'show_beta_banner')
        from .beta_feedback import refresh_banner_preference
        refresh_banner_preference()

    qconnect(self.form.show_beta_banner.toggled, on_beta_banner_toggle)

    # --- טאב מראה: מראה דף הבית ---
    # מדחה לאחר כל ה-setup_global hooks (כולל progress-bar שמוסיף שורה קשיחה ב-gridLayout_2)
    def add_appearance_items():
        row = self.form.gridLayout_2.rowCount()

        section_label_home = QLabel('אויסזען פונעם הויפט בלאט', mw)
        _font = section_label_home.font()
        _font.setBold(True)
        section_label_home.setFont(_font)
        self.form.gridLayout_2.addWidget(section_label_home, row, 0, 1, 2)

        row += 1
        self.form.auto_scroll = QCheckBox('גליט אויטאמאטיש צום לעצטן אויסגעקליבענעם פעקל', mw)
        self.form.auto_scroll.setChecked(config.get('auto_scroll', False))
        self.form.gridLayout_2.addWidget(self.form.auto_scroll, row, 0, 1, 2)
        qconnect(self.form.auto_scroll.stateChanged, lambda state, confVal='auto_scroll': save_conf(state, confVal))

        row += 1
        # #260 — ניסוח מצב דחוס בלי סוגריים סביב תיאור הסטטיסטיקות.
        self.form.compact_mode = QCheckBox('צוזאמענגעדריקטער מצב — הויפט עקראן מיט געדיכטע פעקלעך און קליינע אייקאנען', mw)
        self.form.compact_mode.setChecked(config.get('compact_mode', False))
        self.form.gridLayout_2.addWidget(self.form.compact_mode, row, 0, 1, 2)

        def on_compact_toggle(state):
            save_conf(state, 'compact_mode')
            mw.reset()

        qconnect(self.form.compact_mode.stateChanged, on_compact_toggle)

        row += 1
        hlayout = QHBoxLayout()
        label = QLabel("אויסשטעל גרייס אינעם צוזאמענגעדריקטן מצב (%):")
        self.form.compact_scale = QSpinBox(mw)
        self.form.compact_scale.setRange(60, 100)
        self.form.compact_scale.setValue(config.get('compact_scale', 100))
        hlayout.addWidget(label)
        hlayout.addWidget(self.form.compact_scale)
        hlayout.addStretch()
        self.form.gridLayout_2.addLayout(hlayout, row, 0, 1, 2)

        def on_scale_change(val):
            save_conf(val, 'compact_scale')
            # #188 — שינוי העדפה מרענן פעם אחת מיד, בלי מונה שממשיך לרענן את כל המסך.
            mw.reset()

        qconnect(self.form.compact_scale.valueChanged, on_scale_change)

        row += 1
        # #175 — ההעדפה שייכת לטאב מראה כי היא משנה את מראה המסך הראשי, לא את התנהגות החזרה.
        self.form.grayscale_mode = QCheckBox('הויפט עקראן אין גראע שאטירונגען (אן קאלירן)', mw)
        self.form.grayscale_mode.setChecked(config.get('grayscale_mode', False))
        self.form.gridLayout_2.addWidget(self.form.grayscale_mode, row, 0, 1, 2)

        def on_grayscale_toggle(state):
            save_conf(bool(state), 'grayscale_mode')
            mw.reset()

        qconnect(self.form.grayscale_mode.stateChanged, on_grayscale_toggle)

    from PyQt6.QtCore import QTimer
    QTimer.singleShot(0, add_appearance_items)

    # --- טאב חזרה: התראות ---
    section_label_alerts = QLabel('<b>מעלדונגען</b>', mw)
    self.form.verticalLayout_5.addWidget(section_label_alerts)

    self.form.alert_overdue = QCheckBox('ווייז א מעלדונג ווען מען הייבט אן די היינטיגע חזרה און מער ווי 50 פראגעס זענען פארשפעטיגט', mw)
    self.form.alert_overdue.setChecked(config['alert_overdue'])
    self.form.verticalLayout_5.addWidget(self.form.alert_overdue)
    qconnect(self.form.alert_overdue.stateChanged, lambda state, confVal='alert_overdue': save_conf(state, confVal))

    section_label_today_total = QLabel('<b>סך הכל קארטלעך פאר חזרה</b>', mw)
    self.form.verticalLayout_5.addWidget(section_label_today_total)

    today_total_description = QLabel(
        'די איינשטעלונגען גייען אן אויפן דרוק אויף "סך הכל קארטלעך פאר חזרה" אויפן הויפט עקראן און אויפן צייטווייליגן פעקל וואס מען שאפט דארט.',
        mw,
    )
    today_total_description.setWordWrap(True)
    self.form.verticalLayout_5.addWidget(today_total_description)

    self.form.filter_include_new = QCheckBox('נעם מיט נייע קארטלעך אין דער חזרה', mw)
    self.form.filter_include_new.setChecked(config.get('filter_include_new', False))
    self.form.verticalLayout_5.addWidget(self.form.filter_include_new)
    qconnect(
        self.form.filter_include_new.stateChanged,
        lambda state, confVal='filter_include_new': save_conf(bool(state), confVal),
    )

    filter_order_layout = QHBoxLayout()
    filter_order_label = QLabel('ווייז סדר אינעם צייטווייליגן פעקל:', mw)
    self.form.filter_order = QComboBox(mw)
    current_order = config.get('filter_order', 1)
    current_index = 0
    for index, (value, label) in enumerate(FILTER_ORDER_OPTIONS):
        self.form.filter_order.addItem(label, value)
        if value == current_order:
            current_index = index
    self.form.filter_order.setCurrentIndex(current_index)
    filter_order_layout.addWidget(filter_order_label)
    filter_order_layout.addWidget(self.form.filter_order)
    filter_order_layout.addStretch()
    self.form.verticalLayout_5.addLayout(filter_order_layout)

    def on_filter_order_change(index):
        save_conf(self.form.filter_order.itemData(index), 'filter_order')

    qconnect(self.form.filter_order.currentIndexChanged, on_filter_order_change)


    def on_scale_change(val):
        save_conf(val, 'compact_scale')
        # #188 — אין restart של timer; אם הפונקציה תופעל בעתיד היא תרענן ישירות פעם אחת.
        mw.reset()



aqt.preferences.Preferences.setup_global = wrap(aqt.preferences.Preferences.setup_global, too_much_overdue_alert_set,
                                                "after")


def alert_if_too_much_overdue(deck_name):
    today_str = str(datetime.date.today())
    if alert_overdue() and last_overdue_alert() != today_str and str(last_overdue_alert()) != today_str:
        save_conf(today_str, 'last_overdue_alert')
        overdue_count = len(mw.col.find_cards(deck_name))
        if overdue_count > 50:
            showWarning(
                f"אכטונג! יעצט זענען פארשפעטיגט {overdue_count} פראגעס. עס איז ראטזאם זיי צו פארענדיגן, כדי נישט צו פארגעסן דאס געלערנטע.\n \n(די מעלדונג קומט איינמאל א טאג און מען קען זי אויסשאלטן אינעם מעניו \"טעקע\">\"איינשטעלונגען\">\"חזרה\").")


def remove_temp_filtered_deck_in_main(state, _oldstate):
    if state == "deckBrowser":
        if (old_f_deck := mw.col.decks.id_for_name(DECK_NAME_TODAY)) is not None:
            mw.col.decks.remove([old_f_deck])
        try:  # hide reviewer edit bar
            mw.bottomWeb.setVisible(False)
            mw.reviewer.more_toolbar.hide()
        except AttributeError:
            pass
    elif state != "review":
        mw.bottomWeb.setVisible(False)
    else:
        mw.bottomWeb.setVisible(True)


gui_hooks.state_will_change.append(remove_temp_filtered_deck_in_main)

def _tut_on_note_added(note):
    global _tut_step
    if _tut_step == 3:
        _tut_step = 4
        _tut_clear_qt()
        from aqt.utils import tooltip
        tooltip(
            "<div style='direction:rtl;text-align:center;font-size:15px;line-height:1.8;'>"
            "&#127881; <b>א פראגע איז צוגעלייגט געווארן!</b><br>"
            "פארמאכט דעם פענסטער און גייט צוריק צום הויפט עקראן<br>"
            "כדי צו דריקן אויפן פעקל און אנהייבן צו לערנען."
            "</div>",
            period=6000
        )

gui_hooks.add_cards_did_add_note.append(_tut_on_note_added)
gui_hooks.add_cards_did_init.append(_tut_setup_add_cards)

def _tut_on_note_added(note):
    global _tut_step
    if _tut_step == 3:
        _tut_step = 4
        _tut_clear_qt()
        from aqt.utils import tooltip
        tooltip(
            "<div style='direction:rtl;text-align:center;font-size:15px;line-height:1.8;'>"
            "&#127881; <b>די פראגע איז מיט הצלחה צוגעלייגט געווארן!</b><br>"
            "מען קען צולייגן נאך פראגעס, אדער פארמאכן דעם פענסטער<br>"
            "און צוריקגיין צום הויפט עקראן."
            "</div>",
            period=7000
        )

gui_hooks.add_cards_did_add_note.append(_tut_on_note_added)
gui_hooks.add_cards_did_init.append(_tut_setup_add_cards)
gui_hooks.add_cards_did_init.append(_tut_setup_add_cards)
gui_hooks.reviewer_did_show_question.append(_tut_on_show_question)
gui_hooks.reviewer_did_show_answer.append(_tut_on_show_answer)
gui_hooks.reviewer_did_answer_card.append(_tut_on_answer_card)

sql_to_get_count_of_cards_n_decks = """
SELECT count(*) FROM cards
UNION
SELECT count(id) FROM decks """


# 104. Icon for finished but buried
def finished_but_buried_icon(num):
    return """
   <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
   class="bi bi-hourglass-split text-warning" viewBox="0 0 16 16">
   <path d="M2.5 15a.5.5 0 1 1 0-1h1v-1a4.5 4.5 0 0 1 2.557-4.06c.29-.139.443-.377.443-.59v-.7c0-.213-.154-.451-.443-.59A4.5 4.5 0 0 1 3.5 3V2h-1a.5.5 0 0 1 0-1h11a.5.5 0 0 1 0 1h-1v1a4.5 4.5 0 0 1-2.557 4.06c-.29.139-.443.377-.443.59v.7c0 .213.154.451.443.59A4.5 4.5 0 0 1 12.5 13v1h1a.5.5 0 0 1 0 1h-11zm2-13v1c0 .537.12 1.045.337 1.5h6.326c.216-.455.337-.963.337-1.5V2h-7zm3 6.35c0 .701-.478 1.236-1.011 1.492A3.5 3.5 0 0 0 4.5 13s.866-1.299 3-1.48V8.35zm1 0v3.17c2.134.181 3 1.48 3 1.48a3.5 3.5 0 0 0-1.989-3.158C8.978 9.586 8.5 9.052 8.5 8.351z"/>
   </svg>
   פארענדיגט
   """
