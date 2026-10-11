"""Build the Manual and FAQ mdBook outputs as one searchable site."""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
MDBOOK_ROOT = ROOT / "mdbook"
ADDON_GUIDES_ROOT = ROOT / "addons" / "torah" / "guides-framework" / "docs_ankiweb_net"
OUTPUT_ROOT = ADDON_GUIDES_ROOT
MANUAL_SOURCE = ROOT / "manual"
FAQ_SOURCE = ROOT / "faq"
MANUAL_BOOK = MDBOOK_ROOT / "manual"
FAQ_BOOK = MDBOOK_ROOT / "faq"
if not MANUAL_SOURCE.exists():
    MANUAL_SOURCE = MANUAL_BOOK / "src"
if not FAQ_SOURCE.exists():
    FAQ_SOURCE = FAQ_BOOK / "src"
UNIFIED_SEARCHER = MDBOOK_ROOT / "shared" / "unified-searcher.js"
VERIFY_SEARCH = ROOT / "tools" / "verify_unified_search.js"


def retry_windows_file_operation(description: str, operation) -> None:
    """Retry transient Windows sharing violations caused by scanners/indexers."""
    delays = (0.1, 0.2, 0.4, 0.8, 1.0, 1.0, 1.0, 1.0)
    for attempt, delay in enumerate(delays, start=1):
        try:
            operation()
            return
        except OSError as error:
            winerror = getattr(error, "winerror", None)
            if sys.platform != "win32" or (winerror not in {5, 32} and error.errno not in {13, 22}):
                raise
            if attempt == len(delays):
                raise
            print(f"Windows file lock while {description}; retrying ({attempt}/{len(delays)})...")
            time.sleep(delay)


def write_text_with_retry(path: Path, text: str) -> None:
    retry_windows_file_operation(
        f"writing {path.relative_to(ROOT)}",
        lambda: path.write_text(text, encoding="utf-8"),
    )


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for attr, value in attrs:
            if attr in {"href", "src"} and value:
                self.links.append((attr, value))


def clean_directory(path: Path) -> None:
    if path.exists():
        retry_windows_file_operation(
            f"removing {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}",
            lambda: shutil.rmtree(path),
        )
    path.mkdir(parents=True, exist_ok=True)


def copy_tree(source: Path, destination: Path, ignored_names: set[str] | None = None) -> None:
    ignored_names = ignored_names or set()
    clean_directory(destination)

    def ignore(directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignored_names or name == "__pycache__"}

    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=ignore)


def sync_sources() -> None:
    if not MANUAL_SOURCE.exists():
        raise FileNotFoundError(f"Manual source not found: {MANUAL_SOURCE}")
    if not FAQ_SOURCE.exists():
        raise FileNotFoundError(f"FAQ source not found: {FAQ_SOURCE}")

    if MANUAL_SOURCE.resolve() != (MANUAL_BOOK / "src").resolve():
        copy_tree(MANUAL_SOURCE, MANUAL_BOOK / "src", {".idea", "searcher.js"})
    if FAQ_SOURCE.resolve() != (FAQ_BOOK / "src").resolve():
        copy_tree(FAQ_SOURCE, FAQ_BOOK / "src", {".idea"})


def command_available(command: str) -> bool:
    return shutil.which(command) is not None or shutil.which(command + ".exe") is not None


def remove_toml_section(text: str, section: str) -> str:
    pattern = re.compile(rf"(?ms)^\[{re.escape(section)}\]\s*\n.*?(?=^\[|\Z)")
    return pattern.sub("", text)


def adjust_book_toml(book_toml: Path) -> list[str]:
    text = book_toml.read_text(encoding="utf-8")
    removed: list[str] = []

    preprocessor_commands = {
        "preprocessor.toc": "mdbook-toc",
        "preprocessor.admonish": "mdbook-admonish",
    }
    for section, command in preprocessor_commands.items():
        if f"[{section}]" in text and not command_available(command):
            text = remove_toml_section(text, section)
            removed.append(command)

    optional_renderer_commands = {"output.linkcheck": "mdbook-linkcheck"}
    for section, command in optional_renderer_commands.items():
        if f"[{section}]" in text and not command_available(command):
            text = remove_toml_section(text, section)
            removed.append(command)

    book_toml.write_text(text, encoding="utf-8")
    return removed


