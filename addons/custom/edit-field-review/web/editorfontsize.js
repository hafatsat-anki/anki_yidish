/**
 * פונקציה ראשית לשינוי סגנון (גודל/גופן).
 * מחליפה את הלוגיקה הישנה בשימוש ב-execCommand לתמיכה ב-Ctrl+Z
 * ובניקוי סלקטיבי של סגנונות.
 */
function fontsi(selection, style, arg) {
  if (!selection || selection.rangeCount === 0) return;

  // טיפול ביחידות מידה עבור גודל גופן
  if (style === "font-size" && arg !== "unset" && arg !== "'unset'") {
    // המרת המספר למחרוזת ובדיקה אם צריך להוסיף pt
    var argStr = String(arg);
    if (argStr.indexOf("pt") === -1 && argStr.indexOf("px") === -1) {
      arg += "pt";
    }
  }

  var range = selection.getRangeAt(0);
  var shouldApply = arg !== "unset" && arg !== "'unset'" && arg !== "'none'";

  // #140 — כמו במנוע font-size של העורך: סמן ריק נשמר כ-style pending ומוחל על התו הראשון שיוקלד.
  if (range.collapsed) {
    if (!shouldApply) return;
    insertLiveStyleSpan(selection, range, style, arg);
    return;
  }

  // #140 — לא משתמשים ב-insertHTML לבחירה רגילה: הוא משחזר רק את הפרגמנט ועלול למחוק עיצוב שנמצא בהורים.
  if (shouldApply) {
    var applied = applyStyleToRangeText(selection, range, style, arg);
    if (applied) return;
  }

  // 1. שכפול התוכן (במקום גזירה) כדי לאפשר ל-execCommand לנהל את ההחלפה וה-Undo
  var contentFragment = range.cloneContents();

  // 2. ניקוי חכם: מעבר על כל האלמנטים בתוך הבחירה והסרת הסגנון *הספציפי* שאנו משנים כרגע.
  var allElements = contentFragment.querySelectorAll("*");
  allElements.forEach(function (el) {
    if (el.style) {
      // הסרת הסגנון הספציפי מהצאצאים כדי שהסגנון החדש (שיעטוף אותם) יקבע
      el.style.removeProperty(style);

      // ניקוי שאריות של תגיות style ריקות
      if (el.getAttribute("style") === "" || el.style.length === 0) {
        el.removeAttribute("style");
      }
    }
  });

  // #140 — fallback נדיר בלבד: בחירה שלא ניתן לטפל בה כטקסטים בודדים.

  // 3. יצירת המעטפת החדשה (Span)
  var span = document.createElement("span");
  span.appendChild(contentFragment); // הכנסת התוכן המנוקה

  // החלת הסגנון החדש על המעטפת (אלא אם כן הפקודה היא "unset")
  if (arg !== "unset" && arg !== "'unset'" && arg !== "'none'") {
    span.style.setProperty(style, arg, "important");
  }

  // 4. ביצוע השינוי בפועל באמצעות מנוע הדפדפן
  // פעולה זו נרשמת בהיסטוריה ומאפשרת ביטול (Undo) תקין בלחיצה אחת
  if (style === "font-size" && (arg === "unset" || arg === "'unset'")) {
    // אם הפקודה היא איפוס גודל, נשתמש ב-removeFormat או פשוט נכניס את ה-HTML הנקי
    document.execCommand("insertHTML", false, span.innerHTML);
  } else {
    document.execCommand("insertHTML", false, span.outerHTML);
  }
}

// פונקציה זו נקראת על ידי הקוד בפייתון (editbar.py -> ExtraEditorCommands -> set_style)
function setstyle(style, arg) {
  fontsi(document.getSelection(), style, arg);
}

// #140 — פונקציות עזר שהותאמו ממנוע font-size כדי להחיל סגנון בלי להרוס בלוקים ורשימות.
var EFDRC_STYLE_BLOCK_TAGS = new Set([
  "LI", "P", "DIV", "UL", "OL", "H1", "H2", "H3", "H4", "H5", "H6",
  "BLOCKQUOTE", "PRE", "TR", "TD", "TH", "TABLE", "TBODY", "THEAD"
]);

