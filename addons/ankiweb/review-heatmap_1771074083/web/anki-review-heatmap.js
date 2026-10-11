

var __vite_style__ = document.createElement("style");
__vite_style__.innerHTML =
  '/* Cal-HeatMap CSS */\n\n.cal-heatmap-container {\n	display: block;\n}\n\n.cal-heatmap-container .graph\n{\n	font-family: "Lucida Grande", Lucida, Verdana, sans-serif;\n}\n\n.cal-heatmap-container .graph-label\n{\n	fill: #e2e1e1;\n	font-size: 10px\n}\n\n.cal-heatmap-container .graph, .cal-heatmap-container .graph-legend rect {\n	shape-rendering: crispedges\n}\n\n.cal-heatmap-container .graph-rect\n{\n	fill: #ededed\n}\n\n.cal-heatmap-container .graph-subdomain-group rect:hover\n{\n	stroke: #000;\n	stroke-width: 1px\n}\n\n.cal-heatmap-container .subdomain-text {\n	font-size: 8px;\n	fill: #999;\n	pointer-events: none\n}\n\n.cal-heatmap-container .hover_cursor:hover {\n	cursor: pointer\n}\n\n.cal-heatmap-container .qi {\n	background-color: #999;\n	fill: #999\n}\n\n/*\nRemove comment to apply this style to date with value equal to 0\n.q0\n{\n	background-color: #fff;\n	fill: #fff;\n	stroke: #ededed\n}\n*/\n\n.cal-heatmap-container .q1\n{\n	background-color: #dae289;\n	fill: #dae289\n}\n\n.cal-heatmap-container .q2\n{\n	background-color: #cedb9c;\n	fill: #9cc069\n}\n\n.cal-heatmap-container .q3\n{\n	background-color: #b5cf6b;\n	fill: #669d45\n}\n\n.cal-heatmap-container .q4\n{\n	background-color: #637939;\n	fill: #637939\n}\n\n.cal-heatmap-container .q5\n{\n	background-color: #3b6427;\n	fill: #3b6427\n}\n\n.cal-heatmap-container rect.highlight\n{\n	stroke:#444;\n	stroke-width:1\n}\n\n.cal-heatmap-container text.highlight\n{\n	fill: #444\n}\n\n.cal-heatmap-container rect.highlight-now\n{\n	stroke: red\n}\n\n.cal-heatmap-container text.highlight-now\n{\n	fill: red;\n	font-weight: 800\n}\n\n.cal-heatmap-container .domain-background {\n	fill: none;\n	shape-rendering: crispedges\n}\n\n.cal-heatmap-container .day-name-rect {\n	fill: transparent;\n}\n\n.cal-heatmap-container .day-name-text {\n	font-size: 10px;\n	fill: #999;\n}\n\n.ch-tooltip {\n	padding: 10px;\n	background: #222;\n	color: #bbb;\n	font-size: 12px;\n	line-height: 1.4;\n	width: 140px;\n	position: absolute;\n	z-index: 99999;\n	text-align: center;\n	border-radius: 2px;\n	box-shadow: 2px 2px 2px rgba(0,0,0,0.2);\n	display: none;\n	box-sizing: border-box;\n}\n\n.ch-tooltip::after{\n	position: absolute;\n	width: 0;\n	height: 0;\n	border-color: transparent;\n	border-style: solid;\n	content: "";\n	padding: 0;\n	display: block;\n	bottom: -6px;\n	left: 50%;\n	margin-left: -6px;\n    border-width: 6px 6px 0;\n    border-top-color: #222;\n}\n/* \nThis file is part of the Review Heatmap add-on for Anki\n\nCustom Heatmap CSS\n\nCopyright: (c) 2016-2022 Glutanimate <https://glutanimate.com/>\nLicense: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>\n*/\n\n/* Special classes:\n"rh-platform-mac": Set when run on macOS\n"rh-platform-win": Set when run on Windows\n"rh-platform-lin": Set when run on Linux\n"rh-theme-olive", "rh-theme-lime", "rh-theme-ice",\n    "rh-theme-magenta", "rh-theme-flame": Set when respective theme active\n"rh-mode-year": Set when calendar set to year mode\n"rh-mode-months": Set when calendar set to months mode\n"rh-view-deckbrowser", "rh-view-overview", "rh-view-stats": Set when drawn\n    on respective view\n"rh-disable-stats": Set when streak stats disabled\n"rh-disable-heatmap": Set when heatmap disabled\n"night_mode": Set when night mode active (provided by Night Mode add-on)\n*/\n\n/* General layout */\n/* ################################################################### */\n\n.rh-container {\n    margin-top: 1em;\n}\n\n.heatmap {\n    display:inline-block;\n}\n.heatmap-controls {\n    margin-bottom: 0;\n}\n\n/* Heatmap graph adjustments */\n/* ################################################################### */\n\n.cal-heatmap-container .graph {\n    font-family: unset;\n}\n.graph-label {\n    fill: #808080;\n}\n\n/* Graph rects */\n.cal-heatmap-container rect.highlight-now {\n    stroke: black;\n}\n.cal-heatmap-container rect.highlight {\n    stroke: #E9002E;\n}\n.cal-heatmap-container .graph-rect {\n    fill: #eaeaea;\n}\n.night_mode .cal-heatmap-container .graph-rect {\n    fill: #222222;\n}\n\n/* Holy days (Shabbat & Yom Tov) */\n.cal-heatmap-container rect.holy-day {\n    stroke: #cc9900;\n    stroke-width: 1.5px;\n}\n.night_mode .cal-heatmap-container rect.holy-day {\n    stroke: #886600;\n    stroke-width: 1.5px;\n}\n/* אישיו #446: מקווקו רק כאשר היום עצמו והיום הבא מסווגים כאסורים במלאכה. */\n.cal-heatmap-container rect.holy-day.holy-day-followed {\n    stroke-dasharray: 3 2;\n}\n\n/* Heatmap hover tooltip */\n/* ################################################################### */\n\n.ch-tooltip {\n    color: rgb(240, 240, 240);\n    animation: 0.5s ease 0s normal forwards 1 fadein;\n    -webkit-animation: 0.5s ease 0s normal forwards 1 fadein;\n}\n/* Delay tooltip using fadein */\n@keyframes fadein {\n    0% { opacity:0; }\n    66% { opacity:0; }\n    100% { opacity:0.9; }\n}\n@-webkit-keyframes fadein {\n    0% { opacity:0; }\n    66% { opacity:0; }\n    100% { opacity:0.9; }\n}\n\n/* Heatmap button area */\n/* ################################################################### */\n.alignleft {\n    float: left;\n    width:33.33333%;\n    text-align:left;\n}\n.aligncenter {\n    float: left;\n    width:33.33333%;\n    text-align:center;\n}\n.alignright {\n    float: left;\n    width:33.33333%;\n    text-align:right;\n}\n\n/* Heatmap buttons */\n/* ################################################################### */\n\n/* Regular buttons */\n.hm-btn {\n    height: 100%;\n    display: inline-block;\n    cursor: pointer;\n    background: #e6e6e6;\n    color: #808080;\n    padding: 2px 8px;\n    border-radius: 3px;\n    margin-left: 2px;\n    text-decoration: none;\n    user-select: none;\n    vertical-align: center;\n}\n.hm-btn:hover {\n    background: #bfbfbf;\n}\n.hm-btn:active {\n    background: #000;\n}\n.night_mode .hm-btn {\n    background-color: #313d45;\n}\n.night_mode .hm-btn:hover {\n    background-color: #374f5b;\n}\n.night_mode .hm-btn:active {\n    background-color: #433376;\n}\n\n\n/* Options button */\n.opts-btn {\n    padding: 2px 4px;\n}\n.opts-btn:hover {\n    background: #bfbfbf;\n}\n.opts-btn>img {\n    position:relative;\n    top: calc(50% - 12px);\n    height: 10px;\n    width: 10px;\n}\n\n/* Heatmap activity type widget */\n/* ################################################################### */\n.hm-sel {\n    display: inline-block;\n    height: 100%;\n    padding: 4px 8px;\n    font-size: 80%;\n    cursor: pointer;\n    color: #808080;\n    border-radius: 3px;\n    user-select: none;\n    border: none;\n    -webkit-appearance: none;\n    -moz-appearance: none;\n    appearance: none;\n    background: url(qrc:/review_heatmap/icons/down.svg) 96% / 10% no-repeat #e6e6e6;\n}\nselect.hm-sel:hover {\n    background: url(qrc:/review_heatmap/icons/down.svg) 96% / 10% no-repeat #bfbfbf;\n}\nselect.hm-sel:active, select.hm-sel:focus {\n    background: url(qrc:/review_heatmap/icons/down.svg) 96% / 10% no-repeat #e6e6e6;\n}\n\n/* Heatmap links */\n/* ################################################################### */\n\n/* we use these instead of regular links to prevent bugs with page navigation,\n   prevent the link color from changing on click, etc.*/\n\n.linkspan {\n     cursor:pointer;\n     color:blue;\n     text-decoration:underline;\n}\n\n.night_mode .linkspan {\n    color: white;\n}\n\n/* Streak stats */\n/* ################################################################### */\n\n/* TODO: investigate why we had two copies of these */\n.streak {margin-top: 0.5em;}\n.streak-info {\n    margin-right: 1em;\n}\n.sstats {\n    font-weight: bold;\n    color: #E6E6E6;\n}\n\n\n\n\n\n/* Color themes */\n/* ################################################################### */\n\n\n/* FORECAST RECT COLORS */\n/*\n- same for every theme \n- reverse order because of negative value workaround \n*/\n.cal-heatmap-container .q1{fill: #525252}\n.cal-heatmap-container .q2{fill: #616161}\n.cal-heatmap-container .q3{fill: #707070}\n.cal-heatmap-container .q4{fill: #7F7F7F}\n.cal-heatmap-container .q5{fill: #8E8E8E}\n.cal-heatmap-container .q6{fill: #9D9D9D}\n.cal-heatmap-container .q7{fill: #ACACAC}\n.cal-heatmap-container .q8{fill: #BBBBBB}\n.cal-heatmap-container .q9{fill: #CACACA}\n.cal-heatmap-container .q10{fill: #D9D9D9}\n\n.night_mode .cal-heatmap-container .q1{fill: #5d5f5f}\n.night_mode .cal-heatmap-container .q2{fill: #585a5a}\n.night_mode .cal-heatmap-container .q3{fill: #535555}\n.night_mode .cal-heatmap-container .q4{fill: #4e5050}\n.night_mode .cal-heatmap-container .q5{fill: #494b4b}\n.night_mode .cal-heatmap-container .q6{fill: #444646}\n.night_mode .cal-heatmap-container .q7{fill: #3f4141}\n.night_mode .cal-heatmap-container .q8{fill: #3a3c3c}\n.night_mode .cal-heatmap-container .q9{fill: #353737}\n.night_mode .cal-heatmap-container .q10{fill: #313232}\n\n/* REVIEW HISTORY COLORS */\n/*\n- different between each theme\n*/\n\n/* olive */\n.rh-theme-olive .cal-heatmap-container .q11{fill: #dae289}\n.rh-theme-olive .cal-heatmap-container .q12{fill: #bbd179}\n.rh-theme-olive .cal-heatmap-container .q13{fill: #9cc069}\n.rh-theme-olive .cal-heatmap-container .q14{fill: #8ab45d}\n.rh-theme-olive .cal-heatmap-container .q15{fill: #78a851}\n.rh-theme-olive .cal-heatmap-container .q16{fill: #669d45}\n.rh-theme-olive .cal-heatmap-container .q17{fill: #648b3f}\n.rh-theme-olive .cal-heatmap-container .q18{fill: #637939}\n.rh-theme-olive .cal-heatmap-container .q19{fill: #4f6e30}\n.rh-theme-olive .cal-heatmap-container .q20{fill: #3b6427}\n\n.rh-theme-olive .rh-col11{color: #dae289}\n.rh-theme-olive .rh-col12{color: #bbd179}\n.rh-theme-olive .rh-col13{color: #9cc069}\n.rh-theme-olive .rh-col14{color: #8ab45d}\n.rh-theme-olive .rh-col15{color: #78a851}\n.rh-theme-olive .rh-col16{color: #669d45}\n.rh-theme-olive .rh-col17{color: #648b3f}\n.rh-theme-olive .rh-col18{color: #637939}\n.rh-theme-olive .rh-col19{color: #4f6e30}\n.rh-theme-olive .rh-col20{color: #3b6427}\n\n.night_mode .rh-theme-olive .cal-heatmap-container .q11{fill: #3b6427}\n.night_mode .rh-theme-olive .cal-heatmap-container .q12{fill: #4f6e30}\n.night_mode .rh-theme-olive .cal-heatmap-container .q13{fill: #637939}\n.night_mode .rh-theme-olive .cal-heatmap-container .q14{fill: #648b3f}\n.night_mode .rh-theme-olive .cal-heatmap-container .q15{fill: #669d45}\n.night_mode .rh-theme-olive .cal-heatmap-container .q16{fill: #78a851}\n.night_mode .rh-theme-olive .cal-heatmap-container .q17{fill: #8ab45d}\n.night_mode .rh-theme-olive .cal-heatmap-container .q18{fill: #9cc069}\n.night_mode .rh-theme-olive .cal-heatmap-container .q19{fill: #bbd179}\n.night_mode .rh-theme-olive .cal-heatmap-container .q20{fill: #dae289}\n\n.night_mode .rh-theme-olive .rh-col11{color: #3b6427}\n.night_mode .rh-theme-olive .rh-col12{color: #4f6e30}\n.night_mode .rh-theme-olive .rh-col13{color: #637939}\n.night_mode .rh-theme-olive .rh-col14{color: #648b3f}\n.night_mode .rh-theme-olive .rh-col15{color: #669d45}\n.night_mode .rh-theme-olive .rh-col16{color: #78a851}\n.night_mode .rh-theme-olive .rh-col17{color: #8ab45d}\n.night_mode .rh-theme-olive .rh-col18{color: #9cc069}\n.night_mode .rh-theme-olive .rh-col19{color: #bbd179}\n.night_mode .rh-theme-olive .rh-col20{color: #dae289}\n\n/* lime */\n.rh-theme-lime .cal-heatmap-container .q11{fill: #d6e685}\n.rh-theme-lime .cal-heatmap-container .q12{fill: #bddb7a}\n.rh-theme-lime .cal-heatmap-container .q13{fill: #a4d06f}\n.rh-theme-lime .cal-heatmap-container .q14{fill: #8cc665}\n.rh-theme-lime .cal-heatmap-container .q15{fill: #74ba58}\n.rh-theme-lime .cal-heatmap-container .q16{fill: #5cae4c}\n.rh-theme-lime .cal-heatmap-container .q17{fill: #44a340}\n.rh-theme-lime .cal-heatmap-container .q18{fill: #378f36}\n.rh-theme-lime .cal-heatmap-container .q19{fill: #2a7b2c}\n.rh-theme-lime .cal-heatmap-container .q20{fill: #1e6823}\n\n.rh-theme-lime .rh-col11{color: #d6e685}\n.rh-theme-lime .rh-col12{color: #bddb7a}\n.rh-theme-lime .rh-col13{color: #a4d06f}\n.rh-theme-lime .rh-col14{color: #8cc665}\n.rh-theme-lime .rh-col15{color: #74ba58}\n.rh-theme-lime .rh-col16{color: #5cae4c}\n.rh-theme-lime .rh-col17{color: #44a340}\n.rh-theme-lime .rh-col18{color: #378f36}\n.rh-theme-lime .rh-col19{color: #2a7b2c}\n.rh-theme-lime .rh-col20{color: #1e6823}\n\n.night_mode .rh-theme-lime .cal-heatmap-container .q11{fill: #1e6823}\n.night_mode .rh-theme-lime .cal-heatmap-container .q12{fill: #2a7b2c}\n.night_mode .rh-theme-lime .cal-heatmap-container .q13{fill: #378f36}\n.night_mode .rh-theme-lime .cal-heatmap-container .q14{fill: #44a340}\n.night_mode .rh-theme-lime .cal-heatmap-container .q15{fill: #5cae4c}\n.night_mode .rh-theme-lime .cal-heatmap-container .q16{fill: #74ba58}\n.night_mode .rh-theme-lime .cal-heatmap-container .q17{fill: #8cc665}\n.night_mode .rh-theme-lime .cal-heatmap-container .q18{fill: #a4d06f}\n.night_mode .rh-theme-lime .cal-heatmap-container .q19{fill: #bddb7a}\n.night_mode .rh-theme-lime .cal-heatmap-container .q20{fill: #d6e685}\n\n.night_mode .rh-theme-lime .rh-col11{color: #1e6823}\n.night_mode .rh-theme-lime .rh-col12{color: #2a7b2c}\n.night_mode .rh-theme-lime .rh-col13{color: #378f36}\n.night_mode .rh-theme-lime .rh-col14{color: #44a340}\n.night_mode .rh-theme-lime .rh-col15{color: #5cae4c}\n.night_mode .rh-theme-lime .rh-col16{color: #74ba58}\n.night_mode .rh-theme-lime .rh-col17{color: #8cc665}\n.night_mode .rh-theme-lime .rh-col18{color: #a4d06f}\n.night_mode .rh-theme-lime .rh-col19{color: #bddb7a}\n.night_mode .rh-theme-lime .rh-col20{color: #d6e685}\n\n/* ice */\n.rh-theme-ice .cal-heatmap-container .q11{fill: #a8d5f6}\n.rh-theme-ice .cal-heatmap-container .q12{fill: #95c8f3}\n.rh-theme-ice .cal-heatmap-container .q13{fill: #82bbf0}\n.rh-theme-ice .cal-heatmap-container .q14{fill: #70afee}\n.rh-theme-ice .cal-heatmap-container .q15{fill: #5da2eb}\n.rh-theme-ice .cal-heatmap-container .q16{fill: #4a95e8}\n.rh-theme-ice .cal-heatmap-container .q17{fill: #3889e6}\n.rh-theme-ice .cal-heatmap-container .q18{fill: #257ce3}\n.rh-theme-ice .cal-heatmap-container .q19{fill: #126fe0}\n.rh-theme-ice .cal-heatmap-container .q20{fill: #0063de}\n\n.rh-theme-ice .rh-col11{color: #a8d5f6}\n.rh-theme-ice .rh-col12{color: #95c8f3}\n.rh-theme-ice .rh-col13{color: #82bbf0}\n.rh-theme-ice .rh-col14{color: #70afee}\n.rh-theme-ice .rh-col15{color: #5da2eb}\n.rh-theme-ice .rh-col16{color: #4a95e8}\n.rh-theme-ice .rh-col17{color: #3889e6}\n.rh-theme-ice .rh-col18{color: #257ce3}\n.rh-theme-ice .rh-col19{color: #126fe0}\n.rh-theme-ice .rh-col20{color: #0063de}\n\n.night_mode .rh-theme-ice .cal-heatmap-container .q11{fill: #0063de}\n.night_mode .rh-theme-ice .cal-heatmap-container .q12{fill: #126fe0}\n.night_mode .rh-theme-ice .cal-heatmap-container .q13{fill: #257ce3}\n.night_mode .rh-theme-ice .cal-heatmap-container .q14{fill: #3889e6}\n.night_mode .rh-theme-ice .cal-heatmap-container .q15{fill: #4a95e8}\n.night_mode .rh-theme-ice .cal-heatmap-container .q16{fill: #5da2eb}\n.night_mode .rh-theme-ice .cal-heatmap-container .q17{fill: #70afee}\n.night_mode .rh-theme-ice .cal-heatmap-container .q18{fill: #82bbf0}\n.night_mode .rh-theme-ice .cal-heatmap-container .q19{fill: #95c8f3}\n.night_mode .rh-theme-ice .cal-heatmap-container .q20{fill: #a8d5f6}\n\n.night_mode .rh-theme-ice .rh-col11{color: #0063de}\n.night_mode .rh-theme-ice .rh-col12{color: #126fe0}\n.night_mode .rh-theme-ice .rh-col13{color: #257ce3}\n.night_mode .rh-theme-ice .rh-col14{color: #3889e6}\n.night_mode .rh-theme-ice .rh-col15{color: #4a95e8}\n.night_mode .rh-theme-ice .rh-col16{color: #5da2eb}\n.night_mode .rh-theme-ice .rh-col17{color: #70afee}\n.night_mode .rh-theme-ice .rh-col18{color: #82bbf0}\n.night_mode .rh-theme-ice .rh-col19{color: #95c8f3}\n.night_mode .rh-theme-ice .rh-col20{color: #a8d5f6}\n\n/* magenta */\n.rh-theme-magenta .cal-heatmap-container .q11{fill: #fde0dd}\n.rh-theme-magenta .cal-heatmap-container .q12{fill: #fcc5c0}\n.rh-theme-magenta .cal-heatmap-container .q13{fill: #fa9fb5}\n.rh-theme-magenta .cal-heatmap-container .q14{fill: #f768a1}\n.rh-theme-magenta .cal-heatmap-container .q15{fill: #ea4e9c}\n.rh-theme-magenta .cal-heatmap-container .q16{fill: #dd3497}\n.rh-theme-magenta .cal-heatmap-container .q17{fill: #ae017e}\n.rh-theme-magenta .cal-heatmap-container .q18{fill: #7a0177}\n.rh-theme-magenta .cal-heatmap-container .q19{fill: #610070}\n.rh-theme-magenta .cal-heatmap-container .q20{fill: #49006a}\n\n.rh-theme-magenta .rh-col11{color: #fde0dd}\n.rh-theme-magenta .rh-col12{color: #fcc5c0}\n.rh-theme-magenta .rh-col13{color: #fa9fb5}\n.rh-theme-magenta .rh-col14{color: #f768a1}\n.rh-theme-magenta .rh-col15{color: #ea4e9c}\n.rh-theme-magenta .rh-col16{color: #dd3497}\n.rh-theme-magenta .rh-col17{color: #ae017e}\n.rh-theme-magenta .rh-col18{color: #7a0177}\n.rh-theme-magenta .rh-col19{color: #610070}\n.rh-theme-magenta .rh-col20{color: #49006a}\n\n.night_mode .rh-theme-magenta .cal-heatmap-container .q11{fill: #49006a}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q12{fill: #610070}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q13{fill: #7a0177}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q14{fill: #ae017e}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q15{fill: #dd3497}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q16{fill: #ea4e9c}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q17{fill: #f768a1}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q18{fill: #fa9fb5}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q19{fill: #fcc5c0}\n.night_mode .rh-theme-magenta .cal-heatmap-container .q20{fill: #fde0dd}\n\n.night_mode .rh-theme-magenta .rh-col11{color: #49006a}\n.night_mode .rh-theme-magenta .rh-col12{color: #610070}\n.night_mode .rh-theme-magenta .rh-col13{color: #7a0177}\n.night_mode .rh-theme-magenta .rh-col14{color: #ae017e}\n.night_mode .rh-theme-magenta .rh-col15{color: #dd3497}\n.night_mode .rh-theme-magenta .rh-col16{color: #ea4e9c}\n.night_mode .rh-theme-magenta .rh-col17{color: #f768a1}\n.night_mode .rh-theme-magenta .rh-col18{color: #fa9fb5}\n.night_mode .rh-theme-magenta .rh-col19{color: #fcc5c0}\n.night_mode .rh-theme-magenta .rh-col20{color: #fde0dd}\n\n\n/* flame */\n.rh-theme-flame .cal-heatmap-container .q11{fill: #ffeda0}\n.rh-theme-flame .cal-heatmap-container .q12{fill: #fed976}\n.rh-theme-flame .cal-heatmap-container .q13{fill: #feb24c}\n.rh-theme-flame .cal-heatmap-container .q14{fill: #fd8d3c}\n.rh-theme-flame .cal-heatmap-container .q15{fill: #fc6d33}\n.rh-theme-flame .cal-heatmap-container .q16{fill: #fc4e2a}\n.rh-theme-flame .cal-heatmap-container .q17{fill: #e31a1c}\n.rh-theme-flame .cal-heatmap-container .q18{fill: #d00d21}\n.rh-theme-flame .cal-heatmap-container .q19{fill: #bd0026}\n.rh-theme-flame .cal-heatmap-container .q20{fill: #800026}\n\n.rh-theme-flame .rh-col11{color: #ffeda0}\n.rh-theme-flame .rh-col12{color: #fed976}\n.rh-theme-flame .rh-col13{color: #feb24c}\n.rh-theme-flame .rh-col14{color: #fd8d3c}\n.rh-theme-flame .rh-col15{color: #fc6d33}\n.rh-theme-flame .rh-col16{color: #fc4e2a}\n.rh-theme-flame .rh-col17{color: #e31a1c}\n.rh-theme-flame .rh-col18{color: #d00d21}\n.rh-theme-flame .rh-col19{color: #bd0026}\n.rh-theme-flame .rh-col20{color: #800026}\n\n.night_mode .rh-theme-flame .cal-heatmap-container .q11{fill: #800026}\n.night_mode .rh-theme-flame .cal-heatmap-container .q12{fill: #bd0026}\n.night_mode .rh-theme-flame .cal-heatmap-container .q13{fill: #d00d21}\n.night_mode .rh-theme-flame .cal-heatmap-container .q14{fill: #e31a1c}\n.night_mode .rh-theme-flame .cal-heatmap-container .q15{fill: #fc4e2a}\n.night_mode .rh-theme-flame .cal-heatmap-container .q16{fill: #fc6d33}\n.night_mode .rh-theme-flame .cal-heatmap-container .q17{fill: #fd8d3c}\n.night_mode .rh-theme-flame .cal-heatmap-container .q18{fill: #feb24c}\n.night_mode .rh-theme-flame .cal-heatmap-container .q19{fill: #fed976}\n.night_mode .rh-theme-flame .cal-heatmap-container .q20{fill: #ffeda0}\n\n.night_mode .rh-theme-flame .rh-col11{color: #800026}\n.night_mode .rh-theme-flame .rh-col12{color: #bd0026}\n.night_mode .rh-theme-flame .rh-col13{color: #d00d21}\n.night_mode .rh-theme-flame .rh-col14{color: #e31a1c}\n.night_mode .rh-theme-flame .rh-col15{color: #fc4e2a}\n.night_mode .rh-theme-flame .rh-col16{color: #fc6d33}\n.night_mode .rh-theme-flame .rh-col17{color: #fd8d3c}\n.night_mode .rh-theme-flame .rh-col18{color: #feb24c}\n.night_mode .rh-theme-flame .rh-col19{color: #fed976}\n.night_mode .rh-theme-flame .rh-col20{color: #ffeda0}\n\n/* Streak stats: override theme colors for readability */\n.streak .sstats {\n    color: #555555;\n}\n.night_mode .streak .sstats {\n    color: #CCCCCC;\n}\n\n\n/* Platform-specific adjustments / workarounds */\n/* ################################################################### */\n';
