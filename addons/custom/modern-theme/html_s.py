from __future__ import annotations

import re as _re

from aqt import mw


def _h(s):
    return _re.sub(r'\s{2,}', ' ', s).strip()

# SVG symbols – defined once in the page, referenced cheaply per deck row
_SVG_DEFS = (
    '<svg style="display:none" xmlns="http://www.w3.org/2000/svg">'
    '<symbol id="ic-empty" viewBox="0 0 16 16">'
    '<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>'
    '<path d="M11.354 4.646a.5.5 0 0 0-.708 0l-6 6a.5.5 0 0 0 .708.708l6-6a.5.5 0 0 0 0-.708z"/>'
    '</symbol>'
    '<symbol id="ic-done" viewBox="0 0 16 16">'
    '<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>'
    '</symbol>'
    '<symbol id="ic-filtered" viewBox="0 0 16 16">'
    '<path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zM3.5 5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1 0-1zM5 8.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm2 3a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 0 1h-1a.5.5 0 0 1-.5-.5z"/>'
    '</symbol>'
    '<symbol id="ic-due" viewBox="0 0 16 16">'
    '<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-8 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>'
    '</symbol>'
    '<symbol id="ic-overdue" viewBox="0 0 16 16">'
    '<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>'
    '</symbol>'
    '<symbol id="ic-buried" viewBox="0 0 16 16">'
    '<path d="M2.5 15a.5.5 0 1 1 0-1h1v-1a4.5 4.5 0 0 1 2.557-4.06c.29-.139.443-.377.443-.59v-.7c0-.213-.154-.451-.443-.59A4.5 4.5 0 0 1 3.5 3V2h-1a.5.5 0 0 1 0-1h11a.5.5 0 0 1 0 1h-1v1a4.5 4.5 0 0 1-2.557 4.06c-.29.139-.443.377-.443.59v.7c0 .213.154.451.443.59A4.5 4.5 0 0 1 12.5 13v1h1a.5.5 0 0 1 0 1h-11zm2-13v1c0 .537.12 1.045.337 1.5h6.326c.216-.455.337-.963.337-1.5V2h-7zm3 6.35c0 .701-.478 1.236-1.011 1.492A3.5 3.5 0 0 0 4.5 13s.866-1.299 3-1.48V8.35zm1 0v3.17c2.134.181 3 1.48 3 1.48a3.5 3.5 0 0 0-1.989-3.158C8.978 9.586 8.5 9.052 8.5 8.351z"/>'
    '</symbol>'
    '<symbol id="ic-btn-write" viewBox="-3 0 24 24">'
    '<rect fill="none" height="24" width="24"/>'
    '<path d="M3,10h11v2H3V10z M3,8h11V6H3V8z M3,16h7v-2H3V16z M18.01,12.87l0.71-0.71c0.39-0.39,1.02-0.39,1.41,0l0.71,0.71 c0.39,0.39,0.39,1.02,0,1.41l-0.71,0.71L18.01,12.87z M17.3,13.58l-5.3,5.3V21h2.12l5.3-5.3L17.3,13.58z"/>'
    '</symbol>'
    '<symbol id="ic-btn-browse" viewBox="-3 0 24 24">'
    '<path d="M0 0h24v24H0V0z" fill="none"/>'
    '<path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>'
    '</symbol>'
    '<symbol id="ic-btn-subdeck" viewBox="-3 -4 26 26">'
    '<path d="M0 0h24v24H0V0z" fill="none"/>'
    '<path d="M3 5H1v16c0 1.1.9 2 2 2h16v-2H3V5zm18-4H7c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V3c0-1.1-.9-2-2-2zm0 16H7V3h14v14z"/>'
    '</symbol>'
    '<symbol id="ic-btn-play" viewBox="0 0 16 16">'
    '<path d="M10.804 8 5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 0 1 0 1.392l-6.363 3.692C4.713 13.69 4 13.353 4 12.69V3.31c0-.653.713-1 1.233-.696l6.363 3.692z"/>'
    '</symbol>'
    '</svg>'
)

tooltip_style_fix = "z-index: 10000;;"


def _fullscreen_window_controls_html() -> str:
    # #281 — פקדי מסך מלא עברו ל-QWidget שמאזין לשינוי מצב החלון, כדי שיופיעו גם אחרי F11/תפריט בלי רינדור מחדש של ה-WebView.
    return ""


