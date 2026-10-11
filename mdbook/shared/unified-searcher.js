"use strict";

window.search = window.search || {};

function getBookRoot() {
  if (typeof window.path_to_root === "string") {
    return window.path_to_root;
  }
  try {
    if (typeof path_to_root === "string") {
      return path_to_root;
    }
  } catch (error) {
    return "";
  }
  return "";
}

function getSiteRoot() {
  if (typeof window.path_to_site_root === "string") {
    return window.path_to_site_root;
  }
  return getBookRoot() + "../";
}

function isExternalOrRooted(href) {
  return (
    !href ||
    href.startsWith("#") ||
    href.startsWith("/") ||
    href.startsWith("./") ||
    href.startsWith("../") ||
    /^[a-z][a-z0-9+.-]*:/i.test(href)
  );
}

(function fixMdbookSidebarLinks() {
  const bookRoot = getBookRoot();
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) {
    return;
  }

  let currentPage = document.location.href.split("#")[0].split("?")[0];
  if (currentPage.endsWith("/")) {
    currentPage += "index.html";
  }

  function revealSidebarBranch(link) {
    let parent = link.parentElement;
    if (parent && parent.classList.contains("chapter-item")) {
      parent.classList.add("expanded");
    }
    while (parent) {
      if (
        parent.tagName === "LI" &&
        parent.previousElementSibling &&
        parent.previousElementSibling.classList.contains("chapter-item")
      ) {
        parent.previousElementSibling.classList.add("expanded");
      }
      parent = parent.parentElement;
    }
  }

  Array.from(sidebar.querySelectorAll("a[href]")).forEach((link, index) => {
    const href = link.getAttribute("href");
    if (bookRoot && !isExternalOrRooted(href)) {
      link.setAttribute("href", bookRoot + href);
    }

    if (
      link.href === currentPage ||
      (index === 0 && bookRoot === "" && currentPage.endsWith("/index.html"))
    ) {
      link.classList.add("active");
      revealSidebarBranch(link);
    }
  });

  Array.from(sidebar.querySelectorAll("a.toggle")).forEach((toggle) => {
    if (toggle.dataset.mdbookSidebarFixed === "true") {
      return;
    }
    toggle.dataset.mdbookSidebarFixed = "true";
    toggle.addEventListener("click", (event) => {
      event.currentTarget.parentElement.classList.toggle("expanded");
    });
  });

  const activeSection = sidebar.querySelector(".active");
  if (activeSection) {
    activeSection.scrollIntoView({ block: "center" });
  }
})();