def heading_slug(title: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", title)
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\s\-\u0590-\u05ff]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text.strip().lower())


def fallback_toc(markdown: str) -> str:
    if "<!-- toc -->" not in markdown:
        return markdown

    toc_items: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{2,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        slug = heading_slug(title)
        if slug:
            toc_items.append(f'<li class="toc-level-{level}"><a href="#{slug}">{title}</a></li>')

    if not toc_items:
        return markdown.replace("<!-- toc -->", "")

    toc_html = "\n".join(
        [
            '<details class="fallback-toc" open>',
            "<summary>אינהאלט</summary>",
            "<ul>",
            *toc_items,
            "</ul>",
            "</details>",
        ]
    )
    return markdown.replace("<!-- toc -->", toc_html)


def fallback_admonish(markdown: str) -> str:
    labels = {
        "warning": "אזהרה",
        "note": "הערה",
        "tip": "טיפ",
        "info": "מידע",
        "danger": "זהירות",
    }

    def replace_block(match: re.Match[str]) -> str:
        kind = match.group("kind") or "note"
        body = match.group("body").strip("\n")
        title = labels.get(kind, kind)
        quote_lines = [f"> **{title}**", ">"]
        quote_lines.extend(f"> {line}" if line else ">" for line in body.splitlines())
        return "\n".join(quote_lines)

    pattern = re.compile(r"```admonish\s+(?P<kind>\w+)[^\n]*\n(?P<body>.*?)\n```", re.DOTALL)
    return pattern.sub(replace_block, markdown)


def apply_fallback_preprocessors(temp_root: Path, removed_commands: list[str]) -> None:
    source_root = temp_root / "src"
    if not source_root.exists():
        return
    needs_toc = "mdbook-toc" in removed_commands
    needs_admonish = "mdbook-admonish" in removed_commands
    if not needs_toc and not needs_admonish:
        return

    for markdown_path in source_root.rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")
        if needs_toc:
            text = fallback_toc(text)
        if needs_admonish:
            text = fallback_admonish(text)
        markdown_path.write_text(text, encoding="utf-8")


def copy_book_root_for_build(book_root: Path, temp_parent: Path) -> tuple[Path, list[str]]:
    temp_root = temp_parent / book_root.name

    def ignore(directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in {"book", "book.zip", "mdbook.exe"}
            or (Path(directory) == book_root and name == ".git")
        }

    shutil.copytree(book_root, temp_root, ignore=ignore)
    removed_preprocessors = adjust_book_toml(temp_root / "book.toml")
    apply_fallback_preprocessors(temp_root, removed_preprocessors)
    return temp_root, removed_preprocessors


def mdbook_executable(book_root: Path) -> Path | str:
    local_exe = book_root / "mdbook.exe"
    if local_exe.exists():
        return local_exe
    executable = shutil.which("mdbook")
    if executable:
        return executable
    raise FileNotFoundError(f"mdbook executable not found in {book_root}")


def run_mdbook_build(book_root: Path, output_dir: Path, temp_parent: Path) -> list[str]:
    clean_directory(output_dir)
    temp_root, removed_preprocessors = copy_book_root_for_build(book_root, temp_parent)
    executable = mdbook_executable(book_root)
    command = [str(executable), "build", "--dest-dir", str(output_dir), str(temp_root)]
    subprocess.run(command, cwd=ROOT, check=True)
    return removed_preprocessors


def js_search_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"JSON\.parse\((?P<literal>'(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\")\)", text)
    if not match:
        raise ValueError(f"Could not find JSON.parse payload in {path}")
    json_text = ast.literal_eval(match.group("literal"))
    return json.loads(json_text)