def nav(context: None | str = None):
    write = ""
    if context == "reviewer":
        curr_name = mw.col.decks.current()["id"] if mw.state == "review" else ""

        write = f"""
                    <li class="d-none d-lg-block" style="padding-top: 10px;">|</li>
            <li class="nav-item" href=# onclick='pycmd("Add_deck_Card:{curr_name}")'>
                <span class="nav-link statscursor" data-tt="nav-write">
                    <svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" height="24px"
                        viewBox="-3 0 24 24" width="24px" fill="var(--bs-body-color)">
                        <rect fill="none" height="24" width="24" />
                        <path
                            d="M3,10h11v2H3V10z M3,8h11V6H3V8z M3,16h7v-2H3V16z M18.01,12.87l0.71-0.71c0.39-0.39,1.02-0.39,1.41,0l0.71,0.71 c0.39,0.39,0.39,1.02,0,1.41l-0.71,0.71L18.01,12.87z M17.3,13.58l-5.3,5.3V21h2.12l5.3-5.3L17.3,13.58z" />
                    </svg> <span class="d-none d-lg-inline">שרייבט א פראגע</span>
                    </span>
            </li>"""
    return f"""

<nav class="navbar navbar-expand fixed-top bg-body-tertiary w-100 anki-navbar sticky-top"   id="navbar">
    <div class="container-fluid p-0">
        <ul class="navbar-nav mb-auto" style="list-style-type: none; padding-inline-start:0px; margin-bottom:0px;">
            <li class="nav-item" href=# onclick='pycmd("menuCol")'>
                <span class="nav-link statscursor" data-tt="nav-menu">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" viewBox="0 0 24 24"
                        fill="var(--bs-body-color)">
                        <path d="M0 0h24v24H0V0z" fill="none" />
                        <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
                    </svg>
                    <span class="d-none d-lg-inline">מעניו</span>
                </span>
            </li>
            <li class="d-none d-lg-block" style="padding-top: 10px;">|</li>
            <li class="nav-item" href=# onclick='pycmd("deckBrowser")'>
                <span class="nav-link statscursor" data-tt="nav-home">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" viewBox="-2 0 24 24"
                        fill="var(--bs-body-color)">
                        <path d="M0 0h24v24H0V0z" fill="none" />
                        <path
                            d="M19 15v4H5v-4h14m1-2H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1v-6c0-.55-.45-1-1-1zM7 18.5c-.82 0-1.5-.67-1.5-1.5s.68-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM19 5v4H5V5h14m1-2H4c-.55 0-1 .45-1 1v6c0 .55.45 1 1 1h16c.55 0 1-.45 1-1V4c0-.55-.45-1-1-1zM7 8.5c-.82 0-1.5-.67-1.5-1.5S6.18 5.5 7 5.5s1.5.68 1.5 1.5S7.83 8.5 7 8.5z" />
                    </svg>
                    <span class="d-none d-lg-inline ">הויפט עקראן</span>
                    </span>
            </li>
           <!-- <li class="nav-item" href=# onclick='pycmd("add_deck")'>
            <li class="d-none d-lg-block" style="padding-top: 10px;">|</li>
                <span class="nav-link statscursor tooltip_bar">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20px" height="20px" viewBox="-3 -4 26 26"
                        fill="var(--bs-body-color)">
                        <path d="M0 0h24v24H0V0z" fill="none" />
                        <path
                            d="M3 5H1v16c0 1.1.9 2 2 2h16v-2H3V5zm18-4H7c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V3c0-1.1-.9-2-2-2zm0 16H7V3h14v14z" />
                    </svg>
                    <span class="d-none d-lg-inline">שאף א פעקל</span>
                    <span class="tooltiptext tooltip-bottom">שאף א נייעם נושא.<br>מען דארף שאפן א נושא כדי די פראגעס אין דער זאמלונג זאלן זיין מסודר, ווי ש״ס, הלכה.</span> </span>
            </li>--->
            {write}
            <li class="d-none d-lg-block" style="padding-top: 10px;">|</li>
            <li class="nav-item" href=# onclick='pycmd("onBrowse")'>
                <span class="nav-link statscursor" data-tt="nav-browse">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" viewBox="-3 0 24 24"
                        fill="var(--bs-body-color)">
                        <path d="M0 0h24v24H0V0z" fill="none" />
                        <path
                            d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
                    </svg>
                    <span class="d-none d-lg-inline">בלעטערט דורך קארטלעך</span>
                    </span>
            </li>
            <li class="d-none d-lg-block" style="padding-top: 10px;">|</li>
            <li class="nav-item" href=# onclick='pycmd("FilteredDialog")'>
                <span class="nav-link statscursor" data-tt="nav-filter">
                    <svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" width="24px" height="24px"
                        viewBox="0 0 24 24" fill="var(--bs-body-color)">
                        <g>
                            <path d="M0,0h24 M24,24H0" fill="none" />
                            <path
                                d="M7,6h10l-5.01,6.3L7,6z M4.25,5.61C6.27,8.2,10,13,10,13v6c0,0.55,0.45,1,1,1h2c0.55,0,1-0.45,1-1v-6 c0,0,3.72-4.8,5.74-7.39C20.25,4.95,19.78,4,18.95,4H5.04C4.21,4,3.74,4.95,4.25,5.61z" />
                            <path d="M0,0h24v24H0V0z" fill="none" />
                        </g>
                    </svg>
                    <span class="d-none d-lg-inline">פילטערט פראגעס</span>
                    </span>
            </li>
            <li class="d-none d-lg-block" style="padding-top: 10px;">|</li>
            <li class="nav-item" href=# onclick='pycmd("Stats")'>
                <span class="nav-link statscursor" data-tt="nav-stats">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" viewBox="0 -2 24 24"
                        fill="var(--bs-body-color)">
                        <path d="M0 0h24v24H0V0z" fill="none" />
                        <path d="M5 9.2h3V19H5V9.2zM10.6 5h2.8v14h-2.8V5zm5.6 8H19v6h-2.8v-6z" />
                    </svg>
                    <span class="d-none d-lg-inline">ווייז סטאטיסטיק</span>
                </span>
            </li>
            <li class="d-none d-lg-block" style="padding-top: 10px;">|</li>
            <li class="nav-item" href=# onclick='pycmd("menu_Help")'>
                <span class="nav-link statscursor" data-tt="nav-help">
                    <svg xmlns="http://www.w3.org/2000/svg" height="22px" viewBox="-3 -2 26 26" width="22px"
                        fill="var(--bs-body-color)">
                        <path d="M0 0h24v24H0V0z" fill="none" />
                        <path
                            d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z" />
                    </svg>
                    <span class="d-none d-lg-inline">הילף</span>
                </span>
            </li>
        </ul>
        """ + """
        <form class="d-flex me-auto" role="search">
            <input id="searchcards" type="text"
                style="background:transparent; border-radius: 20px; color: var(--bs-body-color); direction: rtl; text-align: right;"
                placeholder="זוכן קארטלעך..." value="" class="form-control me-2" size="20">
        </form>
        <script>
            var input = document.getElementById("searchcards");
            input.addEventListener("keypress", function (event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    pycmd("browser_search:" + this.value)
                    this.value = ""
                }
            });

        </script>
    </div>
</nav>
""" + _fullscreen_window_controls_html()