(function search(searchState) {
  const searchWrap = document.getElementById("search-wrapper");
  const searchbar = document.getElementById("searchbar");
  const searchresults = document.getElementById("searchresults");
  const searchresultsOuter = document.getElementById("searchresults-outer");
  const searchresultsHeader = document.getElementById("searchresults-header");
  const searchicon = document.getElementById("search-toggle");
  const content = document.getElementById("content");

  let searchindex = null;
  let docUrls = [];
  let docs = {};
  let initialized = false;
  let activeSearchIndexUrl = null;
  let resultsOptions = {
    limit_results: 30,
    teaser_word_count: 30,
  };

  const marker = typeof Mark !== "undefined" && content ? new Mark(content) : null;

  function hasFocus() {
    return searchbar === document.activeElement;
  }

  searchState.hasFocus = hasFocus;

  if (
    !searchWrap ||
    !searchbar ||
    !searchresults ||
    !searchresultsOuter ||
    !searchresultsHeader ||
    !searchicon
  ) {
    return;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function escapeLunrTerm(value) {
    return String(value).replace(/[+\-!(){}[\]^\"~*?:\\/]/g, "\\$&");
  }

  function splitSearchTerms(term) {
    return term.trim().split(/\s+/).filter(Boolean);
  }

  function markFromUrl() {
    if (!marker) {
      return;
    }
    try {
      const urlParams = new URLSearchParams(window.location.search);
      if (!urlParams.has("highlight")) {
        return;
      }
      const term = decodeURIComponent(urlParams.get("highlight"));
      marker.mark(term, {
        element: "mark",
        className: "highlight",
        separateWordSearch: true,
      });
      setTimeout(() => {
        const firstMark = document.querySelector("mark.highlight");
        if (firstMark && !window.location.hash) {
          firstMark.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 100);
    } catch (error) {
      console.error("Error highlighting search terms:", error);
    }
  }

  function initLunrIndex(indexData) {
    if (typeof lunr === "undefined") {
      console.error("Lunr is not loaded; unified search cannot start.");
      return;
    }

    docs = (((indexData || {}).documentStore || {}).docs) || {};
    searchState.docs = docs;

    searchindex = lunr(function buildIndex() {
      if (lunr.he) {
        this.use(lunr.he);
      }

      this.ref("id");
      this.field("title", { boost: 10 });
      this.field("body");
      this.field("breadcrumbs");

      Object.keys(docs).forEach((id) => {
        const doc = docs[id] || {};
        this.add({
          id,
          title: doc.title || "",
          body: doc.body || "",
          breadcrumbs: doc.breadcrumbs || "",
        });
      });
    });
  }

  function init(config) {
    if (initialized) {
      return;
    }
    initialized = true;

    docUrls = config.doc_urls || [];
    resultsOptions = Object.assign(resultsOptions, config.results_options || {});
    initLunrIndex(config.index);

    searchbar.addEventListener("input", () => {
      doSearch(searchbar.value);
    });

    searchicon.addEventListener("click", () => {
      if (searchWrap.classList.contains("hidden")) {
        showSearch(true);
        searchbar.focus();
      } else {
        showSearch(false);
      }
    });

    document.addEventListener("keydown", (event) => {
      const targetName = (event.target && event.target.nodeName) || "";
      const targetType = (event.target && event.target.type) || "";
      const typingTarget = /^(?:input|select|textarea)$/i.test(targetName);

      if (!hasFocus() && (typingTarget || targetType === "textarea" || targetType === "text")) {
        return;
      }

      if (event.key === "Escape") {
        showSearch(false);
        if (marker) {
          marker.unmark();
        }
      } else if (!hasFocus() && (event.key === "s" || event.key === "/")) {
        event.preventDefault();
        showSearch(true);
        searchbar.focus();
      }
    });

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("search")) {
      const term = decodeURIComponent(urlParams.get("search"));
      searchbar.value = term;
      showSearch(true);
      doSearch(term);
    }
  }

  function showSearch(yes) {
    if (yes) {
      searchWrap.classList.remove("hidden");
      searchicon.setAttribute("aria-expanded", "true");
      window.scrollTo(0, 0);
    } else {
      searchWrap.classList.add("hidden");
      searchicon.setAttribute("aria-expanded", "false");
    }
  }

  function clearSearchResults() {
    while (searchresults.firstChild) {
      searchresults.removeChild(searchresults.firstChild);
    }
  }

  function formatMetric(count, term) {
    if (count === 0) {
      return "קיין רעזולטאטן זענען נישט געפונען פאר '" + term + "'.";
    }
    if (count === 1) {
      return "איין זוך רעזולטאט פאר '" + term + "':";
    }
    return count + " זוך רעזולטאטן פאר '" + term + "':";
  }

  function isUnifiedDocUrl(url) {
    return url.startsWith("manual/") || url.startsWith("faq/");
  }

  function buildResultUrl(docUrl, term) {
    let pageUrl = docUrl || "";
    let anchor = "";
    const hashIndex = pageUrl.indexOf("#");
    if (hashIndex !== -1) {
      anchor = pageUrl.slice(hashIndex);
      pageUrl = pageUrl.slice(0, hashIndex);
    }

    const root = isUnifiedDocUrl(pageUrl) ? getSiteRoot() : getBookRoot();
    const joiner = pageUrl.indexOf("?") === -1 ? "?" : "&";
    const encodedTerm = encodeURIComponent(term).replace(/'/g, "%27");
    return root + pageUrl + joiner + "highlight=" + encodedTerm + anchor;
  }

  function makeTeaser(body, terms) {
    if (!body) {
      return "";
    }

    const bodyText = String(body);
    const bodyLower = bodyText.toLowerCase();
    let foundIndex = -1;

    terms.forEach((term) => {
      if (foundIndex !== -1) {
        return;
      }
      foundIndex = bodyLower.indexOf(term.toLowerCase());
    });

    if (foundIndex === -1) {
      foundIndex = 0;
    }

    const start = Math.max(0, foundIndex - 50);
    const end = Math.min(bodyText.length, foundIndex + 150);
    let teaser = escapeHtml(bodyText.substring(start, end));

    if (start > 0) {
      teaser = "..." + teaser;
    }
    if (end < bodyText.length) {
      teaser += "...";
    }

    terms.forEach((term) => {
      if (!term) {
        return;
      }
      const regex = new RegExp("(" + escapeRegExp(escapeHtml(term)) + ")", "gi");
      teaser = teaser.replace(regex, "<strong>$1</strong>");
    });

    return teaser;
  }

  function renderResult(result, terms, term) {
    const doc = docs[result.ref] || {};
    const item = document.createElement("li");
    const link = document.createElement("a");
    const title = document.createElement("div");
    const breadcrumbs = document.createElement("div");
    const teaser = document.createElement("div");

    link.href = buildResultUrl(docUrls[result.ref], term);
    title.className = "search-title";
    breadcrumbs.className = "search-breadcrumbs";
    teaser.className = "search-teaser";
    title.textContent = doc.title || "";
    breadcrumbs.textContent = doc.breadcrumbs || "";
    teaser.innerHTML = makeTeaser(doc.body || "", terms);

    link.appendChild(title);
    link.appendChild(breadcrumbs);
    link.appendChild(teaser);
    item.appendChild(link);
    searchresults.appendChild(item);
  }

  function doSearch(rawTerm) {
    const term = rawTerm.trim();
    clearSearchResults();

    if (!searchindex || term === "") {
      searchresultsOuter.classList.add("hidden");
      if (marker) {
        marker.unmark();
      }
      return;
    }

    const terms = splitSearchTerms(term);
    const wildcardQuery = terms.map((searchTerm) => escapeLunrTerm(searchTerm) + "*").join(" ");
    let results = [];

    try {
      results = searchindex.search(wildcardQuery);
      if (results.length === 0) {
        results = searchindex.search(terms.map(escapeLunrTerm).join(" "));
      }
    } catch (error) {
      console.error("Search failed:", error);
    }

    const count = Math.min(results.length, resultsOptions.limit_results || 30);
    searchresultsHeader.innerText = formatMetric(count, term);
    searchresultsOuter.classList.remove("hidden");

    for (let index = 0; index < count; index += 1) {
      renderResult(results[index], terms, term);
    }

    try {
      const url = new URL(window.location.href);
      url.searchParams.set("search", term);
      url.searchParams.delete("highlight");
      window.history.replaceState({}, "", url);
    } catch (error) {
      console.warn("Could not update the search URL:", error);
    }
  }

  function loadSearchIndexAt(urls, index) {
    if (index >= urls.length) {
      console.error("Could not load any search index.");
      return;
    }

    const url = urls[index];
    activeSearchIndexUrl = url;
    const script = document.createElement("script");
    script.src = url;
    script.id = "search-index-" + index;
    script.onload = () => {
      if (activeSearchIndexUrl !== url) {
        return;
      }
      if (window.search && window.search.index) {
        init(window.search);
      } else {
        loadSearchIndexAt(urls, index + 1);
      }
    };
    script.onerror = () => {
      loadSearchIndexAt(urls, index + 1);
    };
    document.head.appendChild(script);
  }

  function loadSearchIndex() {
    const candidates = [];
    const unifiedIndex = window.path_to_searchindex_js || "";
    const localIndex = getBookRoot() + "searchindex.js";

    if (unifiedIndex) {
      candidates.push(unifiedIndex);
    }
    if (localIndex && !candidates.includes(localIndex)) {
      candidates.push(localIndex);
    }

    loadSearchIndexAt(candidates, 0);
  }

  markFromUrl();
  if (searchState.index) {
    init(searchState);
  } else {
    loadSearchIndex();
  }
})(window.search);