document.head.appendChild(__vite_style__);
(function (factory) {
  typeof define === "function" && define.amd ? define(factory) : factory();
})(function () {

  "use strict";
  var calHeatmap = "";
  var reviewHeatmap = "";
  /*! cal-heatmap v3.6.3.2-anki2150 (2022)
   *  ---------------------------------------------
   *  Fork of Cal-HeatMap for use in the Anki add-on Review Heatmap
   *  https://github.com/glutanimate/cal-heatmap
   *  Licensed under the MIT license
   *  Copyright 2014 Wan Qi Chen
   *  Copyright 2018-2022 Glutanimate
   *  Contributors: gakada, Srdjan Prpa
    */
  var d3 = window.d3;
  var CalHeatMap = function () {
    var self = this;
    this.allowedDataType = ["json", "csv", "tsv", "txt"];
    this.options = {
      itemSelector: "#cal-heatmap",
      paintOnLoad: true,
      range: 12,
      cellSize: 10,
      cellPadding: 2,
      cellRadius: 0,
      domainGutter: 2,
      domainMargin: [0, 0, 0, 0],
      domain: "hour",
      subDomain: "min",
      colLimit: null,
      rowLimit: null,
      weekStartOnMonday: false,
      dayLabel: false,
      start: new Date(),//היום הנוכחי
      minDate: null,
      maxDate: null,
      today: new Date(),
      data: "",
      dataType: this.allowedDataType[0],
      dataPostPayload: null,
      dataRequestHeaders: null,
      considerMissingDataAsZero: false,
      loadOnInit: true,
      verticalOrientation: false,
      domainDynamicDimension: true,
      label: {
        position: "bottom",
        align: "center",
        offset: {
          x: 0,
          y: 0
        },
        rotate: null,
        width: 100,
        height: null
      },
      legend: [10, 20, 30, 40],
      displayLegend: true,
      legendCellSize: 10,
      legendCellPadding: 2,
      legendMargin: [0, 0, 0, 0],
      legendVerticalPosition: "bottom",
      legendHorizontalPosition: "left",
      legendOrientation: "horizontal",
      legendColors: null,
      highlight: [],
      itemName: ["item", "items"],
      domainLabelFormat: null,
      subDomainTitleFormat: {
        empty: "{date}",
        filled: "{count} {name} {connector} {date}"
      },
      subDomainDateFormat: null,
      subDomainTextFormat: null,
      legendTitleFormat: {
        lower: "less than {min} {name}",
        inner: "between {down} and {up} {name}",
        upper: "more than {max} {name}"
      },
      animationDuration: 500,
      nextSelector: false,
      previousSelector: false,
      itemNamespace: "cal-heatmap",
      tooltip: false,
      onClick: null,
      afterLoad: null,
      afterLoadNextDomain: null,
      afterLoadPreviousDomain: null,
      onComplete: null,
      afterLoadData: function (data) {
        return data;
      },
      afterUpdate: null,
      onMaxDomainReached: null,
      onMinDomainReached: null
    };
    this._domainType = {
      "min": {
        name: "minute",
        level: 10,
        maxItemNumber: 60,
        defaultRowNumber: 10,
        defaultColumnNumber: 6,
        row: function (d2) {
          return self.getSubDomainRowNumber(d2);
        },
        column: function (d2) {
          return self.getSubDomainColumnNumber(d2);
        },
        position: {
          x: function (d2) {
            return Math.floor(d2.getMinutes() / self._domainType.min.row(d2));
          },
          y: function (d2) {
            return d2.getMinutes() % self._domainType.min.row(d2);
          }
        },
        format: {
          date: "%H:%M, %A %B %-e, %Y",
          legend: "",
          connector: "at"
        },
        extractUnit: function (d2) {
          return new Date(d2.getFullYear(), d2.getMonth(), d2.getDate(), d2.getHours(), d2.getMinutes()).getTime();
        }
      },
      "hour": {
        name: "hour",
        level: 20,
        maxItemNumber: function (d2) {
          switch (self.options.domain) {
            case "day":
              return 24;
            case "week":
              return 24 * 7;
            case "month":
              return 24 * (self.options.domainDynamicDimension ? self.getDayCountInMonth(d2) : 31);
          }
        },
        defaultRowNumber: 6,
        defaultColumnNumber: function (d2) {
          switch (self.options.domain) {
            case "day":
              return 4;
            case "week":
              return 28;
            case "month":
              return self.options.domainDynamicDimension ? self.getDayCountInMonth(d2) : 31;
          }
        },
        row: function (d2) {
          return self.getSubDomainRowNumber(d2);
        },
        column: function (d2) {
          return self.getSubDomainColumnNumber(d2);
        },
        position: {
          x: function (d2) {
            if (self.options.domain === "month") {
              if (self.options.colLimit > 0 || self.options.rowLimit > 0) {
                return Math.floor((d2.getHours() + (d2.getDate() - 1) * 24) / self._domainType.hour.row(d2));
              }
              return Math.floor(d2.getHours() / self._domainType.hour.row(d2)) + (d2.getDate() - 1) * 4;
            } else if (self.options.domain === "week") {
              if (self.options.colLimit > 0 || self.options.rowLimit > 0) {
                return Math.floor((d2.getHours() + self.getWeekDay(d2) * 24) / self._domainType.hour.row(d2));
              }
              return Math.floor(d2.getHours() / self._domainType.hour.row(d2)) + self.getWeekDay(d2) * 4;
            }
            return Math.floor(d2.getHours() / self._domainType.hour.row(d2));
          },
          y: function (d2) {
            var p = d2.getHours();
            if (self.options.colLimit > 0 || self.options.rowLimit > 0) {
              switch (self.options.domain) {
                case "month":
                  p += (d2.getDate() - 1) * 24;
                  break;
                case "week":
                  p += self.getWeekDay(d2) * 24;
                  break;
              }
            }
            return Math.floor(p % self._domainType.hour.row(d2));
          }
        },
        format: {
          date: "%Hh, %A %B %-e, %Y",
          legend: "%H:00",
          connector: "at"
        },
        extractUnit: function (d2) {
          return new Date(d2.getFullYear(), d2.getMonth(), d2.getDate(), d2.getHours()).getTime();
        }
      },
      "day": {
        name: "day",
        level: 30,
        maxItemNumber: function (d2) {
          switch (self.options.domain) {
            case "week":
              return 7;
            case "month":
              return self.options.domainDynamicDimension ? self.getDayCountInMonth(d2) : 31;
            case "year":
              return self.options.domainDynamicDimension ? self.getDayCountInYear(d2) : 366;
          }
        },
        defaultColumnNumber: function (d2) {
          d2 = new Date(d2);
          switch (self.options.domain) {
            case "week":
              return 1;
            case "month":
              return self.options.domainDynamicDimension && !self.options.verticalOrientation ? self.getWeekNumber(new Date(d2.getFullYear(), d2.getMonth() + 1, 0)) - self.getWeekNumber(d2) + 1 : 6;
            case "year":
              return self.options.domainDynamicDimension ? self.getWeekNumber(new Date(d2.getFullYear(), 11, 31)) - self.getWeekNumber(new Date(d2.getFullYear(), 0)) + 1 : 54;
          }
        },
        defaultRowNumber: 7,
        row: function (d2) {
          return self.getSubDomainRowNumber(d2);
        },
        column: function (d2) {
          return self.getSubDomainColumnNumber(d2);
        },
        position: {
          x: function (d2) {
            switch (self.options.domain) {
              case "week":
                return Math.floor(self.getWeekDay(d2) / self._domainType.day.row(d2));
              case "month":
                if (self.options.colLimit > 0 || self.options.rowLimit > 0) {
                  return Math.floor((d2.getDate() - 1) / self._domainType.day.row(d2));
                }
                return self.getWeekNumber(d2) - self.getWeekNumber(new Date(d2.getFullYear(), d2.getMonth()));
              case "year":
                if (self.options.colLimit > 0 || self.options.rowLimit > 0) {
                  return Math.floor((self.getDayOfYear(d2) - 1) / self._domainType.day.row(d2));
                }
                return self.getWeekNumber(d2);
            }
          },
          y: function (d2) {
            var p = self.getWeekDay(d2);
            if (self.options.colLimit > 0 || self.options.rowLimit > 0) {
              switch (self.options.domain) {
                case "year":
                  p = self.getDayOfYear(d2) - 1;
                  break;
                case "week":
                  p = self.getWeekDay(d2);
                  break;
                case "month":
                  p = d2.getDate() - 1;
                  break;
              }
            }
            return Math.floor(p % self._domainType.day.row(d2));
          }
        },
        format: {
          date: "%A %B %-e, %Y",
          legend: "%e %b",
          connector: "on"
        },
        extractUnit: function (d2) {
          return new Date(d2.getFullYear(), d2.getMonth(), d2.getDate()).getTime();
        }
      },
      "week": {
        name: "week",
        level: 40,
        maxItemNumber: 54,
        defaultColumnNumber: function (d2) {
          d2 = new Date(d2);
          switch (self.options.domain) {
            case "year":
              return self._domainType.week.maxItemNumber;
            case "month":
              return self.options.domainDynamicDimension ? self.getWeekNumber(new Date(d2.getFullYear(), d2.getMonth() + 1, 0)) - self.getWeekNumber(d2) : 5;
          }
        },
        defaultRowNumber: 1,
        row: function (d2) {
          return self.getSubDomainRowNumber(d2);
        },
        column: function (d2) {
          return self.getSubDomainColumnNumber(d2);
        },
        position: {
          x: function (d2) {
            switch (self.options.domain) {
              case "year":
                return Math.floor(self.getWeekNumber(d2) / self._domainType.week.row(d2));
              case "month":
                return Math.floor(self.getMonthWeekNumber(d2) / self._domainType.week.row(d2));
            }
          },
          y: function (d2) {
            return self.getWeekNumber(d2) % self._domainType.week.row(d2);
          }
        },
        format: {
          date: "%B Week #%W",
          legend: "%B Week #%W",
          connector: "in"
        },
        extractUnit: function (d2) {
          var dt = new Date(d2.getFullYear(), d2.getMonth(), d2.getDate());
          var weekDay = dt.getDay() - (self.options.weekStartOnMonday ? 1 : 0);
          if (weekDay < 0) {
            weekDay = 6;
          }
          dt.setDate(dt.getDate() - weekDay);
          return dt.getTime();
        }
      },
      "month": {
        name: "month",
        level: 50,
        maxItemNumber: 12,
        defaultColumnNumber: 12,
        defaultRowNumber: 1,
        row: function () {
          return self.getSubDomainRowNumber();
        },
        column: function () {
          return self.getSubDomainColumnNumber();
        },
        position: {
          x: function (d2) {
            return Math.floor(d2.getMonth() / self._domainType.month.row(d2));
          },
          y: function (d2) {
            return d2.getMonth() % self._domainType.month.row(d2);
          }
        },
        format: {
          date: "%B %Y",
          legend: "%B",
          connector: "in"
        },
        extractUnit: function (d2) {
          return new Date(d2.getFullYear(), d2.getMonth()).getTime();
        }
      },
      "year": {
        name: "year",
        level: 60,
        row: function () {
          return self.options.rowLimit || 1;
        },
        column: function () {
          return self.options.colLimit || 1;
        },
        position: {
          x: function () {
            return 1;
          },
          y: function () {
            return 1;
          }
        },
        format: {
          date: "%Y",
          legend: "%Y",
          connector: "in"
        },
        extractUnit: function (d2) {
          return new Date(d2.getFullYear()).getTime();
        }
      }
    };
    for (var type in this._domainType) {
      if (this._domainType.hasOwnProperty(type)) {
        var d = this._domainType[type];
        this._domainType["x_" + type] = {
          name: "x_" + type,
          level: d.type,
          maxItemNumber: d.maxItemNumber,
          defaultRowNumber: d.defaultRowNumber,
          defaultColumnNumber: d.defaultColumnNumber,
          row: d.column,
          column: d.row,
          position: {
            x: d.position.y,
            y: d.position.x
          },
          format: d.format,
          extractUnit: d.extractUnit
        };
      }
    }
    this.lastInsertedSvg = null;
    this._completed = false;
    this._domains = d3.map();
    this.graphDim = {
      width: 0,
      height: 0
    };
    this.legendDim = {
      width: 0,
      height: 0
    };
    this.NAVIGATE_LEFT = 1;
    this.NAVIGATE_RIGHT = 2;
    this.RESET_ALL_ON_UPDATE = 0;
    this.RESET_SINGLE_ON_UPDATE = 1;
    this.APPEND_ON_UPDATE = 2;
    this.DEFAULT_LEGEND_MARGIN = 10;
    this.root = null;
    this.tooltip = null;
    this._maxDomainReached = false;
    this._minDomainReached = false;
    this.domainPosition = new DomainPosition();
    this.Legend = null;
    this.legendScale = null;
    this.DSTDomain = [];
    this._init = function () {
      // - אולי אחראי רק להיום הנוכחי? מפעיל את הלוח שנה בפעם הראשונה
      self.getDomain(self.options.start).map(function (d2) {
        return d2.getTime();
      }).map(function (d2) {
        self._domains.set(d2, self.getSubDomain(d2).map(function (d4) {
          return { t: self._domainType[self.options.subDomain].extractUnit(d4), v: null };
        }));
      });
      self.root = d3.select(self.options.itemSelector).append("svg").attr("class", "cal-heatmap-container");
      self.tooltip = d3.select(self.options.itemSelector).attr("style", function () {
        var current = d3.select(self.options.itemSelector).attr("style");
        return (current !== null ? current : "") + "position:relative;";
      }).append("div").attr("class", "ch-tooltip");
      self.root.attr("x", 0).attr("y", 0).append("svg").attr("class", "graph");
      self.Legend = new Legend(self);
      if (self.options.paintOnLoad) {
        _initCalendar();
      }
      return true;
    };
    function _initCalendar() {
      self.verticalDomainLabel = self.options.label.position === "top" || self.options.label.position === "bottom";
      self.domainVerticalLabelHeight = self.options.label.height === null ? Math.max(25, self.options.cellSize * 2) : self.options.label.height;
      self.domainHorizontalLabelWidth = 0;
      if (self.options.domainLabelFormat === "" && self.options.label.height === null) {
        self.domainVerticalLabelHeight = 0;
      }
      if (!self.verticalDomainLabel) {
        self.domainVerticalLabelHeight = 0;
        self.domainHorizontalLabelWidth = self.options.label.width;
      }
      self.paint();
      if (self.options.nextSelector !== false) {
        d3.select(self.options.nextSelector).on("click." + self.options.itemNamespace, function () {
          d3.event.preventDefault();
          return self.loadNextDomain(1);
        });
      }
      if (self.options.previousSelector !== false) {
        d3.select(self.options.previousSelector).on("click." + self.options.itemNamespace, function () {
          d3.event.preventDefault();
          return self.loadPreviousDomain(1);
        });
      }
      // self.Legend.redraw(self.graphDim.width - self.options.domainGutter - self.options.cellPadding);
      self.afterLoad();
      var domains = self.getDomainKeys();
      if (self.options.loadOnInit) {
        self.getDatas(self.options.data, new Date(domains[0]), self.getSubDomain(domains[domains.length - 1]).pop(), function () {
          self.fill();
          self.onComplete();
        });
      } else {
        self.onComplete();
      }
      self.checkIfMinDomainIsReached(domains[0]);
      var c = self.getNextDomain();
      self.checkIfMaxDomainIsReached(self.getNextDomain().getTime());
    }
    function w(d2, outer) {
      // קובע את הרוחב של הקונטינר  של הלוח שנה. 684 זה הרוחב המקסימלי לשנה עברית. צריך לשנות לזיהוי אוטומטי של הרוחב של השנה הנוכחית כיון שזה לא ממורכז. 
      // var width = self.options.cellSize * self._domainType[self.options.subDomain].column(d2) + self.options.cellPadding * self._domainType[self.options.subDomain].column(d2);
      var num_days = get_rosh(d2, 0, 'num_days');
      // var width = 684
      var width = (Math.round(num_days / 7) * (self.options.cellSize + self.options.cellPadding)) + 24
      if (arguments.length === 2 && outer === true) {
        return (width += self.domainHorizontalLabelWidth + self.options.domainGutter + self.options.domainMargin[1] + self.options.domainMargin[3]);
      }
      return width;
    }
    function h(d2, outer) {
      // קובע את הגובה של  הקונטינר  של הלוח שנה
      var height = self.options.cellSize * self._domainType[self.options.subDomain].row(d2) + self.options.cellPadding * self._domainType[self.options.subDomain].row(d2);
      if (arguments.length === 2 && outer === true) {
        height += self.options.domainGutter + self.domainVerticalLabelHeight + self.options.domainMargin[0] + self.options.domainMargin[2];
      }
      return height;
    }
    this.paint = function (navigationDir) {
      // מסדר את הריבועים של הלוח שנה במקומם הגובה נקבע לפי ימות השבוע
      var options = self.options;
      if (arguments.length === 0) {
        navigationDir = false;
      }
      var domainSvg = self.root.select(".graph").selectAll(".graph-domain").data(function () {
        var data = self.getDomainKeys();
        return navigationDir === self.NAVIGATE_LEFT ? data.reverse() : data;
      }, function (d2) {
        return d2;
      });
      var enteringDomainDim = 0;
      var exitingDomainDim = 0;
      if (options.dayLabel && options.domain === "month" && options.subDomain === "day") {
        var daysOfTheWeek = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
        if (options.weekStartOnMonday) {
          daysOfTheWeek.push("sunday");
        } else {
          daysOfTheWeek.shif("sunday");
        }
        var daysOfTheWeekAbbr = daysOfTheWeek.map(function (day) {
          return self.formatDate(d3.time[day](new Date()), "%a").charAt(0);
        });
        this.root.selectAll(".day-name").remove();
        var dayLabelSvgGroup = this.root.append("svg").attr("class", "day-name").attr("x", 0).attr("y", 0);
        var dayLabelSvg = dayLabelSvgGroup.selectAll("g").data(daysOfTheWeekAbbr).enter().append("g");
        dayLabelSvg
          .append("rect")
          .attr("class", "day-name-rect")
          .attr("viewBox", `0 0 ${options.cellSize} ${options.cellSize}`)
          // .attr("width", options.cellSize)
          // .attr("height", options.cellSize)
          .attr("x", 0)
          .attr("y", function (data, index) {
            return index * options.cellSize + index * options.cellPadding;
          });
        dayLabelSvg.append("text").attr("class", "day-name-text").attr("dominant-baseline", "central").attr("x", 0).attr("y", function (data, index) {
          return index * options.cellSize + index * options.cellPadding + options.cellSize / 2;
        }).text(function (data) {
          return data;
        });
      }
      var svg = domainSvg.enter().append("svg").attr("width", function (d2) {
        return w(d2, true) / 15 + "vw";
      }).attr("height", function (d2) {
        return h(d2, true);
      }).attr("x", function (d2) {
        if (options.verticalOrientation) {
          self.graphDim.width = Math.max(self.graphDim.width, w(d2, true));
          return 0;
        } else {
          return getDomainPosition(d2, self.graphDim, "width", w(d2, true));
        }
      }).attr("y", function (d2) {
        if (options.verticalOrientation) {
          return getDomainPosition(d2, self.graphDim, "height", h(d2, true));
        } else {
          self.graphDim.height = Math.max(self.graphDim.height, h(d2, true));
          return 0;
        }
      }).attr("class", function (d2) {
        // קובע את שם המחלקה ללוח שנה
        var classname = "graph-domain";
        var date = new Date(d2);
        switch (options.domain) {
          case "hour":
            classname += " h_" + date.getHours();
          case "day":
            classname += " d_" + date.getDate() + " dy_" + date.getDay();
          case "week":
            classname += " w_" + self.getWeekNumber(date);
          case "month":
            classname += " m_" + (date.getMonth() + 1);
          case "year":
            classname += " y_" + date.getFullYear();
        }
        return classname;
      });
      self.lastInsertedSvg = svg;
      function getDomainPosition(domainIndex, graphDim, axis, domainDim) {
        var tmp = 0;
        // גם כאן טופל מימין לשמאל במעבר
        switch (navigationDir) {
          case false:
            tmp = graphDim[axis];
            graphDim[axis] += domainDim;
            self.domainPosition.setPosition(648 - domainIndex, tmp);
            return tmp;
          case self.NAVIGATE_LEFT:
            self.domainPosition.setPosition(648 - domainIndex, graphDim[axis]);
            enteringDomainDim = domainDim;
            exitingDomainDim = self.domainPosition.getPositionFromIndex(1);
            self.domainPosition.shiftRightBy(exitingDomainDim);
            return graphDim[axis];
          case self.NAVIGATE_RIGHT:
            tmp = -domainDim;
            enteringDomainDim = -tmp;
            exitingDomainDim = graphDim[axis] - self.domainPosition.getLast();
            self.domainPosition.setPosition(648 - domainIndex, tmp);
            self.domainPosition.shiftLeftBy(enteringDomainDim);
            return tmp;
          // לפני שינוי
          //             switch (navigationDir) {
          //   case false:
          //     tmp = graphDim[axis];
          //     graphDim[axis] += domainDim;
          //     self.domainPosition.setPosition(domainIndex, tmp);
          //     return tmp;
          //   case self.NAVIGATE_RIGHT:
          //     self.domainPosition.setPosition(domainIndex, graphDim[axis]);
          //     enteringDomainDim = domainDim;
          //     exitingDomainDim = self.domainPosition.getPositionFromIndex(1);
          //     self.domainPosition.shiftRightBy(exitingDomainDim);
          //     return graphDim[axis];
          //   case self.NAVIGATE_LEFT:
          //     tmp = -domainDim;
          //     enteringDomainDim = -tmp;
          //     exitingDomainDim = graphDim[axis] - self.domainPosition.getLast();
          //     self.domainPosition.setPosition(domainIndex, tmp);
          //     self.domainPosition.shiftLeftBy(enteringDomainDim);
          //     return tmp;
        }
      }
      svg.append("rect").attr("width", function (d2) {
        return (w(d2, true) - options.domainGutter - options.cellPadding)/15 +"vw";
      }).attr("height", function (d2) {
        return h(d2, true) - options.domainGutter - options.cellPadding;
      }).attr("class", "domain-background");
      var subDomainSvgGroup = svg.append("svg").attr("x", function () {
        if (options.label.position === "left") {
          return self.domainHorizontalLabelWidth + options.domainMargin[3];
        } else {
          return options.domainMargin[3];
        }
      }).attr("y", function () {
        if (options.label.position === "top") {
          return self.domainVerticalLabelHeight + options.domainMargin[0];
        } else {
          return options.domainMargin[0];
        }
      }).attr("class", "graph-subdomain-group");
      var rect = subDomainSvgGroup.selectAll("g").data(function (d2) {
        // הדפסת המערך של כל השנה המוצגת
        // console.log(self._domains.get(d2));
        return self._domains.get(d2);
      }).enter().append("g");
      rect.append("rect").attr("class", function (d2) {
        return "graph-rect" + self.getHighlightClassName(d2.t) + (options.onClick !== null ? " hover_cursor" : "");
      }).attr("width", options.cellSize/15 + "vw").attr("height", options.cellSize).attr("x", function (d2) {
        return self.positionSubDomainX(d2.t);
      }).attr("y", function (d2) {
        return self.positionSubDomainY(d2.t);
      }).on("click", function (d2) {
        if (options.onClick !== null) {
          var clickVal = d2.v;
          if ((clickVal === 0 || clickVal === null) && (d2.n > 0 || d2.a > 0)) {
            clickVal = 0.1;
          }
          return self.onClick(new Date(d2.t), clickVal);
        }
      }).call(function (selection) {
        if (options.cellRadius > 0) {
          selection.attr("rx", options.cellRadius).attr("ry", options.cellRadius);
        }
        if (self.legendScale !== null && options.legendColors !== null && options.legendColors.hasOwnProperty("base")) {
          selection.attr("fill", options.legendColors.base);
        }
        if (options.tooltip) {
          // קובע את מיקום הטולטיפ
          selection.on("mouseover", function (d2) {
            var tipHtml = self.getSubDomainTitle(d2);
            var globalTip = showReviewHeatmapTooltip(tipHtml, d3.event);
            if (globalTip) {
              self.tooltip.attr("style", "display:none").html("");
            } else {
              var domainNode = this.parentNode.parentNode;
              self.tooltip.html(tipHtml).attr("style", "display: block;");
              var tooltipPositionX = self.positionSubDomainX(d2.t).replace("vw", "") * 15 - self.tooltip[0][0].offsetWidth / 2 + options.cellSize / 2;
              var tooltipPositionY = self.positionSubDomainY(d2.t) - self.tooltip[0][0].offsetHeight - options.cellSize / 2;
              tooltipPositionX += parseInt(domainNode.getAttribute("x"), 10);
              tooltipPositionY += parseInt(domainNode.getAttribute("y"), 10);
              self.tooltip.attr("style", "display: block; left: " + tooltipPositionX / 15 + "vw; top: " + tooltipPositionY + "px;");
            }
          });
          selection.on("mousemove", function () {
            var globalTip = document.getElementById("global_tooltip");
            if (!globalTip || globalTip.style.display === "none") {
              return;
            }
            positionReviewHeatmapTooltip(globalTip, d3.event);
          });
          selection.on("mouseout", function () {
            hideReviewHeatmapTooltip();
            self.tooltip.attr("style", "display:none").html("");
          });
        }
      });
      if (!options.tooltip) {
        rect.append("title").text(function (d2) {
          return self.formatDate(new Date(d2.t), options.subDomainDateFormat);
        });
      }
      if (options.domainLabelFormat !== "") {
        svg.append("text").attr("class", "graph-label").attr("y", function (d2) {
          var y = options.domainMargin[0];
          switch (options.label.position) {
            case "top":
              y += self.domainVerticalLabelHeight / 2;
              break;
            case "bottom":
              y += h(d2) + self.domainVerticalLabelHeight / 2;
          }
          return y + options.label.offset.y * (options.label.rotate === "right" && options.label.position === "right" || options.label.rotate === "left" && options.label.position === "left" ? -1 : 1);
        }).attr("x", function (d2) {
          var x = options.domainMargin[3];
          switch (options.label.position) {
            case "right":
              x += w(d2);
              break;
            case "bottom":
            case "top":
              x += w(d2) / 2;
          }
          if (options.label.align === "right") {
            return x + self.domainHorizontalLabelWidth - options.label.offset.x * (options.label.rotate === "right" ? -1 : 1);
          }
          return x + options.label.offset.x;
        }).attr("text-anchor", function () {
          switch (options.label.align) {
            case "start":
            case "left":
              return "start";
            case "end":
            case "right":
              return "end";
            default:
              return "middle";
          }
        }).attr("dominant-baseline", function () {
          return self.verticalDomainLabel ? "middle" : "top";
        }).text(function (d2) {
          return get_rosh(d2, 0, 'name');
          // return self.formatDate(new Date(d2), options.domainLabelFormat);
        }).call(domainRotate);
      }
      function domainRotate(selection) {
        switch (options.label.rotate) {
          case "right":
            selection.attr("transform", function (d2) {
              var s = "rotate(90), ";
              switch (options.label.position) {
                case "right":
                  s += "translate(-" + w(d2) + " , -" + w(d2) + ")";
                  break;
                case "left":
                  s += "translate(0, -" + self.domainHorizontalLabelWidth + ")";
                  break;
              }
              return s;
            });
            break;
          case "left":
            selection.attr("transform", function (d2) {
              var s = "rotate(270), ";
              switch (options.label.position) {
                case "right":
                  // case "left":
                  s += "translate(-" + (w(d2) + self.domainHorizontalLabelWidth) + " , " + w(d2) + ")";
                  break;
                // case "right":
                case "left":
                  s += "translate(-" + self.domainHorizontalLabelWidth + " , " + self.domainHorizontalLabelWidth + ")";
                  break;
              }
              return s;
            });
            break;
        }
      }
      if (options.subDomainTextFormat !== null) {
        rect.append("text").attr("class", function (d2) {
          return "subdomain-text" + self.getHighlightClassName(d2.t);
        }).attr("x", function (d2) {
          return self.positionSubDomainX(d2.t) + options.cellSize / 2;
        }).attr("y", function (d2) {
          return self.positionSubDomainY(d2.t) + options.cellSize / 2;
        }).attr("text-anchor", "middle").attr("dominant-baseline", "central").text(function (d2) {
          return self.formatDate(new Date(d2.t), options.subDomainTextFormat);
        });
      }
      if (navigationDir !== false) {
        // משפיע על האנימציה במעבר שנה
        domainSvg.transition().duration(options.animationDuration).attr("x", function (d2) {
          // השורה הבאה עושה בעיות אחרי העריכה לימין ושמאל
          // return options.verticalOrientation ? 0 : self.domainPosition.getPosition(d2)
          return 0;
        }).attr("y", function (d2) {
          return options.verticalOrientation ? self.domainPosition.getPosition(d2) : 0;
        });
      }
      var tempWidth = self.graphDim.width;
      var tempHeight = self.graphDim.height;
      if (options.verticalOrientation) {
        self.graphDim.height += enteringDomainDim - exitingDomainDim;
      } else {
        self.graphDim.width += enteringDomainDim - exitingDomainDim;
      }
      domainSvg.exit().transition().duration(options.animationDuration).attr("x", function (d2) {
        if (options.verticalOrientation) {
          return 0;
        } else {
          switch (navigationDir) {
            // מימין לשמאל במעבר לשנה אחרת. משפיע רק על השנה שהיתה
            case self.NAVIGATE_RIGHT:

              return Math.min(self.graphDim.width, tempWidth);
            case self.NAVIGATE_LEFT:
              return -w(d2, true);
          }
        }
      }).attr("y", function (d2) {
        if (options.verticalOrientation) {
          switch (navigationDir) {
            case self.NAVIGATE_LEFT:
              return Math.min(self.graphDim.height, tempHeight);
            case self.NAVIGATE_RIGHT:
              return -h(d2, true);
          }
        } else {
          return 0;
        }
      }).remove();
      self.resize();
    };
  };
  CalHeatMap.prototype = {
    init: function (settings) {
      var parent = this;
      var options = parent.options = mergeRecursive(parent.options, settings);
      var amount = this.options.amount;
      validateDomainType();
      validateSelector(options.itemSelector, false, "itemSelector");
      if (parent.allowedDataType.indexOf(options.dataType) === -1) {
        throw new Error("The data type '" + options.dataType + "' is not valid data type");
      }
      if (d3.select(options.itemSelector)[0][0] === null) {
        throw new Error("The node '" + options.itemSelector + "' specified in itemSelector does not exist");
      }
      try {
        validateSelector(options.nextSelector, true, "nextSelector");
        validateSelector(options.previousSelector, true, "previousSelector");
      } catch (error) {
        console.log(error.message);
        return false;
      }
      if (!settings.hasOwnProperty("subDomain")) {
        this.options.subDomain = getOptimalSubDomain(settings.domain);
      }
      if (typeof options.itemNamespace !== "string" || options.itemNamespace === "") {
        console.log("itemNamespace can not be empty, falling back to cal-heatmap");
        options.itemNamespace = "cal-heatmap";
      }
      var s = ["data", "onComplete", "onClick", "afterLoad", "afterLoadData", "afterLoadPreviousDomain", "afterLoadNextDomain", "afterUpdate"];
      for (var k in s) {
        if (settings.hasOwnProperty(s[k])) {
          options[s[k]] = settings[s[k]];
        }
      }
      options.subDomainDateFormat = typeof options.subDomainDateFormat === "string" || typeof options.subDomainDateFormat === "function" ? options.subDomainDateFormat : this._domainType[options.subDomain].format.date;
      options.domainLabelFormat = typeof options.domainLabelFormat === "string" || typeof options.domainLabelFormat === "function" ? options.domainLabelFormat : this._domainType[options.domain].format.legend;
      options.subDomainTextFormat = typeof options.subDomainTextFormat === "string" && options.subDomainTextFormat !== "" || typeof options.subDomainTextFormat === "function" ? options.subDomainTextFormat : null;
      options.domainMargin = expandMarginSetting(options.domainMargin);
      options.legendMargin = expandMarginSetting(options.legendMargin);
      options.highlight = parent.expandDateSetting(options.highlight);
      options.itemName = expandItemName(options.itemName);
      options.colLimit = parseColLimit(options.colLimit);
      options.rowLimit = parseRowLimit(options.rowLimit);
      // המרת רשימות הימים לחיפוש מהיר לפי אפוק ולפי תאריך (תיקון #57/#446).
      // בחלק מגרסאות Cal-HeatMap זמן התא אינו זהה בדיוק לחצות המקומית.
      options.holy_days_set = options.holy_days ? new Set(options.holy_days) : null;
      options.hatch_days_set = options.hatch_days ? new Set(options.hatch_days) : null;
      options.holy_days_keys = buildSpecialDateKeys(options.holy_days);
      options.hatch_days_keys = buildSpecialDateKeys(options.hatch_days);
      if (!settings.hasOwnProperty("legendMargin")) {
        autoAddLegendMargin();
      }
      autoAlignLabel();
      function validateSelector(selector, canBeFalse, name) {
        if ((canBeFalse && selector === false || selector instanceof Element || typeof selector === "string") && selector !== "") {
          return true;
        }
        throw new Error("The " + name + " is not valid");
      }
      function getOptimalSubDomain(domain) {
        switch (domain) {
          case "year":
            return "month";
          case "month":
            return "day";
          case "week":
            return "day";
          case "day":
            return "hour";
          default:
            return "min";
        }
      }
      function validateDomainType() {
        if (!parent._domainType.hasOwnProperty(options.domain) || options.domain === "min" || options.domain.substring(0, 2) === "x_") {
          throw new Error("The domain '" + options.domain + "' is not valid");
        }
        if (!parent._domainType.hasOwnProperty(options.subDomain) || options.subDomain === "year") {
          throw new Error("The subDomain '" + options.subDomain + "' is not valid");
        }
        if (parent._domainType[options.domain].level <= parent._domainType[options.subDomain].level) {
          throw new Error("'" + options.subDomain + "' is not a valid subDomain to '" + options.domain + "'");
        }
        return true;
      }
      function autoAlignLabel() {
        if (!settings.hasOwnProperty("label") || settings.hasOwnProperty("label") && !settings.label.hasOwnProperty("align")) {
          switch (options.label.position) {
            case "left":
              options.label.align = "right";
              break;
            case "right":
              options.label.align = "left";
              break;
            default:
              options.label.align = "center";
          }
          if (options.label.rotate === "left") {
            options.label.align = "right";
          } else if (options.label.rotate === "right") {
            options.label.align = "left";
          }
        }
        if (!settings.hasOwnProperty("label") || settings.hasOwnProperty("label") && !settings.label.hasOwnProperty("offset")) {
          if (options.label.position === "left" || options.label.position === "right") {
            options.label.offset = {
              x: 10,
              y: 15
            };
          }
        }
      }
      function autoAddLegendMargin() {
        switch (options.legendVerticalPosition) {
          case "top":
            options.legendMargin[2] = parent.DEFAULT_LEGEND_MARGIN;
            break;
          case "bottom":
            options.legendMargin[0] = parent.DEFAULT_LEGEND_MARGIN;
            break;
          case "middle":
          case "center":
            options.legendMargin[options.legendHorizontalPosition === "right" ? 3 : 1] = parent.DEFAULT_LEGEND_MARGIN;
        }
      }
      function expandMarginSetting(value) {
        if (typeof value === "number") {
          value = [value];
        }
        if (!Array.isArray(value)) {
          console.log("Margin only takes an integer or an array of integers");
          value = [0];
        }
        switch (value.length) {
          case 1:
            return [value[0], value[0], value[0], value[0]];
          case 2:
            return [value[0], value[1], value[0], value[1]];
          case 3:
            return [value[0], value[1], value[2], value[1]];
          case 4:
            return value;
          default:
            return value.slice(0, 4);
        }
      }
      function expandItemName(value) {
        if (typeof value === "string") {
          return [value, value + (value !== "" ? "s" : "")];
        }
        if (Array.isArray(value)) {
          if (value.length === 1) {
            return [value[0], value[0] + "s"];
          } else if (value.length > 2) {
            return value.slice(0, 2);
          }
          return value;
        }
        return ["item", "items"];
      }
      function parseColLimit(value) {
        return value > 0 ? value : null;
      }
      function parseRowLimit(value) {
        if (value > 0 && options.colLimit > 0) {
          console.log("colLimit and rowLimit are mutually exclusive, rowLimit will be ignored");
          return null;
        }
        return value > 0 ? value : null;
      }
      return this._init();
    },
    expandDateSetting: function (value) {
      if (!Array.isArray(value)) {
        value = [value];
      }
      return value.map(function (data) {
        if (data === "now") {
          return new Date();
        }
        if (data instanceof Date) {
          return data;
        }
        return false;
      }).filter(function (d) {
        return d !== false;
      });
    },
    fill: function (svg) {
      var parent = this;
      var options = parent.options;
      if (arguments.length === 0) {
        svg = parent.root.selectAll(".graph-domain");
      }
      var rect = svg.selectAll("svg").selectAll("g").data(function (d) {
        return parent._domains.get(d);
      });
      function addStyle(element) {
        if (parent.legendScale === null) {
          return false;
        }
        element.attr("fill", function (d) {
          // קובע האם התאים יצבעו לפי אחוזים או לפי כמות |\
          
          var cell_color_logic = options.amount ? d.a : d.v;

          // נלמדו רק כרטיסים חדשים (לא חלק מהתזמון) — הצג גוון בהיר מינימלי
          if (!options.amount && (cell_color_logic === 0 || cell_color_logic === null) && d.n > 0) {
            cell_color_logic = 0.1;
          }

          if (
            cell_color_logic === null &&
            options.hasOwnProperty("considerMissingDataAsZero") &&
            !options.considerMissingDataAsZero
          ) {
            if (options.legendColors.hasOwnProperty("base")) {
              return options.legendColors.base;
            }
          }
          if (
            options.legendColors !== null &&
            options.legendColors.hasOwnProperty("empty") &&
            (cell_color_logic === 0 ||
              (cell_color_logic === null &&
                options.hasOwnProperty("considerMissingDataAsZero") &&
                options.considerMissingDataAsZero))
          ) {
            return options.legendColors.empty;
          }
          if (
            cell_color_logic < 0 &&
            options.legend[0] > 0 &&
            options.legendColors !== null &&
            options.legendColors.hasOwnProperty("overflow")
          ) {
            return options.legendColors.overflow;
          }
          return parent.legendScale(
            Math.min(
              cell_color_logic,
              options.legend[options.legend.length - 1]
            )
          );
        });
      }
      rect.transition().duration(options.animationDuration).select("rect").attr("class", function (d) {
        var cell_color_logic = options.amount ? d.a : d.v;
        if (!options.amount && (cell_color_logic === 0 || cell_color_logic === null) && d.n > 0) {
          cell_color_logic = 0.1;
        }
        var htmlClass = parent.getHighlightClassName(d.t).trim().split(" ");
        var pastDate = parent.dateIsLessThan(d.t, new Date());
        var sameDate = parent.dateIsEqual(d.t, new Date());
        //משפיע על תאים ריקים עתידיים|\
        if (parent.legendScale === null || cell_color_logic === null && (options.hasOwnProperty("considerMissingDataAsZero") && !options.considerMissingDataAsZero) && !options.legendColors.hasOwnProperty("base")) {
          htmlClass.push("graph-rect");
        }
        if (sameDate) {
          htmlClass.push("now");
        } else if (!pastDate) {
          htmlClass.push("future");
        }

        if (cell_color_logic !== null) {
          htmlClass.push(parent.Legend.getClass(cell_color_logic, parent.legendScale === null));
        } else if (options.considerMissingDataAsZero && pastDate) {
          htmlClass.push(parent.Legend.getClass(0, parent.legendScale === null));
        }
        if (options.onClick !== null) {
          htmlClass.push("hover_cursor");
        }
        // אישיו #57/#446: זהב לכל חג; קווקו ביום אסור במלאכה שגם היום שאחריו אסור.
        var isHolyDay = hasSpecialDate(options.holy_days_set, options.holy_days_keys, d.t);
        var isHatchDay = hasSpecialDate(options.hatch_days_set, options.hatch_days_keys, d.t);
        // Reuse this cell's classification for its class and all stroke attributes.
        if (isHolyDay) {
          this.setAttribute("stroke", "#cc9900");
          this.setAttribute("stroke-width", "2");
        } else {
          this.removeAttribute("stroke");
          this.removeAttribute("stroke-width");
        }
        if (isHatchDay) {
          this.setAttribute("stroke-dasharray", "3 2");
        } else {
          this.removeAttribute("stroke-dasharray");
        }
        if (isHolyDay) {
          htmlClass.push("holy-day");
          if (isHatchDay) {
            htmlClass.push("holy-day-followed");
          }
        }
        return htmlClass.join(" ");
      }).call(addStyle);
      rect.transition().duration(options.animationDuration).select("title").text(function (d) {
        return parent.getSubDomainTitle(d);
      });
      function formatSubDomainText(element) {
        if (typeof options.subDomainTextFormat === "function") {
          element.text(function (d) {
            return options.subDomainTextFormat(d.t, d.v);
          });
        }
      }
      rect.transition().duration(options.animationDuration).select("text").attr("class", function (d) {
        return "subdomain-text" + parent.getHighlightClassName(d.t);
      }).call(formatSubDomainText);
    },
    formatStringWithObject: function (formatted, args) {
      for (var prop in args) {
        if (args.hasOwnProperty(prop)) {
          var regexp = new RegExp("\\{" + prop + "\\}", "gi");
          formatted = formatted.replace(regexp, args[prop]);
        }
      }
      return formatted;
    },
    triggerEvent: function (eventName, successArgs, skip) {
      if (arguments.length === 3 && skip || this.options[eventName] === null) {
        return true;
      }
      if (typeof this.options[eventName] === "function") {
        if (typeof successArgs === "function") {
          successArgs = successArgs();
        }
        return this.options[eventName].apply(this, successArgs);
      } else {
        console.log("Provided callback for " + eventName + " is not a function.");
        return false;
      }
    },
    onClick: function (d, itemNb) {
      return this.triggerEvent("onClick", [d, itemNb]);
    },
    afterLoad: function () {
      return this.triggerEvent("afterLoad");
    },
    onComplete: function () {
      var response = this.triggerEvent("onComplete", [], this._completed);
      this._completed = true;
      return response;
    },
    afterLoadPreviousDomain: function (start) {
      var parent = this;
      return this.triggerEvent("afterLoadPreviousDomain", function () {
        var subDomain = parent.getSubDomain(start);
        return [subDomain.shift(), subDomain.pop()];
      });
    },
    afterLoadNextDomain: function (start) {
      var parent = this;
      return this.triggerEvent("afterLoadNextDomain", function () {
        var subDomain = parent.getSubDomain(start);
        return [subDomain.shift(), subDomain.pop()];
      });
    },
    onMinDomainReached: function (reached) {
      this._minDomainReached = reached;
      return this.triggerEvent("onMinDomainReached", [reached]);
    },
    onMaxDomainReached: function (reached) {
      this._maxDomainReached = reached;
      return this.triggerEvent("onMaxDomainReached", [reached]);
    },
    checkIfMinDomainIsReached: function (date, upperBound) {
      if (this.minDomainIsReached(date)) {
        this.onMinDomainReached(true);
      }
      if (arguments.length === 2) {
        if (this._maxDomainReached && !this.maxDomainIsReached(upperBound)) {
          this.onMaxDomainReached(false);
        }
      }
    },
    checkIfMaxDomainIsReached: function (date, lowerBound) {
      if (this.maxDomainIsReached(date)) {
        this.onMaxDomainReached(true);
      }
      if (arguments.length === 2) {
        if (this._minDomainReached && !this.minDomainIsReached(lowerBound)) {
          this.onMinDomainReached(false);
        }
      }
    },
    afterUpdate: function () {
      return this.triggerEvent("afterUpdate");
    },
    formatNumber: d3.format(",g"),
    formatDate: function (d, format) {
      if (arguments.length < 2) {
        format = "title";
      }
      if (typeof format === "function") {
        return format(d);
      } else {
        var f = d3.time.format(format);
        return f(d);
      }
    },
    getSubDomainTitle: function (d) {
      if (d.v === null && !this.options.considerMissingDataAsZero) {
        var emptyObject = {
          // תאריך עברי על הטולטיפ
          date: Convert_date_to_heb(new Date(d.t)),
          // date: this.formatDate(new Date(d.t), this.options.subDomainDateFormat)
        };
        if (typeof this.options.subDomainTitleFormat === "function") {
          return this.options.subDomainTitleFormat(true, emptyObject, d);
        } else {
          return this.formatStringWithObject(this.options.subDomainTitleFormat.empty, emptyObject);
        }
      } else {
        var value = d.v;
        var sch = d.s;
        var news = d.n;
        var ans = d.a;
        if (value === null && this.options.considerMissingDataAsZero) {
          value = 0;
        }
        var object = {
          per: this.formatNumber(value),
          sch: this.formatNumber(sch),
          ans: this.formatNumber(ans),
          news: this.formatNumber(news),
          name: this.options.itemName[value !== 1 ? 1 : 0],
          connector: this._domainType[this.options.subDomain].format.connector,
          // תאריך עברי על הטולטיפ
         date: Convert_date_to_heb(new Date(d.t))
//           date: this.formatDate(new Date(d.t), this.options.subDomainDateFormat)
          //  date: this.formatDate(new Date(d.t), '%Y-%m-%d , %H:%M:%S')
        };
        if (typeof this.options.subDomainTitleFormat === "function") {
          return this.options.subDomainTitleFormat(false, object, d);
        } else {
          return this.formatStringWithObject(this.options.subDomainTitleFormat.filled, object);
        }
      }
    },
    loadNextDomain: function (n) {
      if (this._maxDomainReached || n === 0) {
        return false;
      }
      var bound = this.loadNewDomains(this.NAVIGATE_RIGHT, this.getDomain(this.getNextDomain(), n));
      this.afterLoadNextDomain(bound.end);
      this.checkIfMaxDomainIsReached(this.getNextDomain().getTime(), bound.start);
      return true;
    },
    loadPreviousDomain: function (n) {
      if (this._minDomainReached || n === 0) {
        return false;
      }
      var bound = this.loadNewDomains(this.NAVIGATE_LEFT, this.getDomain(this.getDomainKeys()[0], -n).reverse());
      this.afterLoadPreviousDomain(bound.start);
      this.checkIfMinDomainIsReached(bound.start, bound.end);
      return true;
    },
    loadNewDomains: function (direction, newDomains) {
      var parent = this;
      var backward = direction === this.NAVIGATE_LEFT;
      var i = -1;
      var total = newDomains.length;
      var domains = this.getDomainKeys();
      function buildSubDomain(d) {
        return { t: parent._domainType[parent.options.subDomain].extractUnit(d), v: null };
      }
      while (++i < total) {
        if (backward && this.minDomainIsReached(newDomains[i])) {
          newDomains = newDomains.slice(0, i + 1);
          break;
        }
        if (!backward && this.maxDomainIsReached(newDomains[i])) {
          newDomains = newDomains.slice(0, i);
          break;
        }
      }
      newDomains = newDomains.slice(-this.options.range);
      for (i = 0, total = newDomains.length; i < total; i++) {
        this._domains.set(newDomains[i].getTime(), this.getSubDomain(newDomains[i]).map(buildSubDomain));
        this._domains.remove(backward ? domains.pop() : domains.shift());
      }
      domains = this.getDomainKeys();
      if (backward) {
        newDomains = newDomains.reverse();
      }
      this.paint(direction);
      this.getDatas(this.options.data, newDomains[0], this.getSubDomain(newDomains[newDomains.length - 1]).pop(), function () {
        parent.fill(parent.lastInsertedSvg);
      });
      return {
        start: newDomains[backward ? 0 : 1],
        end: domains[domains.length - 1]
      };
    },
    maxDomainIsReached: function (datetimestamp) {
            // console.log(this.options.maxDate !== null && this.options.maxDate.getTime() < datetimestamp)

      return this.options.maxDate !== null && this.options.maxDate.getTime() < datetimestamp;
    },
    minDomainIsReached: function (datetimestamp) {
      return this.options.minDate !== null && this.options.minDate.getTime() >= datetimestamp;
    },
    getDomainKeys: function () {
      return this._domains.keys().map(function (d) {
        return parseInt(d, 10);
      }).sort(function (a, b) {
        return a - b;
      });
    },
    positionSubDomainX: function (d) {
      var index = this._domainType[this.options.subDomain].position.x(new Date(d));
      // יישור מימין לשמאל של הלוח שנה
      var posxltr = index * this.options.cellSize + index * this.options.cellPadding;
      // var maxiwidth = self.options.cellSize * self._domainType[self.options.subDomain].column(d2) + self.options.cellPadding * self._domainType[self.options.subDomain].column(d2);
      //todo: לסדר את הלוח שנה ממורכז ולבטל את החישוב של רוחב השנה לכל אחד מהתאים בנפרד.
      var num_days = get_rosh(d,0,'num_days');
      var width = (Math.round(num_days / 7) * (this.options.cellSize + this.options.cellPadding)) + 12;
      return (width - posxltr) / 15 + "vw";
      // return index * this.options.cellSize + index * this.options.cellPadding;
    },
    positionSubDomainY: function (d) {
      var index = this._domainType[this.options.subDomain].position.y(new Date(d));
      return index * this.options.cellSize + index * this.options.cellPadding;
    },
    getSubDomainColumnNumber: function (d) {
      if (this.options.rowLimit > 0) {
        var i = this._domainType[this.options.subDomain].maxItemNumber;
        if (typeof i === "function") {
          i = i(d);
        }
        return Math.ceil(i / this.options.rowLimit);
      }
      var j = this._domainType[this.options.subDomain].defaultColumnNumber;
      if (typeof j === "function") {
        j = j(d);
      }
      return this.options.colLimit || j;
    },
    getSubDomainRowNumber: function (d) {
      if (this.options.colLimit > 0) {
        var i = this._domainType[this.options.subDomain].maxItemNumber;
        if (typeof i === "function") {
          i = i(d);
        }
        return Math.ceil(i / this.options.colLimit);
      }
      var j = this._domainType[this.options.subDomain].defaultRowNumber;
      if (typeof j === "function") {
        j = j(d);
      }
      return this.options.rowLimit || j;
    },
    getHighlightClassName: function (d) {
      d = new Date(d);
      if (this.options.highlight.length > 0) {
        for (var i in this.options.highlight) {
          if (this.dateIsEqual(this.options.highlight[i], d)) {
            return this.isNow(this.options.highlight[i]) ? " highlight-now" : " highlight";
          }
        }
      }
      return "";
    },
    isNow: function (d) {
      return this.dateIsEqual(d, this.options.today);
    },
    dateIsEqual: function (dateA, dateB) {
      if (!(dateA instanceof Date)) {
        dateA = new Date(dateA);
      }
      if (!(dateB instanceof Date)) {
        dateB = new Date(dateB);
      }
      switch (this.options.subDomain) {
        case "x_min":
        case "min":
          return dateA.getFullYear() === dateB.getFullYear() && dateA.getMonth() === dateB.getMonth() && dateA.getDate() === dateB.getDate() && dateA.getHours() === dateB.getHours() && dateA.getMinutes() === dateB.getMinutes();
        case "x_hour":
        case "hour":
          return dateA.getFullYear() === dateB.getFullYear() && dateA.getMonth() === dateB.getMonth() && dateA.getDate() === dateB.getDate() && dateA.getHours() === dateB.getHours();
        case "x_day":
        case "day":
          return dateA.getFullYear() === dateB.getFullYear() && dateA.getMonth() === dateB.getMonth() && dateA.getDate() === dateB.getDate();
        case "x_week":
        case "week":
          return dateA.getFullYear() === dateB.getFullYear() && this.getWeekNumber(dateA) === this.getWeekNumber(dateB);
        case "x_month":
        case "month":
          return dateA.getFullYear() === dateB.getFullYear() && dateA.getMonth() === dateB.getMonth();
        default:
          return false;
      }
    },
    dateIsLessThan: function (dateA, dateB) {
      if (!(dateA instanceof Date)) {
        dateA = new Date(dateA);
      }
      if (!(dateB instanceof Date)) {
        dateB = new Date(dateB);
      }
      function normalizedMillis(date, subdomain) {
        switch (subdomain) {
          case "x_min":
          case "min":
            return new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes()).getTime();
          case "x_hour":
          case "hour":
            return new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours()).getTime();
          case "x_day":
          case "day":
            return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
          case "x_week":
          case "week":
          case "x_month":
          case "month":
            return new Date(date.getFullYear(), date.getMonth()).getTime();
          default:
            return date.getTime();
        }
      }
      return normalizedMillis(dateA, this.options.subDomain) < normalizedMillis(dateB, this.options.subDomain);
    },
    getDayOfYear: d3.time.format("%j"),
    getWeekNumber: function (d) {
      // !!!
      // var f = this.options.weekStartOnMonday === true ? d3.time.format("%W") : d3.time.format("%U");
      // return f(d);
      var rosh = get_rosh(d);
      var rosh_d = new Date(rosh);

      var day_of_rosh = rosh_d.getDay();
      var day_of_first_week = rosh + (86400000 * 7) - (day_of_rosh * 86400000);

      if (d < day_of_first_week) return 0;
      return Math.floor((d - day_of_first_week) / 86400000 / 7) + 1;
    },
    getMonthWeekNumber: function (d) {
      if (typeof d === "number") {
        d = new Date(d);
      }
      var monthFirstWeekNumber = this.getWeekNumber(new Date(d.getFullYear(), d.getMonth()));
      return this.getWeekNumber(d) - monthFirstWeekNumber - 1;
    },
    getWeekNumberInYear: function (d) {
    },
    getDayCountInMonth: function (d) {
      return this.getEndOfMonth(d).getDate();
    },
    getDayCountInYear: function (d) {
      if (typeof d === "number") {
        d = new Date(d);
      }
      // !!!
      var rosh = get_rosh(d);
      return get_rosh(rosh, 0, 'num_days');

      // return get_num_in_year(rosh);
      // return new Date(d.getFullYear(), 1, 29).getMonth() === 1 ? 366 : 365;
    },
    getWeekDay: function (d) {
      if (this.options.weekStartOnMonday === false) {
        return d.getDay();
      }
      return d.getDay() === 0 ? 6 : d.getDay() - 1;
    },
    getEndOfMonth: function (d) {
      if (typeof d === "number") {
        d = new Date(d);
      }
      return new Date(d.getFullYear(), d.getMonth() + 1, 0);
    },
    jumpDate: function (date, count, step) {
      var d = new Date(date);
      switch (step) {
        case "hour":
          d.setHours(d.getHours() + count);
          break;
        case "day":
          d.setHours(d.getHours() + count * 24);
          break;
        case "week":
          d.setHours(d.getHours() + count * 24 * 7);
          break;
        case "month":
          d.setMonth(d.getMonth() + count);
          break;
        case "year":
          // d.setFullYear(d.getFullYear() + count);
          // !!!
          d = get_rosh(d, count);
      }
      return new Date(d);
    },
    getMinuteDomain: function (d, range) {
      var start = new Date(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours());
      var stop = null;
      if (range instanceof Date) {
        stop = new Date(range.getFullYear(), range.getMonth(), range.getDate(), range.getHours());
      } else {
        stop = new Date(+start + range * 1e3 * 60);
      }
      return d3.time.minutes(Math.min(start, stop), Math.max(start, stop));
    },
    getHourDomain: function (d, range) {
      var start = new Date(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours());
      var stop = null;
      if (range instanceof Date) {
        stop = new Date(range.getFullYear(), range.getMonth(), range.getDate(), range.getHours());
      } else {
        stop = new Date(start);
        stop.setHours(stop.getHours() + range);
      }
      var domains = d3.time.hours(Math.min(start, stop), Math.max(start, stop));
      var i = 0;
      var total = domains.length;
      for (i = 0; i < total; i++) {
        if (i > 0 && domains[i].getHours() === domains[i - 1].getHours()) {
          this.DSTDomain.push(domains[i].getTime());
          domains.splice(i, 1);
          break;
        }
      }
      if (typeof range === "number" && domains.length > Math.abs(range)) {
        domains.splice(domains.length - 1, 1);
      }
      return domains;
    },
    getDayDomain: function (d, range) {
      var start = new Date(d.getFullYear(), d.getMonth(), d.getDate());
      var stop = null;
      if (range instanceof Date) {
        stop = new Date(range.getFullYear(), range.getMonth(), range.getDate());
      } else {
        stop = new Date(start);
        stop = new Date(stop.setDate(stop.getDate() + parseInt(range, 10)));
      }
      return d3.time.days(Math.min(start, stop), Math.max(start, stop));
    },
    getWeekDomain: function (d, range) {
      var weekStart;
      if (this.options.weekStartOnMonday === false) {
        weekStart = new Date(d.getFullYear(), d.getMonth(), d.getDate() - d.getDay());
      } else {
        if (d.getDay() === 1) {
          weekStart = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        } else if (d.getDay() === 0) {
          weekStart = new Date(d.getFullYear(), d.getMonth(), d.getDate());
          weekStart.setDate(weekStart.getDate() - 6);
        } else {
          weekStart = new Date(d.getFullYear(), d.getMonth(), d.getDate() - d.getDay() + 1);
        }
      }
      var endDate = new Date(weekStart);
      var stop = range;
      if (typeof range !== "object") {
        stop = new Date(endDate.setDate(endDate.getDate() + range * 7));
      }
      return this.options.weekStartOnMonday === true ? d3.time.mondays(Math.min(weekStart, stop), Math.max(weekStart, stop)) : d3.time.sundays(Math.min(weekStart, stop), Math.max(weekStart, stop));
    },
    getMonthDomain: function (d, range) {
      var start = new Date(d.getFullYear(), d.getMonth());
      var stop = null;
      if (range instanceof Date) {
        stop = new Date(range.getFullYear(), range.getMonth());
      } else {
        stop = new Date(start);
        stop = stop.setMonth(stop.getMonth() + range);
      }
      return d3.time.months(Math.min(start, stop), Math.max(start, stop));
    },
    getYearDomain: function (d, range) {
      var start = new Date(d.getFullYear(), 0);
      var stop = null;
      if (range instanceof Date) {
        stop = new Date(range.getFullYear(), 0);
        d = new Date();
        range = 1;

      } else {
        stop = new Date(d.getFullYear() + range, 0);
      }
      // return d3.time.years(Math.min(start, stop), Math.max(start, stop));
      // !!!
      var y = [];
      var c = 0;
      if (range > 0) c = range - 1;
      else c = range;
      var rosh = get_rosh(d, c);
      y.push(new Date(rosh));
      return y;
    },
    getDomain: function (date, range) {
      if (typeof date === "number") {
        date = new Date(date);
      }
      if (arguments.length < 2) {
        range = this.options.range;
      }
      switch (this.options.domain) {
        // קובע את הצבע
        case "hour":
          var domains = this.getHourDomain(date, range);
          if (typeof range === "number" && domains.length < range) {
            if (range > 0) {
              domains.push(this.getHourDomain(domains[domains.length - 1], 2)[1]);
            } else {
              domains.shift(this.getHourDomain(domains[0], -2)[0]);
            }
          }
          return domains;
        case "day":
          return this.getDayDomain(date, range);
        case "week":
          return this.getWeekDomain(date, range);
        case "month":
          return this.getMonthDomain(date, range);
        case "year":
          return this.getYearDomain(date, range);
      }
    },
    getSubDomain: function (date) {
      if (typeof date === "number") {
        date = new Date(date);
      }
      var parent = this;
      var computeDaySubDomainSize = function (date2, domain) {
        switch (domain) {
          case "year":
            return parent.getDayCountInYear(date2);
          case "month":
            return parent.getDayCountInMonth(date2);
          case "week":
            return 7;
        }
      };
      var computeMinSubDomainSize = function (date2, domain) {
        switch (domain) {
          case "hour":
            return 60;
          case "day":
            return 60 * 24;
          case "week":
            return 60 * 24 * 7;
        }
      };
      var computeHourSubDomainSize = function (date2, domain) {
        switch (domain) {
          case "day":
            return 24;
          case "week":
            return 168;
          case "month":
            return parent.getDayCountInMonth(date2) * 24;
        }
      };
      var computeWeekSubDomainSize = function (date2, domain) {
        if (domain === "month") {
          var endOfMonth = new Date(date2.getFullYear(), date2.getMonth() + 1, 0);
          var endWeekNb = parent.getWeekNumber(endOfMonth);
          var startWeekNb = parent.getWeekNumber(new Date(date2.getFullYear(), date2.getMonth()));
          if (startWeekNb > endWeekNb) {
            startWeekNb = 0;
            endWeekNb++;
          }
          return endWeekNb - startWeekNb + 1;
        } else if (domain === "year") {
          return parent.getWeekNumber(new Date(date2.getFullYear(), 11, 31));
        }
      };
      switch (this.options.subDomain) {
        case "x_min":
        case "min":
          return this.getMinuteDomain(date, computeMinSubDomainSize(date, this.options.domain));
        case "x_hour":
        case "hour":
          return this.getHourDomain(date, computeHourSubDomainSize(date, this.options.domain));
        case "x_day":
        case "day":
          return this.getDayDomain(date, computeDaySubDomainSize(date, this.options.domain));
        case "x_week":
        case "week":
          return this.getWeekDomain(date, computeWeekSubDomainSize(date, this.options.domain));
        case "x_month":
        case "month":
          return this.getMonthDomain(date, 12);
      }
    },
    getNextDomain: function (n) {
      if (arguments.length === 0) {
        n = 1;
      }
      return this.getDomain(this.jumpDate(this.getDomainKeys().pop(), n, this.options.domain), 1)[0];
    },
    getPreviousDomain: function (n) {
      if (arguments.length === 0) {
        n = 1;
      }
      return this.getDomain(this.jumpDate(this.getDomainKeys().shift(), -n, this.options.domain), 1)[0];
    },
    getDatas: function (source, startDate, endDate, callback, afterLoad, updateMode) {
      var self = this;
      if (arguments.length < 5) {
        afterLoad = true;
      }
      if (arguments.length < 6) {
        updateMode = this.APPEND_ON_UPDATE;
      }
      var _callback = function (error, data) {
        if (afterLoad !== false) {
          if (typeof afterLoad === "function") {
            data = afterLoad(data);
          } else if (typeof self.options.afterLoadData === "function") {
            data = self.options.afterLoadData(data);
          } else {
            console.log("Provided callback for afterLoadData is not a function.");
          }
        } else if (self.options.dataType === "csv" || self.options.dataType === "tsv") {
          data = this.interpretCSV(data);
        }
        self.parseDatas(data, updateMode, startDate, endDate);
        if (typeof callback === "function") {
          callback();
        }
      };
      switch (typeof source) {
        case "string":
          if (source === "") {
            _callback(null, {});
            return true;
          } else {
            var url = this.parseURI(source, startDate, endDate);
            var requestType = "GET";
            if (self.options.dataPostPayload !== null) {
              requestType = "POST";
            }
            var payload = null;
            if (self.options.dataPostPayload !== null) {
              payload = this.parseURI(self.options.dataPostPayload, startDate, endDate);
            }
            var xhr = null;
            switch (this.options.dataType) {
              case "json":
                xhr = d3.json(url);
                break;
              case "csv":
                xhr = d3.csv(url);
                break;
              case "tsv":
                xhr = d3.tsv(url);
                break;
              case "txt":
                xhr = d3.text(url, "text/plain");
                break;
            }
            if (self.options.dataRequestHeaders !== null) {
              for (var header in self.options.dataRequestHeaders) {
                if (self.options.dataRequestHeaders.hasOwnProperty(header)) {
                  xhr.header(header, self.options.dataRequestHeaders[header]);
                }
              }
            }
            xhr.send(requestType, payload, _callback);
          }
          return false;
        case "object":
          if (source === Object(source)) {
            _callback(null, source);
            return false;
          }
        default:
          _callback(null, {});
          return true;
      }
    },
    parseDatas: function (data, updateMode, startDate, endDate) {
      if (updateMode === this.RESET_ALL_ON_UPDATE) {
        this._domains.forEach(function (key, value) {
          value.forEach(function (element, index2, array) {
            array[index2].v = null;
          });
        });
      }
      var temp = {};
      var extractTime = function (d2) {
        return d2.t;
      };
      for (var d in data) {
        var date = new Date(d * 1e3);
        var domainUnit = this.getDomain(date)[0].getTime();
        if (this.DSTDomain.indexOf(domainUnit) >= 0) {
          if (this._domains.has(domainUnit - 3600 * 1e3)) {
            domainUnit -= 3600 * 1e3;
          }
        }

        if (isNaN(d) || !data.hasOwnProperty(d) || !this._domains.has(domainUnit) || !(domainUnit >= +startDate && domainUnit < +endDate)) {
          continue;
        }
        var subDomainsData = this._domains.get(domainUnit);
        if (!temp.hasOwnProperty(domainUnit)) {
          temp[domainUnit] = subDomainsData.map(extractTime);
        }
        // מאכלס את הערך!!!
        var index = temp[domainUnit].indexOf(this._domainType[this.options.subDomain].extractUnit(date));
        // if (updateMode === this.RESET_SINGLE_ON_UPDATE) {
        //   subDomainsData[index].v = data[d];
        // } else {
        //   if (!isNaN(subDomainsData[index].v)) {
        //     subDomainsData[index].v += data[d];
        //   } else {
        //     subDomainsData[index].v = data[d];
        //   }
        // }
        if (subDomainsData[index]) {
          // כמות שתוזמנו 
          subDomainsData[index].s = data[d][0];
          // סהכ כרטיסים חדשים 
          subDomainsData[index].n = data[d][1];
          // כמות שנענו
          subDomainsData[index].a = data[d][2];
          // האחוזים - משפיע על הצבע
          subDomainsData[index].v = data[d][3];
          // סהכ כרטיסים שנענו 
          subDomainsData[index].c = data[d][4];
          // סהכ כרטיסים מתוזמנים שהושלמו
          subDomainsData[index].d = data[d][5];
        }
      }
    },
    parseURI: function (str, startDate, endDate) {
      str = str.replace(/\{\{t:start\}\}/g, startDate.getTime() / 1e3);
      str = str.replace(/\{\{t:end\}\}/g, endDate.getTime() / 1e3);
      str = str.replace(/\{\{d:start\}\}/g, startDate.toISOString());
      str = str.replace(/\{\{d:end\}\}/g, endDate.toISOString());
      return str;
    },
    interpretCSV: function (data) {
      var d = {};
      var keys = Object.keys(data[0]);
      var i, total;
      for (i = 0, total = data.length; i < total; i++) {
        d[data[i][keys[0]]] = +data[i][keys[1]];
      }
      return d;
    },
    resize: function () {
      var parent = this;
      var options = parent.options;
      var legendWidth = options.displayLegend ? parent.Legend.getDim("width") + options.legendMargin[1] + options.legendMargin[3] : 0;
      var legendHeight = options.displayLegend ? parent.Legend.getDim("height") + options.legendMargin[0] + options.legendMargin[2] : 0;
      var graphWidth = parent.graphDim.width - options.domainGutter - options.cellPadding;
      var graphHeight = parent.graphDim.height - options.domainGutter - options.cellPadding;
      var dayLabelWidth = 0;
      if (options.dayLabel && options.domain === "month" && options.subDomain === "day") {
        dayLabelWidth = options.cellSize + options.cellPadding;
      }
      // קונטיינר ראשי
      this.root.transition().duration(options.animationDuration).attr("width", function () {
        if (options.legendVerticalPosition === "middle" || options.legendVerticalPosition === "center") {
          return (graphWidth + legendWidth + dayLabelWidth) / 15 + "vw";
        }
        return (Math.max(graphWidth, legendWidth) + dayLabelWidth) / 15 + "vw";
      }).attr("height", function () {
        if (options.legendVerticalPosition === "middle" || options.legendVerticalPosition === "center") {
          return Math.max(graphHeight, legendHeight);
        }
        return graphHeight + legendHeight;
      });
      this.root.select(".graph").transition().duration(options.animationDuration).attr("y", function () {
        if (options.legendVerticalPosition === "top") {
          return legendHeight;
        }
        return 0;
      }).attr("x", function () {
        if ((options.legendVerticalPosition === "middle" || options.legendVerticalPosition === "center") && options.legendHorizontalPosition === "left") {
          return legendWidth + dayLabelWidth;
        }
        return dayLabelWidth;
      });
    },
    next: function (n) {
      if (arguments.length === 0) {
        n = 1;
      }
      return this.loadNextDomain(n);
    },
    previous: function (n) {
      if (arguments.length === 0) {
        n = 1;
      }
      return this.loadPreviousDomain(n);
    },
    jumpTo: function (date, reset) {
      if (arguments.length < 2) {
        reset = false;
      }
      var domains = this.getDomainKeys();
      // !!!
      // var firstDomain = domains[0];
      // var lastDomain = domains[domains.length - 1];
      var currentDomain = domains[0];
      var date_key = get_rosh(date, 0, 'key');
      var currentDomain_key = get_rosh(currentDomain, 0, 'key');

      // if (date < firstDomain) {
      if (date < currentDomain) {

        return this.loadPreviousDomain(currentDomain_key - date_key);
        // return this.loadPreviousDomain(this.getDomain(firstDomain, date).length);
      } else {
        if (reset) {
          return this.loadNextDomain(date_key - currentDomain_key);
          // return this.loadNextDomain(this.getDomain(firstDomain, date).length);
        }
        if (date > currentDomain) {
          return this.loadNextDomain(date_key - currentDomain_key);
          // return this.loadNextDomain(this.getDomain(lastDomain, date).length);
        }
      }
      return false;
    },
    rewind: function () {
      this.jumpTo(this.options.start, true);
    },
    update: function (dataSource, afterLoad, updateMode) {
      if (arguments.length === 0) {
        dataSource = this.options.data;
      }
      if (arguments.length < 2) {
        afterLoad = true;
      }
      if (arguments.length < 3) {
        updateMode = this.RESET_ALL_ON_UPDATE;
      }
      var domains = this.getDomainKeys();
      var self = this;
      this.getDatas(dataSource, new Date(domains[0]), this.getSubDomain(domains[domains.length - 1]).pop(), function () {
        self.fill();
        self.afterUpdate();
      }, afterLoad, updateMode);
    },
    setLegend: function () {
      var oldLegend = this.options.legend.slice(0);
      if (arguments.length >= 1 && Array.isArray(arguments[0])) {
        this.options.legend = arguments[0];
      }
      if (arguments.length >= 2) {
        if (Array.isArray(arguments[1]) && arguments[1].length >= 2) {
          this.options.legendColors = [arguments[1][0], arguments[1][1]];
        } else {
          this.options.legendColors = arguments[1];
        }
      }
      if (arguments.length > 0 && !arrayEquals(oldLegend, this.options.legend) || arguments.length >= 2) {
        this.Legend.buildColors();
        this.fill();
      }
      this.Legend.redraw(this.graphDim.width - this.options.domainGutter - this.options.cellPadding);
    },
    removeLegend: function () {
      if (!this.options.displayLegend) {
        return false;
      }
      this.options.displayLegend = false;
      this.Legend.remove();
      return true;
    },
    showLegend: function () {
      if (this.options.displayLegend) {
        return false;
      }
      this.options.displayLegend = true;
      this.Legend.redraw(this.graphDim.width - this.options.domainGutter - this.options.cellPadding);
      return true;
    },
    highlight: function (args) {
      if ((this.options.highlight = this.expandDateSetting(args)).length > 0) {
        this.fill();
        return true;
      }
      return false;
    },
    destroy: function (callback) {
      this.root.transition().duration(this.options.animationDuration).attr("width", 0).attr("height", 0).remove().each("end", function () {
        if (typeof callback === "function") {
          callback();
        } else if (typeof callback !== "undefined") {
          console.log("Provided callback for destroy() is not a function.");
        }
      });
      return null;
    },
    getSVG: function () {
      var styles = {
        ".cal-heatmap-container": {},
        ".graph": {},
        ".graph-rect": {},
        "rect.highlight": {},
        "rect.now": {},
        "rect.highlight-now": {},
        "text.highlight": {},
        "text.now": {},
        "text.highlight-now": {},
        ".domain-background": {},
        ".graph-label": {},
        ".subdomain-text": {},
        ".q0": {},
        ".qi": {}
      };
      for (var j = 1, total = this.options.legend.length + 1; j <= total; j++) {
        styles[".q" + j] = {};
      }
      var root = this.root;
      var whitelistStyles = [
        "stroke",
        "stroke-width",
        "stroke-opacity",
        "stroke-dasharray",
        "stroke-dashoffset",
        "stroke-linecap",
        "stroke-miterlimit",
        "fill",
        "fill-opacity",
        "fill-rule",
        "marker",
        "marker-start",
        "marker-mid",
        "marker-end",
        "alignement-baseline",
        "baseline-shift",
        "dominant-baseline",
        "glyph-orientation-horizontal",
        "glyph-orientation-vertical",
        "kerning",
        "text-anchor",
        "shape-rendering",
        "text-transform",
        "font-family",
        "font",
        "font-size",
        "font-weight"
      ];
      var filterStyles = function (attribute, property, value) {
        if (whitelistStyles.indexOf(property) !== -1) {
          styles[attribute][property] = value;
        }
      };
      var getElement = function (e) {
        return root.select(e)[0][0];
      };
      for (var element in styles) {
        if (!styles.hasOwnProperty(element)) {
          continue;
        }
        var dom = getElement(element);
        if (dom === null) {
          continue;
        }
        if ("getComputedStyle" in window) {
          var cs = getComputedStyle(dom, null);
          if (cs.length !== 0) {
            for (var i = 0; i < cs.length; i++) {
              filterStyles(element, cs.item(i), cs.getPropertyValue(cs.item(i)));
            }
          } else {
            for (var k in cs) {
              if (cs.hasOwnProperty(k)) {
                filterStyles(element, k, cs[k]);
              }
            }
          }
        } else if ("currentStyle" in dom) {
          var css = dom.currentStyle;
          for (var p in css) {
            filterStyles(element, p, css[p]);
          }
        }
      }
      var string = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><style type="text/css"><![CDATA[ ';
      for (var style in styles) {
        string += style + " {\n";
        for (var l in styles[style]) {
          string += "	" + l + ":" + styles[style][l] + ";\n";
        }
        string += "}\n";
      }
      string += "]]></style>";
      string += new XMLSerializer().serializeToString(this.root[0][0]);
      string += "</svg>";
      return string;
    }
  };
  var DomainPosition = function () {
    this.positions = d3.map();
  };
  DomainPosition.prototype.getPosition = function (d) {
    return this.positions.get(d);
  };
  DomainPosition.prototype.getPositionFromIndex = function (i) {
    var domains = this.getKeys();
    return this.positions.get(domains[i]);
  };
  DomainPosition.prototype.getLast = function () {
    var domains = this.getKeys();
    return this.positions.get(domains[domains.length - 1]);
  };
  DomainPosition.prototype.setPosition = function (d, dim) {
    this.positions.set(d, dim);
  };
  DomainPosition.prototype.shiftRightBy = function (exitingDomainDim) {
    this.positions.forEach(function (key, value) {
      this.set(key, value - exitingDomainDim);
    });
    var domains = this.getKeys();
    this.positions.remove(domains[0]);
  };
  DomainPosition.prototype.shiftLeftBy = function (enteringDomainDim) {
    this.positions.forEach(function (key, value) {
      this.set(key, value + enteringDomainDim);
    });
    var domains = this.getKeys();
    this.positions.remove(domains[domains.length - 1]);
  };
  DomainPosition.prototype.getKeys = function () {
    return this.positions.keys().sort(function (a, b) {
      return parseInt(a, 10) - parseInt(b, 10);
    });
  };
  var Legend = function (calendar) {
    this.calendar = calendar;
    this.computeDim();
    if (calendar.options.legendColors !== null) {
      this.buildColors();
    }
  };
  Legend.prototype.computeDim = function () {
    var options = this.calendar.options;
    this.dim = {
      width: options.legendCellSize * (options.legend.length + 1) + options.legendCellPadding * options.legend.length,
      height: options.legendCellSize
    };
  };
  Legend.prototype.remove = function () {
    this.calendar.root.select(".graph-legend").remove();
    this.calendar.resize();
  };
  Legend.prototype.redraw = function (width) {
    if (!this.calendar.options.displayLegend) {
      return false;
    }
    var parent = this;
    var calendar = this.calendar;
    var legend = calendar.root;
    var legendItem;
    var options = calendar.options;
    this.computeDim();
    var _legend = options.legend.slice(0);
    _legend.push(_legend[_legend.length - 1] + 1);
    var legendElement = calendar.root.select(".graph-legend");
    if (legendElement[0][0] !== null) {
      legend = legendElement;
      legendItem = legend.select("g").selectAll("rect").data(_legend);
    } else {
      legend = options.legendVerticalPosition === "top" ? legend.insert("svg", ".graph") : legend.append("svg");
      legend.attr("x", getLegendXPosition()).attr("y", getLegendYPosition());
      legendItem = legend.attr("class", "graph-legend").attr("height", parent.getDim("height")).attr("width", parent.getDim("width")).append("g").selectAll().data(_legend);
    }
    legendItem.enter().append("rect").call(legendCellLayout).attr("class", function (d) {
      return calendar.Legend.getClass(d, calendar.legendScale === null);
    }).attr("fill-opacity", 0).call(function (selection) {
      if (calendar.legendScale !== null && options.legendColors !== null && options.legendColors.hasOwnProperty("base")) {
        selection.attr("fill", options.legendColors.base);
      }
    }).append("title");
    legendItem.exit().transition().duration(options.animationDuration).attr("fill-opacity", 0).remove();
    legendItem.transition().delay(function (d, i) {
      return options.animationDuration * i / 10;
    }).call(legendCellLayout).attr("fill-opacity", 1).call(function (element) {
      element.attr("fill", function (d, i) {
        if (calendar.legendScale === null) {
          return "";
        }
        if (i === 0) {
          return calendar.legendScale(d - 1);
        }
        return calendar.legendScale(options.legend[i - 1]);
      });
      element.attr("class", function (d) {
        return calendar.Legend.getClass(d, calendar.legendScale === null);
      });
    });
    function legendCellLayout(selection) {
      selection.attr("width", options.legendCellSize).attr("height", options.legendCellSize).attr("x", function (d, i) {
        return i * (options.legendCellSize + options.legendCellPadding);
      });
    }
    legendItem.select("title").text(function (d, i) {
      if (i === 0) {
        return calendar.formatStringWithObject(options.legendTitleFormat.lower, {
          min: options.legend[i],
          name: options.itemName[1]
        });
      } else if (i === _legend.length - 1) {
        return calendar.formatStringWithObject(options.legendTitleFormat.upper, {
          max: options.legend[i - 1],
          name: options.itemName[1]
        });
      } else {
        return calendar.formatStringWithObject(options.legendTitleFormat.inner, {
          down: options.legend[i - 1],
          up: options.legend[i],
          name: options.itemName[1]
        });
      }
    });
    legend.transition().duration(options.animationDuration).attr("x", getLegendXPosition()).attr("y", getLegendYPosition()).attr("width", parent.getDim("width")).attr("height", parent.getDim("height"));
    legend.select("g").transition().duration(options.animationDuration).attr("transform", function () {
      if (options.legendOrientation === "vertical") {
        return "rotate(90 " + options.legendCellSize / 2 + " " + options.legendCellSize / 2 + ")";
      }
      return "";
    });
    function getLegendXPosition() {
      switch (options.legendHorizontalPosition) {
        case "right":
          if (options.legendVerticalPosition === "center" || options.legendVerticalPosition === "middle") {
            return width + options.legendMargin[3];
          }
          return width - parent.getDim("width") - options.legendMargin[1];
        case "middle":
        case "center":
          return Math.round(width / 2 - parent.getDim("width") / 2);
        default:
          return options.legendMargin[3];
      }
    }
    function getLegendYPosition() {
      if (options.legendVerticalPosition === "bottom") {
        return calendar.graphDim.height + options.legendMargin[0] - options.domainGutter - options.cellPadding;
      }
      return options.legendMargin[0];
    }
    calendar.resize();
  };
  Legend.prototype.getDim = function (axis) {
    var isHorizontal = this.calendar.options.legendOrientation === "horizontal";
    switch (axis) {
      case "width":
        return this.dim[isHorizontal ? "width" : "height"];
      case "height":
        return this.dim[isHorizontal ? "height" : "width"];
    }
  };
  Legend.prototype.buildColors = function () {
    var options = this.calendar.options;
    if (options.legendColors === null) {
      this.calendar.legendScale = null;
      return false;
    }
    var _colorRange = [];
    if (Array.isArray(options.legendColors)) {
      _colorRange = options.legendColors;
    } else if (options.legendColors.hasOwnProperty("min") && options.legendColors.hasOwnProperty("max")) {
      _colorRange = [options.legendColors.min, options.legendColors.max];
    } else {
      options.legendColors = null;
      return false;
    }
    var _legend = options.legend.slice(0);
    if (_legend[0] > 0) {
      _legend.unshift(0);
    } else if (_legend[0] <= 0) {
      _legend.unshift(_legend[0] - (_legend[_legend.length - 1] - _legend[0]) / _legend.length);
    }
    var colorScale = d3.scale.linear().range(_colorRange).interpolate(d3.interpolateHcl).domain([d3.min(_legend), d3.max(_legend)]);
    var legendColors = _legend.map(function (element) {
      return colorScale(element);
    });
    this.calendar.legendScale = d3.scale.threshold().domain(options.legend).range(legendColors);
    return true;
  };
  Legend.prototype.getClass = function (n, withCssClass) {
    if (n === null || isNaN(n)) {
      return "";
    }
    var index = [this.calendar.options.legend.length + 1];
    for (var i = 0, total = this.calendar.options.legend.length - 1; i <= total; i++) {
      if (this.calendar.options.legend[0] > 0 && n < 0) {
        index = ["1", "i"];
        break;
      }
      if (n <= this.calendar.options.legend[i]) {
        index = [i + 1];
        break;
      }
    }
    if (n === 0) {
      index.push(0);
    }
    index.unshift("");
    return (index.join(" r") + (withCssClass ? index.join(" q") : "")).trim();
  };
  // אישיו #57/#446: השוואה לפי תאריך מונעת היעלמות סימון בגלל הפרש אזור זמן/DST.
  function specialDateKey(timestamp) {
    var date = new Date(Number(timestamp) * 1000);
    return date.getFullYear() + "-" + date.getMonth() + "-" + date.getDate();
  }
  function buildSpecialDateKeys(days) {
    var keys = new Set();
    if (!Array.isArray(days)) {
      return keys;
    }
    days.forEach(function (day) {
      if (Number.isFinite(Number(day))) {
        keys.add(specialDateKey(day));
      }
    });
    return keys;
  }
  function hasSpecialDate(epochSet, dateKeys, timestamp) {
    if (!epochSet) {
      return false;
    }
    var epoch = Math.round(Number(timestamp) / 1000);
    return epochSet.has(epoch) || dateKeys && dateKeys.has(specialDateKey(epoch));
  }

  function mergeRecursive(obj1, obj2) {
    for (var p in obj2) {
      try {
        if (obj2[p].constructor === Object) {
          obj1[p] = mergeRecursive(obj1[p], obj2[p]);
        } else {
          obj1[p] = obj2[p];
        }
      } catch (e) {
        obj1[p] = obj2[p];
      }
    }
    return obj1;
  }
  function arrayEquals(arrayA, arrayB) {
    if (!arrayB || !arrayA) {
      return false;
    }
    if (arrayA.length !== arrayB.length) {
      return false;
    }
    for (var i = 0; i < arrayA.length; i++) {
      if (arrayA[i] instanceof Array && arrayB[i] instanceof Array) {
        if (!arrayEquals(arrayA[i], arrayB[i])) {
          return false;
        }
      } else if (arrayA[i] !== arrayB[i]) {
        return false;
      }
    }
    return true;
  }
  if (typeof define === "function" && define.amd) {
    define(["d3"], function () {
      return CalHeatMap;
    });
  } else if (typeof module === "object" && module.exports) {
    module.exports = CalHeatMap;
  } else {
    window.CalHeatMap = CalHeatMap;
  }
  function bridgeCommand(command) {
    return pycmd(command);
  }
  function getReviewHeatmapGlobalTooltip() {
    var tooltip = document.getElementById("global_tooltip");
    if (!tooltip && document.body) {
      tooltip = document.createElement("div");
      tooltip.id = "global_tooltip";
      tooltip.style.cssText = "position:fixed;display:none;background:#333;color:#fff;border:1px solid #555;padding:5px 10px;border-radius:5px;font-size:0.9rem;font-family:var(--bs-body-font-family, Arial, sans-serif);z-index:99999;pointer-events:none;box-shadow:0 4px 6px rgba(0,0,0,.3);max-width:300px;text-align:center;direction:rtl;";
      document.body.appendChild(tooltip);
    }
    return tooltip;
  }
  function positionReviewHeatmapTooltip(tooltip, event) {
    if (!tooltip || !event) {
      return;
    }
    var x = event.clientX + 15;
    var y = event.clientY + 15;
    if (x + 310 > window.innerWidth) {
      x = event.clientX - 175;
    }
    if (y + tooltip.offsetHeight + 10 > window.innerHeight) {
      y = event.clientY - tooltip.offsetHeight - 10;
    }
    tooltip.style.left = x + "px";
    tooltip.style.top = y + "px";
  }
  function showReviewHeatmapTooltip(html, event) {
    var tooltip = getReviewHeatmapGlobalTooltip();
    if (!tooltip) {
      return null;
    }
    tooltip.innerHTML = html;
    tooltip.style.display = "block";
    positionReviewHeatmapTooltip(tooltip, event);
    return tooltip;
  }
  function hideReviewHeatmapTooltip() {
    var tooltip = document.getElementById("global_tooltip");
    if (tooltip) {
      tooltip.style.display = "none";
    }
  }

  class ReviewHeatmap {

    constructor(options) {
      this.options = options;
      this.heatmap = null;
    }
    create(data) {
      let calStartDate = applyDateOffset(new Date());
      let calMinDate = applyDateOffset(new Date(this.options.start));
      let calMaxDate = applyDateOffset(new Date(this.options.stop));
      let calTodayDate = applyDateOffset(new Date(this.options.today));
      // if (this.options.domain === "month") {
      //   let padding = this.options.range / 2;
      //   let paddingLower = Math.round(padding - 1);
      //   let paddingUpper = Math.round(padding + 1);
      //   calStartDate.setMonth(calStartDate.getMonth() - paddingLower);
      //   calStartDate.setDate(1);
      //   if (calMinDate.getTime() > calStartDate.getTime()) {
      //     calStartDate = calMinDate;
      //   }
      //   let tempDate = new Date(calTodayDate);
      //   tempDate.setMonth(tempDate.getMonth() + paddingUpper);
      //   tempDate.setDate(1);
      //   if (tempDate.getTime() > calMaxDate.getTime()) {
      //     calMaxDate = tempDate;
      //   }
      // }
      let heatmap = new CalHeatMap();
      heatmap.init({
        domain: this.options.domain,
        subDomain: this.options.subdomain,
        range: this.options.range,
        minDate: calMinDate,
        // maxDate: calMaxDate,
        cellSize: 10,
        verticalOrientation: false,
        dayLabel: true,
        domainMargin: [1, 1, 1, 1],
        itemName: ["card", "cards"],
        highlight: calTodayDate,
        today: calTodayDate,
        start: calStartDate,
        legend: this.options.legend,
        displayLegend: false,
        domainLabelFormat: this.options.domLabForm,
        amount: this.options.amount,
        holy_days: this.options.holy_days,
        hatch_days: this.options.hatch_days,
        tooltip: true,
        subDomainTitleFormat: (isEmpty, formatData, cellData) => {
          // console.log(formatData);
          let tooltip;
          let sch = formatData.sch;
          if (sch !== void 0 && sch.startsWith("-")) {
            sch = sch.substring(1);
          };
          if (isEmpty) {
            tooltip = `${Date.now() < cellData.t ? "<b>אין</b> חזרות מתוזמנות ל" : "<b>לא</b> תוזמנו כרטיסים ב"}${formatData.date}`;
          } else {
            var label = "";
            var scheduled = Math.abs(Number(cellData.s || 0));
            var answered = Math.abs(Number(cellData.a || 0));
            var firstReviews = Math.abs(Number(cellData.n || 0));
            var totalCards = Math.abs(Number(cellData.c || 0));
            var completedScheduled = Math.abs(Number(cellData.d || 0));
            var percent = cellData.v === null || cellData.v === void 0 ? 0 : cellData.v;

            if (cellData.s < 0) {
              label = scheduled === 1 ? "מתוזמן כרטיס <b>אחד</b>" : `<b>${scheduled}</b> קארטלעך זענען מתוזמן`;
            } else {
              // #309 — מבנה טולטיפ לפי דרישה: בוצעו → מתוזמנות → אחוז → חדשות → נוספות
              var extraReviews = answered - completedScheduled - firstReviews;
              if (extraReviews < 0) extraReviews = 0;
              var lines = [];
              lines.push(`געמאכט <b>${answered}</b> חזרות אויף <b>${totalCards}</b> קארטלעך`);
              lines.push(`<b>${completedScheduled}</b> מתוזמנע חזרות פון <b>${scheduled}</b> וואס זענען מתוזמן געווארן`);
              lines.push(`(פראצענט פארענדיגט - <b>${percent}%</b>)`);
              if (firstReviews > 0) {
                lines.push(`<b>${firstReviews}</b> נייע`);
              }
              if (extraReviews > 0) {
                lines.push(`<b>${extraReviews}</b> נאך חזרות`);
              }
              label = lines.join("<br>");
            }

            tooltip = `דעם ${formatData.date}<br>${label}`;
          }
          return tooltip;
        },
        onClick: (date, nb) => {
          if (nb === null || nb == 0) {
            heatmap.highlight(calTodayDate);
            return;
          }
          let cmd = this.options.whole ? "" : "deck:current ";
          let today = new Date(calTodayDate);
          today.setHours(0, 0, 0);
          let diffSecs = Math.abs(today.getTime() - date.getTime()) / 1e3;
          let diffDays = Math.round(diffSecs / 86400);
          if (diffDays === 0) {
            let cutoff1 = date.getTime() + this.options.offset * 3600 * 1e3;
            let cutoff2 = cutoff1 + 86400 * 1e3;
            cmd = "ridtoday:" + cutoff1 + ":" + cutoff2;
          } else if (nb >= 0) {
            if (!window.rhNewFinderAPI) {
              let cutoff1 = date.getTime() + this.options.offset * 3600 * 1e3;
              let cutoff2 = cutoff1 + 86400 * 1e3;
              cmd += "rid:" + cutoff1 + ":" + cutoff2;
            } else {
              cmd += "prop:rated=" + (diffDays ? -diffDays : 0);
            }
          } else {
            cmd += "prop:due=" + diffDays;
          }
          bridgeCommand("revhm_browse:" + cmd);
          heatmap.highlight([calTodayDate, date]);
        },
        afterLoadData: function afterLoadData(timestamps) {
          let results = {};
          for (let timestamp_string in timestamps) {
            let value = timestamps[timestamp_string];
            let timestamp = parseInt(timestamp_string, 10);
            results[timestamp + tzOffsetByTimestamp(timestamp)] = value;
          }
          return results;
        },
        data
      });
      this.heatmap = heatmap;
    }
    onHmHome(event, button) {
      // if (event.shiftKey) {
      //   bridgeCommand("revhm_modeswitch");
      // } else {
        this.heatmap.rewind();
      // }
    }
    onHmNavigate(event, button, direction) {
      if (direction === "next") {
        if (event.shiftKey) {
          this.heatmap.jumpTo(this.heatmap.options.maxDate, false);
        } else {
          this.heatmap.next(this.heatmap.options.range);
        }
      } else {
        if (event.shiftKey) {
          this.heatmap.jumpTo(this.heatmap.options.minDate, false);
        } else {
          this.heatmap.previous(this.heatmap.options.range);
        }
      }
    }
    onHmOpts(event, button) {
      // if (event.shiftKey) {
      //   bridgeCommand("revhm_themeswitch");
      // } else {
        bridgeCommand("revhm_opts");
      // }
    }
    onHmContrib(event, button) {
      // if (event.shiftKey) {
      //   bridgeCommand("revhm_snanki");
      // } else {
        bridgeCommand("revhm_contrib");
      // }
    }
  }
  function applyDateOffset(date) {
    return new Date(date.getTime() + date.getTimezoneOffset() * 60 * 1e3);
  }
  function tzOffsetByTimestamp(timestamp) {
    // תיקון #53: ביום מעבר לשעון קיץ (לדוגמה 24/3/2023 בישראל), UTC-midnight
    // עלול ליפול בדיוק על נקודת המעבר. שימוש ב-getTimezoneOffset() של רגע
    // ה-UTC-midnight מחזיר את ה-offset של שעון קיץ, ובהפחתתו מהtimestamp
    // נופלים על 23:00 של היום הקודם בשעון חורף — כך התא של ב' ניסן תשפ"ג
    // (24/3/2023) נמחק מהלוח.
    // הפתרון: לבנות local-midnight של אותו calendar day של UTC-midnight,
    // ולהשתמש בהפרש ביניהם — כך כל תא ימופה ל-local midnight אמיתי שלו
    // ללא תלות בנקודת חיתוך DST.
    let utcDate = new Date(timestamp * 1e3);
    let localMidnight = new Date(
      utcDate.getUTCFullYear(),
      utcDate.getUTCMonth(),
      utcDate.getUTCDate()
    );
    return Math.floor((localMidnight.getTime() - timestamp * 1e3) / 1000);
  }
  globalThis.ReviewHeatmap = ReviewHeatmap;
});



