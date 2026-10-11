(function () {
  window.EFDRC = {};
  const EFDRC = window.EFDRC;
  EFDRC.shortcuts = [];

  // --- ניהול מצב ---
  EFDRC.modalActive = false;
  EFDRC.blurTimer = null;
  EFDRC.savedSelectionState = null;
  // #178 — שומרים reference לשדה האחרון שנערך, כי בזמן סגירת חלון document.activeElement כבר עשוי להיות body.
  EFDRC.activeEditableField = null;
  // #178 — snapshot טקסטואלי נשמר בנפרד מה-DOM, למקרה שהשדה כבר התנתק בזמן beforeunload/pagehide.
  EFDRC.activeEditableSnapshot = null;
  // #178 — שמירה אוטומטית קצרה אחרי סיום הקלדה מונעת אובדן תוכן גם לפני blur או סגירת חלון.
  EFDRC.autoSaveTimers = new WeakMap();
  EFDRC.lastAutoSavedHtml = new WeakMap();
  // #178 — delay קצר יותר שומר מיד אחרי שההקלדה נרגעת, לפני שהמשתמש מספיק לעזוב את השדה.
  EFDRC.autoSaveDelay = 250;

  // --- פונקציות עזר לניווט ב-DOM ---

  function getDomPath(root, node) {
    const path = [];
    let current = node;
    while (current !== root) {
      if (!current.parentNode) return null;
      const index = Array.prototype.indexOf.call(
        current.parentNode.childNodes,
        current
      );
      path.unshift(index);
      current = current.parentNode;
    }
    return path;
  }

  function getNodeFromPath(root, path) {
    let current = root;
    for (const index of path) {
      if (!current || !current.childNodes || !current.childNodes[index])
        return null;
      current = current.childNodes[index];
    }
    return current;
  }

  // לכידת מצב הבחירה
  function captureSelection() {
    const sel = window.getSelection();
    if (sel.rangeCount === 0) return null;

    let range = sel.getRangeAt(0);
    let container = range.commonAncestorContainer;

    if (container.nodeType === 3) container = container.parentElement;
    const fieldEl = container.closest("[data-EFDRCfield]");

    if (!fieldEl) return null;

    // **תיקון קריטי**: איחוד שברי טקסט לפני חישוב הנתיב
    // זה מונע את הבעיה שהבחירה קופצת לאות סמוכה או מתרחבת
    fieldEl.normalize();

    // עדכון ה-Range למקרה ש-normalize שינה משהו (הדפדפן בדרך כלל מעדכן לבד, אבל ליתר ביטחון)
    if (sel.rangeCount > 0) range = sel.getRangeAt(0);

    return {
      fieldId: fieldEl.getAttribute("data-EFDRCfield"),
      startPath: getDomPath(fieldEl, range.startContainer),
      startOffset: range.startOffset,
      endPath: getDomPath(fieldEl, range.endContainer),
      endOffset: range.endOffset,
      // #161 — start/end alone lose the active end of a backward selection.
      backward: window.HafRtlEditing.isBackward(sel),
    };
  }

  // שחזור הבחירה
  function restoreSelection(state) {
    if (!state) return null;

    const fieldEl = document.querySelector(
      `[data-EFDRCfield='${state.fieldId}']`
    );
    if (!fieldEl) return null;

    fieldEl.setAttribute("contenteditable", "true");
    fieldEl.focus();

    // גם כאן מאחדים כדי לוודא שהמבנה תואם למה שנשמר
    fieldEl.normalize();

    const startNode = getNodeFromPath(fieldEl, state.startPath);
    const endNode = getNodeFromPath(fieldEl, state.endPath);

    if (startNode && endNode) {
      try {
        const range = document.createRange();

        // **הגנה**: וידוא שהאופסט לא חורג מאורך הטקסט
        const safeStartOffset =
          startNode.nodeType === 3
            ? Math.min(state.startOffset, startNode.length)
            : state.startOffset;

        const safeEndOffset =
          endNode.nodeType === 3
            ? Math.min(state.endOffset, endNode.length)
            : state.endOffset;

        range.setStart(startNode, safeStartOffset);
        range.setEnd(endNode, safeEndOffset);

        const sel = window.getSelection();
        // #161 — preserve anchor/focus through modal close and card reload.
        window.HafRtlEditing.restoreRange(sel, range, state.backward);
        return fieldEl;
      } catch (e) {
        console.error("EFDRC: Failed to restore range", e);
      }
    }
    return fieldEl;
  }

  // --- לוגיקה ראשית ---

  EFDRC.rememberEditableField = function (el) {
    // #178 — בכל שינוי/פוקוס נשמרים nid+field+html כדי ששמירה סופית לא תהיה תלויה ב-activeElement.
    if (!el || !el.hasAttribute || !el.hasAttribute("data-EFDRCfield")) return null;
    EFDRC.activeEditableField = el;
    const snapshot = {
      nid: el.getAttribute("data-EFDRCnid"),
      field: el.getAttribute("data-EFDRCfield"),
      html: el.innerHTML,
    };
    EFDRC.activeEditableSnapshot = snapshot;
    return snapshot;
  };

  EFDRC.saveAndReload = function (el, keepSelection) {
    if (EFDRC.CONF.remove_span) removeSpan(el);

    // ניקוי המצב השמור אלא אם כן נתבקשנו לשמור אותו (לרצף פעולות)
    if (!keepSelection) {
      EFDRC.savedSelectionState = null;
    }

    if (el.hasAttribute("data-EFDRCnid")) {
      EFDRC.cleanResize(el);
      // #161 — formatting changed the DOM; old modal paths cannot be reused
      // when the saved field is rendered again after the bridge round trip.
      if (keepSelection) EFDRC.savedSelectionState = captureSelection();
      const snapshot = EFDRC.rememberEditableField(el);
      EFDRC.lastAutoSavedHtml.set(el, el.innerHTML);
      // #178 — שמירה סופית נשלחת ב-base64 כדי שגם HTML עם #/עברית/שורות יישמר במסלול אמין לפי nid.
      window.pycmd(
        "EFDRC!savefinal64#" +
          snapshot.nid +
          "#" +
          snapshot.field +
          "#" +
          b64EncodeUnicode(snapshot.html)
      );
    }
  };

  // #178 — autosave שומר את השדה ברקע בלי לרענן את ה-Reviewer ובלי להוציא את המשתמש מעריכת הטקסט.
  EFDRC.saveWithoutReload = function (el) {
    if (!el || !el.hasAttribute || !el.hasAttribute("data-EFDRCnid")) return false;
    EFDRC.rememberEditableField(el);
    const currentHtml = el.innerHTML;
    if (EFDRC.lastAutoSavedHtml.get(el) === currentHtml) return false;
    EFDRC.lastAutoSavedHtml.set(el, currentHtml);
    window.pycmd(
      "EFDRC!save64#" +
        el.getAttribute("data-EFDRCnid") +
        "#" +
        el.getAttribute("data-EFDRCfield") +
        "#" +
        b64EncodeUnicode(currentHtml)
    );
    return true;
  };

  // #178 — מאתחלים debounce לכל שדה כדי לשמור אחרי שההקלדה נרגעת, לפני שהמשתמש עוזב את העריכה.
  EFDRC.scheduleAutoSave = function (el) {
    if (!el || !el.matches || !el.matches("[data-EFDRCfield]")) return;
    const oldTimer = EFDRC.autoSaveTimers.get(el);
    if (oldTimer) clearTimeout(oldTimer);
    const timer = setTimeout(() => {
      EFDRC.autoSaveTimers.delete(el);
      if (!EFDRC.modalActive && el.isConnected) EFDRC.saveWithoutReload(el);
    }, EFDRC.autoSaveDelay);
    EFDRC.autoSaveTimers.set(el, timer);
  };

  // נקרא מפייתון *לפני* פתיחת החלון
  EFDRC.prepareForModal = function () {
    EFDRC.modalActive = true;
    if (EFDRC.blurTimer) clearTimeout(EFDRC.blurTimer);

    // שמירה של המצב הנוכחי
    const state = captureSelection();
    if (state) {
      EFDRC.savedSelectionState = state;
    }
  };

  // נקרא מפייתון *אחרי* סגירת החלון
  EFDRC.finishModal = function (cmd, val) {
    // 1. שחזור
    const el = restoreSelection(EFDRC.savedSelectionState);

    // 2. ביצוע
    if (el && cmd && val) {
      const sel = window.getSelection();
      // מוודאים שיש בחירה ושהיא לא "ממוטטת" (סמן מהבהב ללא טקסט)
      if (sel.rangeCount > 0 && !sel.isCollapsed) {
        document.execCommand(cmd, false, val);
        // #161 — retain the original active end even if execCommand resets it.
        if (sel.rangeCount) window.HafRtlEditing.restoreRange(
          sel, sel.getRangeAt(0), EFDRC.savedSelectionState.backward
        );
        // שמירה ורענון, עם בקשה לשמור את המיקום לרענון הבא
        EFDRC.saveAndReload(el, true);
      } else {
        EFDRC.saveAndReload(el, false);
      }
    } else if (el) {
      // ביטול
      el.focus();
    }

    setTimeout(() => {
      EFDRC.modalActive = false;
    }, 300);
  };

  // נקרא בכל טעינת כרטיס
  EFDRC.serveCard = function () {
    const els = document.querySelectorAll("[data-EFDRCfield]");
    for (const el of els) {
      if (EFDRC.CONF.ctrl_click) {
        const fldName = b64DecodeUnicode(el.getAttribute("data-EFDRCfield"));
        el.setAttribute("data-placeholder", fldName);
      } else {
        el.setAttribute("contenteditable", "true");
      }
      for (const handlerInfo of handlers) {
        el.setAttribute(handlerInfo[0], `EFDRC.${handlerInfo[1]}(event, this)`);
      }
    }

    // שחזור מצב אם קיים
    if (EFDRC.savedSelectionState) {
      restoreSelection(EFDRC.savedSelectionState);
      EFDRC.savedSelectionState = null;
    }
  };

  // --- אירועים ---

  EFDRC.handleFocus = function (event, target) {
    if (EFDRC.blurTimer) clearTimeout(EFDRC.blurTimer);
    // #178 — focus הוא הרגע האמין ביותר לזכור איזה שדה צריך להישמר אם החלון ייסגר בלי blur רגיל.
    EFDRC.rememberEditableField(target);

    if (
      typeof window.showTooltip === "function" &&
      typeof window.showTooltip2 === "undefined"
    ) {
      window.showTooltip2 = window.showTooltip;
      window.showTooltip = function (event, tooltip, element) {
        EFDRC.tooltip = { ev: event, tt: tooltip, el: element };
      };
      window.showTooltip.hide = function () {};
      window.invokeTooltipAtSelectedElm2 = window.invokeTooltipAtSelectedElm;
      window.invokeTooltipAtSelectedElm = function () {
        window.invokeTooltipAtSelectedElm2();
        window.showTooltip2(
          EFDRC.tooltip.ev,
          EFDRC.tooltip.tt,
          EFDRC.tooltip.el
        );
      };
    }
    const fld = target.getAttribute("data-EFDRCfield");
    window.pycmd("EFDRC!focuson#" + fld);
  };

  EFDRC.handleBlur = function (event, target) {
    EFDRC.blurTimer = setTimeout(() => {
      if (!EFDRC.modalActive) {
        if (typeof showTooltip2 === "function") {
          window.showTooltip = window.showTooltip2;
          delete window.showTooltip2;
          window.invokeTooltipAtSelectedElm =
            window.invokeTooltipAtSelectedElm2;
          delete window.invokeTooltipAtSelectedElm2;
        }

        const el = target;
        EFDRC.flushEditableField(el, false);
        window.pycmd("EFDRC!reload");
      }
    }, 150);
  };

  EFDRC.flushEditableField = function (el, keepSelection) {
    if (!el || !el.matches || !el.matches("[data-EFDRCfield]")) {
      return EFDRC.saveSnapshotAndReload(EFDRC.activeEditableSnapshot);
    }
    if (!el.isConnected) return EFDRC.saveSnapshotAndReload(EFDRC.activeEditableSnapshot);
    // #178 — שומרים גם כאשר הפוקוס עוזב את ה-WebView/חלון Anki לפני שאירוע blur רגיל מספיק להסתיים.
    if (EFDRC.blurTimer) clearTimeout(EFDRC.blurTimer);
    // #178 — flush סופי מבטל autosave ממתין כדי שלא יישלח save רקע אחרי ריענון הכרטיס.
    const pendingAutoSave = EFDRC.autoSaveTimers.get(el);
    if (pendingAutoSave) clearTimeout(pendingAutoSave);
    EFDRC.autoSaveTimers.delete(el);
    if (EFDRC.modalActive) return false;
    el.setAttribute("contenteditable", "false");
    EFDRC.saveAndReload(el, keepSelection);
    if (EFDRC.activeEditableField === el) EFDRC.activeEditableField = null;
    return true;
  };

  const flushActiveEditableField = function () {
    // #178 — fallback לשדה האחרון שנערך מונע איבוד מידע כש-activeElement כבר לא מצביע על השדה.
    const active = document.activeElement;
    const el = active && active.matches && active.matches("[data-EFDRCfield]")
      ? active
      : EFDRC.activeEditableField;
    if (EFDRC.flushEditableField(el, false)) {
      EFDRC.activeEditableSnapshot = null;
      window.pycmd("EFDRC!reload");
    }
  };

  // --- שאר הקוד הסטנדרטי ---
  const removeSpan = function (el) {
    const elems = el.getElementsByTagName("span");
    for (let x = 0; x < elems.length; x++) {
      const span = elems[x];
      const children = span.childNodes;
      for (let y = 0; y < children.length; y++) {
        span.parentNode.insertBefore(children[y], span.nextSibling);
      }
      span.parentNode.removeChild(span);
    }
  };

  const wrapCloze = function (event, el, altKey) {
    let highest = 0;
    const val = el.innerHTML;
    let m;
    const myRe = /\{\{c(\d+)::/g;
    while ((m = myRe.exec(val)) !== null) {
      highest = Math.max(highest, m[1]);
    }
    if (!altKey) {
      highest += 1;
    }
    highest = Math.max(1, highest);
    EFDRC.wrapInternal(el, "{{c" + highest + "::", "}}", false);
    event.preventDefault();
  };

  const ctrlLinkEnable = function () {
    const links = document.querySelectorAll("[data-EFDRCfield] a");
    for (const el of links) {
      el.setAttribute("contenteditable", "false");
    }
  };

  const ctrlLinkDisable = function () {
    const links = document.querySelectorAll(
      "[data-EFDRCfield] a[contenteditable='false']"
    );
    for (const el of links) {
      el.removeAttribute("contenteditable");
    }
  };

  const b64DecodeUnicode = function (str) {
    return decodeURIComponent(
      window
        .atob(str)
        .split("")
        .map(function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
  };

  // #178 — autosave שולח HTML ב-base64 כדי שתווי #/שורות/עברית לא ישברו הודעת pycmd.
  const b64EncodeUnicode = function (str) {
    return window.btoa(
      encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function (_match, hex) {
        return String.fromCharCode("0x" + hex);
      })
    );
  };

  EFDRC.saveSnapshotAndReload = function (snapshot) {
    // #178 — fallback לסגירת חלון: אם ה-DOM כבר לא זמין, שומרים את ה-snapshot האחרון לפי nid ושדה.
    if (!snapshot || !snapshot.nid || !snapshot.field) return false;
    window.pycmd(
      "EFDRC!savefinal64#" +
        snapshot.nid +
        "#" +
        snapshot.field +
        "#" +
        b64EncodeUnicode(snapshot.html || "")
    );
    return true;
  };

  EFDRC.handlePaste = function (e) {
    if (!EFDRC.CONF.process_paste) return;
    const paste = e.clipboardData || window.clipboardData;
    if (
      paste.types.length === 0 ||
      (paste.types.length === 1 && paste.types[0] === "text/plain")
    )
      return;
    e.preventDefault();
    window.pycmd("EFDRC!paste");
  };

  const editableTargetForShortcut = function (event) {
    // #138 — קיצורי Ctrl+B/Ctrl+I לפעמים מגיעים ל-window ולא ל-onkeydown שעל השדה, לכן מאתרים את השדה הפעיל גם מה-selection.
    const eventTarget = event.target && event.target.closest
      ? event.target.closest("[data-EFDRCfield]")
      : null;
    if (eventTarget) return eventTarget;
    const active = document.activeElement;
    if (active && active.closest) {
      const activeTarget = active.closest("[data-EFDRCfield]");
      if (activeTarget) return activeTarget;
    }
    const selection = window.getSelection && window.getSelection();
    const node = selection && selection.anchorNode;
    const element = node && (node.nodeType === Node.TEXT_NODE ? node.parentElement : node);
    return element && element.closest ? element.closest("[data-EFDRCfield]") : null;
  };

  const handleRegisteredShortcut = function (ev, target) {
    // #138 — מאזין capture ומאזין inline יכולים לראות את אותו אירוע; דגל זה מונע הפעלה כפולה של bold/italic.
    if (ev.EFDRCShortcutHandled) return true;
    for (const scutInfo of EFDRC.shortcuts) {
      if (!matchShortcut(ev, scutInfo)) continue;
      const handled = scutInfo.handler(ev, target);
      if (handled !== -1) {
        // #138 — WebEngine may continue the same key event into contenteditable
        // after applying an Alt/Ctrl style. Stop it before the shortcut letter is inserted.
        ev.preventDefault();
        ev.stopImmediatePropagation();
        // #178 — קיצורי עיצוב/קלוז לא תמיד מפעילים input, לכן שומרים גם אחרי handler של קיצור.
        EFDRC.scheduleAutoSave(target);
        ev.EFDRCShortcutHandled = true;
      }
      return handled !== -1;
    }
    return false;
  };

  EFDRC.handleKeydown = function (ev, target) {
    // #178 — כל הקלדה מעדכנת את השדה הפעיל למקרה שהחלון ייסגר לפני blur.
    EFDRC.rememberEditableField(target);
    handleRegisteredShortcut(ev, target);
    if (isCtrlKey(ev.code)) EFDRC.ctrldown();
    // #161 — modified arrows are handled once by the shared capture listener.
    ev.stopPropagation();
  };

  EFDRC.handleKeyUp = (ev, target) => {
    if (isCtrlKey(ev.code)) EFDRC.ctrlup();
    // #178 — keyup משלים את input עבור דפדפני WebEngine שלא מדווחים כל שינוי contenteditable בצורה עקבית.
    EFDRC.rememberEditableField(target);
    EFDRC.scheduleAutoSave(target);
    ev.stopPropagation();
  };
  EFDRC.handleInput = (ev, target) => {
    // #178 — input מכסה שינויי תוכן שאינם עוברים דרך keydown, כמו הדבקה או IME.
    EFDRC.rememberEditableField(target);
    EFDRC.scheduleAutoSave(target);
  };
  EFDRC.handleKeyPress = (ev, target) => {
    ev.stopPropagation();
  };

  const specialCharCodes = {
    "-": "minus",
    "=": "equal",
    "[": "bracketleft",
    "]": "bracketright",
    ";": "semicolon",
    "'": "quote",
    "`": "backquote",
    "\\": "backslash",
    ",": "comma",
    ".": "period",
    "/": "slash",
  };

  const registerShortcut = function (shortcut, handler) {
    // #138 — shortcut-manager יכול לשמור ערך ריק או <nop>; מדלגים עליו כדי שלא יישבר רישום שאר הקיצורים.
    if (typeof shortcut !== "string") return;
    shortcut = shortcut.trim();
    if (!shortcut || shortcut.toLowerCase() === "<nop>") return;
    const shortcutKeys = shortcut
      .toLowerCase()
      .split(/[+]/)
      .map((key) => key.trim());
    const modKeys = ["ctrl", "shift", "alt"];
    const scutInfo = {};
    modKeys.forEach((modKey) => {
      scutInfo[modKey] = shortcutKeys.includes(modKey) ||
        (modKey === "ctrl" && shortcutKeys.includes("control"));
    });
    let mainKey = shortcutKeys[shortcutKeys.length - 1];
    // Qt names '+' as Ctrl++; splitting otherwise leaves an empty key.
    if (!mainKey && shortcut.endsWith("+")) mainKey = "+";
    // #138 — שומרים גם את המקש כפי שנכתב, כדי שקיצורים כמו Ctrl+ת יעבדו לפי event.key ולא רק לפי event.code.
    const rawMainKey = mainKey;
    const hebrewKeys = {"א":"t", "ב":"c", "ג":"d", "ד":"s", "ה":"v",
      "ו":"u", "ז":"z", "ח":"j", "ט":"y", "י":"h", "כ":"f", "ל":"k",
      "מ":"n", "נ":"b", "ס":"x", "ע":"g", "פ":"p", "צ":"m",
      "ק":"e", "ר":"r", "ש":"a", "ת":",", "ך":"l", "ם":"o", "ן":"i", "ף":";", "ץ":"."};
    mainKey = hebrewKeys[mainKey] || mainKey;
    // #138 — legacy configs may still contain A/Shift+A. Such a value must
    // never turn ordinary typing into a formatting command inside the reviewer.
    const isLetter = rawMainKey.length === 1 && /[a-zA-Z\u0590-\u05ff]/.test(rawMainKey);
    if (isLetter && !scutInfo.ctrl && !scutInfo.alt) {
      console.warn("EFDRC: ignored unsafe letter shortcut", shortcut);
      return;
    }
    if (mainKey.length === 1) {
      if (/\d/.test(mainKey)) mainKey = "digit" + mainKey;
      else if (/[a-zA-Z]/.test(mainKey)) mainKey = "key" + mainKey;
      else {
        const code = specialCharCodes[mainKey];
        if (code) mainKey = code;
      }
    }
    scutInfo.key = mainKey;
    // #138 — rawKey מאפשר תמיכה בפריסת מקלדת עברית ובתווים שלא ממופים ל-code לטיני.
    scutInfo.rawKey = rawMainKey;
    scutInfo.handler = handler;
    EFDRC.shortcuts.push(scutInfo);
  };
  EFDRC.registerShortcut = registerShortcut;

  const matchShortcut = function (event, scutInfo) {
    if (scutInfo.ctrl !== (event.ctrlKey || event.metaKey)) return false;
    // #138 — אחרי חסימת אות/Shift+אות, התאמת Shift חייבת להיות מדויקת.
    if (scutInfo.shift !== event.shiftKey) return false;
    if (scutInfo.alt !== event.altKey) return false;
    // #138 — קודם מנסים code יציב לפריסות לטיניות, ואז key בפועל עבור מקשים עבריים כמו ת.
    const eventCode = (event.code || "").toLowerCase();
    const eventKey = (event.key || "").toLowerCase();
    return scutInfo.key === eventCode || (!!scutInfo.rawKey && scutInfo.rawKey === eventKey);
  };

  const registerFormattingShortcut = function () {
    for (const key in EFDRC.CONF.special_formatting) {
      const format = EFDRC.CONF.special_formatting[key];
      // #138 — shortcut-manager מציג גם פעולות עיצוב שהכפתור שלהן לא פעיל; אם יש להן קיצור ו-command הן צריכות לעבוד בעריכה במבחן.
      if (!format.command || !format.shortcut) continue;
      const shortcut = format.shortcut;
      registerShortcut(shortcut, (event, el) => {
        if (format.arg)
          document.execCommand(format.command, false, format.arg.value);
        else document.execCommand(format.command, false);
        // #178 — execCommand לא תמיד מפעיל input, לכן פעולות עיצוב מקבלות autosave מפורש.
        EFDRC.scheduleAutoSave(el);
      });
    }
    // #138 v2 — כשהמשתמש מגדיר קיצור אחר ל-bold/italic/underline, חוסמים את הקיצור
    // הדיפולטי של הדפדפן (Ctrl+B/I/U) כדי שלא יהיה כפילות. אם הקיצור הוגדר זהה
    // לדיפולט — לא רושמים בלוקר, כי הוא כבר רשום כקיצור אמיתי לעיל.
    const formattingDefaults = {
      bold: "Ctrl + B",
      italic: "Ctrl + I",
      underline: "Ctrl + U",
    };
    const normalize = (s) => (s || "").replace(/\s+/g, "").toLowerCase();
    for (const formatKey in formattingDefaults) {
      const formatConf = EFDRC.CONF.special_formatting[formatKey];
      const defaultShortcut = formattingDefaults[formatKey];
      if (!formatConf) continue;
      if (normalize(formatConf.shortcut) === normalize(defaultShortcut)) continue;
      // רושמים no-op handler שמונע את הפעולה הדיפולטית של הדפדפן.
      registerShortcut(defaultShortcut, () => {
        // חוסם בלבד; ה-handleRegisteredShortcut יבצע preventDefault.
      });
    }
  };

  const isCtrlKey = function (keycode) {
    // #161 — Ctrl-click editing must work with either Control/Meta key.
    return ["ControlLeft", "ControlRight", "MetaLeft", "MetaRight"].includes(keycode);
  };

  window.addEventListener("keydown", function (ev) {
    if (isCtrlKey(ev.code)) EFDRC.ctrldown();
    // #138 — capture listener מבטיח ש-Ctrl+B/Ctrl+I יפעלו גם כש-WebEngine לא מפעיל את ה-onkeydown שעל השדה עצמו.
    const target = editableTargetForShortcut(ev);
    if (target && handleRegisteredShortcut(ev, target)) ev.stopPropagation();
  }, true);
  window.addEventListener("keyup", function (ev) {
    if (isCtrlKey(ev.code)) EFDRC.ctrlup();
  });
  window.addEventListener("blur", flushActiveEditableField);
  window.addEventListener("beforeunload", flushActiveEditableField);
  window.addEventListener("pagehide", flushActiveEditableField);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") flushActiveEditableField();
  });

  // #161 — shared_libs/web/rtl_editing.js owns Shift/Ctrl navigation for BOTH
  // editor and reviewer, including dynamically replaced fields.

  EFDRC.registerConfig = function (confStr) {
    // #138 — config עשוי להגיע כמחרוזת JSON או כאובייקט JS בזמן live reload; שני המצבים צריכים לרשום קיצורים.
    EFDRC.CONF = typeof confStr === "string" ? JSON.parse(confStr) : confStr;
    EFDRC.CONF.span = EFDRC.CONF.tag === "span";
    EFDRC.resizeImageMode = EFDRC.CONF.resize_image_default_state;
  };

  EFDRC.setupReviewer = function () {
    // #138 — בכל טעינת קונפיג מחדש מנקים את הרשימה כדי שקיצורים ישנים לא יישארו פעילים לצד החדשים.
    EFDRC.shortcuts = [];
    // Explicit style bindings take priority over legacy inline cloze defaults.
    for (const [name, shortcut] of Object.entries(EFDRC.CONF.review_preset_shortcuts || {})) {
      registerShortcut(shortcut, () => window.pycmd("EFDRC!preset#" + name));
    }
    registerFormattingShortcut();
    registerShortcut(EFDRC.CONF.shortcuts["image-resize"], (event) => {
      EFDRC.resizeImageMode = !EFDRC.resizeImageMode;
      EFDRC.maybeResizeOrClean();
    });
    registerShortcut(EFDRC.CONF.shortcuts.cloze, (event, el) => {
      wrapCloze(event, el, false);
    });
    registerShortcut(EFDRC.CONF.shortcuts["cloze-alt"], (event, el) => {
      wrapCloze(event, el, true);
    });
    registerShortcut("Backspace", (event, el) => {
      // #141 — Backspace חייב להישאר פעולת דפדפן רגילה; במצב span מדלגים רק על ניקוי העטיפה.
      if (!EFDRC.CONF.span && EFDRC.CONF.remove_span) setTimeout(() => removeSpan(el), 0);
      return -1;
    });
    registerShortcut("Delete", (event, el) => {
      // #141 — Delete משתמש באותו נתיב כדי שלא יחסום מחיקה בזמן עריכה במבחן.
      if (!EFDRC.CONF.span && EFDRC.CONF.remove_span) setTimeout(() => removeSpan(el), 0);
      return -1;
    });
  };

  const handlers = [
    ["onpaste", "handlePaste"],
    ["onfocus", "handleFocus"],
    ["onblur", "handleBlur"],
    ["oninput", "handleInput"],
    ["onkeydown", "handleKeydown"],
    ["onkeyup", "handleKeyUp"],
    ["onkeypress", "handleKeyPress"],
  ];

  EFDRC.ctrldown = function () {
    if (EFDRC.CONF.ctrl_click) {
      const els = document.querySelectorAll("[data-EFDRCfield]");
      for (const el of els) el.setAttribute("contenteditable", "true");
    } else {
      ctrlLinkEnable();
    }
  };

  EFDRC.ctrlup = function () {
    if (EFDRC.CONF.ctrl_click) {
      const els = document.querySelectorAll("[data-EFDRCfield]");
      for (const el of els) {
        if (el !== document.activeElement)
          el.setAttribute("contenteditable", "false");
      }
    } else {
      ctrlLinkDisable();
    }
  };

  EFDRC.showRawField = function (encoded, nid, fld) {
    const val = b64DecodeUnicode(encoded);
    const elems = document.querySelectorAll(`[data-EFDRCfield='${fld}']`);
    for (let e = 0; e < elems.length; e++) {
      const elem = elems[e];
      if (elem.innerHTML !== val) elem.innerHTML = val;
      // #178 — אחרי טעינת הערך הגולמי זוכרים את מצב הבסיס כדי ש-autosave לא ישלח שמירה מיותרת מיד בפוקוס.
      EFDRC.lastAutoSavedHtml.set(elem, elem.innerHTML);
      elem.setAttribute("data-EFDRCnid", nid);
      if (document.activeElement === elem) EFDRC.rememberEditableField(elem);
    }
    EFDRC.maybeResizeOrClean(true);
  };

  // #357 — העתקה/גרירה של טקסט מהכרטיס (גם שלא במצב עריכה) גררה איתה את רקע הכרטיס,
  // כי Chromium מוסיף לפרגמנט שבלוח את הסגנונות המחושבים של האלמנטים העוטפים (רקע ה-.card
  // או תא הטבלה). במקום זה אנחנו מסדרים בעצמנו את ה-HTML של הבחירה בלבד (cloneContents):
  // עיצוב שהוחל על הטקסט עצמו (span עם צבע/רקע inline) נשמר, ורקע שמגיע מ-CSS של הכרטיס
  // לא נכלל, כי מחלקות הכרטיס לא קיימות אצל היעד.
  function selectionHTML() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return null;
    const container = document.createElement("div");
    for (let i = 0; i < sel.rangeCount; i++) {
      container.appendChild(sel.getRangeAt(i).cloneContents());
    }
    return { html: container.innerHTML, text: sel.toString() };
  }

  document.addEventListener("copy", function (e) {
    if (!e.clipboardData) return;
    const data = selectionHTML();
    if (!data) return;
    e.clipboardData.setData("text/html", data.html);
    e.clipboardData.setData("text/plain", data.text);
    e.preventDefault();
  });

  document.addEventListener("dragstart", function (e) {
    if (!e.dataTransfer) return;
    // גרירת תמונה/אלמנט (ללא בחירת טקסט) נשארת בהתנהגות הרגילה של הדפדפן.
    const data = selectionHTML();
    if (!data) return;
    e.dataTransfer.setData("text/html", data.html);
    e.dataTransfer.setData("text/plain", data.text);
  });
})();
