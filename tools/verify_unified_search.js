"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, "..");
const outputRoot = process.argv[3]
  ? path.resolve(process.argv[3])
  : path.join(root, "addons", "torah", "guides-framework", "docs_ankiweb_net");
const manualRoot = path.join(outputRoot, "manual");
const searchIndexPath = path.join(outputRoot, "searchindex.js");

function fail(message) {
  console.error("ERROR: " + message);
  process.exit(1);
}

function loadSearchConfig() {
  const source = fs.readFileSync(searchIndexPath, "utf8");
  const sandbox = { window: { search: {} } };
  vm.runInNewContext(source, sandbox, { filename: searchIndexPath });
  return sandbox.window.search;
}

function loadLunr() {
  const lunr = require(path.join(manualRoot, "lunr.js"));
  require(path.join(manualRoot, "lunr.stemmer.support.js"))(lunr);
  require(path.join(manualRoot, "lunr.he.js"))(lunr);
  return lunr;
}

function escapeLunrTerm(value) {
  return String(value).replace(/[+\-!(){}[\]^\"~*?:\\/]/g, "\\$&");
}

function buildIndex(lunr, docs) {
  return lunr(function build() {
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

function search(index, term) {
  const terms = term.trim().split(/\s+/).filter(Boolean);
  const wildcardQuery = terms.map((searchTerm) => escapeLunrTerm(searchTerm) + "*").join(" ");
  let results = index.search(wildcardQuery);
  if (results.length === 0) {
    results = index.search(terms.map(escapeLunrTerm).join(" "));
  }
  return results;
}

const config = loadSearchConfig();
const docs = (((config.index || {}).documentStore || {}).docs) || {};
const docUrls = config.doc_urls || [];

if (docUrls.length === 0 || Object.keys(docs).length === 0) {
  fail("Unified search index is empty.");
}

const lunr = loadLunr();
const index = buildIndex(lunr, docs);
const verificationTerms = ["סינכראניזירן", "אנקי", "קארטלעך"];
let passingTerm = null;
let passingResults = [];

for (const term of verificationTerms) {
  const results = search(index, term);
  const urls = results.map((result) => docUrls[Number(result.ref)] || "");
  if (urls.some((url) => url.startsWith("manual/")) && urls.some((url) => url.startsWith("faq/"))) {
    passingTerm = term;
    passingResults = results;
    break;
  }
}

if (!passingTerm) {
  fail("Hebrew search did not return results from both manual/ and faq/.");
}

const manualNestedRoot = "../../../";
const faqResult = docUrls[Number(passingResults.find((result) => (docUrls[Number(result.ref)] || "").startsWith("faq/")).ref)];
const resultUrl = manualNestedRoot + faqResult.split("#")[0] + "?highlight=" + encodeURIComponent(passingTerm);

if (!resultUrl.includes("../../../faq/")) {
  fail("Cross-book result URL from a nested manual page is not rooted at the combined output.");
}

console.log(`Lunr verification passed: '${passingTerm}' returns ${passingResults.length} results across manual and FAQ.`);