def merge_search_indexes() -> dict:
    combined_doc_urls: list[str] = []
    combined_docs: dict[str, dict[str, str]] = {}
    combined_doc_info: dict[str, dict[str, int]] = {}

    books = [
        ("manual", "מדריך", OUTPUT_ROOT / "manual" / "searchindex.js"),
        ("faq", "אפט געפרעגטע פראגעס", OUTPUT_ROOT / "faq" / "searchindex.js"),
    ]

    for book_id, label, searchindex_path in books:
        config = js_search_config(searchindex_path)
        doc_urls = config.get("doc_urls", [])
        document_store = config.get("index", {}).get("documentStore", {})
        docs = document_store.get("docs", {})

        for old_id, doc_url in enumerate(doc_urls):
            source_doc = docs.get(str(old_id), {})
            new_id = str(len(combined_doc_urls))
            title = str(source_doc.get("title") or "")
            body = str(source_doc.get("body") or "")
            breadcrumbs = str(source_doc.get("breadcrumbs") or title)
            combined_doc_urls.append(f"{book_id}/{doc_url}")
            combined_docs[new_id] = {
                "title": title,
                "body": body,
                "breadcrumbs": f"{label} > {breadcrumbs}" if breadcrumbs else label,
            }
            combined_doc_info[new_id] = {"body": len(body), "title": len(title), "breadcrumbs": len(breadcrumbs)}

    combined = {
        "doc_urls": combined_doc_urls,
        "index": {"documentStore": {"docs": combined_docs, "docInfo": combined_doc_info}},
        "results_options": {"limit_results": 50, "teaser_word_count": 30},
        "search_options": {},
    }
    return combined


def write_unified_searchindex(config: dict) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    script_literal = json.dumps(payload, ensure_ascii=False)
    script = f"window.search = Object.assign(window.search || {{}}, JSON.parse({script_literal}));\n"
    write_text_with_retry(OUTPUT_ROOT / "searchindex.js", script)


def install_shared_assets() -> None:
    if not UNIFIED_SEARCHER.exists():
        raise FileNotFoundError(f"Missing shared searcher: {UNIFIED_SEARCHER}")
    for book_id in ("manual", "faq"):
        destination = OUTPUT_ROOT / book_id / "unified-searcher.js"
        retry_windows_file_operation(
            f"copying {destination.relative_to(ROOT)}",
            lambda: shutil.copy2(UNIFIED_SEARCHER, destination),
        )


def sidebar_href_needs_prefix(href: str) -> bool:
    return not (
        not href
        or href.startswith("#")
        or href.startswith("/")
        or href.startswith("./")
        or href.startswith("../")
        or re.match(r"^[a-z][a-z0-9+.-]*:", href, re.IGNORECASE)
    )


def rewrite_sidebar_links(book_output: Path) -> None:
    sidebar_pattern = re.compile(r'(<nav id="sidebar".*?</nav>)', re.DOTALL)
    href_pattern = re.compile(r'href="([^"]+)"')

    for html_path in book_output.rglob("*.html"):
        relative_parent = html_path.parent.relative_to(book_output)
        depth = len(relative_parent.parts)
        if depth == 0:
            continue
        prefix = "../" * depth
        html = html_path.read_text(encoding="utf-8", errors="ignore")

        def rewrite_sidebar(match: re.Match[str]) -> str:
            sidebar_html = match.group(1)

            def rewrite_href(href_match: re.Match[str]) -> str:
                href = href_match.group(1)
                if sidebar_href_needs_prefix(href):
                    return f'href="{prefix}{href}"'
                return href_match.group(0)

            return href_pattern.sub(rewrite_href, sidebar_html)

        rewritten = sidebar_pattern.sub(rewrite_sidebar, html, count=1)
        if rewritten != html:
            write_text_with_retry(html_path, rewritten)