# **-deck_table-**
deck_tree_top = """

<script>
    function fill_deck_btns(root) {{
        var scope = root || document;
        scope.querySelectorAll('.dbtns:not([data-f])').forEach(function(el) {{
            var d = el.closest('[data-deck-id]').dataset.deckId;
            // #85b — data-cmd האלט דעם באפעל; event delegation אויף .dbtns באארבעט דעם דרוק.
            el.innerHTML = `<span data-tt="btn-write" data-cmd="Add_deck_Card:${{d}}"><svg><use href="#ic-btn-write"/></svg></span><span data-tt="btn-browse" data-cmd="browser_deck:${{d}}"><svg><use href="#ic-btn-browse"/></svg></span><span data-tt="btn-subdeck" data-cmd="add_sub_deck:${{d}}"><svg class="sm"><use href="#ic-btn-subdeck"/></svg></span><span data-tt="btn-test" data-cmd="open:${{d}}"><svg class="xs"><use href="#ic-btn-play"/></svg></span>`;
            el.dataset.f = '1';
        }});
    }}
    // #85b — event delegation: א דרוק אויפן קנעפל deck → pycmd, אנשטאט inline onclick אויף יעדן קנעפל.
    document.addEventListener('click', function(e) {{
        var btn = e.target.closest && e.target.closest('.dbtns [data-cmd]');
        if (!btn) return;
        e.stopPropagation();
        e.preventDefault();
        pycmd(btn.dataset.cmd);
    }}, true);
</script>
 <!-- #280/#282 — דער פעקל שפאלט איז נישט sticky, אויסגעריכט צום סטאטיסטיק שפאלט, און גליט אינעווייניג ווען מען דארף. -->
 <div class="{col_class} modern-deck-tree-panel" style="margin-top: 4px;">
            <div class="stats_row modern-deck-toolbar-row" style="margin-top: 0;">
            <div class="top-level-drag-row">
                <div class="accordion-item" style="border-radius: 20px 20px 0px 0px; padding: 0.2rem!important;">
                    <div class="d-flex align-items-center gap-1 flex-wrap">
                         <!-- געווענליכער מצב: א קנעפל אריינצוגיין אינעם אויסוואל מצב (☑) -->
                         <!-- אויסוואל/אריינלייג מצב: אן אפזאג קנעפל — אלעמאל זעבאר -->
                         <button id="btn-select-mode" onclick='enterSelectMode()' class="btn btn-sm deck-toolbar-btn deck-mode-normal" title="אויסקלייבן פעקלעך צו שניידן/קאפירן">
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
                                <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
                            </svg>
                         </button>
                         <button id="btn-exit-mode" onclick='exitSelectMode()' class="btn btn-sm deck-toolbar-btn deck-mode-select-paste" title="אפזאגן">
                            ✘ אפזאגן
                         </button>
                         <!-- געווענליכער מצב: שאפן א פעקל -->
                         <button id="btn-add-deck" href=# onclick='pycmd("add_deck")' class="btn btn-sm deck-toolbar-btn deck-mode-normal">
                            <span class="statscursor" data-tt="btn-add-deck">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20px" height="20px" viewBox="-3 -4 26 26"
                                    fill="var(--bs-body-color)">
                                    <path d="M0 0h24v24H0V0z" fill="none" />
                                    <path
                                        d="M3 5H1v16c0 1.1.9 2 2 2h16v-2H3V5zm18-4H7c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V3c0-1.1-.9-2-2-2zm0 16H7V3h14v14z" />
                                </svg>
                                <span>שאף א פעקל</span>
                            </span>
                         </button>
                         <!-- אויסוואל מצב: קאפירן -->
                         <!-- #129 follow-up: די אויסוואל מצב קנעפלעך האבן דעם אלגעמיינעם אויסשטעל deck-toolbar-btn. -->
                         <!-- #191 — די פעולה קנעפלעך אינעם אויסוואל מצב באקומען א באזונדערן טעקסט/ראם קאליר און האלטן דעם אויסשטעל פונעם שאפן א פעקל קנעפל. -->
                         <button id="btn-copy" onclick='deckSelectAction("copy")' class="btn btn-sm deck-toolbar-btn deck-toolbar-action-copy deck-mode-select" title="קאפיר">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6zM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1H2z"/>
                            </svg> קאפיר
                         </button>
                         <!-- אויסוואל מצב: שניידן -->
                         <!-- #191 — שניידן באקומט א באזונדערן פעולה קאליר, כדי צו אונטערשיידן פון קאפירן. -->
                         <button id="btn-cut" onclick='deckSelectAction("cut")' class="btn btn-sm deck-toolbar-btn deck-toolbar-action-cut deck-mode-select" title="שנייד">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M3.5 3.5c-.614-.884-.074-1.962.858-2.5L8 7.226 11.642 1c.932.538 1.472 1.616.858 2.5L8.81 8.61l1.556 2.661a2.5 2.5 0 1 1-.794.637L8 9.73l-1.572 2.177a2.5 2.5 0 1 1-.794-.637L7.19 8.61 3.5 3.5zm2.5 10a1.5 1.5 0 1 0-3 0 1.5 1.5 0 0 0 3 0zm7 0a1.5 1.5 0 1 0-3 0 1.5 1.5 0 0 0 3 0z"/>
                            </svg> שנייד
                         </button>
                         <!-- פראבלעם 11: קאפירן נאר דעם פעקל סטרוקטור (אן פראגעס) -->
                         <!-- #191 — דער סטרוקטור באקומט א קאלירטן ראם און טעקסט, אן צו טוישן דעם קנעפל פארמאט. -->
                         <button id="btn-copy-structure" onclick='deckSelectAction("copy_structure")' class="btn btn-sm deck-toolbar-btn deck-toolbar-action-structure deck-mode-select" title="קאפיר נאר דעם סטרוקטור">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M.54 3.87.5 3a2 2 0 0 1 2-2h3.672a2 2 0 0 1 1.414.586l.828.828A2 2 0 0 0 9.828 3h3.982a2 2 0 0 1 1.992 2.181l-.637 7A2 2 0 0 1 13.174 14H2.826a2 2 0 0 1-1.991-1.819l-.637-7a2 2 0 0 1 .342-1.31zM2.19 4a1 1 0 0 0-.996 1.09l.637 7a1 1 0 0 0 .995.91h10.348a1 1 0 0 0 .995-.91l.637-7A1 1 0 0 0 13.81 4H2.19zm4.69-1.707A1 1 0 0 0 6.172 2H2.5a1 1 0 0 0-1 .981l.006.139C1.72 3.042 1.95 3 2.19 3h5.396l-.707-.707z"/>
                            </svg> סטרוקטור
                         </button>
                         <!-- פראבלעם 11: אויסמעקן אנגעצייכנטע פעקלעך (מיט באשטעטיגונג) -->
                         <!-- #191 — אויסמעקן איז אנגעצייכנט מיט א שטענדיגן ווארענונג קאליר, אבער בלייבט אינעם זעלבן קנעפל סטיל. -->
                         <button id="btn-delete-selected" onclick='deckSelectDelete()' class="btn btn-sm deck-toolbar-btn deck-toolbar-action-delete deck-mode-select" title="מעק אויס אנגעצייכנטע פעקלעך">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3h11V2h-11v1z"/>
                            </svg> מעק אויס
                         </button>
                         <!-- אריינלייג מצב: מעלדונג -->
                         <span id="paste-info" class="deck-mode-paste" style="font-size: 13px; color: var(--bs-success); font-weight:500; padding: 4px 8px;"></span>
                """
