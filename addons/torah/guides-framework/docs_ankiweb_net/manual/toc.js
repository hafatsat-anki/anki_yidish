// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item affix "><a href="intro.html">הקדמה</a></li><li class="chapter-item "><a href="background.html"><strong aria-hidden="true">1.</strong> הינטערגרונט</a></li><li class="chapter-item "><a href="platform/intro.html"><strong aria-hidden="true">2.</strong> הערות פאר יעדער פלאטפארמע</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="platform/windows/intro.html"><strong aria-hidden="true">2.1.</strong> Windows</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="platform/windows/installing.html"><strong aria-hidden="true">2.1.1.</strong> אינסטאלירן און דערהייבן</a></li><li class="chapter-item "><a href="platform/windows/installation-issues.html"><strong aria-hidden="true">2.1.2.</strong> פראבלעמען ביים אינסטאלירן</a></li><li class="chapter-item "><a href="platform/windows/startup-issues.html"><strong aria-hidden="true">2.1.3.</strong> פראבלעמען ביים אויפמאכן</a></li><li class="chapter-item "><a href="platform/windows/display-issues.html"><strong aria-hidden="true">2.1.4.</strong> פראבלעמען מיט דער אויסזען</a></li><li class="chapter-item "><a href="platform/windows/copy-and-paste.html"><strong aria-hidden="true">2.1.5.</strong> פראבלעמען ביים קאפירן און איינקלעבן</a></li><li class="chapter-item "><a href="platform/windows/text-size.html"><strong aria-hidden="true">2.1.6.</strong> טעקסט-גרייס</a></li><li class="chapter-item "><a href="platform/windows/permission-problems.html"><strong aria-hidden="true">2.1.7.</strong> פראבלעמען מיט צוטריט-רעכטן</a></li><li class="chapter-item "><a href="platform/windows/damaged_collection.html"><strong aria-hidden="true">2.1.8.</strong> געשעדיגטע זאמלונגען</a></li></ol></li></ol></li><li class="chapter-item "><a href="getting-started.html"><strong aria-hidden="true">3.</strong> אנהייבן צו ארבעטן</a></li><li class="chapter-item "><a href="getting-help.html"><strong aria-hidden="true">4.</strong> באקומען הילף</a></li><li class="chapter-item "><a href="deck-browser.html"><strong aria-hidden="true">5.</strong> דער פעקלעך-עקראן</a></li><li class="chapter-item "><a href="studying.html"><strong aria-hidden="true">6.</strong> לערנען</a></li><li class="chapter-item "><a href="editing.html"><strong aria-hidden="true">7.</strong> צולייגן און רעדאקטירן</a></li><li class="chapter-item "><a href="math.html"><strong aria-hidden="true">8.</strong> מאטעמאטיק און סימבאלן</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="templates/intro.html"><strong aria-hidden="true">8.1.</strong> קארטל-מוסטערן</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="templates/fields.html"><strong aria-hidden="true">8.1.1.</strong> אריינשטעלן פעלדער</a></li><li class="chapter-item "><a href="templates/styling.html"><strong aria-hidden="true">8.1.2.</strong> אויסשטעל און HTML</a></li><li class="chapter-item "><a href="templates/generation.html"><strong aria-hidden="true">8.1.3.</strong> שאפן קארטלעך</a></li><li class="chapter-item "><a href="templates/errors.html"><strong aria-hidden="true">8.1.4.</strong> פרופונגען און פעלערן</a></li></ol></li></ol></li><li class="chapter-item "><a href="preferences.html"><strong aria-hidden="true">9.</strong> פרעפערענצן</a></li><li class="chapter-item "><a href="deck-options.html"><strong aria-hidden="true">10.</strong> פעקל-איינשטעלונגען</a></li><li class="chapter-item "><a href="profiles.html"><strong aria-hidden="true">11.</strong> פראפילן</a></li><li class="chapter-item "><a href="browsing.html"><strong aria-hidden="true">12.</strong> דורכבלעטערן</a></li><li class="chapter-item "><a href="filtered-decks.html"><strong aria-hidden="true">13.</strong> געפילטערטע פעקלעך</a></li><li class="chapter-item "><a href="searching.html"><strong aria-hidden="true">14.</strong> זוכן</a></li><li class="chapter-item "><a href="question-bank.html"><strong aria-hidden="true">15.</strong> דער שאלות-מאגר</a></li><li class="chapter-item "><a href="importing/intro.html"><strong aria-hidden="true">16.</strong> אימפארטירן</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="importing/single-questions.html"><strong aria-hidden="true">16.1.</strong> אימפארטירן באזונדערע שאלות פון א פייל</a></li><li class="chapter-item "><a href="importing/xml-kalizcor.html"><strong aria-hidden="true">16.2.</strong> אימפארטירן XML פון קלזכור</a></li><li class="chapter-item "><a href="importing/text-files.html"><strong aria-hidden="true">16.3.</strong> טעקסט-פיילס</a></li><li class="chapter-item "><a href="importing/packaged-decks.html"><strong aria-hidden="true">16.4.</strong> פארפאקטע פעקלעך</a></li></ol></li><li class="chapter-item "><a href="exporting.html"><strong aria-hidden="true">17.</strong> עקספארטירן</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="printing-word.html"><strong aria-hidden="true">17.1.</strong> דרוקן און עקספארטירן צו Word</a></li></ol></li><li class="chapter-item "><a href="backups.html"><strong aria-hidden="true">18.</strong> רעזערוו-קאפיעס</a></li><li class="chapter-item "><a href="files.html"><strong aria-hidden="true">19.</strong> פייל-פארוואלטונג</a></li><li class="chapter-item "><a href="stats.html"><strong aria-hidden="true">20.</strong> סטאטיסטיק</a></li><li class="chapter-item "><a href="media.html"><strong aria-hidden="true">21.</strong> מעדיע</a></li><li class="chapter-item "><a href="leeches.html"><strong aria-hidden="true">22.</strong> שווערע קארטלעך</a></li><li class="chapter-item "><a href="troubleshooting.html"><strong aria-hidden="true">23.</strong> לייזן פראבלעמען</a></li><li class="chapter-item "><a href="syncing.html"><strong aria-hidden="true">24.</strong> סינכראניזירן מיט AnkiWeb</a></li><li class="chapter-item "><a href="misc.html"><strong aria-hidden="true">25.</strong> פארשידענע ענינים</a></li><li class="chapter-item affix "><a href="contrib.html">ביישטייערן</a></li><li class="chapter-item affix "><a href="faqs.html">אפטע פראגעס</a></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString().split("#")[0].split("?")[0];
        if (current_page.endsWith("/")) {
            current_page += "index.html";
        }
        var links = Array.prototype.slice.call(this.querySelectorAll("a"));
        var l = links.length;
        for (var i = 0; i < l; ++i) {
            var link = links[i];
            var href = link.getAttribute("href");
            if (href && !href.startsWith("#") && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The "index" page is supposed to alias the first chapter in the book.
            if (link.href === current_page || (i === 0 && path_to_root === "" && current_page.endsWith("/index.html"))) {
                link.classList.add("active");
                var parent = link.parentElement;
                if (parent && parent.classList.contains("chapter-item")) {
                    parent.classList.add("expanded");
                }
                while (parent) {
                    if (parent.tagName === "LI" && parent.previousElementSibling) {
                        if (parent.previousElementSibling.classList.contains("chapter-item")) {
                            parent.previousElementSibling.classList.add("expanded");
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sessionStorage.setItem('sidebar-scroll', this.scrollTop);
            }
        }, { passive: true });
        var sidebarScrollTop = sessionStorage.getItem('sidebar-scroll');
        sessionStorage.removeItem('sidebar-scroll');
        if (sidebarScrollTop) {
            // preserve sidebar scroll position when navigating via links within sidebar
            this.scrollTop = sidebarScrollTop;
        } else {
            // scroll sidebar to current active section when navigating via "next/previous chapter" buttons
            var activeSection = document.querySelector('#sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        var sidebarAnchorToggles = document.querySelectorAll('#sidebar a.toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(function (el) {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define("mdbook-sidebar-scrollbox", MDBookSidebarScrollbox);