var _GEMATRIOS = {
  1: 'א',
  2: 'ב',
  3: 'ג',
  4: 'ד',
  5: 'ה',
  6: 'ו',
  7: 'ז',
  8: 'ח',
  9: 'ט',
  10: 'י',
  20: 'כ',
  30: 'ל',
  40: 'מ',
  50: 'נ',
  60: 'ס',
  70: 'ע',
  80: 'פ',
  90: 'צ',
  100: 'ק',
  200: 'ר',
  300: 'ש',
  400: 'ת'
}

function Division_without_a_remainder(num, Divide) {
  var c = num - (num % Divide);
  return (c / Divide);
}

function _stringify_gematria(letters) {
  // Insert geresh or gershayim symbols into gematria.

  len = letters.length
  if (len > 1) {
    return `${letters.slice(0, -1)}"${letters.slice(-1)}`;
  }
  else if (len == 1) {
    return letters + "'"
  }
  else {
    return ""
  }
}
function _get_letters(num) {
  //Convert numbers under 1,000 into raw letters.
  var ones = num % 10;
  var tens = num % 100 - ones;
  var hundreds = num % 1000 - tens - ones;
  var four_hundreds = ''
  for (let i = 0; i < Division_without_a_remainder(hundreds, 400); i++) {
    four_hundreds += 'ת'
  }
  var hundreds = hundreds % 400;
  if (ones == 0) { var ones = '' } else { var ones = _GEMATRIOS[ones]; }
  if (tens == 0) { var tens = '' } else { var tens = _GEMATRIOS[tens]; }
  if (hundreds == 0) { var hundreds = '' } else { var hundreds = _GEMATRIOS[hundreds]; }
  letters = four_hundreds + hundreds + tens + ones;
  return letters.replace(/יה/g, 'טו').replace(/יו/g, 'טז')
}
function _num_to_str(num, thousands = false) {
  /*Return gematria string for number.

  Parameters
  ----------
    num : int
      The number to get the Hebrew letter representation
  thousands: bool, optional
      True if the hebrew returned should include a letter for the
      thousands place ie. 'ה׳' for five thousand.

    Returns
  -------
    str
      The Hebrew representation of the number. */
  var letters = _stringify_gematria(_get_letters(num));
  if (thousands == true && Division_without_a_remainder(num, 1000) != 0) {
    thousand = _get_letters(Division_without_a_remainder(num, 1000)) + "'";
    var letters = thousand + letters
  }
  return letters

}