def remove_templates_from_manual_sidebar(book_output: Path) -> None:
    sidebar_pattern = re.compile(r'(<nav id="sidebar".*?</nav>)', re.DOTALL)
    templates_section_pattern = re.compile(
        r'<li><ol class="section"><li class="chapter-item[^>]*>'
        r'<a href="(?:\.\./)*templates/intro\.html".*?</ol></li></ol></li>',
        re.DOTALL,
    )
    editing_toggle_pattern = re.compile(
        r'(<a href="(?:\.\./)*editing\.html"[^>]*>.*?</a>)'
        r'<a class="toggle"><div>❱</div></a>',
        re.DOTALL,
    )

    for html_path in book_output.rglob("*.html"):
        html = html_path.read_text(encoding="utf-8", errors="ignore")

        def rewrite_sidebar(match: re.Match[str]) -> str:
            sidebar_html = match.group(1)
            sidebar_html = templates_section_pattern.sub("", sidebar_html)
            sidebar_html = editing_toggle_pattern.sub(r"\1", sidebar_html)
            return sidebar_html

        rewritten = sidebar_pattern.sub(rewrite_sidebar, html, count=1)
        if rewritten != html:
            write_text_with_retry(html_path, rewritten)


def is_external_link(value: str) -> bool:
    parsed = urlsplit(value)
    return bool(parsed.scheme and parsed.scheme not in {"file"}) or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:"))


def local_link_target(html_path: Path, value: str) -> Path | None:
    if is_external_link(value):
        return None
    parsed = urlsplit(value)
    raw_path = unquote(parsed.path)
    if not raw_path:
        return None
    if raw_path.startswith("/"):
        return None
    target = (html_path.parent / raw_path).resolve()
    if value.endswith("/") or raw_path.endswith("/"):
        target = target / "index.html"
    return target


def verify_links() -> tuple[int, int, list[str]]:
    errors: list[str] = []
    internal_links = 0
    cross_book_links = 0

    for html_path in OUTPUT_ROOT.rglob("*.html"):
        parser = LinkParser()
        parser.feed(html_path.read_text(encoding="utf-8", errors="ignore"))
        for _attr, value in parser.links:
            target = local_link_target(html_path, value)
            if target is None:
                continue
            if target.suffix == ".md":
                errors.append(f"Markdown link left in HTML: {html_path.relative_to(ROOT)} -> {value}")
                continue
            if target.suffix not in {".html", ".css", ".js", ".png", ".svg", ".woff", ".woff2", ".ttf", ".otf", ".ico"}:
                continue
            internal_links += 1
            if not target.exists():
                errors.append(f"Missing target: {html_path.relative_to(ROOT)} -> {value}")
            try:
                relative_target = target.relative_to(OUTPUT_ROOT)
                relative_source = html_path.relative_to(OUTPUT_ROOT)
                if relative_source.parts[0] != relative_target.parts[0] and relative_target.parts[0] in {"manual", "faq"}:
                    cross_book_links += 1
            except ValueError:
                pass

    return internal_links, cross_book_links, errors


