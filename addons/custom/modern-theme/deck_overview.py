import re
import time
from dataclasses import dataclass

import aqt
from anki.hooks import wrap
from aqt import gui_hooks
from aqt.operations.deck import add_deck_dialog
from aqt.overview import Overview, OverviewBottomBar
from aqt.theme import theme_manager
from aqt.utils import shortcut, tr
from PyQt6.QtGui import QCursor

from .config import *
from .deck_browser import DECK_NAME_TODAY, nav
from .utils import inBrowser, safe_division

current_epoch = None
start_of_anki_epoche_day = None
next_anki_day_start = None
days_from_crt = None


def update_times():
    global current_epoch, start_of_anki_epoche_day, next_anki_day_start, days_from_crt
    current_epoch = int(time.time())
    # באג timezone תוקן: day_cutoff ו-today מטפלים נכון באיזור זמן ובהגדרת rollover
    next_anki_day_start = mw.col.sched.day_cutoff
    start_of_anki_epoche_day = next_anki_day_start - 86400
    days_from_crt = mw.col.sched.today


addon = mw.addonManager.addonFromModule(__name__)
base = "/_addons/" + addon

# 105. Overflow auto for vertical scrolling
Overview._body = f"""
<center>
<style>
html {{
 direction: rtl;
}}
html, body {{
 height: 100%%;
 overflow-y: scroll !important;
}}
body {{
 direction: rtl;
}}
</style>
<body class="%(body_class)s" style="background-color: #f2f3f4;">
 <div class="container mt-3">
 <ul class="breadcrumb">
 %(parents)s
 </ul>
 </div>

 <div class="container w-auto">
 <div class="row my-4 h-75">
 <div class="text-center">
 <h1>%(deck)s</h1>
 <br>
 <div>%(desc)s<div>

 <div id="study_button" class="mb-1"></div>
 %(btn_buf)s
 </div>
 </div>
 </div>
 <div class="container bottom-0 position-absolute w-90" style="position: static !important;">

               %(progress)s

      <div class="row my-4 w-100">
      <div class="col-2 px-4 pb-3 mx-auto bg-light stats_row d-flex flex-column align-items-stretch justify-content-center overview-stats-container">
            %(table)s


            <table cellpadding="5">
            <tbody><tr><td align="center" valign="top" style="padding: 0px;">
            <table cellspacing="5">
            <tbody>

                <tr>
                    <td>פאר מארגן:</td>
                    <td>
                        <b>
                            <span class="text-info">%(tomorrow)s</span>
                        </b>
                    </td>
                </tr>

            </tbody></table>
            </td><td align="center">
            </td></tr></tbody></table>

        </div>

 <div class="col-7 px-4 pb-3 mx-auto bg-light stats_row d-flex flex-column align-items-stretch justify-content-between overview-stats-container" %(hide_cal)s>
 <div class="display-6"> קאלענדאר</div>
 <br>
 <div id="hm">
 </div>
 </div>
 <div class="col-2 px-4 pb-3 mx-auto bg-light stats_row d-flex flex-column align-items-stretch justify-content-between overview-stats-container">
 <div class="col plotlygroup" style="padding:2%%">
 <div id="my_dataviz"></div>
 </div>
 <div id="legend"></div>
 </div>

 </div>
 </div>
 </div>
</body>

<script>
      function check3DFunction() {{
      try {{
        child = document.querySelector(".rh-container")
        parent = document.querySelector("#hm")
        parent.appendChild(child);


  // רונדע עקן פאר פארשריט סרגלים
        // Get all progress bar elements within the "progress" container
          var progressBarElements = document.querySelectorAll(".progress");
          // Loop through each progress element
          progressBarElements.forEach((progressElement) => {{
              // Loop through the children of the progress element
              const children = progressElement.querySelectorAll(".progress-bar");
              // Loop through the progress bar elements
              for (var i = 0; i < children.length; i++) {{
                  var progressBar = children[i];

                  // Get the current width of the progress bar element
                  var width = progressBar.style.minWidth;

                  // Check if the width is not "0.0%%"
                  if (width !== "0%%") {{
                      // Add "border-radius: 10px" to the element's style
                      progressBar.style.borderTopRightRadius = "var(--bs-progress-border-radius)";
                      progressBar.style.borderBottomRightRadius = "var(--bs-progress-border-radius)";
                      break
                  }}
              }}
              for (var i = children.length-1; i >= 1; i--) {{
                  var progressBar = children[i];
                  // Get the current width of the progress bar element
                  var width = progressBar.style.minWidth;

                  // Check if the width is not "0.0%%"
                  if (width !== "0%%") {{
                      // Add "border-radius: 10px" to the element's style
                      progressBar.style.borderTopLeftRadius = "var(--bs-progress-border-radius)";
                      progressBar.style.borderBottomLeftRadius = "var(--bs-progress-border-radius)";
                      break;
                  }}
              }}
          }});
   }} catch (error) {{
    // The function '3d' does not exist yet, wait for 1 second and check again
      console.log(error);
    setTimeout(check3DFunction, 100);
  }}
 }}
check3DFunction();
        child = document.querySelector("#study")
        parent = document.querySelector("#study_button")
        parent.appendChild(child);


var currentElement = document.querySelectorAll('.overview-stats-container');
currentElement.forEach(element => {{
if ({1 if theme_manager.night_mode else 0}) {{
    element.classList.add("night-mode");
}}
}});

        </script>
</center>
%(pie_script)s
"""