reset_search_button = """
                <button class="btn btn-sm deck-toolbar-btn deck-mode-normal"
                onclick="return pycmd('deckBrowser')">שטעל צוריק די זוכעניש</button>
         """
search_row = """
                        <input id="searchdecks"
                        type="text"
                        size="10"
                        style="background:transparent; border-radius: 20px; color: var(--bs-body-color); direction: rtl; display: inline-block;
                            text-align: right; font-size: 12px; width: 30%; margin-inline-start: auto"
                        placeholder="זוכן פעקלעך..."
                        value=""
                        class="form-control"
                        >

                         <script>
                            var input = document.getElementById("searchdecks");
                            input.addEventListener("keypress", function(event) {
                                if (event.key === "Enter") {
                                    event.preventDefault();
                                    pycmd("search_decks:" + this.value)
                                    this.value = ""
                              }
                            });

                            /* ====== אויסוואל מצב פאר פעקלעך - State Machine ====== */
                            /* מעגליכע מצבים: 'normal' | 'select' | 'paste' */
                            var _mode = 'normal';
                            var _clipboardAction = null;
                            var _selectedDeckIds = [];

                            function _setMode(mode) {
                                _mode = mode;
                                document.body.setAttribute('data-deck-mode', mode);
                            }

                            function onDeckClick(event, el) {
                                var dk = typeof el !== 'string' && el.closest && el.closest('[data-deck-id]');
                                var deckId = dk ? dk.dataset.deckId : el;
                                if (_mode === 'paste') {
                                    event.stopPropagation();
                                    event.preventDefault();
                                    pycmd('deck_paste:' + _clipboardAction + ':' + deckId + ':' + _selectedDeckIds.join(','));
                                    return false;
                                }
                                if (_mode === 'select') {
                                    event.stopPropagation();
                                    event.preventDefault();
                                    var cb = dk
                                        ? dk.querySelector('.deck-select-cb')
                                        : document.querySelector('.deck[data-deck-id="' + deckId + '"] .deck-select-cb');
                                    if (cb) cb.checked = !cb.checked;
                                    return false;
                                }
                                if (event.shiftKey) return pycmd('select:' + deckId);
                                return pycmd('open:' + deckId);
                            }

                            function enterSelectMode() {
                                _selectedDeckIds = [];
                                document.querySelectorAll('.deck-select-cb').forEach(function(cb) { cb.checked = false; });
                                _setMode('select');
                            }

                            function exitSelectMode() {
                                _selectedDeckIds = [];
                                _clipboardAction = null;
                                document.querySelectorAll('.deck-select-cb').forEach(function(cb) { cb.checked = false; });
                                _setMode('normal');
                            }

                            function deckSelectAction(action) {
                                _selectedDeckIds = [];
                                document.querySelectorAll('.deck-select-cb:checked').forEach(function(cb) {
                                    _selectedDeckIds.push(cb.closest('[data-deck-id]').dataset.deckId);
                                });
                                if (_selectedDeckIds.length === 0) {
                                    pycmd('deck_select_error:קיין פעקלעך זענען נישט אויסגעקליבן געווארן');
                                    return;
                                }
                                _clipboardAction = action;
                                // פראבלעם 11: א פאסיג קעפל פארן סארט אריינלייג פעולה (שניידן / קאפירן / קאפירן דעם סטרוקטור)
                                var infoText = 'צו קאפירן';
                                if (action === 'cut') infoText = 'צו שניידן';
                                else if (action === 'copy_structure') infoText = 'צו קאפירן דעם סטרוקטור (אן פראגעס)';
                                document.getElementById('paste-info').textContent = 'דריקט אויפן פעקל וואו איר ווילט אריינלייגן ' + infoText;
                                _setMode('paste');
                            }

                            // פראבלעם 11: אויסמעקן אנגעצייכנטע פעקלעך נאכן באניצער באשטעטיגונג
                            function deckSelectDelete() {
                                _selectedDeckIds = [];
                                document.querySelectorAll('.deck-select-cb:checked').forEach(function(cb) {
                                    _selectedDeckIds.push(cb.closest('[data-deck-id]').dataset.deckId);
                                });
                                if (_selectedDeckIds.length === 0) {
                                    pycmd('deck_select_error:קיין פעקלעך זענען נישט אויסגעקליבן געווארן');
                                    return;
                                }
                                pycmd('deck_delete_selected:' + _selectedDeckIds.join(','));
                            }

                            /* ====== Mouse-based drag-and-drop (HTML5 DnD ארבעט נישט אין-Qt WebEngine) ====== */
                            var _dd = { active: false, sourceId: null, sourceName: null,
                                        ghost: null, lastHighlight: null, startX: 0, startY: 0 };

                            function _deckOf(el) {
                                var dk = el && el.closest && el.closest('[data-deck-id]');
                                if (!dk) return null;
                                return { id: dk.dataset.deckId, name: dk.dataset.deckName,
                                         row: dk.querySelector(':scope > .accordion-button') };
                            }

                            document.addEventListener('mousedown', function(e) {
                                if (_mode !== 'normal') return;
                                var info = _deckOf(e.target);
                                if (!info) return;
                                _dd.sourceId   = info.id;
                                _dd.sourceName = info.name || info.id;
                                _dd.startX = e.clientX;
                                _dd.startY = e.clientY;
                                _dd.active = false;
                            }, true);

                            document.addEventListener('mousemove', function(e) {
                                if (!_dd.sourceId) return;
                                var dx = e.clientX - _dd.startX, dy = e.clientY - _dd.startY;
                                if (!_dd.active && Math.abs(dx) + Math.abs(dy) > 6) {
                                    _dd.active = true;
                                    if (document.body) {
                                        var g = document.createElement('div');
                                        g.style.cssText = 'position:fixed;pointer-events:none;z-index:9999;'
                                            + 'background:var(--bs-body-bg,#fff);color:var(--bs-body-color);'
                                            + 'border:1px solid var(--bs-border-color,#ccc);border-radius:8px;'
                                            + 'padding:6px 14px;max-width:300px;'
                                            + 'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
                                            + 'font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.25);';
                                        g.textContent = '↳ ' + _dd.sourceName;
                                        document.body.appendChild(g);
                                        _dd.ghost = g;
                                    }
                                }
                                if (!_dd.active) return;
                                if (_dd.ghost) {
                                    _dd.ghost.style.left = (e.clientX + 14) + 'px';
                                    _dd.ghost.style.top  = (e.clientY - 10) + 'px';
                                    _dd.ghost.style.visibility = 'hidden';
                                }
                                var el = document.elementFromPoint(e.clientX, e.clientY);
                                if (_dd.ghost) _dd.ghost.style.visibility = '';
                                var info = _deckOf(el);
                                var targetRow = info && info.row;
                                if (_dd.lastHighlight && _dd.lastHighlight !== targetRow)
                                    _dd.lastHighlight.style.outline = '';
                                if (info && info.id !== _dd.sourceId && targetRow) {
                                    targetRow.style.outline = '2px solid var(--bs-primary,#0d6efd)';
                                    _dd.lastHighlight = targetRow;
                                } else {
                                    _dd.lastHighlight = null;
                                }
                            }, true);

                            document.addEventListener('mouseup', function(e) {
                                if (!_dd.sourceId) return;
                                if (_dd.ghost) { _dd.ghost.remove(); _dd.ghost = null; }
                                if (_dd.lastHighlight) { _dd.lastHighlight.style.outline = ''; }
                                if (_dd.active) {
                                    var el = document.elementFromPoint(e.clientX, e.clientY);
                                    var info = _deckOf(el);
                                    if (info && info.id !== _dd.sourceId)
                                        pycmd('drag:' + _dd.sourceId + ',' + info.id);
                                    else if (!info)
                                        pycmd('drag:' + _dd.sourceId + ',');
                                }
                                _dd.sourceId = null; _dd.active = false; _dd.lastHighlight = null;
                            }, true);
                         </script>
                    </div>                    </div>

                    </div>"""
