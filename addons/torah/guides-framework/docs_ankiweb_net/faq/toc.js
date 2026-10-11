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
        this.innerHTML = '<ol class="chapter"><li class="chapter-item affix "><a href="index.html">מבוא צו אפט געפרעגטע שאלות</a></li><li class="chapter-item affix "><a href="getting-help.html">באקומען הילף</a></li><li class="chapter-item affix "><a href="when-problems-occur.html">ווען עס קומען פראבלעמען</a></li><li class="chapter-item affix "><a href="restoring-an-automatic-backup-recovering-from-data-loss.html">צוריקברענגען אן אויטאמאטישן גיבוי נאך פארלוסט פון דאטן</a></li><li class="chapter-item affix "><li class="spacer"></li><li class="chapter-item affix "><li class="part-title">קארטלעך און רשומות</li><li class="chapter-item "><a href="linking-cards-together.html"><strong aria-hidden="true">1.</strong> קען מען פארבינדן קארטלעך איינער מיטן צווייטן?</a></li><li class="chapter-item "><a href="can-i-reveal-parts-of-a-card-one-at-a-time.html"><strong aria-hidden="true">2.</strong> קען מען אנטפלעקן טיילן פון א קארטל איינס נאכן צווייטן?</a></li><li class="chapter-item "><a href="cards-are-reversed-appearing-twice.html"><strong aria-hidden="true">3.</strong> פארקערטע קארטלעך / קארטלעך ווייזן זיך צוויי מאל</a></li><li class="chapter-item "><a href="errors-when-recording.html"><strong aria-hidden="true">4.</strong> תקלות ביים רעקארדירן</a></li><li class="chapter-item "><a href="multiple-choice-questions.html"><strong aria-hidden="true">5.</strong> שאלות מיט עטליכע אויסקלייב־ענטפערס</a></li><li class="chapter-item "><a href="no-cloze-found-on-card.html"><strong aria-hidden="true">6.</strong> קיין אויסגעלאזטע ווערטער זענען נישט געפונען געווארן אינעם קארטל</a></li><li class="chapter-item "><a href="printing-cards-in-your-collection.html"><strong aria-hidden="true">7.</strong> דרוקן קארטלעך פון אייער אוסף</a></li><li class="chapter-item "><a href="removing-duplicate-note-types.html"><strong aria-hidden="true">8.</strong> אראפנעמען דאפלטע סארטן רשומות</a></li><li class="chapter-item "><a href="some-updates-were-ignored-because-the-note-type-has-changed.html"><strong aria-hidden="true">9.</strong> טייל דערהיינטיגונגען זענען איגנארירט געווארן ווייל דער סארט רשומה האט זיך געטוישט</a></li><li class="chapter-item "><a href="sounds-or-images-have-gone-missing.html"><strong aria-hidden="true">10.</strong> מעדיע־טעקעס פון קול/בילדער זענען פארשוואונדן!</a></li><li class="chapter-item "><a href="sticky-fields.html"><strong aria-hidden="true">11.</strong> ווען מען לייגט צו א נייעם קארטל, ווערן געוויסע פעלדער נישט אויסגעליידיגט!</a></li><li class="chapter-item affix "><li class="spacer"></li><li class="chapter-item affix "><li class="part-title">פעקלעך</li><li class="chapter-item "><a href="hiding-decks.html"><strong aria-hidden="true">12.</strong> באהאלטן פעקלעך</a></li><li class="chapter-item "><a href="how-do-i-move-cards-between-decks.html"><strong aria-hidden="true">13.</strong> ווי אזוי פירט מען קארטלעך אריבער צווישן פעקלעך?</a></li><li class="chapter-item "><a href="merging-or-combining-two-decks.html"><strong aria-hidden="true">14.</strong> צונויפמישן/צונויפשטעלן צוויי פעקלעך</a></li><li class="chapter-item "><a href="timestamps-in-the-future.html"><strong aria-hidden="true">15.</strong> אימפארט/עקספארט גייט נישט צוליב צייט־שטעמפלען אין דער צוקונפט</a></li><li class="chapter-item affix "><li class="spacer"></li><li class="chapter-item affix "><li class="part-title">תזמון</li><li class="chapter-item "><a href="anki-is-not-showing-me-all-my-cards.html"><strong aria-hidden="true">16.</strong> אנקי ווייזט מיר נישט אלע מיינע קארטלעך!</a></li><li class="chapter-item "><a href="study-in-a-particular-order.html"><strong aria-hidden="true">17.</strong> קען מען לערנען די קארטלעך אין א באשטימטן סדר?</a></li><li class="chapter-item "><a href="due-times-after-a-break.html"><strong aria-hidden="true">18.</strong> חזרה־צייטן נאך א הפסקה</a></li><li class="chapter-item "><a href="extra-copies-of-a-card-are-coming-up.html"><strong aria-hidden="true">19.</strong> נאך קאפיעס פון א קארטל ווייזן זיך</a></li><li class="chapter-item "><a href="hard-good-interval-longer-than-good-easy.html"><strong aria-hidden="true">20.</strong> דער אפשטאנד פון שווער/גוט איז לענגער ווי פון גוט/גרינג</a></li><li class="chapter-item "><a href="i-am-going-on-vacation-can-i-pause-the-scheduler.html"><strong aria-hidden="true">21.</strong> איך פאר אויף וואקאציע. קען איך אפשטעלן דעם מתזמן?</a></li><li class="chapter-item "><a href="resetting-progress-in-a-deck.html"><strong aria-hidden="true">22.</strong> צוריקשטעלן דעם פארשריט אין א פעקל</a></li><li class="chapter-item "><a href="settings-for-using-anki-to-prepare-for-a-large-exam.html"><strong aria-hidden="true">23.</strong> אנקי־איינשטעלונגען זיך צו גרייטן פאר א גרויסער בחינה</a></li><li class="chapter-item "><a href="the-anki-2.1-scheduler.html"><strong aria-hidden="true">24.</strong> דער אנקי 2.1־מתזמן</a></li><li class="chapter-item "><a href="the-2021-scheduler.html"><strong aria-hidden="true">25.</strong> דער Anki־מתזמן v3</a></li><li class="chapter-item "><a href="what-spaced-repetition-algorithm.html"><strong aria-hidden="true">26.</strong> וועלכן אלגאריטם פון חזרות מיט אפשטאנדן נוצט אנקי?</a></li><li class="chapter-item "><a href="frequently-asked-questions-about-fsrs.html"><strong aria-hidden="true">27.</strong> אפט געפרעגטע שאלות וועגן FSRS</a></li><li class="chapter-item affix "><li class="spacer"></li><li class="chapter-item affix "><li class="part-title">סינכראניזירן און AnkiWeb</li><li class="chapter-item "><a href="syncing.html"><strong aria-hidden="true">28.</strong> סינכראניזירן און AnkiWeb</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="moving-questions-between-computers.html"><strong aria-hidden="true">28.1.</strong> ווי אזוי פירט מען די שאלות פון איין קאמפיוטער צום צווייטן?</a></li><li class="chapter-item "><a href="can-i-sync-only-some-of-my-decks.html"><strong aria-hidden="true">28.2.</strong> קען מען סינכראניזירן נאר א טייל פון מיינע פעקלעך?</a></li><li class="chapter-item "><a href="synchronizing-multiple-profiles.html"><strong aria-hidden="true">28.3.</strong> סינכראניזירן עטליכע פראפילן</a></li><li class="chapter-item "><a href="media-files-may-take-time-to-sync.html"><strong aria-hidden="true">28.4.</strong> סינכראניזירן מעדיע־טעקעס קען נעמען צייט</a></li><li class="chapter-item "><a href="sounds-or-images-are-not-appearing-on-ankiweb-or-the-mobile-clients.html"><strong aria-hidden="true">28.5.</strong> קלאנגען/בילדער ווייזן זיך נישט אין AnkiWeb אדער מאבילע אפליקאציעס</a></li><li class="chapter-item "><a href="error-establishing-a-secure-connection-when-syncing.html"><strong aria-hidden="true">28.6.</strong> תקלה ביים שאפן א זיכערע פארבינדונג ביים סינכראניזירן</a></li><li class="chapter-item "><a href="syncing-failed-connection-timed-out-errors-when-syncing.html"><strong aria-hidden="true">28.7.</strong> סינכראניזירן איז נישט געלונגען: די פארבינדונג־צייט איז אויסגעגאנגען</a></li><li class="chapter-item "><a href="ankiweb-account-removal.html"><strong aria-hidden="true">28.8.</strong> אויסמעקן אן AnkiWeb־קאנטע</a></li><li class="chapter-item "><a href="are-there-limits-on-file-sizes-on-ankiweb.html"><strong aria-hidden="true">28.9.</strong> זענען דא שיעורים פאר טעקע־גרייסן אין AnkiWeb?</a></li><li class="chapter-item "><a href="email-verification.html"><strong aria-hidden="true">28.10.</strong> באשטעטיגן אן אימעיל־אדרעס</a></li><li class="chapter-item "><a href="emails-not-being-received.html"><strong aria-hidden="true">28.11.</strong> אימעילס קומען נישט אן צוליב ספאם</a></li><li class="chapter-item "><a href="outlook-silently-discards-email.html"><strong aria-hidden="true">28.12.</strong> Outlook.com פארשווינדט אימעילס שטילערהייט</a></li></ol></li><li class="chapter-item "><li class="spacer"></li><li class="chapter-item affix "><li class="part-title">אנקי פארן קאמפיוטער</li><li class="chapter-item "><a href="shortcut-not-working.html"><strong aria-hidden="true">29.</strong> א קורצוועג־קנעפל ארבעט נישט</a></li><li class="chapter-item "><a href="anki-must-be-able-to-connect-to-a-local-port.html"><strong aria-hidden="true">30.</strong> אנקי מוז קענען פארבינדן זיך צו א לאקאלן פארט</a></li><li class="chapter-item "><a href="anki-says-my-clock-is-wrong.html"><strong aria-hidden="true">31.</strong> אנקי זאגט אז מיין זייגער איז נישט ריכטיג</a></li><li class="chapter-item "><a href="changing-the-interface-language.html"><strong aria-hidden="true">32.</strong> טוישן די שפראך פונעם ממשק</a></li><li class="chapter-item "><a href="my-antivirus-program-says-anki-is-infected.html"><strong aria-hidden="true">33.</strong> מיין אנטיווירוס־פראגראם זאגט אז Anki איז אנגעשטעקט!</a></li><li class="chapter-item affix "><li class="spacer"></li><li class="chapter-item affix "><li class="part-title">פארשידענע</li><li class="chapter-item "><a href="how-can-i-donate.html"><strong aria-hidden="true">34.</strong> ווי אזוי קען מען ביישטייערן?</a></li></ol>';
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