def toggle_dark_mode(*args):
    if mw.state == "overview":
        if theme_manager.night_mode:
            mw.overview.web.eval(
                """
                var currentElement = document.querySelectorAll('.overview-stats-container');
                currentElement.forEach(element => {
                        element.classList.add("night-mode");
            });
            """)
        else:
            mw.overview.web.eval(
                """
                var currentElement = document.querySelectorAll('.overview-stats-container');
                currentElement.forEach(element => {
                element.classList.remove("night-mode");
            });
            """)


gui_hooks.theme_did_change.append(toggle_dark_mode)
gui_hooks.state_did_change.append(toggle_dark_mode)


@dataclass
class OverviewContent:
    parents: str
    deck: str
    shareLink: str
    desc: str
    # childs: str
    table: str
    # learned_todeay: int
    tomorrow: int
    btn_buf: str
    progress: str
    pie_script: str
    hide_cal: str  # Added
    body_class: str


def _renderPagemmmm(self: aqt.overview.Overview, _old) -> None:
    update_times()
    deck = self.mw.col.decks.current()
    deck_name = deck["name"]
    if deck_name == DECK_NAME_TODAY:
        mw.moveToState("deckBrowser")
        return
    parents = ""
    self.sid = deck.get("sharedFrom")
    for deck_ in deck_name.split("::")[:-1]:
        full_parent_name = deck_name[0: deck_name.find(deck_)] + deck_
        parents += f''' <li class="breadcrumb-item"><a href="#" onclick="pycmd('move_to_deck:{full_parent_name}'); return false">{deck_}</a></li>'''
    parents += f' <li class="breadcrumb-item active"><a>{deck_name.split("::")[-1]}</a></li>'
    if self.sid:
        self.sidVer = deck.get("ver", None)
        shareLink = '<a class=smallLink href="review">Reviews and Updates</a>'
    else:
        shareLink = ""

    links = [
        ["O", "opts", tr.actions_options()],
    ]
    is_dyn = mw.col.decks.current()["dyn"]
    if is_dyn:
        links.append(["R", "refresh", tr.actions_rebuild()])
        links.append(["E", "empty", tr.studying_empty()])
    else:
        links.append(["C", "studymore", tr.actions_custom_study()])
        links.append(["", "AddCard", "לייג צו א פראגע"])
    if mw.col.sched.have_buried():
        links.append(["U", "unbury", "ברענג צוריק פון באזייטיגן"])
    if not is_dyn:
        links.append(["", "description", tr.scheduling_description()])
    btn_buf = ""
    for b in links:
        if b[0]:
            b[0] = tr.actions_shortcut_key(val=shortcut(b[0]))
        btn_buf += """
    <button title="{}" onclick='pycmd("{}")'>{}</button>""".format(*tuple(
            b
        ))
    # showText(self._table(), copyBtn=True)
    try:
        table = self._table().replace("width=400", "")
    except (AttributeError, TypeError, AssertionError):
        # #180 — אם החפיסה הנוכחית כבר לא זמינה, חוזרים למסך הראשי במקום לתת ל-Anki להפיל AssertionError.
        mw.moveToState("deckBrowser")
        return
    if self.mw.col.sched._is_finished():
        remove_study_button_script = """ <script>
                                 let elem =document.getElementById("study_button");
                                 elem.remove()
                             </script>
                         """
    else:
        remove_study_button_script = ""
    sql_deck_name = re.escape(mw.col.decks.current()['name']).replace("'", "''").replace("::", "")
    days_from_crt_1 = days_from_crt + 1

    tomorrow: int = mw.col.db.first(f"""
    SELECT
 SUM(((c.queue in (2,3) and
                 (case when c.odue != 0 then c.odue else c.due end) = {days_from_crt_1}) or (c.queue in (1,4) and
                     (((case when c.odue != 0 then c.odue else c.due end) - {next_anki_day_start}) / 86400) = 1)))
                      AS tomorrow_count
FROM cards c where c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)') or
                        (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))""")[
        0]
    # if self.mw.col.sched._is_finished():
    # Hide calendar if empty stats (calculated in progress_line or pie_script usually, checking counts)


    card_count = mw.col.db.first(f"SELECT count() from cards where did = {deck['id']}")[0]
    hide_cal_style = 'style="display:none;"' if card_count == 0 else ''
    #     return
    content = OverviewContent(
        parents=str(parents)[1:-1],
        deck=deck_name.split("::")[-1],
        shareLink=shareLink,
        desc=self._desc(deck),
        # childs=childs(),
        table=table,
        tomorrow=tomorrow or 0,
        btn_buf=btn_buf,
        progress=progress_line(),
        pie_script=pie_script() + remove_study_button_script,
        hide_cal=hide_cal_style,
        # אישיו #414: קריאת קונפיג modern-theme עוברת דרך הקורא המוגן כדי שערך חסר לא יפיל את המסך.
        body_class="modern-grayscale" if get_config().get("grayscale_mode", False) else "",
    )
    gui_hooks.overview_will_render_content(self, content)
    self.web.stdHtml(
        self._body % content.__dict__,
        css=["css/overview.css"],
        js=["js/vendor/jquery.min.js"],
        context=self,
    )