function ensurePendingStyleHandler(root) {
  if (!root || root._efdrPendingStyleHandlerAttached) return;
  root._efdrPendingStyleHandlerAttached = true;
  root.addEventListener("beforeinput", function (event) {
    var entries = root._efdrPendingStyleEntries;
    if (!entries || event.inputType !== "insertText" || !event.data || event.isComposing) return;
    var selection = document.getSelection();
    if (!selection || selection.rangeCount === 0) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    var range = selection.getRangeAt(0);
    range.deleteContents();
    var span = document.createElement("span");
    entries.forEach(function (entry) {
      span.style.setProperty(entry[0], entry[1], "important");
    });
    span.textContent = event.data;
    range.insertNode(span);
    var textNode = span.firstChild;
    var caretRange = document.createRange();
    caretRange.setStart(textNode, textNode.textContent.length);
    caretRange.collapse(true);
    selection.removeAllRanges();
    selection.addRange(caretRange);
    root._efdrPendingStyleEntries = null;
  }, true);
}

function insertLiveStyleSpan(selection, range, style, arg) {
  return insertLiveStyleEntries(selection, range, [[style, arg]]);
}

function insertLiveStyleEntries(selection, range, styleEntries) {
  var root = range.startContainer && range.startContainer.getRootNode
    ? range.startContainer.getRootNode()
    : document;
  root._efdrPendingStyleEntries = styleEntries;
  ensurePendingStyleHandler(root);
}

function normalizePresetSize(size) {
  var raw = String(size || "").trim();
  if (!raw) return "";
  var match = raw.match(/^([\d.]+)\s*(px|pt)?$/i);
  if (match) return match[1] + "pt";
  return raw;
}

function applyReviewStylePreset(preset) {
  var selection = document.getSelection();
  if (!selection || selection.rangeCount === 0) return;

  var size = normalizePresetSize(preset.size);
  var entries = [];
  if (preset.font) entries.push(["font-family", preset.font]);
  if (size) entries.push(["font-size", size]);
  if (preset.color) entries.push(["color", preset.color]);
  if (preset.bold) entries.push(["font-weight", "bold"]);
  if (preset.italic) entries.push(["font-style", "italic"]);
  if (preset.underline) entries.push(["text-decoration", "underline"]);
  if (preset.bgColor) entries.push(["background-color", preset.bgColor]);
  if (preset.superscript) entries.push(["vertical-align", "super"]);
  else if (preset.subscript) entries.push(["vertical-align", "sub"]);
  if (!entries.length) return;

  var range = selection.getRangeAt(0);
  if (range.collapsed) {
    insertLiveStyleEntries(selection, range, entries);
    return;
  }
  if (applyStylesToRangeText(selection, range, entries)) return;

  var content = range.cloneContents();
  clearStylesFromFragment(content, entries);
  var span = document.createElement("span");
  entries.forEach(function (entry) {
    span.style.setProperty(entry[0], entry[1], "important");
  });
  span.appendChild(content);
  document.execCommand("insertHTML", false, span.outerHTML);
}

function clearStylesFromFragment(fragment, styleEntries) {
  if (!fragment || !fragment.querySelectorAll) return;
  var properties = styleEntries.map(function (entry) { return entry[0]; });
  fragment.querySelectorAll("*").forEach(function (el) {
    if (!el.style) return;
    properties.forEach(function (prop) {
      el.style.removeProperty(prop);
      if (prop === "text-decoration") {
        el.style.removeProperty("text-decoration-line");
        el.style.removeProperty("text-decoration-style");
        el.style.removeProperty("text-decoration-color");
      }
    });
    if (el.getAttribute("style") === "" || el.style.length === 0) el.removeAttribute("style");
  });
}