def verify_static_output(search_config: dict) -> None:
    link_count, cross_link_count, link_errors = verify_links()
    if link_errors:
        formatted = "\n".join(f"  - {error}" for error in link_errors[:30])
        raise RuntimeError(f"Link verification failed ({len(link_errors)} errors):\n{formatted}")
    if cross_link_count == 0:
        raise RuntimeError("No cross-book links were found in the generated output.")

    doc_urls = search_config.get("doc_urls", [])
    if not any(str(url).startswith("manual/") for url in doc_urls):
        raise RuntimeError("Unified search index has no manual/ URLs.")
    if not any(str(url).startswith("faq/") for url in doc_urls):
        raise RuntimeError("Unified search index has no faq/ URLs.")

    docs = search_config.get("index", {}).get("documentStore", {}).get("docs", {})
    combined_body = "\n".join(str(doc.get("body", "")) for doc in docs.values())
    if "סינכראניזירן" not in combined_body:
        raise RuntimeError("Unified search index does not contain the Hebrew verification term 'סנכרון'.")

    startup_page = OUTPUT_ROOT / "manual" / "platform" / "windows" / "startup-issues.html"
    startup_html = startup_page.read_text(encoding="utf-8", errors="ignore")
    if "unified-searcher.js" not in startup_html or "path_to_site_root" not in startup_html:
        raise RuntimeError("Windows startup page is missing unified search/sidebar support scripts.")

    for html_path in (OUTPUT_ROOT / "manual").rglob("*.html"):
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        if "<!-- toc -->" in html or "```admonish" in html:
            raise RuntimeError(f"Unprocessed mdBook marker remains in {html_path.relative_to(ROOT)}")

    manual_intro = (OUTPUT_ROOT / "manual" / "intro.html").read_text(encoding="utf-8", errors="ignore")
    if 'href="templates/intro.html"' in manual_intro or 'href="../templates/intro.html"' in manual_intro:
        raise RuntimeError("Templates pages are still visible in the manual sidebar.")

    faq_index = (OUTPUT_ROOT / "faq" / "index.html").read_text(encoding="utf-8", errors="ignore")
    if 'href="syncing.html"' not in faq_index or '<a class="toggle">' not in faq_index:
        raise RuntimeError("FAQ sync section is not rendered as a collapsible sidebar section.")

    print(f"Static verification passed: {link_count} local links, {cross_link_count} cross-book links.")


def run_js_search_verification() -> None:
    node = shutil.which("node")
    if not node:
        print("Node.js not found; skipped Lunr runtime verification.")
        return
    if not VERIFY_SEARCH.exists():
        print("verify_unified_search.js not found; skipped Lunr runtime verification.")
        return
    subprocess.run([node, str(VERIFY_SEARCH), str(ROOT)], cwd=ROOT, check=True)


def build(skip_verify: bool = False, skip_js_verify: bool = False, skip_sync: bool = False) -> None:
    if skip_sync:
        print("Skipping sync (--skip-sync); using existing mdbook/*/src content.")
    else:
        print("Syncing Markdown sources into mdbook/*/src...")
        sync_sources()
    clean_directory(OUTPUT_ROOT)

    with tempfile.TemporaryDirectory(prefix="anki-mdbook-") as temp_name:
        temp_parent = Path(temp_name)
        print("Building manual...")
        manual_removed = run_mdbook_build(MANUAL_BOOK, OUTPUT_ROOT / "manual", temp_parent)
        print("Building FAQ...")
        faq_removed = run_mdbook_build(FAQ_BOOK, OUTPUT_ROOT / "faq", temp_parent)

    removed = sorted(set(manual_removed + faq_removed))
    if removed:
        print("Skipped missing preprocessors in temporary build config: " + ", ".join(removed))

    print("Installing shared search UI...")
    install_shared_assets()
    print("Rewriting nested sidebar links...")
    rewrite_sidebar_links(OUTPUT_ROOT / "manual")
    rewrite_sidebar_links(OUTPUT_ROOT / "faq")
    print("Removing template pages from the manual sidebar...")
    remove_templates_from_manual_sidebar(OUTPUT_ROOT / "manual")
    print("Merging search indexes...")
    search_config = merge_search_indexes()
    write_unified_searchindex(search_config)

    if not skip_verify:
        print("Verifying links and unified search index...")
        verify_static_output(search_config)
        if not skip_js_verify:
            run_js_search_verification()

    print(f"Unified mdBook output ready: {OUTPUT_ROOT}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-verify", action="store_true", help="build without static/link verification")
    parser.add_argument("--skip-js-verify", action="store_true", help="skip the Node/Lunr verification step")
    parser.add_argument("--skip-sync", action="store_true", help="skip syncing manual/ and faq/ sources; build from existing mdbook/*/src content")
    args = parser.parse_args()
    build(skip_verify=args.skip_verify, skip_js_verify=args.skip_js_verify, skip_sync=args.skip_sync)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