#####################################################################################################################

def childs() -> str:
    tree = mw.col._backend.deck_tree(now=0)
    a = mw.col.decks.find_deck_in_tree(tree, mw.col.decks.current()["id"])
    return str(a)


def progress_line() -> str:
    update_times()
    sql_deck_name = re.escape(mw.col.decks.current()['name']).replace("'", "''").replace("::", "")

    sql = f"""
    SELECT
        --answered
            SUM(CASE
                    WHEN(c.id in (select cid from revlog where id >= {start_of_anki_epoche_day}000 and ease > 0)
                        and (c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)') or
                         (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))))
                    THEN 1
                    ELSE 0
                END),
        --shc_today
            SUM(CASE
                    WHEN ((c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)')
                    -- or (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))
                     )
        and (c.queue in (2,3)
        and (case when c.odue != 0 then c.odue else c.due end) = {days_from_crt}))
                    THEN 1
                    ELSE 0
                END),
        -- overdue
               SUM(CASE
                        WHEN (((c.queue IN (2, 3) AND c.due <= {days_from_crt}) OR (c.queue IN (1, 4) AND c.due <= {current_epoch + 1200}))
                        AND NOT ((c.queue IN (2, 3) AND c.due = {days_from_crt}) OR (c.queue IN (1, 4) AND ((c.due - {next_anki_day_start}) / 86400) = 0))
                        AND (c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)')))
                       THEN 1
                       ELSE 0
                   END),
        --new
            SUM(CASE
                    WHEN(c.queue = 0 and (c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)') or
                        (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))))
                    THEN 1
                    ELSE 0
                END)

        FROM cards c;
        """
    answered_today, shc_today, overdue_today, new_cards = mw.col.db.first(sql)

    answered_today = answered_today or 0
    shc_today = shc_today or 0
    overdue_today = overdue_today or 0
    new_cards = new_cards or 0

    total = answered_today + shc_today + overdue_today + new_cards
    _p = safe_division(100, total)

    def progress_width(count):
        if count == 0:
            return "max-width: 0% !important; min-width: 0% !important;"
        else:
            return f"width:{count * _p}%"

    new_cards_p = progress_width(new_cards)
    overdue_today_p = progress_width(overdue_today)
    shc_today_p = progress_width(shc_today)
    answered_today_p = progress_width(answered_today)

    html = f"""
    <div class="row my-4 w-100">
        <div class="progress" style="height: 1.5rem; padding-right: 0; padding-left: 0;">
                    <div class="progress-bar bg-success" style="{answered_today_p}">
                        <span class="inner inner-right" onclick='pycmd("revhm_browse:rated:1");' data-tt="ov-studied">
                            {answered_today if answered_today != 0 else ""}
                        </span>
                    </div>
                    <div class="progress-bar bg-today" style="{shc_today_p}">
                        <span class="inner inner-left" onclick='pycmd("filtoday")' data-tt="ov-sched">
                            {shc_today if shc_today != 0 else ""}
                        </span>
                    </div>
                    <div class="progress-bar bg-warning overflow-visible" style="{overdue_today_p}">
                        <span class="inner inner-center" onclick='pycmd("filoverdue")' data-tt="ov-overdue">
                            {overdue_today if overdue_today != 0 else ""}
                        </span>
                    </div>
                    <div class="progress-bar bg-primary" style="{new_cards_p}">
                        <span class="inner inner-center" onclick='pycmd("rev_new");' data-tt="ov-new">
                            {new_cards if new_cards != 0 else ""}
                        </span>
                    </div>
                </div>
        </div>
"""
    return html