function applyStylesToRangeText(selection, range, styleEntries) {
  // #161 — preserve the moving end across preset formatting and DOM changes.
  var backward = window.HafRtlEditing.isBackward(selection);
  var common = range.commonAncestorContainer;
  var root = common.nodeType === Node.TEXT_NODE ? common.parentNode : common;
  if (!root) return false;

  var walker = (root.ownerDocument || document).createTreeWalker(root, NodeFilter.SHOW_TEXT);
  var textNodes = [];
  var node;
  while ((node = walker.nextNode())) {
    if (!node.nodeValue || !range.intersectsNode(node)) continue;
    textNodes.push(node);
  }
  if (!textNodes.length) return false;

  // #312 — שומרים גם firstInserted כדי לשחזר בחירה מלאה ולא רק סמן
  var lastInserted = null;
  var firstInserted = null;
  for (var i = textNodes.length - 1; i >= 0; i--) {
    var textNode = textNodes[i];
    if (!textNode.parentNode) continue;

    var segment = document.createRange();
    segment.selectNodeContents(textNode);
    if (range.compareBoundaryPoints(Range.START_TO_START, segment) > 0) {
      segment.setStart(range.startContainer, range.startOffset);
    }
    if (range.compareBoundaryPoints(Range.END_TO_END, segment) < 0) {
      segment.setEnd(range.endContainer, range.endOffset);
    }
    if (segment.collapsed) continue;

    var extracted = segment.extractContents();
    if (!extracted || extracted.childNodes.length === 0) continue;
    clearStylesFromFragment(extracted, styleEntries);

    var span = document.createElement("span");
    styleEntries.forEach(function (entry) {
      span.style.setProperty(entry[0], entry[1], "important");
    });
    span.appendChild(extracted);
    segment.insertNode(span);
    if (!lastInserted) lastInserted = span;
    firstInserted = span;
  }

  // #312 — שחזור בחירה מלאה במקום סמן בלבד
  if (firstInserted && firstInserted.parentNode) {
    var newRange = document.createRange();
    newRange.setStartBefore(firstInserted);
    newRange.setEndAfter(lastInserted);
    window.HafRtlEditing.restoreRange(selection, newRange, backward);
  }
  return true;
}

function fragmentHasBlock(fragment) {
  if (!fragment || !fragment.querySelectorAll) return false;
  var descendants = Array.from(fragment.querySelectorAll("*"));
  var children = Array.from(fragment.childNodes || []);
  return descendants.concat(children).some(function (node) {
    return node.nodeType === 1 && EFDRC_STYLE_BLOCK_TAGS.has(node.tagName);
  });
}

function applyStyleToRangeText(selection, range, style, arg) {
  // #161 — preserve the moving end across font/size changes, including lists.
  var backward = window.HafRtlEditing.isBackward(selection);
  var common = range.commonAncestorContainer;
  var root = common.nodeType === Node.TEXT_NODE ? common.parentNode : common;
  if (!root) return false;

  var walker = (root.ownerDocument || document).createTreeWalker(root, NodeFilter.SHOW_TEXT);
  var textNodes = [];
  var node;
  while ((node = walker.nextNode())) {
    if (!node.nodeValue || !range.intersectsNode(node)) continue;
    textNodes.push(node);
  }
  if (!textNodes.length) return false;

  // #312 — שומרים גם firstInserted כדי לשחזר בחירה מלאה ולא רק סמן
  var lastInserted = null;
  var firstInserted = null;
  for (var i = textNodes.length - 1; i >= 0; i--) {
    var textNode = textNodes[i];
    if (!textNode.parentNode) continue;

    var segment = document.createRange();
    segment.selectNodeContents(textNode);
    if (range.compareBoundaryPoints(Range.START_TO_START, segment) > 0) {
      segment.setStart(range.startContainer, range.startOffset);
    }
    if (range.compareBoundaryPoints(Range.END_TO_END, segment) < 0) {
      segment.setEnd(range.endContainer, range.endOffset);
    }
    if (segment.collapsed) continue;

    var extracted = segment.extractContents();
    if (!extracted || extracted.childNodes.length === 0) continue;
    Array.from(extracted.querySelectorAll ? extracted.querySelectorAll("*") : []).forEach(function (el) {
      if (!el.style) return;
      el.style.removeProperty(style);
      if (el.getAttribute("style") === "" || el.style.length === 0) el.removeAttribute("style");
    });

    var span = document.createElement("span");
    span.style.setProperty(style, arg, "important");
    span.appendChild(extracted);
    segment.insertNode(span);
    if (!lastInserted) lastInserted = span;
    firstInserted = span;
  }

  // #312 — שחזור בחירה מלאה במקום סמן בלבד
  if (firstInserted && firstInserted.parentNode) {
    var newRange = document.createRange();
    newRange.setStartBefore(firstInserted);
    newRange.setEndAfter(lastInserted);
    window.HafRtlEditing.restoreRange(selection, newRange, backward);
  }
  return true;
}