deck_tree_buttom = """
                <div class="accordion-item" style="border-radius: 0px 0px 20px 20px;">
                    <div class="ms-3" style="text-align: end;">
                        &nbsp;&nbsp;
                        <span><span class="rounded-circle dots bg-secondary"></span> חזרות וואס מען האט היינט געמאכט </span>
                        <span><span class="rounded-circle dots bg-new"></span> נייע </span>
                        <span><span class="rounded-circle dots bg-learn"></span> ביים לערנען </span>
                        <span class="tooltip_bar" data-tt="db-pb" data-n-label="ביים לערנען — די חזרה צייט איז נאך נישט געקומען" data-tooltip-pos="top"><span class="rounded-circle dots pending-learning-dot"></span> ביים לערנען — עס איז נאך נישט צייט </span>
                        <span><span class="rounded-circle dots bg-review"></span> חזרה </span>
                     </div>
                 </div>
        </div>
        </div>
        </div>
        """
deck_browser_new_user = """
<div style="text-align:center; direction:rtl; padding:28px 18px;">
  <div class="Firstrunlabel">ברוכים הבאים צום אנקי פראגראם צו געדענקען תורה!</div>
  <br>
  <div style="font-size:17px; font-weight:500; font-family:SecularOne-Regular; color:var(--fg); max-width:500px; margin:0 auto; line-height:1.8;">
    שאפט א פעקל (נושא), לייגט צו פראגעס און ענטפערס, און דריקט אויפן פעקל צו אנהייבן חזרן לויט דער אנקי שיטה.
  </div>
  <br>
  <div onclick="pycmd('tut_start')"
       style="display:inline-block; background:#27ae60; color:#fff; border-radius:10px;
              padding:12px 30px; font-size:17px; cursor:pointer;
              font-family:SecularOne-Regular,sans-serif; font-weight:600;
              box-shadow:0 4px 14px rgba(39,174,96,.45); user-select:none; line-height:normal;">
    &#9654;&nbsp; א מדריך טריט פאר טריט
  </div>
  <br><br>
  <div style="color:var(--fg); font-size:13px;">
    פאר אויספירליכע מדריכים — עפנט דעם מעניו <b>"הילף"</b>
  </div>
</div>
"""