def pie_script():
    update_times()
    sql_deck_name = re.escape(mw.col.decks.current()['name']).replace("'", "''").replace("::", "")

    res = mw.col.db.first(f"""
                    SELECT
                    SUM(CASE WHEN queue = 0 THEN 1 ELSE 0 END) AS new,
                    SUM(CASE WHEN queue = 1 THEN 1 ELSE 0 END) AS learn,
                    SUM(CASE WHEN queue = 2 THEN 1 ELSE 0 END) AS review,
                    SUM(CASE WHEN queue IN (-2, -3) THEN 1 ELSE 0 END) AS buried,
                    SUM(CASE WHEN queue = -1 THEN 1 ELSE 0 END) AS suspended,
                    SUM(CASE WHEN type IN (2, 3) AND ivl < 21 AND NOT (queue IN (-2, -3) OR queue = -1) THEN 1 ELSE 0 END) AS young,
                    SUM(CASE WHEN type IN (2, 3) AND ivl >= 21 AND NOT (queue IN (-2, -3) OR queue = -1) THEN 1 ELSE 0 END) AS mature
                FROM cards where did in (SELECT id FROM decks where name regexp '(?i)^{sql_deck_name}($|)')""")

    sql = f"""
        SELECT
            -- overdue
               SUM(CASE
                        WHEN (((c.queue IN (2, 3) AND c.due <= {days_from_crt}) OR (c.queue IN (1, 4) AND c.due <= {current_epoch + 1200}))
                        AND NOT ((c.queue IN (2, 3) AND c.due = {days_from_crt}) OR (c.queue IN (1, 4) AND ((c.due - {next_anki_day_start}) / 86400) = 0))
                        AND (c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)')))
                       THEN 1
                       ELSE 0
                   END),
            -- total cards
            SUM(CASE
                    WHEN (c.did IN (SELECT id FROM decks WHERE name regexp '(?i)^{sql_deck_name}($|)') )
                        OR (c.odid != 0 AND c.odid IN (SELECT id FROM decks  where name regexp '(?i)^{sql_deck_name}($|)') )
                    THEN 1
                    ELSE 0
                END),
            --tomorrow
            SUM(CASE
                    WHEN ((c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)')
                    -- or (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))
                     )
        and (c.queue in (2,3)
        and (case when c.odue != 0 then c.odue else c.due end) = {days_from_crt + 1}))
                    THEN 1
                    ELSE 0
                END),
        --today
            SUM(CASE
                    WHEN ((c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)')
                    -- or (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))
                     )
        and (c.queue in (2,3)
        and (case when c.odue != 0 then c.odue else c.due end) = {days_from_crt}))
                    THEN 1
                    ELSE 0
                END),
            --suspended
            SUM(CASE
                    WHEN ((c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))
                          and c.queue = -1)
                    THEN 1
                    ELSE 0
                END),
            --answered
            SUM(CASE
                    WHEN(c.id in (select cid from revlog where id >= {start_of_anki_epoche_day}000 and ease > 0)
                        and (c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)') or
                         (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))))
                    THEN 1
                    ELSE 0
                END),
           --new
            SUM(CASE
                    WHEN(c.type = 0 and (c.did in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)') or
                        (c.odid != 0 and c.odid in (select id from decks where name regexp '(?i)^{sql_deck_name}($|)'))))
                    THEN 1
                    ELSE 0
                END)

        FROM cards c;
         """
    # print(sql)
    overdue, all_deck_cards, tomorrow, today, suspended, studied_rescheduled, new_c = mw.col.db.first(sql)
    studied_rescheduled = studied_rescheduled or 0
    tomorrow = tomorrow or 0
    today = today or 0
    overdue = overdue or 0
    new_c = new_c or 0
    safe_division(100, (studied_rescheduled + new_c + today + overdue))

    new = res[0] or 0
    learn = res[1] or 0
    review = res[2] or 0
    buried = res[3] or 0
    suspended = res[4] or 0
    young = res[5] or 0
    mature = res[6] or 0
    # #274 — review כבר מיוצג דרך young/mature, ולכן לא נכנס שוב למכנה של אחוזי העוגה.
    total_vals = sum([new, learn, buried, suspended, young, mature])
    stats_script = """
        <script>
        let trycount= 0;
          function check3DFunction() {
          try {

    // set the dimensions and margins of the graph
        var w = 100;
        var h = 100;

        //var aColor = [
        //    "#2e7d32",
        //    "#85dd95",
        //    "#00838fcc",
        //    "#b02323",
        //    "#ffdc41",
        //    "#808080"
        //]
        var aColor = [
            "rgb(49, 163, 84)",
            "rgb(116, 196, 118)",
            "var(--state-new)",
            "var(--state-learn)",
            "rgb(255, 220, 65)",
            "grey"
        ]
        //""" + f"""
        //, , review, , , ,
        var dataset = [
            {{ "label": "בוגר", "value": "{mature}", "percent": "{round(safe_division(mature, total_vals) * 100, 2)}", "pycmd":'deck:current ("is:review" -"is:learn") AND "prop:ivl>=21"AND -("is:buried" OR "is:suspended")' }},
            {{ "label": "יונג", "value": "{young}", "percent": "{round(safe_division(young, total_vals) * 100, 2)}", "pycmd":'deck:current  ("is:review" AND -"is:learn") AND "prop:ivl<21"AND -("is:buried" OR "is:suspended")' }},
            {{ "label": "נייע", "value": "{new}", "percent": "{round(safe_division(new, total_vals) * 100, 2)}", "pycmd": 'deck:current "is:new"AND -("is:buried" OR "is:suspended")' }},
            {{ "label": "ביים לערנען", "value": "{learn}", "percent": "{round(safe_division(learn, total_vals) * 100, 2)}", "pycmd": 'deck:current is:learn' }},
            {{ "label": "אפגעשטעלט", "value": "{suspended}", "percent": "{round(safe_division(suspended, total_vals) * 100, 2)}", "pycmd": ' deck:current "is:suspended"' }},
            {{ "label": "באזייטיגט ביז מארגן", "value": "{buried}", "percent": "{round(safe_division(buried, total_vals) * 100, 2)}", "pycmd": ' deck:current "is:buried"' }},
        ];
        //""" + """
        var outerRadius = w / 2;
        var innerRadius = h / 3.5;
        var arc = d3.svg.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius);

        var pie = d3.layout.pie()
            .value(function (d) {
                return d.value;
            });

        var color = d3.scale.category20();

        var svg = d3.select("#my_dataviz")
            .append("svg")
            .attr("width", w)
            .attr("height", h);

        var arcs = svg.selectAll("g.arc")
            .data(pie(dataset))
            .enter()
            .append("g")
            .attr("class", "arc")
            .attr("transform", "translate(" + outerRadius + "," + outerRadius + ")");

        arcs.append("path")
            .attr("fill", function (d, i) {
                return aColor[i];
            })
            // .attr("id", function (d, i) {
            //     return "arc" + i;
            // })
            .attr("d", arc);

        arcs.append("text")
            .attr("transform", function (d) {
                return "translate(" + arc.centroid(d) + ")";
            })
            .attr("text-anchor", "middle")

            // .text(function (d) {
            //     if (d.value == "0") {
            //         return ""
            //     } else {
            //         return d.value;
            //     }
            // })
            ;
            // הילף טעקסט
        arcs.style("cursor", "pointer")
            .on("mouseover", function (d) {
                var tip = document.getElementById('global_tooltip');
                tip.innerHTML = `${d.data.label}:<br><b>${d.value}</b> קארטלעך<br>פראצענט פון אלע קארטלעך: <b>${d.data.percent}</b>`;
                tip.style.display = 'block';
                var selectthegraphs = $('.arc').not(this);
                d3.selectAll(selectthegraphs)
                    .style("opacity", .5);

                d3.select(this).style("stroke", "black");
            })
            .on("mousemove", function () {
                var tip = document.getElementById('global_tooltip');
                var x = d3.event.clientX + 15, y = d3.event.clientY + 15;
                if (x + 310 > window.innerWidth) x = d3.event.clientX - 175;
                if (y + tip.offsetHeight + 10 > window.innerHeight) y = d3.event.clientY - tip.offsetHeight - 10;
                tip.style.left = x + 'px';
                tip.style.top = y + 'px';
            })
            .on("mouseout", function () {
                document.getElementById('global_tooltip').style.display = 'none';

                var selectthegraphs = $('.arc').not(this);
                d3.selectAll(selectthegraphs)
                    .style("opacity", 1);
                d3.select(this).style("stroke", "none");
            })
            .on("click", function (d, i) {
                pycmd(`revhm_browse:${d.data.pycmd}`)
            });

    // ערקלערונג
            var legend = d3.select("#legend").append("svg")
                .attr("class", "legend")
                .attr("width", "220px").attr("viewBox", "0 0 220 168")
                .attr("height", "168px")

                .selectAll("g")
                .data(dataset)
                .enter().append("g")
                // .attr("transform", function (d, i) { return "translate(95," + i * 20 + ")"; });
                .attr("transform", function position(d,i) {
                var c = 1;   // number of columns
                var h = 26;  // legend entry height
                var w = 100; // legend entry width (so we can position the next column)
                var tx = 10; // tx/ty are essentially margin values
                var ty = 10;
                var x = 204;
                var y = Math.floor(i / c) * h + ty;
                return "translate(" + x + "," + y + ")";
    });

            legend.append("rect")
                .attr("width", 10)
                .attr("height", 10)
                .style("fill", function (d, i) {
                    return aColor[i];
                });

            legend.append("text")
                 .attr("x", -14)
                .attr("y", 8)
                .attr("dy", ".35em")
                .text(function (d, i) {return d["label"]; })
                .style("cursor", "pointer")
                .style("fill", "var(--bs-body-color)");


            legend.on("click", function (d, i) {
                   pycmd(`revhm_browse:${d.pycmd}`)
                        })
                    .on("mouseover", function (event) {
                        d3.select(this).style("text-decoration", "underline");
                    }
                )
                .on("mouseout", function (event) {
                    d3.select(this).style("text-decoration", "none");
                })

       } catch (error) {
        // The function '3d' does not exist yet, wait for 1 second and check again
          console.log(error);
          trycount+=1;
          if (trycount < 5) {
        setTimeout(check3DFunction, 100);
      }
      }
    }
    check3DFunction();
            </script> """
    return stats_script


