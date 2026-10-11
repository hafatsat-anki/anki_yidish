let isBrushActive = false;
let copiedStyles = {};

const BLOCK_TAGS = new Set([
    "LI", "P", "DIV", "UL", "OL", "H1", "H2", "H3", "H4", "H5", "H6",
    "BLOCKQUOTE", "PRE", "TR", "TD", "TH", "TABLE", "TBODY", "THEAD"
]);

// ×¤×•× ×§×¦×™×™×ª ×¢×–×¨ ×œ× ×™×§×•×™ ×ª×’×™×•×ª ×¡×’× ×•×Ÿ ×ž×§×•× × ×•×ª
function getCleanedContent(contentFragment) {
    const div = document.createElement("div");
    div.appendChild(contentFragment.cloneNode(true));

    const spans = div.querySelectorAll("span");
    for (let i = spans.length - 1; i >= 0; i--) {
        const span = spans[i];
        if (span.hasAttribute("class") && span.getAttribute("class").length > 0) {
            continue;
        }
        const parent = span.parentNode;
        while (span.firstChild) {
            parent.insertBefore(span.firstChild, span);
        }
        parent.removeChild(span);
    }
    return div.innerHTML;
}

function pasteFormat(selection) {
    if (!copiedStyles || !selection || selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    if (range.collapsed) return;

    const span = document.createElement("span");
    const properties = [
        "fontSize",
        "fontFamily",
        "fontWeight",
        "fontStyle",
        "textDecoration",
        "verticalAlign",
        "color",
        "backgroundColor",
        "textAlign"
    ];

    // #316 — לא מדביקים רקע שקוף; אחרת טקסט ללא רקע "מדביק" רקע ריק שדורס רקע קיים
    properties.forEach(prop => {
        if (copiedStyles[prop]) {
            if (prop === "backgroundColor" && (copiedStyles[prop] === "rgba(0, 0, 0, 0)" || copiedStyles[prop] === "transparent")) return;
            span.style[prop] = copiedStyles[prop];
        }
    });

    const content = range.cloneContents();
    const cleanHTML = getCleanedContent(content);
    span.innerHTML = cleanHTML;

    document.execCommand("insertHTML", false, span.outerHTML);
}

function toggleBrush(sr) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
<g transform="rotate(45 12 12)">
<rect x="10" y="2" width="4" height="10" rx="1" fill="#fff" stroke="#000" stroke-width="2"/>
<rect x="9" y="12" width="6" height="4" rx=".5" fill="#e0e0e0" stroke="#000" stroke-width="2"/>
<rect x="9" y="16" width="6" height="6" rx=".5" fill="#fff" stroke="#000" stroke-width="2"/>
<rect x="10" y="19" width="4" height="2.5" fill="#FF9800"/>
</g></svg>`;

    if (!isBrushActive) {
        const selection = sr.getSelection();

        if (selection.rangeCount > 0 && selection.anchorOffset !== selection.focusOffset) {
          document.body.style.cursor = `url("data:image/svg+xml,${encodeURIComponent(svg)}") 0 20, auto`;

          let anchorNode = selection.anchorNode;
          const element =
            anchorNode.nodeType === 3 ? anchorNode.parentElement : anchorNode;

          // חיפוש צבע רקע אמיתי (background-color אינו תורש, לכן יש לטפס בעץ
          // ולמצוא את ההורה הראשון שמגדיר רקע לא־שקוף)
          let resolvedBgColor = "";
          let parentChecker = element;
          while (
            parentChecker &&
            parentChecker !== sr &&
            parentChecker !== document.body
          ) {
            const parentStyle = window.getComputedStyle(parentChecker);
            const bg = parentStyle.backgroundColor;
            if (bg && bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent") {
              resolvedBgColor = bg;
              break;
            }
            parentChecker = parentChecker.parentElement;
          }

          const computedStyle = window.getComputedStyle(element);
          copiedStyles = {
            color: computedStyle.color,
            backgroundColor: resolvedBgColor || computedStyle.backgroundColor,
            fontSize: computedStyle.fontSize,
            fontWeight: computedStyle.fontWeight,
            fontStyle: computedStyle.fontStyle,
            textDecoration: computedStyle.textDecoration,
            fontFamily: computedStyle.fontFamily,
          };

          isBrushActive = true;
          selection.removeAllRanges();
        }
    }
}

function ensurePendingStyleHandler(root) {
    if (!root || root._hafPendingStyleHandlerAttached) return;
    root._hafPendingStyleHandlerAttached = true;

    root.addEventListener("beforeinput", function (event) {
        const styleEntries = root._hafPendingStyleEntries;
        if (!styleEntries || event.inputType !== "insertText" || !event.data || event.isComposing) return;

        const selection = typeof root.getSelection === "function"
            ? root.getSelection()
            : window.getSelection();
        if (!selection || selection.rangeCount === 0) return;

        event.preventDefault();
        event.stopImmediatePropagation();

        const range = selection.getRangeAt(0);
        range.deleteContents();

        const span = document.createElement("span");
        styleEntries.forEach(([style, value]) => {
            span.style.setProperty(style, value, "important");
        });
        span.textContent = event.data;
        range.insertNode(span);

        const textNode = span.firstChild;
        const caretRange = document.createRange();
        caretRange.setStart(textNode, textNode.textContent.length);
        caretRange.collapse(true);
        selection.removeAllRanges();
        selection.addRange(caretRange);
        root._hafPendingStyleEntries = null;
        setTimeout(() => gText("e"), 0);
    }, true);
}

function insertLiveStyleSpan(selection, range, styleEntries) {
    if (!styleEntries || styleEntries.length === 0) return false;
    const root = range.startContainer && range.startContainer.getRootNode
        ? range.startContainer.getRootNode()
        : document;
    root._hafPendingStyleEntries = styleEntries.map(([style, value]) => [style, value]);
    ensurePendingStyleHandler(root);
    return true;
}

function applyFullStyle(selection, font, size, color, bold, italic, underline, bgColor, superscript, subscript) {
    if (!selection || selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    // #161 — formatting must preserve the end moved by the next Shift+Arrow.
    const backward = window.HafRtlEditing.isBackward(selection);
    const styleEntries = [];
    if (font) styleEntries.push(["font-family", font]);
    size = normalizePresetSize(size);
    if (size) styleEntries.push(["font-size", size]);
    if (color) styleEntries.push(["color", color]);
    if (bold) styleEntries.push(["font-weight", "bold"]);
    if (italic) styleEntries.push(["font-style", "italic"]);
    if (underline) styleEntries.push(["text-decoration", "underline"]);
    if (bgColor) styleEntries.push(["background-color", bgColor]);
    if (superscript) styleEntries.push(["vertical-align", "super"]);
    else if (subscript) styleEntries.push(["vertical-align", "sub"]);

    if (range.collapsed && insertLiveStyleSpan(selection, range, styleEntries)) return;

    const applied = applyInlineStylesAcrossComplexSelection(selection, range, styleEntries);
    if (applied) return;

    const content = range.cloneContents();

    const cleanHTML = getCleanedContent(content);

    const span = document.createElement("span");
    if (font) span.style.fontFamily = font;
    if (size) span.style.fontSize = size;
    if (color) span.style.color = color;
    if (bold) span.style.fontWeight = "bold";
    if (italic) span.style.fontStyle = "italic";
    if (underline) span.style.textDecoration = "underline";
    if (bgColor) span.style.backgroundColor = bgColor;
    if (superscript) span.style.verticalAlign = "super";
    else if (subscript) span.style.verticalAlign = "sub";

    span.innerHTML = cleanHTML;
    range.deleteContents();
    range.insertNode(span);
    if (span.parentNode) {
        try {
            const newRange = document.createRange();
            newRange.selectNodeContents(span);
            window.HafRtlEditing.restoreRange(selection, newRange, backward);
        } catch (e) {
            const caretRange = document.createRange();
            caretRange.setStartAfter(span);
            caretRange.collapse(true);
            selection.removeAllRanges();
            selection.addRange(caretRange);
        }
    }
}

function findClosestBlockAncestor(node, blockTags) {
    let current = node;
    if (current && current.nodeType === 3) current = current.parentElement;

    while (current) {
        if (current.nodeType === 1 && blockTags.has(current.tagName)) {
            return current;
        }
        current = current.parentElement;
    }
    return null;
}

function clearFragmentInlineStyles(fragment, styleEntries) {
    if (!fragment || !styleEntries || styleEntries.length === 0) return;

    const properties = new Set(styleEntries.map(([style]) => style));
    if (properties.has("text-decoration")) {
        properties.add("text-decoration-line");
        properties.add("text-decoration-style");
        properties.add("text-decoration-color");
    }

    if (!fragment.querySelectorAll) return;

    fragment.querySelectorAll("*").forEach(el => {
        if (!el.style) return;
        properties.forEach(prop => el.style.removeProperty(prop));
        if (el.getAttribute("style") === "") {
            el.removeAttribute("style");
        }
    });
}

function applyInlineStylesAcrossComplexSelection(selection, range, styleEntries) {
    if (!styleEntries || styleEntries.length === 0) return false;
    // #161 — capture direction before extracting/replacing text nodes.
    const backward = window.HafRtlEditing.isBackward(selection);

    const common = range.commonAncestorContainer;
    const root = common.nodeType === Node.TEXT_NODE ? common.parentNode : common;
    if (!root) return false;

    const walker = (root.ownerDocument || document).createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) {
        if (!node.nodeValue || !range.intersectsNode(node)) continue;
        textNodes.push(node);
    }

    if (textNodes.length === 0) return false;

    let endMostInserted = null;
    let startMostInserted = null;
    for (let i = textNodes.length - 1; i >= 0; i--) {
        const textNode = textNodes[i];
        if (!textNode.parentNode) continue;

        const segment = document.createRange();
        segment.selectNodeContents(textNode);

        if (range.compareBoundaryPoints(Range.START_TO_START, segment) > 0) {
            segment.setStart(range.startContainer, range.startOffset);
        }
        if (range.compareBoundaryPoints(Range.END_TO_END, segment) < 0) {
            segment.setEnd(range.endContainer, range.endOffset);
        }

        if (segment.collapsed) continue;

        const extracted = segment.extractContents();
        if (!extracted || extracted.childNodes.length === 0) continue;
        clearFragmentInlineStyles(extracted, styleEntries);

        const span = document.createElement("span");
        styleEntries.forEach(([style, value]) => {
            span.style.setProperty(style, value, "important");
        });
        span.appendChild(extracted);

        segment.insertNode(span);
        if (!endMostInserted) endMostInserted = span;
        startMostInserted = span; // תמיד מתעדכן → לבסוף מצביע על ה-span הראשון
    }

    if (startMostInserted && endMostInserted && startMostInserted.parentNode && endMostInserted.parentNode) {
        try {
            const newRange = document.createRange();
            newRange.setStartBefore(startMostInserted);
            newRange.setEndAfter(endMostInserted);
            window.HafRtlEditing.restoreRange(selection, newRange, backward);
        } catch (e) {
            const caretRange = document.createRange();
            caretRange.setStartAfter(endMostInserted);
            caretRange.collapse(true);
            selection.removeAllRanges();
            selection.addRange(caretRange);
        }
    }

    return true;
}

function applyInlineStyleAcrossComplexSelection(selection, range, style, arg) {
    return applyInlineStylesAcrossComplexSelection(selection, range, [[style, arg]]);
}

// ×©×™× ×•×™ ×’×•×“×œ/×’×•×¤×Ÿ ×‘×•×“×“
function fontsi(selection, style, arg) {
    if (!selection || selection.rangeCount === 0) return;
    // #161 — ordered Range boundaries are not the selection's anchor/focus.
    const backward = window.HafRtlEditing.isBackward(selection);
    if (style === "font-size" && arg !== "unset") arg += "pt";

    const range = selection.getRangeAt(0);
    if (range.collapsed && arg !== "unset" && arg !== "'none'") {
        insertLiveStyleSpan(selection, range, [[style, arg]]);
        return;
    }
    const contentFragment = range.cloneContents();

    // × ×™×§×•×™ ×”×¡×˜×™×™×œ ×”×§×™×™× ×ž×›×œ ×”-descendants
    contentFragment.querySelectorAll("*").forEach(el => {
        if (el.style) {
            el.style.removeProperty(style);
            if (el.getAttribute("style") === "") {
                el.removeAttribute("style");
            }
        }
    });

    // ×‘×œ×•×§×™× ×‘×ª×•×š ×”×¡×œ×§×©×Ÿ (×›×’×•×Ÿ <li>, <p>, <div>) ×œ× ×™×›×•×œ×™× ×œ×”×™×•×ª ×¢×˜×•×¤×™× ×‘-<span>.
    // ×¢×˜×™×¤×” ×›×–×• ×™×•×¦×¨×ª HTML ×œ× ×ª×§×™×Ÿ ×©×”×“×¤×“×¤×Ÿ "×ž×ª×§×Ÿ" ×¢"×™ ×”×•×¡×¤×ª ×™×¨×™×“×ª ×©×•×¨×” (#11).
    // ×œ×›×Ÿ ×¢×•×˜×¤×™× ××ª ×”×ª×•×›×Ÿ ×”×¤× ×™×ž×™ ×©×œ ×›×œ ×‘×œ×•×§ ×‘× ×¤×¨×“ ×•×©×•×ž×¨×™× ×¢×œ ×ž×‘× ×” ×”×¨×©×™×ž×”.
    const wrapper = document.createElement("div");
    wrapper.appendChild(contentFragment);

    const hasBlock = Array.from(wrapper.childNodes).some(
        n => n.nodeType === 1 && BLOCK_TAGS.has(n.tagName)
    );

    const shouldApply = (arg !== "unset" && arg !== "'none'");

    const startBlock = findClosestBlockAncestor(range.startContainer, BLOCK_TAGS);
    const endBlock = findClosestBlockAncestor(range.endContainer, BLOCK_TAGS);
    const crossesBlockBoundaries = shouldApply && startBlock && endBlock && startBlock !== endBlock;

    // When selection crosses block boundaries, avoid rebuilding block HTML in one insert.
    // Re-applying style per text segment keeps list/item structure stable.
    if (crossesBlockBoundaries) {
        const applied = applyInlineStyleAcrossComplexSelection(selection, range, style, arg);
        if (applied) return;
    }

    if (shouldApply && hasBlock) {
        // ×›×©×”×¡×œ×§×©×Ÿ ×ž×ª×—×™×œ ×‘×ª×•×š ×‘×œ×•×§ (LI, P ×•×›×“'), ×”×‘×œ×•×§ ×”×¨××©×•×Ÿ ×‘×¤×¨×’×ž× ×˜ ×”×•×
        // "×—×œ×§×™" â€” ×¢×˜×™×¤×ª×• ×ž×—×“×© ×‘-LI ×ª×’×¨×•× ×œ×¤×™×¦×•×œ ×©×•×¨×” (#11).
        // ×œ×›×Ÿ ×‘×ž×§×¨×” ×–×” ×ž×•×¦×™××™× ××ª ×ª×•×›× ×• ×™×©×™×¨×•×ª ×œ×œ× ×¢×˜×™×¤×ª ×”×‘×œ×•×§.
        let startsInsideBlock = false;
        let checkNode = range.startContainer;
        if (checkNode.nodeType === 3) checkNode = checkNode.parentElement;
        while (checkNode) {
            if (checkNode.nodeType === 1 && BLOCK_TAGS.has(checkNode.tagName)) {
                startsInsideBlock = true;
                break;
            }
            checkNode = checkNode.parentElement;
        }

        const originalChildren = Array.from(wrapper.childNodes);
        while (wrapper.firstChild) wrapper.removeChild(wrapper.firstChild);

        let inlineGroup = null;
        let isFirstBlock = true;
        originalChildren.forEach(child => {
            if (child.nodeType === 1 && BLOCK_TAGS.has(child.tagName)) {
                inlineGroup = null;
                const span = document.createElement("span");
                span.style.setProperty(style, arg, "important");
                while (child.firstChild) span.appendChild(child.firstChild);
                if (isFirstBlock && startsInsideBlock) {
                    // ×”×¡×œ×§×©×Ÿ ×ž×ª×—×™×œ ×‘×ª×•×š ×‘×œ×•×§ â€” ××œ × ×¢×˜×•×£ ×©×•×‘ ×‘-LI/P
                    wrapper.appendChild(span);
                } else {
                    child.appendChild(span);
                    wrapper.appendChild(child);
                }
                isFirstBlock = false;
            } else {
                if (!inlineGroup) {
                    inlineGroup = document.createElement("span");
                    inlineGroup.style.setProperty(style, arg, "important");
                    wrapper.appendChild(inlineGroup);
                }
                inlineGroup.appendChild(child);
            }
        });
    } else if (shouldApply) {
        // ××™×Ÿ ×‘×œ×•×§×™× â€” ×‘×˜×•×— ×œ×¢×˜×•×£ ××ª ×›×œ ×”×¤×¨×’×ž× ×˜ ×‘×¡×¤××Ÿ ×™×—×™×“
        const span = document.createElement("span");
        while (wrapper.firstChild) span.appendChild(wrapper.firstChild);
        span.style.setProperty(style, arg, "important");
        wrapper.appendChild(span);
    }
    // ×× arg === "unset" â€” ×›×‘×¨ × ×™×§×™× ×• ××ª ×”×¡×˜×™×™×œ ×ž×›×œ ×”-descendants ×•××™×Ÿ ×¦×•×¨×š ×œ×¢×˜×•×£

    const fragment = document.createDocumentFragment();
    let firstInserted = null;
    let lastInserted = null;
    while (wrapper.firstChild) {
        const node = fragment.appendChild(wrapper.firstChild);
        if (!firstInserted) firstInserted = node;
        lastInserted = node;
    }

    range.deleteContents();
    range.insertNode(fragment);

    if (firstInserted && lastInserted && firstInserted.parentNode && lastInserted.parentNode) {
        try {
            const newRange = document.createRange();
            newRange.setStartBefore(firstInserted);
            newRange.setEndAfter(lastInserted);
            window.HafRtlEditing.restoreRange(selection, newRange, backward);
        } catch (e) {
            const caretRange = document.createRange();
            caretRange.setStartAfter(lastInserted);
            caretRange.collapse(true);
            selection.removeAllRanges();
            selection.addRange(caretRange);
        }
    }
}

// ×”×œ×•×’×™×§×” ×”××ž×™×ª×™×ª â€” × ×§×¨××ª ×›×©×™×© shadow root
function updateEditorButtons(shadowRoot) {
    try {
        const sel = shadowRoot.getSelection();
        if (!sel || sel.rangeCount === 0) return;

        const range = sel.getRangeAt(0);

        const parent = range.commonAncestorContainer.nodeType === 1
            ? range.commonAncestorContainer
            : range.commonAncestorContainer.parentElement;
        if (!parent) return;

        const computedSz = getComputedStyle(parent).getPropertyValue("font-size");
        const displaySize = Math.round(parseFloat(computedSz) * 0.75);

        // ×–×™×”×•×™ ×”×× ×™×© ×¡×œ×§×©×Ÿ ××ž×™×ª×™
        const hasRealSelection = !sel.isCollapsed
            || !range.collapsed
            || sel.toString().length > 0
            || sel.anchorNode !== sel.focusNode
            || sel.anchorOffset !== sel.focusOffset;

        let isMixedSize = false;
        let isMixedFont = false;
        if (hasRealSelection) {
            const ancestor = range.commonAncestorContainer;
            const root = ancestor.nodeType === Node.TEXT_NODE ? ancestor.parentElement : ancestor;
            const sizeSet = new Set();
            const fontSet = new Set();
            const walker = (root.ownerDocument || document).createTreeWalker(root, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walker.nextNode())) {
                if (range.intersectsNode(node) && node.parentElement) {
                    const cs = getComputedStyle(node.parentElement);
                    sizeSet.add(cs.getPropertyValue('font-size'));
                    fontSet.add(cs.getPropertyValue('font-family').replace(/['"]/g, '').split(',')[0].trim());
                }
            }
            if (sizeSet.size > 1) isMixedSize = true;
            if (fontSet.size > 1) isMixedFont = true;
        }

        // ×¢×“×›×•×Ÿ ×›×¤×ª×•×¨ ×’×•×“×œ
        const sizeBtn = document.getElementById("size");
        if (sizeBtn) {
            if (isMixedSize) {
                sizeBtn.textContent = "(מערערע)";
            } else if (displaySize && !isNaN(displaySize)) {
                sizeBtn.textContent = displaySize;
            } else {
                sizeBtn.textContent = "גרייס";
            }
        }

        // ×¢×“×›×•×Ÿ ×›×¤×ª×•×¨ ×’×•×¤×Ÿ
        let fnt = getComputedStyle(parent).getPropertyValue("font-family");
        fnt = fnt.replace(/['"]/g, "");
        const fnbtn = document.getElementById("font");
        if (fnbtn) {
            if (isMixedFont) {
                fnbtn.textContent = "(מרובה)";
                fnbtn.style.fontFamily = "";
            } else if (fnt) {
                fnt = fnt.split(",")[0];
                fnbtn.textContent = fnt + " אבגד ";
                fnbtn.style.fontFamily = fnt;
            } else {
                fnbtn.textContent = "גופן";
            }
        }
    } catch (e) {
        console.error("Error in updateEditorButtons:", e);
    }
}

// gText × ×§×¨××ª ×’× ×ž-Python ××—×¨×™ ×”×—×œ×ª ×¢×™×¦×•×‘
function gText(e) {
    document.querySelectorAll(".rich-text-editable").forEach(rte => {
        if (rte.shadowRoot) updateEditorButtons(rte.shadowRoot);
    });
}

function forEachRichText(callback) {
    document.querySelectorAll(".rich-text-editable").forEach(callback);
}

function scheduleNextEditorFrame(callback) {
    if (window.requestAnimationFrame) {
        window.requestAnimationFrame(callback);
    } else {
        setTimeout(callback, 0);
    }
}

const _editorMutationScans = [];
let _editorMutationObserver = null;
let _editorMutationScanQueued = false;

function scheduleEditorMutationScans() {
    if (_editorMutationScanQueued) return;
    _editorMutationScanQueued = true;

    scheduleNextEditorFrame(function() {
        _editorMutationScanQueued = false;
        _editorMutationScans.forEach(function(scan) {
            try {
                scan();
            } catch (error) {
                console.error("Error in font-size editor setup scan:", error);
            }
        });
    });
}

function ensureEditorMutationObserver() {
    if (_editorMutationObserver || !document.body) return;
    _editorMutationObserver = new MutationObserver(scheduleEditorMutationScans);
    _editorMutationObserver.observe(document.body, { childList: true, subtree: true });
}

function registerEditorMutationScan(scan) {
    _editorMutationScans.push(scan);
    ensureEditorMutationObserver();
    if (!_editorMutationObserver && document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", ensureEditorMutationObserver, { once: true });
    }
    scheduleEditorMutationScans();
}

// #161 — arrow navigation belongs to shared_libs/web/rtl_editing.js, also used
// in the reviewer. Keeping a second handler here caused the fixes to diverge.

// #138 — Qt can activate a style QShortcut and still let WebEngine receive the
// same Alt/Ctrl letter. Keep a normalized blocklist so that second delivery
// cannot replace the selected text with the shortcut letter.
let _hafFontSizeShortcutBlocklist = new Set();

function normalizeEditorShortcut(shortcut) {
    const rawParts = String(shortcut || "")
        // #138 — keep a literal '+' key instead of confusing Ctrl++ with Ctrl.
        .replace(/\+\s*$/, "+plus")
        .split("+")
        .map((part) => part.trim().toLowerCase())
        .filter(Boolean);
    const normalized = new Set(rawParts.map((part) => part === "control" ? "ctrl" : part));
    const main = rawParts.find((part) => !["ctrl", "control", "shift", "alt", "meta", "cmd", "command"].includes(part));
    const parts = [];
    if (normalized.has("ctrl") || normalized.has("control") || normalized.has("meta") || normalized.has("cmd") || normalized.has("command")) parts.push("ctrl");
    if (normalized.has("shift")) parts.push("shift");
    if (normalized.has("alt")) parts.push("alt");
    if (main) parts.push(main);
    return parts.join("+");
}

function shortcutFromEditorEvent(event) {
    let main = String(event.key || "").toLowerCase();
    const code = String(event.code || "");
    if (/^Key[A-Z]$/.test(code)) main = code.slice(3).toLowerCase();
    else if (/^Digit[0-9]$/.test(code)) main = code.slice(5);
    else if (/^F(?:[1-9]|1[0-2])$/.test(code)) main = code.toLowerCase();
    // #138 — punctuation is configured as ';' or ',', not 'Semicolon'/'Comma'.
    return normalizeEditorShortcut([
        event.ctrlKey || event.metaKey ? "ctrl" : "",
        event.shiftKey ? "shift" : "",
        event.altKey ? "alt" : "",
        main,
    ].filter(Boolean).join("+"));
}

function blockConfiguredEditorShortcut(event) {
    // #138 — Hebrew shortcuts can match the printed key or the physical Latin key.
    const printed = normalizeEditorShortcut([
        event.ctrlKey || event.metaKey ? "ctrl" : "",
        event.shiftKey ? "shift" : "",
        event.altKey ? "alt" : "",
        event.key,
    ].filter(Boolean).join("+"));
    if (!_hafFontSizeShortcutBlocklist.has(shortcutFromEditorEvent(event)) &&
        !_hafFontSizeShortcutBlocklist.has(printed)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
}

window.HafFontSizeSetShortcutBlocklist = function(shortcuts) {
    _hafFontSizeShortcutBlocklist = new Set(
        (Array.isArray(shortcuts) ? shortcuts : [])
            .map(normalizeEditorShortcut)
            .filter(Boolean)
    );
};

// ×—×™×‘×•×¨ ×œ-shadow roots â€” ×‘××ž×¦×¢×•×ª MutationObserver ×›×“×™ ×œ×ª×¤×•×¡ ××œ×ž× ×˜×™× ×©× ×•×¦×¨×™× ×ž××•×—×¨
function attachToRichText(rte) {
    if (!rte.shadowRoot || rte._gTextAttached) return;
    rte._gTextAttached = true;
    const sr = rte.shadowRoot;
    // #138 — capture runs before contenteditable inserts the letter.
    sr.addEventListener("keydown", blockConfiguredEditorShortcut, true);
    sr.addEventListener("mouseup", () => setTimeout(() => updateEditorButtons(sr), 50));
    sr.addEventListener("keyup", () => setTimeout(() => updateEditorButtons(sr), 50));
}

function scanRichTextAttachments() {
    forEachRichText(attachToRichText);
}

registerEditorMutationScan(scanRichTextAttachments);


function updatePresetButtonsVisually(presets) {
    presets.forEach((p, i) => {
        const btn = document.getElementById(`preset_${i}`);
        if (btn) {
            btn.textContent = "א";
            btn.style.setProperty('padding', '0', 'important');
            btn.style.setProperty('margin', '0', 'important');
            btn.style.setProperty('display', 'flex', 'important');
            btn.style.setProperty('justify-content', 'center', 'important');
            btn.style.setProperty('align-items', 'center', 'important');
            // #137 — שטעל נישט קיין אייגנשאפט אויב זי איז ליידיג (= אן א טויש)
            if (p.font) btn.style.setProperty('font-family', p.font, 'important');
            if (p.color) btn.style.setProperty('color', p.color, 'important');
            btn.style.setProperty('font-weight', p.bold ? 'bold' : 'normal', 'important');
            btn.style.setProperty('font-style', p.italic ? 'italic' : 'normal', 'important');
            btn.style.setProperty('text-decoration', p.underline ? 'underline' : 'none', 'important');
            if (p.bgColor) btn.style.setProperty('background-color', p.bgColor, 'important');
            const size = parseInt((p.size || '').replace(/\D/g, '')) || 0;
            if (size > 0) {
                const displaySize = Math.min(size, 22);
                btn.style.setProperty('font-size', displaySize + 'px', 'important');
            }
            // #133 — דערהיינטיגונג tooltip מיט די סטיל פרטים אנשטאט "טוען..."
            const parts = [];
            if (p.font) parts.push(p.font);
            if (size > 0) parts.push(size + 'px');
            if (p.bold) parts.push('דיק');
            if (p.italic) parts.push('שיף');
            if (p.underline) parts.push('אונטערשטרייכן');
            // אישיו #400: דער הילף טעקסט ווייזט אויך דעם סטיל קיצור קנעפל.
            btn.title = 'סטיל ' + (i + 1) + ': ' + (parts.join(', ') || 'אן א טויש') + (p.shortcut ? '\nקיצור: ' + p.shortcut : '');
        }
    });
}

function updatePresetButtonsVisuallyOnStart(presets) {
    let attempts = 0;
    const maxAttempts = 50;

    const intervalId = setInterval(() => {
        const firstBtn = document.getElementById("preset_0");

        if (firstBtn) {
            updatePresetButtonsVisually(presets);
            clearInterval(intervalId);
        }

        attempts++;
        if (attempts >= maxAttempts) {
            clearInterval(intervalId);
        }
    }, 200);
}

// =========================================================
// ×ª×™×§×•×Ÿ #52 â€” ×©×ž×™×¨×ª ×’×•×“×œ ×’×•×¤×Ÿ ×•×¡×•×’ ×’×•×¤×Ÿ ×‘×”×“×‘×§×” ×ž×•×•×¨×“
// =========================================================

function cleanPastedHtml(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const body = doc.body;

    // ×”×¡×¨×ª ×ª×’×™ ×ž×˜×/×¡×˜×™×™×œ/×¡×§×¨×™×¤×˜ ×©Word ×ž×•×¡×™×£
    body.querySelectorAll('meta, style, script').forEach(el => el.remove());

    body.querySelectorAll('*').forEach(el => {
        const tag = el.tagName.toUpperCase();

        // ×©×ž×™×¨×ª ×¢×¨×›×™ ×”×¡×˜×™×™×œ ×œ×¤× ×™ × ×™×§×•×™
        const fontSize   = el.style.fontSize;
        const fontFamily = el.style.fontFamily;
        const color      = el.style.color;
        const fontWeight = el.style.fontWeight;
        const fontStyle  = el.style.fontStyle;
        const textDec    = el.style.textDecoration;
        const bgColor    = el.style.backgroundColor;

        // ×©×ž×™×¨×ª ××˜×¨×™×‘×™×•×˜×™× ×—×™×•× ×™×™× ×œ×¤×™ ×ª×’
        const src  = tag === 'IMG' ? el.getAttribute('src')  : null;
        const alt  = tag === 'IMG' ? el.getAttribute('alt')  : null;
        const href = tag === 'A'   ? el.getAttribute('href') : null;

        // × ×™×§×•×™ ×›×œ ×”××˜×¨×™×‘×™×•×˜×™×
        [...el.attributes].forEach(attr => el.removeAttribute(attr.name));

        // ×©×—×–×•×¨ ××˜×¨×™×‘×™×•×˜×™× ×—×™×•× ×™×™×
        if (src)  el.setAttribute('src',  src);
        if (alt)  el.setAttribute('alt',  alt);
        if (href) el.setAttribute('href', href);

        // ×‘× ×™×™×ª ×”×¡×˜×™×™×œ ×”× ×§×™ â€” ×©×•×ž×¨×™× ×¨×§ ×ž××¤×™×™× ×™ ×¤×•× ×˜ ×•×¢×™×¦×•×‘
        const parts = [];
        if (fontSize)   parts.push(`font-size:${fontSize}`);
        if (fontFamily) {
            const first = fontFamily.split(',')[0].trim();
            parts.push(`font-family:${first}`);
        }
        if (color)   parts.push(`color:${color}`);
        if (fontWeight && fontWeight !== 'normal' && fontWeight !== '400')
            parts.push(`font-weight:${fontWeight}`);
        if (fontStyle && fontStyle !== 'normal')
            parts.push(`font-style:${fontStyle}`);
        if (textDec && textDec !== 'none')
            parts.push(`text-decoration:${textDec}`);
        if (bgColor && bgColor !== 'transparent' && bgColor !== 'rgba(0, 0, 0, 0)')
            parts.push(`background-color:${bgColor}`);

        if (parts.length > 0) el.setAttribute('style', parts.join(';'));
    });

    // #350 — ה-HTML אינעם קאפיר ברעט (באזונדער פון ווארד) אנטהאלט נייע שורות און רווחים צווישן די טאגס; ביים אריינלייגן ווערן זיי
    // איבעריגע רווחים אינעם טעקסט. מען קוועטשט יעדן רצף פון רווחים/נייע שורות צו איין רווח
    // (אן אויסצומעקן אן אמתן רווח צווישן ווערטער).
    const walker = doc.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    for (const t of textNodes) {
        t.nodeValue = t.nodeValue.replace(/[ \t]*[\r\n]+[ \t]*/g, ' ');
    }

    return body.innerHTML.trim();
}

function setupWordPasteFix() {
    const processed = new WeakSet();

    function attachTo(host) {
        const sr = host.shadowRoot;
        if (!sr || processed.has(sr)) return;
        processed.add(sr);

        sr.addEventListener('paste', function (e) {
            const cd = e.clipboardData;
            if (!cd) return;
            const html = cd.getData('text/html');
            if (!html) return;  // ×˜×§×¡×˜ ×¨×’×™×œ ×‘×œ×‘×“ â€” Anki ×™×˜×¤×œ

            e.preventDefault();
            e.stopImmediatePropagation();

            const cleaned = cleanPastedHtml(html);
            document.execCommand('insertHTML', false, cleaned);
        }, true);  // capture phase â€” ×œ×¤× ×™ ×”×¤×™×œ×˜×¨ ×©×œ Anki
    }

    function scan() {
        forEachRichText(attachTo);
    }

    registerEditorMutationScan(scan);
}

setupWordPasteFix();

// =========================================================
// ×¢×™×¦×•×‘ ×¨×ž×– ×‘×¢×•×¨×š â€” CSS ×‘-shadow root + ×›×¤×ª×•×¨ ×‘×™×˜×•×œ ×‘×¨×™×—×•×£
// =========================================================
var _HINT_CSS = [
    'span.haf-hint {',
    '    color: #0070c9 !important;',
    '    background-color: rgba(0,112,201,0.08) !important;',
    '    border-bottom: 2px dashed #0070c9 !important;',
    '    cursor: default;',
    '    unicode-bidi: isolate;',
    '}',
].join('\n');

function injectHintStyles(sr) {
    if (!sr || sr.querySelector('#haf-hint-style')) return;
    var style = document.createElement('style');
    style.id = 'haf-hint-style';
    style.textContent = _HINT_CSS;
    sr.appendChild(style);
}

function setupHintHover(sr) {
    if (!sr || sr.__hintHoverDone) return;
    sr.__hintHoverDone = true;

    sr.addEventListener('mouseover', function(e) {
        var hint = e.target.closest ? e.target.closest('span.haf-hint') : null;
        if (!hint || hint.querySelector('.haf-hint-remove')) return;

        var btn = document.createElement('span');
        btn.className = 'haf-hint-remove';
        btn.textContent = '\u2715';
        btn.title = '\u05de\u05d1\u05d8\u05dc \u05d0\u05ea \u05d4\u05e8\u05de\u05d6 \u2014 \u05d4\u05d8\u05e7\u05e1\u05d8 \u05e0\u05e9\u05d0\u05e8';
        btn.setAttribute('contenteditable', 'false');
        // #16 — unicode-bidi:isolate האלט דעם אלגאריטם BiDi פון צו רוקן דעם-X ווען דער רמז אנטהאלט נומערן/ענגליש
        btn.style.cssText = (
            'display:inline-block;margin:0 2px;background:#e05252;color:white !important;' +
            'font-size:9px;padding:0 3px;border-radius:3px;cursor:pointer;' +
            'font-family:sans-serif;line-height:1.4;vertical-align:middle;' +
            'border-bottom:none !important;unicode-bidi:isolate;'
        );

        btn.addEventListener('mousedown', function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var parent = hint.parentNode;
            if (!parent) return;
            Array.from(hint.childNodes).forEach(function(child) {
                if (child !== btn) {
                    parent.insertBefore(child, hint);
                }
            });
            parent.removeChild(hint);
        });

        hint.appendChild(btn);
    });

    sr.addEventListener('mouseout', function(e) {
        var hint = e.target.closest ? e.target.closest('span.haf-hint') : null;
        if (!hint) return;
        var related = e.relatedTarget;
        if (related && hint.contains(related)) return;
        var btnEl = hint.querySelector('.haf-hint-remove');
        if (btnEl) btnEl.remove();
    });
}

function setupEditorHints() {
    forEachRichText(function(sel) {
        var sr = sel.shadowRoot;
        if (!sr) return;
        injectHintStyles(sr);
        setupHintHover(sr);
    });
}

registerEditorMutationScan(setupEditorHints);

// ××™×§×•×Ÿ SVG ×œ×›×¤×ª×•×¨ ×”×¨×ž×– ×‘×¡×¨×’×œ ×”×¢×•×¨×š
function setupHintButtonIcon() {
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C5 20 1 12 1 12a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9 9 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>' +
        '<line x1="1" y1="1" x2="23" y2="23"/>' +
        '</svg>';
    var attempts = 0;
    var id = setInterval(function() {
        var btn = document.getElementById('hint_btn');
        if (btn) {
            btn.innerHTML = svg;
            btn.style.setProperty('display', 'flex', 'important');
            btn.style.setProperty('align-items', 'center', 'important');
            btn.style.setProperty('justify-content', 'center', 'important');
            clearInterval(id);
        }
        if (++attempts >= 50) clearInterval(id);
    }, 200);
}
setupHintButtonIcon();


// =========================================================
// ×›×¤×ª×•×¨ ×¨×ž×– â€” ×¢×•×˜×£ ×˜×§×¡×˜ ×ž×¡×•×ž×Ÿ ×‘-<span class="haf-hint">
// =========================================================
function applyHint() {
    var applied = false;
    var root = document.querySelectorAll(".rich-text-editable");
    root.forEach(function(sel) {
        var sr = sel.shadowRoot;
        if (!sr) return;
        var selection = sr.getSelection();
        if (!selection || selection.rangeCount === 0) return;
        var range = selection.getRangeAt(0);
        if (range.collapsed) return;

        var content = range.cloneContents();
        var span = document.createElement("span");
        span.className = "haf-hint";
        span.appendChild(content);
        document.execCommand("insertHTML", false, span.outerHTML);
        applied = true;
    });
    if (!applied) {
        alert("קיין טעקסט איז נישט אויסגעקליבן געווארן!");
    }
}

function normalizePresetSize(size) {
    const raw = String(size || "").trim();
    if (!raw) return "";
    const match = raw.match(/^([\d.]+)\s*(px|pt)?$/i);
    if (match) return match[1] + "pt";
    return raw;
}
