"use strict";

window.search = window.search || {};

(function search() {
  // משתנים גלובליים לניהול החיפוש
  const search_wrap = document.getElementById("search-wrapper"),
    searchbar = document.getElementById("searchbar"),
    searchresults = document.getElementById("searchresults"),
    searchresults_outer = document.getElementById("searchresults-outer"),
    searchresults_header = document.getElementById("searchresults-header"),
    searchicon = document.getElementById("search-toggle"),
    content = document.getElementById("content");

  let searchindex = null,
    doc_urls = [],
    results_options = {
      limit_results: 30,
      teaser_word_count: 30,
    };

  // אתחול Mark.js להדגשת תוצאות
  let marker = null;
  if (typeof Mark !== "undefined" && content) {
    marker = new Mark(content);
  }

  // פונקציה שמחלצת את הטקסט הגולמי מתוך המבנה של ElasticLunr
  // וממירה אותו לאינדקס של Lunr עם תמיכה בעברית
  function initLunrIndex(elasticData) {
    const docInfo = elasticData.documentStore.docInfo;
    const docs = elasticData.documentStore.docs;

    // בניית אינדקס Lunr חדש
    searchindex = lunr(function () {
      // הפעלת תמיכה בעברית
      if (lunr.he) {
        this.use(lunr.he);
      } else {
        console.warn("Lunr Hebrew support not found");
      }

      this.ref("id");
      this.field("title", { boost: 10 });
      this.field("body");
      this.field("breadcrumbs");

      // הוספת המסמכים לאינדקס
      for (let id in docs) {
        if (docs.hasOwnProperty(id)) {
          this.add({
            id: id,
            title: docs[id].title,
            body: docs[id].body,
            breadcrumbs: docs[id].breadcrumbs,
          });
        }
      }
    });

    // שמירת המסמכים המקוריים לשימוש ביצירת התקציר (Teaser)
    window.search.docs = docs;
  }

  function init(config) {
    doc_urls = config.doc_urls;

    // כאן הקסם: במקום לטעון את האינדקס כ-ElasticLunr,
    // אנחנו לוקחים את המידע הגולמי ובונים אינדקס Lunr
    initLunrIndex(config.index);

    // הגדרת אירועי UI
    searchbar.addEventListener("keyup", function () {
      doSearch(searchbar.value);
    });

    searchicon.addEventListener("click", function () {
      if (search_wrap.classList.contains("hidden")) {
        showSearch(true);
        searchbar.focus();
      } else {
        showSearch(false);
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        showSearch(false);
        if (marker) marker.unmark();
      }
      // קיצור דרך S או /
      if (!hasFocus() && (e.key === "s" || e.key === "/")) {
        e.preventDefault();
        showSearch(true);
        searchbar.focus();
      }
    });

    // בדיקה אם יש חיפוש ב-URL בעת טעינת העמוד
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("search")) {
      const term = decodeURIComponent(urlParams.get("search"));
      searchbar.value = term;
      showSearch(true);
      doSearch(term);
    }
  }

  function hasFocus() {
    return searchbar === document.activeElement;
  }

  function showSearch(yes) {
    if (yes) {
      search_wrap.classList.remove("hidden");
      searchicon.setAttribute("aria-expanded", "true");
      window.scrollTo(0, 0);
    } else {
      search_wrap.classList.add("hidden");
      searchicon.setAttribute("aria-expanded", "false");
    }
  }

  function doSearch(term) {
    term = term.trim();

    if (!searchindex) return;

    const searchResultsList = document.getElementById("searchresults");
    searchResultsList.innerHTML = "";

    if (term === "") {
      searchresults_outer.classList.add("hidden");
      if (marker) marker.unmark();
      return;
    }

    // ביצוע החיפוש ב-Lunr
    // שימוש ב-wildcard אוטומטי כדי למצוא תחיליות
    let results = [];
    try {
      results = searchindex.search(term + "*");
      // אם אין תוצאות, נסה חיפוש מדויק יותר למקרה שהכוכבית מפריעה
      if (results.length === 0) results = searchindex.search(term);
    } catch (e) {
      console.error(e);
    }

    searchresults_header.innerText =
      results.length + " זוך רעזולטאטן פאר '" + term + "':";
    searchresults_outer.classList.remove("hidden");

    const count = Math.min(results.length, results_options.limit_results);

    for (let i = 0; i < count; i++) {
      const result = results[i];
      const doc = window.search.docs[result.ref];
      const url = doc_urls[result.ref];

      const item = document.createElement("li");

      // יצירת התקציר
      const teaser = makeTeaser(doc.body, term.split(" "));

      item.innerHTML = `
                <a href="${url}?highlight=${encodeURIComponent(term)}">
                    <div class="search-title">${doc.title}</div>
                    <div class="search-breadcrumbs">${doc.breadcrumbs}</div>
                    <div class="search-teaser">${teaser}</div>
                </a>
            `;
      searchResultsList.appendChild(item);
    }

    // עדכון URL ללא רענון
    const url = new URL(window.location);
    url.searchParams.set("search", term);
    window.history.replaceState({}, "", url);
  }

  // פונקציה ליצירת תקציר (Teaser) מכיוון ש-Lunr לא מספק זאת מובנה
  function makeTeaser(body, terms) {
    if (!body) return "";
    const bodyLower = body.toLowerCase();
    let foundIndex = -1;

    for (let term of terms) {
      if (!term) continue;
      term = term.toLowerCase();
      foundIndex = bodyLower.indexOf(term);
      if (foundIndex !== -1) break;
    }

    if (foundIndex === -1) foundIndex = 0;

    const start = Math.max(0, foundIndex - 50);
    const end = Math.min(body.length, foundIndex + 150);

    let teaser = body.substring(start, end);
    if (start > 0) teaser = "..." + teaser;
    if (end < body.length) teaser = teaser + "...";

    // הדגשת מילים בתקציר
    terms.forEach((term) => {
      if (!term) return;
      // Regex פשוט להחלפה שאינה תלויה באותיות גדולות/קטנות (למרות שבעברית זה פחות קריטי)
      const regex = new RegExp(`(${term})`, "gi");
      teaser = teaser.replace(regex, "<strong>$1</strong>");
    });

    return teaser;
  }

  // טעינת הנתונים מקובץ האינדקס של mdBook
  function loadSearchIndex() {
    const script = document.createElement("script");
    script.src = window.path_to_searchindex_js || "searchindex.js";
    script.onload = function () {
      // הפונקציה init תיקרא אוטומטית כאשר הקובץ נטען
      // כי אנחנו נחבר אותה ל-window.search.init למטה
      if (window.search && window.search.index) {
        init(window.search);
      }
    };
    document.head.appendChild(script);
  }

  // חיבור לממשק הגלובלי כדי ש-searchindex.js יוכל לקרוא לנו
  // בקובץ searchindex.js של mdBook יש קריאה בסוף ל-init
  // אבל אנחנו רוצים לשלוט בתהליך.
  // השיטה הכי בטוחה היא לחכות שהדף ייטען ואז לטעון את הסקריפט ידנית או לתת לו לרוץ.

  // אם הקובץ נטען דינמית ע"י לחיצה (כמו ב-mdBook המקורי):
  const searchScriptId = "search-index-script";
  if (!document.getElementById(searchScriptId)) {
    loadSearchIndex();
  }
})(window.search);