# icons – use SVG symbols (defined once in _SVG_DEFS, injected into deck_tree_top)
empty_icon    = '<svg width="16" height="16" fill="currentColor" class="bi bi-slash-circle"><use href="#ic-empty"/></svg> ליידיג'
finished_icon = '<svg width="16" height="16" fill="currentColor" class="bi bi-check-circle-fill text-success"><use href="#ic-done"/></svg> פארענדיגט!'
filtered_icon = '<svg width="16" height="16" fill="currentColor" class="bi bi-filter-circle-fill text-primary"><use href="#ic-filtered"/></svg> געפילטערט'
due_icon      = '<svg width="16" height="16" fill="currentColor" class="bi bi-record-circle-fill text-warning"><use href="#ic-due"/></svg> פון היינט'


def overdue_icon(num):
    return '<svg width="16" height="16" fill="currentColor" class="bi bi-exclamation-circle-fill text-danger"><use href="#ic-overdue"/></svg> פארשפעטיגט'

# buttons_for_deck: lightweight placeholder; filled by fill_deck_btns() JS on the client
deck_row_buttons_only = '<div class="col-2 deck-buttons-col dbtns"></div>'
# minify all static per-node HTML at module load (one-time cost, saves memory and JS eval time)
deck_tree_buttom = _h(deck_tree_buttom)
deck_tree_buttom += '<script>fill_deck_btns();</script>'
deck_browser_new_user = _h(deck_browser_new_user)
reset_search_button = _h(reset_search_button)
deck_tree_top = _SVG_DEFS + deck_tree_top

# stats_column
stats_conatiner_first_row = """<div class="col-sm-6 col-12 mb-4 modern-stats-col" style="padding-left: calc(var(--bs-gutter-x) * .5); margin-top: 4px; padding-right: 8px;">
        <!-- ערשטע שורה -->
        <div
            class="col px-4 pb-3 mb-1  stats_row d-flex flex-column justify-content-between">
            <!-- <span class="display-6 text-start" style="margin-right: auto!important; cursor:pointer">dashboard...</span> -->
            <span class="display-6 ms-0" style="cursor:pointer;" onclick='on_day_review(event, this)' oncontextmenu='pycmd("stat_context"); return false;' data-tt="st-total"> סך הכל קארטלעך פאר חזרה:{total}
            </span>
            {forecast_alert}
 {time_stats}
            <span class="display-1 mb-2 ms-0" style="cursor:pointer; font-size: 1.5rem;" onclick='pycmd("browser_search: added:1")' data-tt="st-added"> היינט צוגעלייגט:{added}
            </span>
            <!-- <p>progress...</p> -->
            <div class="progress" style="height: 1.5rem;">
                <div class="progress-bar bg-secondary " style="{studied_rescheduled_p}">
                    <span class="inner inner-right" onclick='pycmd("revhm_browse:rated:1 OR resched:1");' data-tt="st-studied">
                        {studied_rescheduled}
                    </span>
                </div>
 {tomorrow_bar}
                <!-- #128 — קארטלעך פון learning זענען אריינגערעכנט אין "פאר היינט", דערפאר איז נישט דא קיין באזונדערער שטריך פאר"ביים לערנען" אין דער גרויסער סטאטיסטיק. -->
                <div class="progress-bar bg-today" style="{due_p}">
                    <span class="inner inner-left" onclick='pycmd("filtoday")' data-tt="st-today">
                        {due}
                    </span>
                </div>
                <div class="progress-bar bg-warning overflow-visible" style="{overdue_p}">
                    <span class="inner inner-center" onclick='pycmd("filoverdue")' data-tt="st-overdue">
                        {overdue}
                    </span>
                </div>
                <div class="progress-bar bg-primary" style="{new_p}">
                    <span class="inner inner-center"   onclick=pycmd("rev_new"); data-tt="st-new">
                        {new}
                    </span>
                </div>
            </div>
            <div>
                <!-- span><span class="rounded-circle dots bg-secondary"></span> בSecondary</span --->
                <span><span class="rounded-circle dots bg-secondary"></span> חזרות וואס מען האט היינט געמאכט </span>
                <!-- #128 — learning ווערט געוויזן אלס א חלק פון"פאר היינט" און נישט אלס א באזונדערע לעגענדע. -->
                <span><span class="rounded-circle dots bg-today"></span>  פאר היינט</span>
                <span><span class="rounded-circle dots bg-warning"></span> פארשפעטיגט </span>
                <span><span class="rounded-circle dots bg-primary"></span> נייע </span>
                <!-- span><span class="rounded-circle dots bg-info"></span> וInfo</span>
                <span><span class="rounded-circle dots bg-light"></span> זLight</span>
                <span><span class="rounded-circle dots bg-dark"></span> חDark</span --->
            </div>
        </div>
        <script>
            function on_day_review(event, button) {{
              if (event.shiftKey) {{
                  pycmd("filall_with_new");
               }} else {{
                pycmd("filall");
               }}
            }}
        </script>"""

