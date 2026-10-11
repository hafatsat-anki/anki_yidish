
# Review Heatmap Add-on for Anki
#
# Copyright (C) 2016-2022  Aristotelis P. <https//glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the accompanied license file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License which
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Static web components and templates
"""

from .libaddon.platform import MODULE_ADDON, PLATFORM

CSS_DISABLE_HEATMAP = "rh-disable-heatmap"
CSS_DISABLE_STATS = "rh-disable-stats"
CSS_PLATFORM_PREFIX = "rh-platform"
CSS_MODE_PREFIX = "rh-mode"
CSS_THEME_PREFIX = "rh-theme"
CSS_VIEW_PREFIX = "rh-view"

WEB_BASE = f"/_addons/{MODULE_ADDON}/web"
# אישיו #57/#446: שינוי גרסת הנכס מונע מ-Anki להציג bundle ישן מהמטמון.
WEB_ASSET_VERSION = "holy-days-4"

HTML_MAIN_ELEMENT: str = f"""
<script type="text/javascript" src="{WEB_BASE}/d3.min.js"></script>
<script type="text/javascript" src="{WEB_BASE}/anki-review-heatmap.js?v={WEB_ASSET_VERSION}"></script>

<script>
var rhPlatform = "{PLATFORM}";
var rhNewFinderAPI = false;
</script>