####################################################################################################################3


Overview._body = nav("Overview") + Overview._body + """
<style>
    /* <!-- body{
        f"background: blue} -
        --> */
"""


def renderDeckBottom(self, _old):
    self.bottom.web.stdHtml("""<style>
    #outer{{
     height:0px;
    }}
     </style>
          <script>
    document.body.style.margin=0
</script>""",
                            css=[],
                            js=[],
                            context=OverviewBottomBar(self),
                            )




def _link_Handler(self, url: str, _old) -> bool:
    if ":" in url:
        (cmd, arg) = url.split(":", 1)
    else:
        cmd = url
    if cmd == "menuCol":
        mw.form.menuCol.exec(QCursor.pos())
    elif cmd == "deckBrowser":
        mw.moveToState("deckBrowser")
    elif cmd == "add_deck":
        if op := add_deck_dialog(parent=mw):
            op.run_in_background()
    elif cmd == "FilteredDialog":
        aqt.dialogs.open("FilteredDeckConfigDialog", aqt.mw)
    elif cmd == "AddCard":
        mw.onAddCard()
    elif cmd == "onBrowse":
        # 3 & 102. Open browser for current deck
        deckName = mw.col.decks.current()['name']
        inBrowser(f'"deck:{deckName}"')
    elif cmd == "Stats":
        mw.onStats()
    elif cmd == "menu_Help":
        mw.form.menuHelp.exec(QCursor.pos())
    elif cmd == "move_to_deck":
        dest = mw.col.decks.id_for_name(arg)
        mw.col.decks.select(dest)
        mw.moveToState("overview")
    elif cmd == "filtoday":
        inBrowser("deck:current prop:due=0")
    elif cmd == "filoverdue":
        inBrowser("deck:current is:due -prop:due=0")
    elif cmd == "filall":
        inBrowser("deck:current ((is:due -rated:1) or (is:learn is:due)) -is:suspended -is:buried")
    elif cmd == "filall_with_new":
        inBrowser("deck:current ((is:due -rated:1) or (is:learn is:due) or is:new) -is:suspended -is:buried")
    elif cmd == "rev_new":
        inBrowser("deck:current is:new -is:suspended -is:buried")
    elif cmd == "browser_search":
        inBrowser(str(arg))
    else:
        return _old(self, url)


def updateRenderingDeckOverview():
    Overview._renderPage = wrap(Overview._renderPage, _renderPagemmmm, "around")
    Overview._linkHandler = wrap(Overview._linkHandler, _link_Handler, 'around')
    Overview._renderBottom = wrap(Overview._renderBottom, renderDeckBottom, "around")
