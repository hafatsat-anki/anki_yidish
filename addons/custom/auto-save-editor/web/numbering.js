// כפתור מספור אוטומטי לשדות קדמיים (#14)

var HafNumbering = {

    _isActive: false,       // האם מספור מופעל
    _activeField: null,     // אינדקס השדה הפעיל
    _currentN: 1,           // ערך המונה הנוכחי

    inject: function (frontIndices, N) {
        HafNumbering._currentN = N;
        setTimeout(function () {
            HafNumbering._doInject(frontIndices, N, 0);
        }, 150);
    },

    _doInject: function (frontIndices, N, attempts) {
        var found = HafNumbering._addButtons(frontIndices, N);
        if (found < frontIndices.length && attempts < 20) {
            setTimeout(function () {
                HafNumbering._doInject(frontIndices, N, attempts + 1);
            }, 100);
            return;
        }
        if (found > 0 && HafNumbering._isActive) {
            var fi = HafNumbering._activeField;
            if (fi === null || frontIndices.indexOf(fi) === -1) {
                fi = frontIndices[0];
                HafNumbering._activeField = fi;
            }
            HafNumbering._waitAndInsert(fi, N, 0);
        }
        HafNumbering._updateButtonStyles();
    },

    _waitAndInsert: function (fi, N, attempts) {
        var fc = document.querySelector(
            '.field-container[data-index="' + fi + '"]'
        );
        if (!fc) {
            if (attempts < 20)
                setTimeout(function () {
                    HafNumbering._waitAndInsert(fi, N, attempts + 1);
                }, 100);
            return;
        }
        var rte = fc.querySelector(".rich-text-editable");
        if (!rte || !rte.shadowRoot) {
            if (attempts < 20)
                setTimeout(function () {
                    HafNumbering._waitAndInsert(fi, N, attempts + 1);
                }, 100);
            return;
        }
        var ae = rte.shadowRoot.querySelector("anki-editable");
        if (!ae) {
            if (attempts < 20)
                setTimeout(function () {
                    HafNumbering._waitAndInsert(fi, N, attempts + 1);
                }, 100);
            return;
        }
        var text = (ae.innerText || ae.textContent || "").trim();
        if (text === "" || text === "\n") {
            HafNumbering._insertAtStart(rte, ae, String(N));
        }
    },

    _insertAtStart: function (rte, ae, n) {
        ae.focus();
        var sel = rte.shadowRoot.getSelection
            ? rte.shadowRoot.getSelection()
            : window.getSelection();
        if (sel) {
            sel.removeAllRanges();
            var range = document.createRange();
            range.setStart(ae.firstChild || ae, 0);
            range.collapse(true);
            sel.addRange(range);
        }
        document.execCommand("insertText", false, n + ". ");
    },

    _makeBtn: function (fi, N) {
        var isThisActive =
            HafNumbering._isActive && HafNumbering._activeField === fi;

        var btn = document.createElement("span");
        btn.className = "haf-num-btn";
        btn.dataset.fi = String(fi);
        btn.title = "דריקט צו אן אדער אויסשאלטן אויטאמאטישע נומערן";
        btn.style.cssText =
            "display:inline-flex;align-items:center;gap:2px;margin:0 2px;" +
            "border:1px solid " +
            (isThisActive
                ? "var(--accent-color,#07c)"
                : "var(--border-subtle,#ccc)") +
            ";border-radius:4px;background:" +
            (isThisActive
                ? "rgba(0,120,200,0.12)"
                : "var(--button-bg,transparent)") +
            ";cursor:pointer;line-height:1.6;vertical-align:middle;padding:1px 4px;";

        // # icon
        var hash = document.createElement("span");
        hash.className = "haf-num-hash";
        hash.textContent = "#";
        hash.style.cssText =
            "opacity:0.45;font-size:10px;pointer-events:none;user-select:none;";
        btn.appendChild(hash);

        // מספר
        var numSpan = document.createElement("span");
        numSpan.className = "haf-num-value";
        numSpan.textContent = String(N);
        numSpan.style.cssText =
            "font-size:12px;font-weight:bold;min-width:14px;" +
            "text-align:center;color:var(--fg,inherit);cursor:pointer;" +
            "border-bottom:1px dashed var(--border-subtle,#aaa);padding:0 2px;";
        btn.appendChild(numSpan);

        // לחיצה על הכפתור (לא על המספר) = toggle active + insert
        btn.addEventListener("click", function (e) {
            if (e.target === numSpan) return;
            e.preventDefault();
            e.stopPropagation();
            HafNumbering._toggleActive(parseInt(btn.dataset.fi));
        });

        // לחיצה על המספר = עריכת ערך
        numSpan.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            HafNumbering._editNumber(numSpan);
        });

        return btn;
    },

    _toggleActive: function (fi) {
        if (HafNumbering._isActive && HafNumbering._activeField === fi) {
            // כיבוי
            HafNumbering._isActive = false;
            HafNumbering._activeField = null;
        } else {
            // הפעלה
            HafNumbering._isActive = true;
            HafNumbering._activeField = fi;
            // הכנס מספור לתחילת השדה — תמיד, גם אם כבר יש תוכן
            var fc = document.querySelector(
                '.field-container[data-index="' + fi + '"]'
            );
            if (fc) {
                var rte = fc.querySelector(".rich-text-editable");
                if (rte && rte.shadowRoot) {
                    var ae = rte.shadowRoot.querySelector("anki-editable");
                    if (ae) {
                        HafNumbering._insertAtStart(
                            rte,
                            ae,
                            String(HafNumbering._currentN)
                        );
                    }
                }
            }
        }
        HafNumbering._updateButtonStyles();
    },

    _updateButtonStyles: function () {
        document.querySelectorAll(".haf-num-btn").forEach(function (btn) {
            var fi = parseInt(btn.dataset.fi);
            var active =
                HafNumbering._isActive && HafNumbering._activeField === fi;
            btn.style.borderColor = active
                ? "var(--accent-color,#07c)"
                : "var(--border-subtle,#ccc)";
            btn.style.background = active
                ? "rgba(0,120,200,0.12)"
                : "var(--button-bg,transparent)";
        });
    },

    _editNumber: function (numSpan) {
        // יוצר input צף מעל המספר — מובטח לעבוד כי הוא ב-document.body
        var rect = numSpan.getBoundingClientRect();
        var input = document.createElement("input");
        input.type = "number";
        input.min = "1";
        input.value = numSpan.textContent.trim();
        input.style.cssText =
            "position:fixed;z-index:99999;" +
            "left:" + rect.left + "px;top:" + (rect.top - 2) + "px;" +
            "width:" + Math.max(rect.width + 16, 40) + "px;" +
            "height:" + Math.max(rect.height + 4, 22) + "px;" +
            "font-size:12px;font-weight:bold;text-align:center;" +
            "border:2px solid var(--accent-color,#07c);border-radius:3px;" +
            "background:var(--canvas,#fff);color:var(--fg,#000);outline:none;" +
            "padding:0;margin:0;";
        document.body.appendChild(input);
        input.focus();
        input.select();

        var done = false;
        var commit = function () {
            if (done) return;
            done = true;
            var val = parseInt(input.value);
            if (isNaN(val) || val < 1) val = 1;
            document
                .querySelectorAll(".haf-num-btn .haf-num-value")
                .forEach(function (v) {
                    v.textContent = String(val);
                });
            HafNumbering._currentN = val;
            pycmd("haf_num_set:" + val);
            if (input.parentNode) input.parentNode.removeChild(input);
        };

        input.addEventListener("blur", commit);
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                input.blur();
            }
            if (e.key === "Escape") {
                done = true;
                if (input.parentNode) input.parentNode.removeChild(input);
            }
        });
    },

    _addButtons: function (frontIndices, N) {
        var count = 0;
        // הסר כפתורים שכבר לא רלוונטיים
        document.querySelectorAll(".haf-num-btn").forEach(function (btn) {
            var fi = parseInt(btn.dataset.fi);
            if (frontIndices.indexOf(fi) === -1 && btn.parentNode) {
                btn.parentNode.removeChild(btn);
            }
        });

        frontIndices.forEach(function (fi) {
            var cont = document.querySelector(
                '.field-container[data-index="' + fi + '"]'
            );
            if (!cont) return;
            var lc = cont.querySelector(".label-container");
            if (!lc) return;
            count++;

            var existing = lc.querySelector(".haf-num-btn");
            if (existing) {
                var val = existing.querySelector(".haf-num-value");
                if (val) val.textContent = String(N);
                return;
            }
            lc.appendChild(HafNumbering._makeBtn(fi, N));
        });
        return count;
    },
};