<div class="rh-container {{classes}}">
{{content}}
</div>
"""

HTML_LOADING: str = """
<div class="rh-loading" data-rh-token="{token}" style="padding: 12px 0; color: #666; text-align: center;">
    <div style="font-weight: 600; margin-bottom: 8px;">מען רעכנט יעצט אויס די חזרות מאפע דאטן</div>
    <div style="height: 6px; max-width: 260px; margin: 0 auto; overflow: hidden; background: #e6e6e6; border-radius: 3px;">
        <div class="rh-loading-bar" style="height: 100%; width: 42%; background: #669d45; border-radius: 3px;"></div>
    </div>
    <style>
    .rh-loading-bar {{
        animation: rh-loading-slide 1.15s ease-in-out infinite;
        transform: translateX(-110%);
    }}
    @keyframes rh-loading-slide {{
        0% {{ transform: translateX(-110%); }}
        55% {{ transform: translateX(160%); }}
        100% {{ transform: translateX(160%); }}
    }}
    .night_mode .rh-loading {{ color: #ccc; }}
    .night_mode .rh-loading > div:nth-child(2) {{ background: #333; }}
    </style>
</div>
"""

# אישיו #57/#446: שכבת SVG נפרדת מקווקוות יום אסור במלאכה שגם היום שאחריו אסור.
JS_SPECIAL_DATE_HATCH: str = """
    // אישיו #57/#446: הסימון מצויר מעל התאים שסומנו במפורש כיום אסור במלאכה שגם היום שאחריו אסור.
    (function() {
        var svgNs = "http://www.w3.org/2000/svg";
        var styleId = "rh-special-date-hatch-style";
        var patternId = "rh-special-date-hatch-pattern";

        if (!document.getElementById(styleId)) {
            var style = document.createElement("style");
            style.id = styleId;
            style.textContent =
                ".cal-heatmap-container .rh-special-date-hatch-line{fill:none;stroke:rgba(80,80,80,.65);stroke-width:1px;}" +
                ".night_mode .cal-heatmap-container .rh-special-date-hatch-line{stroke:rgba(230,230,230,.60);}";
            document.head.appendChild(style);
        }

        function ensurePattern(svg) {
            if (svg.querySelector("#" + patternId)) {
                return;
            }
            var defs = svg.querySelector("defs");
            if (!defs) {
                defs = document.createElementNS(svgNs, "defs");
                svg.insertBefore(defs, svg.firstChild);
            }
            var pattern = document.createElementNS(svgNs, "pattern");
            pattern.setAttribute("id", patternId);
            pattern.setAttribute("patternUnits", "userSpaceOnUse");
            pattern.setAttribute("width", "4");
            pattern.setAttribute("height", "4");
            var path = document.createElementNS(svgNs, "path");
            path.setAttribute("class", "rh-special-date-hatch-line");
            path.setAttribute("d", "M-1,1 L1,-1 M0,4 L4,0 M3,5 L5,3");
            pattern.appendChild(path);
            defs.appendChild(pattern);
        }

        function copyGeometry(source, target) {
            ["x", "y", "width", "height", "rx", "ry"].forEach(function(name) {
                var value = source.getAttribute(name);
                if (value !== null) {
                    target.setAttribute(name, value);
                }
            });
        }

        function applyHatch() {
            var svg = document.querySelector("#cal-heatmap .cal-heatmap-container");
            if (!svg) {
                return;
            }
            ensurePattern(svg);

            svg.querySelectorAll("rect.rh-special-date-hatch").forEach(function(overlay) {
                var group = overlay.parentNode;
                if (!group || !group.querySelector("rect.holy-day.holy-day-followed")) {
                    overlay.remove();
                }
            });

            svg.querySelectorAll("rect.holy-day.holy-day-followed").forEach(function(base) {
                var group = base.parentNode;
                if (!group || group.querySelector("rect.rh-special-date-hatch")) {
                    return;
                }
                var overlay = document.createElementNS(svgNs, "rect");
                overlay.setAttribute("class", "rh-special-date-hatch");
                overlay.setAttribute("fill", "url(#" + patternId + ")");
                overlay.setAttribute("pointer-events", "none");
                copyGeometry(base, overlay);
                if (base.nextSibling) {
                    group.insertBefore(overlay, base.nextSibling);
                } else {
                    group.appendChild(overlay);
                }
            });
        }

        var scheduled = false;
        function scheduleHatch() {
            if (scheduled) {
                return;
            }
            scheduled = true;
            window.requestAnimationFrame(function() {
                scheduled = false;
                applyHatch();
            });
        }

        // אישיו #57/#446: ציור מחדש או מעבר טווח מקבלים את אותו סימון בלי לשנות את נתוני המפה.
        if (window.rhSpecialDateHatchObserver) {
            window.rhSpecialDateHatchObserver.disconnect();
        }
        var heatmapRoot = document.getElementById("cal-heatmap");
        if (heatmapRoot) {
            window.rhSpecialDateHatchObserver = new MutationObserver(scheduleHatch);
            window.rhSpecialDateHatchObserver.observe(heatmapRoot, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ["class"]
            });
        }
        applyHatch();
    })();
"""

# אישיו #446: HTML_HEATMAP עובר format נוסף בזמן הרינדור, לכן סוגריים מסולסלים של JavaScript מוכפלים מראש.
JS_SPECIAL_DATE_HATCH_FOR_FORMAT = JS_SPECIAL_DATE_HATCH.replace("{", "{{").replace("}", "}}")

HTML_HEATMAP: str = f"""
<div class="heatmap" style="max-width:100%; overflow-x:auto; overflow-y:visible;">
    <div class="heatmap-controls">
        <div class="alignleft">
            <span>&nbsp;</span>
        </div>
        <div class="aligncenter">
            <div title="גייט צוריק\n(Shift-click צום ערשטן יאר מיט חזרות)" onclick="reviewHeatmap.onHmNavigate(event, this, 'prev');" class="hm-btn">
                <img height="10px" src="{WEB_BASE}/assets/right.svg" />
            </div>
            <div title="היינט" onclick="reviewHeatmap.onHmHome(event, this);" class="hm-btn">
                <img height="10px" src="{WEB_BASE}/assets/circle.svg" />
            </div>
            <div title="גייט פאראויס\n(Shift-click צום לעצטן יאר מיט חזרות)" onclick="reviewHeatmap.onHmNavigate(event, this, 'next');" class="hm-btn">
                <img height="10px" src="{WEB_BASE}/assets/left.svg" />
            </div>
        </div>
        <div class="alignright">
            <div class="hm-btn opts-btn" title="ווייזט לויטן צאל שאלות" onclick="reviewHeatmap.onHmOpts(event, this);">
                ≡
            </div>
            <div class="hm-btn opts-btn" title="ווייזט לויט פראצענט" onclick="reviewHeatmap.onHmContrib(event, this);">
                %
            </div>
        </div>
        <div style="clear: both;">&nbsp;</div>
    </div>
    <div id="cal-heatmap" style="min-width:max-content;"></div>
</div>
<script type="text/javascript">
    window.reviewHeatmap = new ReviewHeatmap({{options}});
    reviewHeatmap.create({{data}});
{JS_SPECIAL_DATE_HATCH_FOR_FORMAT}
    (function() {{{{
        var resizeTimer;
        window.addEventListener('resize', function() {{{{
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {{{{
                if (window.reviewHeatmap && window.reviewHeatmap.heatmap) {{{{
                    window.reviewHeatmap.heatmap.resize();
                }}}}
            }}}}, 250);
        }}}});
    }}}})();
</script>
"""

HTML_STREAK: str = """
<div class="streak">
    <span class="streak-info">טעגליכער דורכשניט:</span>
    <span title="טעגליכער דורכשניט פאר טעג מיט חזרות"
        class="sstats {class_activity_daily_avg}">{text_activity_daily_avg}</span>
    <span class="streak-info">טעג מיט חזרות:</span>
    <span title="דער פראצענט פון טעג מיט חזרות פון אלע טעג"
        class="sstats {class_pct_days_active}">{text_pct_days_active}%</span>
    <span class="streak-info">לענגסטע רייע:</span>
    <span title="די לענגסטע רייע טעג מיט חזרות פון סיי וועלכן סארט."
        class="sstats {class_streak_max}">{text_streak_max}</span>
    <span class="streak-info">יעצטיגע רייע:</span>
    <span title="די יעצטיגע רייע טעג מיט חזרות פון סיי וועלכן סארט."
        class="sstats {class_streak_cur}">{text_streak_cur}</span>
</div>
"""


HTML_INFO_NODATA: str = ""
# אין מידע להצגה (<span class="linkspan" onclick='pycmd("revhm_opts");'>options</span>).