stats_conatiner_second_row = """
    <!-- צווייטע שורה -->
    <div class="col p-1 mb-1  align-hetmap-center stats_row" style="overflow: visible;">
            <div class="responsive-heatmap">
                <div id="hmper">
                </div>
                <div id="hm">
                </div>
            </div>
        </div>"""
stats_conatiner_third_row = """
        <!-- דריטע שורה -->
        <div class="col gap-3  stats_row">
            <div class="row flex-nowrap">
            <div class='col'>
            <span class="display-6">סטאטיסטיק</span>
                <div id="legend"></div>
            </div>
                <!---------------- the pie chart ------------------------------->
                <div class='col plotlygroup' style="padding:2%">
                    <div id="my_dataviz"></div>
                </div>
                <!---------------- END pie chart ------------------------------->
            </div>
        </div>
    </div>
</div>
"""

stats_js = """
    <script>
    let trycount = 0
      function check3DFunction() {{
      try {{
      const element = document.querySelector('#studiedToday');
        if (element) {{
        element.remove();
        }}
        child = document.querySelector(".rh-container")
        //.classList.add({{HEATMAP_WIDTH}});
        parent = document.querySelector("#hm")
        if (child && parent) {{
            parent.appendChild(child);
        }}

    // set the dimensions and margins of the graph
        var w = 100;
        var h = 100;

    //   var aColor = [
    //       "#2e7d32",
    //       "#85dd95",
    //       "#00838fcc",
    //       "#b02323",
    //       "#ffdc41",
    //       "#808080"
    //   ]
        var aColor = [
            "rgb(49, 163, 84)",
            "rgb(116, 196, 118)",
            "var(--state-new)",
            "var(--state-learn)",
            "rgb(255, 220, 65)",
            "grey"
        ]
        var dataset = [
            {{ "label": "בוגר", "legend_tooltip": "בוגר: א קארטל מיט צייטפלאן מרווחים פון מער ווי דריי וואכן", "value": "{mature}", "percent": "{mature_percent}", "pycmd":'("is:review" -"is:learn") AND "prop:ivl>=21"AND -("is:buried" OR "is:suspended")' }},
            {{ "label": "יונג", "legend_tooltip": "יונג: א קארטל מיט חזרה מרווחים פון ווייניגער ווי דריי וואכן. עס איז באזונדער וויכטיג צו חזרן אזא קארטל אין די באשטימטע צייטן, כדי נישט צו פארגעסן", "value": "{young}", "percent": "{young_percent}", "pycmd":'  ("is:review" AND -"is:learn") AND "prop:ivl<21"AND -("is:buried" OR "is:suspended")' }},
            {{ "label": "נייע", "legend_tooltip": "נייע: קארטלעך וואס איר האט נאך נישט געחזרט", "value": "{new}", "percent": "{new_percent}", "pycmd": '"is:new"AND -("is:buried" OR "is:suspended")' }},
            {{ "label": "ביים לערנען", "legend_tooltip": "ביים לערנען: קארטלעך וואס מען לערנט צום צווייטן מאל, אדער וואס איר האט געדריקט אויף 'נאכאמאל' אין א חזרה", "value": "{learn}", "percent": "{learn_percent}", "pycmd": 'is:learn' }},
            {{ "label": "אפגעשטעלט", "legend_tooltip": "אפגעשטעלט: קארטלעך וואס מען האט אליין אפגעשטעלט ביז מען שאלט זיי ווידער אן", "value": "{suspended}", "percent": "{suspended_percent}", "pycmd": '  "is:suspended"' }},
            {{ "label": "באזייטיגט ביז מארגן", "legend_tooltip": "באזייטיגט: קארטלעך וואס ווארטן ביז מארגן", "value": "{buried}", "percent": "{buried_percent}", "pycmd": '  "is:buried"' }},
        ];
        var outerRadius = w / 2;
        var innerRadius = h / 3.5;
        var arc = d3.svg.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius);

        var pie = d3.layout.pie()
            .value(function (d) {{
                return d.value;
            }});

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
            .attr("fill", function (d, i) {{
                return aColor[i];
            }})
            // .attr("id", function (d, i) {{
            //     return "arc" + i;
            // }})
            .attr("d", arc);

        arcs.append("text")
            .attr("transform", function (d) {{
                return "translate(" + arc.centroid(d) + ")";
            }})
            .attr("text-anchor", "middle")

            // .text(function (d) {{
            //     if (d.value == "0") {{
            //         return ""
            //     }} else {{
            //         return d.value;
            //     }}
            // }})
            ;
            // הילף טעקסט אינעם חלק
        arcs.style("cursor", "pointer")
            .on("mouseover", function (d) {{
                var tip = document.getElementById('global_tooltip');
                tip.innerHTML = `${{d.data.label}}:<br><b>${{d.value}}</b> קארטלעך<br>פראצענט פון אלע קארטלעך: <b>${{d.data.percent}}</b>`;
                tip.style.display = 'block';
                var selectthegraphs = $('.arc').not(this);
                d3.selectAll(selectthegraphs)
                    .style("opacity", .5);

                d3.select(this).style("stroke", "black");
            }})
            .on("mousemove", function () {{
                var tip = document.getElementById('global_tooltip');
                var x = d3.event.clientX + 15, y = d3.event.clientY + 15;
                if (x + 310 > window.innerWidth) x = d3.event.clientX - 175;
                if (y + tip.offsetHeight + 10 > window.innerHeight) y = d3.event.clientY - tip.offsetHeight - 10;
                tip.style.left = x + 'px';
                tip.style.top = y + 'px';
            }})
            .on("mouseout", function () {{
                document.getElementById('global_tooltip').style.display = 'none';

                var selectthegraphs = $('.arc').not(this);
                d3.selectAll(selectthegraphs)
                    .style("opacity", 1);
                d3.select(this).style("stroke", "none");
            }})
            .on("click", function (d, i) {{
                pycmd(`revhm_browse:${{d.data.pycmd}}`)
            }});

            // var thing = svg.append("g")
            //   .attr("id", "thing")
            //   .style("fill", "navy")
            //   .attr("class", "label")
            //   .selectAll('text')
            //   .data(dataset)
            //   .enter()
            //   .append("text")
            //   .style("font-size", "6px")
            //   .append("textPath")
            //   .attr("xlink:href", function (d, i) {{ return "#arc" + i; }})
            //   .style("text-anchor", "middle")
            //   .attr("startOffset", "50%")
            //   .text(function (d) {{ return "d.label"; }});

    // ערקלערונג
            var legend = d3.select("#legend").append("svg")
                .attr("class", "legend")
                .attr("width", "220px").attr("viewBox", "0 0 220 168")
                .attr("height", "168px")

                .selectAll("g")
                .data(dataset)
                .enter().append("g")
                // .attr("transform", function (d, i) {{ return "translate(95," + i * 20 + ")"; }});
                .attr("transform", function position(d,i) {{
                var c = 1;   // number of columns
                var h = 26;  // legend entry height
                var w = 100; // legend entry width (so we can position the next column)
                var tx = 10; // tx/ty are essentially margin values
                var ty = 10;
                var x = 204;
                var y = Math.floor(i / c) * h + ty;
                return "translate(" + x + "," + y + ")";
    }});

            legend.append("rect")
                .attr("width", 10)
                .attr("height", 10)
                .style("fill", function (d, i) {{
                    return aColor[i];
                }});

            legend.append("text")
                 .attr("x", -14)
                .attr("y", 8)
                .attr("dy", ".35em")
                .text(function (d, i) {{return d["label"]; }})
                .style("cursor", "pointer")
                .style("fill", "var(--bs-body-color)");


            legend.on("click", function (d, i) {{
                   pycmd(`revhm_browse:${{d.pycmd}}`)
                        }})
                    .on("mouseover", function (d) {{
                        d3.select(this).style("text-decoration", "underline");
                        var tip = document.getElementById('global_tooltip');
                        tip.innerHTML = `${{d.legend_tooltip}}`;
                        tip.style.display = 'block';
                    }})
                    .on("mousemove", function () {{
                        var tip = document.getElementById('global_tooltip');
                        var x = d3.event.clientX + 15, y = d3.event.clientY + 15;
                        if (x + 310 > window.innerWidth) x = d3.event.clientX - 175;
                        if (y + tip.offsetHeight + 10 > window.innerHeight) y = d3.event.clientY - tip.offsetHeight - 10;
                        tip.style.left = x + 'px';
                        tip.style.top = y + 'px';
                    }})
                    .on("mouseout", function (d) {{
                        d3.select(this).style("text-decoration", "none");
                        document.getElementById('global_tooltip').style.display = 'none';
                    }})

        // רונדע עקן פאר פארשריט סרגלים ווערן באהאנדלט אין-CSS (overflow:hidden אויף .progress)
   }} catch (error) {{
    // The function '3d' does not exist yet, wait for 1 second and check again
	if (!trycount == 0){{
      console.log(error);
   }}
      trycount +=1;
      if (trycount < 5) {{
        setTimeout(check3DFunction, 100);
      }}
  }}
}}
check3DFunction();

// פראבלעם 10: באהאלטן דעם קאלענדאר ראם (heatmap) ווען עס איז נישט דא קיין דאטן צו ווייזן
// אויב נאכן לאדענען דעם צוגאב review-heatmap איז קיין אינהאלט נישט אריינגעלייגט געווארן אין #hm,
// מען באהאלט דעם אויסערליכן האלטער (.align-hetmap-center) כדי נישט צו ווייזן א ליידיגן ווייסן ראם.
(function hideEmptyHeatmap() {{
    var attempts = 0;
    function check() {{
        attempts++;
        var hm = document.getElementById("hm");
        var hmper = document.getElementById("hmper");
        var outer = document.querySelector(".align-hetmap-center");
        if (!outer) return;
        var hmEmpty = !hm || hm.children.length === 0;
        var hmperEmpty = !hmper || hmper.children.length === 0;
        if (hmEmpty && hmperEmpty) {{
            if (attempts < 12) {{
                setTimeout(check, 250);
            }} else {{
                outer.style.display = "none";
            }}
        }}
    }}
    setTimeout(check, 400);
}})();
        </script> """