function Convert_date_to_heb(i) {
  // var s = i.split("-")
  // var y = parseInt(s[0])
  // var m = parseInt(s[1]) - 1
  // var d = parseInt(s[2])
  // const date = new Date(Date.UTC(y, m, d));
  // console.log(typeof(i))
  // const date = new Date(Date.UTC(i));
  var num_heb_dete = new Intl.DateTimeFormat('he-u-ca-hebrew', { year: 'numeric', month: 'numeric', day: 'numeric' }).format(new Date(i))
  var n_h_d = num_heb_dete.split(" ")
  n_h_d[0] = _num_to_str(n_h_d[0])
  n_h_d[n_h_d.length - 1] = _num_to_str(n_h_d[n_h_d.length - 1], thousands = false)
  heb_date_str = ""
  n_h_d.forEach(element => {
    heb_date_str += element
    heb_date_str += " "

  });
  return heb_date_str
}


function get_rosh(d, c = 0, rtrn = 'date') {

  var roshs = [1505941200000, 1536526800000, 1569790800000, 1600462800000, 1630962000000, 1664139600000, 1694811600000, 1727902800000, 1758574800000, 1789160400000, 1822424400000, 1853096400000, 1883682000000, 1916773200000, 1947445200000, 1978030800000, 2011122000000, 2041794000000, 2075058000000, 2105643600000, 2136142800000, 2169406800000, 2199992400000, 2230664400000]
// var roshsss = [1505941196400, 1536526796400, 1569790796400, 1600462796400, 1630961996400, 1664139596400, 1694811596400, 1727902796400, 1758574796400, 1789160396400, 1822424396400, 1853096396400, 1883681996400, 1916773196400, 1947445196400, 1978030796400, 2011121996400, 2041793996400, 2075057996400, 2105643596400, 2136142796400, 2169406796400, 2199992396400, 2230664396400]

  for (rs = 0; rs < roshs.length; rs++) {
    if (d >= roshs[rs] && d < roshs[rs + 1]) {
      var date_rosh = roshs[rs + c];
      switch (rtrn) {
        case 'date': return date_rosh;
        case 'key': return rs;
        case 'name': return _get_letters(new Date(date_rosh).getFullYear() + 3761);
        case 'num_days': return (roshs[rs + c + 1] - date_rosh) / 86400000;
      }

    }
  }
}


function get_num_in_year(rosh) {
  days = {
    1569790800000: 355,
    1600462800000: 353,
    1630962000000: 384,
    1664139600000: 355,
    1694811600000: 355,
    1727902800000: 355,
    1758574800000: 354,
    1789160400000: 385,
    1822424400000: 355,
    1853096400000: 354
  }


  return days[rosh];
}
