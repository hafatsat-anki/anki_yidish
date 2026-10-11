// Add Table - editor-side floating toolbar for editing existing tables
(function () {
  if (window.__addTableToolbarInstalled) return;
  window.__addTableToolbarInstalled = true;

  const BTN_STYLE =
    "margin:1px;padding:2px 7px;cursor:pointer;border:1px solid #bbb;" +
    "background:#f5f5f5;border-radius:3px;font-size:13px;line-height:1;color:#000;";

  const PALETTE = [
    "#ffffff", "#fff2cc", "#ffe599", "#ffd966",
    "#f4cccc", "#ea9999", "#e06666",
    "#d9ead3", "#b6d7a8", "#93c47d",
    "#cfe2f3", "#9fc5e8", "#6fa8dc",
    "#d9d2e9", "#b4a7d6", "#8e7cc3",
    "#d0d0d0", "#a0a0a0", "#666666",
  ];

  function makeToolbar() {
    const tb = document.createElement("div");
    tb.className = "anki-table-toolbar";
    tb.style.cssText =
      "position:fixed;display:none;z-index:99999;background:#fff;" +
      "border:1px solid #888;border-radius:5px;padding:4px;" +
      "box-shadow:0 2px 8px rgba(0,0,0,0.25);direction:rtl;" +
      "font-family:sans-serif;color:#000;white-space:nowrap;";
    const btns = [
      ["add-row-above", "⬆＋", "לייג צו א שורה אויבן"],
      ["add-row-below", "⬇＋", "לייג צו א שורה אונטן"],
      ["add-col-right", "➡＋", "לייג צו א שפאלט רעכטס"],
      ["add-col-left", "⬅＋", "לייג צו א שפאלט לינקס"],
      ["del-row", "−⫶", "מעק אויס די שורה (יעצטיגע)"],
      ["del-col", "−⫯", "מעק אויס דעם שפאלט (יעצטיגן)"],
      ["del-table", "🗑", "מעק אויס די טאבעלע"],
      ["bg-toggle", "🎨", "הינטערגרונט קאליר פאר א צעל אדער צעלן"],
      ["clear-bg", "∅", "נעם אוועק דעם הינטערגרונט פון דער צעל אדער צעלן"],
    ];
    btns.forEach(([act, label, tip]) => {
      const b = document.createElement("button");
      b.dataset.act = act;
      b.textContent = label;
      b.title = tip;
      b.style.cssText = BTN_STYLE;
      tb.appendChild(b);
    });

    const palette = document.createElement("div");
    palette.dataset.role = "palette";
    palette.style.cssText =
      "display:none;margin-top:4px;padding:3px;border-top:1px solid #ddd;";
    PALETTE.forEach((c) => {
      const sw = document.createElement("button");
      sw.dataset.act = "set-bg";
      sw.dataset.color = c;
      sw.title = c;
      sw.style.cssText =
        "display:inline-block;width:18px;height:18px;margin:1px;padding:0;" +
        "border:1px solid #888;border-radius:3px;cursor:pointer;" +
        "background:" + c + ";";
      palette.appendChild(sw);
    });
    tb.appendChild(palette);
    return tb;
  }

  function initShadow(sr) {
    if (sr.__addTableInit) return;
    sr.__addTableInit = true;

    const tb = makeToolbar();
    sr.appendChild(tb);
    const palette = tb.querySelector('[data-role="palette"]');

    let activeCell = null;
    let selectedCells = new Set();
    let selectionPinned = false;
    // Issue: drag-select state — track drag across cells with left mouse button
    let dragging = false;
    let dragMoved = false;    // true once mouse moved to a different cell during drag
    let dragStartCell = null;
    let dragExtend = false;  // whether to add to existing selection (Shift/Ctrl held)

    const SEL_COLOR = "#2b8aef";
    const DEL_COLOR = "#e06666";
    const HINT_COLOR = SEL_COLOR;
    const RESIZE_HIT = 6;

    let hintEl = null;
    function clearHint() {
      if (hintEl && hintEl.parentNode) hintEl.parentNode.removeChild(hintEl);
      hintEl = null;
    }

    function showInsertHint(cell, where) {
      clearHint();
      if (!cell) return;
      const table = cell.closest("table");
      if (!table) return;
      const rect = cell.getBoundingClientRect();
      const tableRect = table.getBoundingClientRect();
      hintEl = document.createElement("div");
      hintEl.style.cssText =
        "position:fixed;z-index:99998;pointer-events:none;" +
        "background:" + HINT_COLOR + ";border-radius:2px;" +
        "box-shadow:0 0 5px " + HINT_COLOR + ";";

      if (where === "above" || where === "below") {
        hintEl.style.height = "4px";
        hintEl.style.width = tableRect.width + "px";
        hintEl.style.left = tableRect.left + "px";
        hintEl.style.top = ((where === "above" ? rect.top : rect.bottom) - 2) + "px";
      } else {
        hintEl.style.width = "4px";
        hintEl.style.height = tableRect.height + "px";
        hintEl.style.top = tableRect.top + "px";
        hintEl.style.left = ((where === "left" ? rect.left : rect.right) - 2) + "px";
      }

      sr.appendChild(hintEl);
    }

    // Issue: the highlight must never be written into the cell itself —
    // inline styles on td/th are part of the field HTML and get saved into
    // the note (blue frame stuck on cards). Instead we draw detached overlay
    // boxes appended to the shadow root, outside the editable content, like
    // the toolbar and insert-hint already are — so saved HTML is untouched
    // no matter how or when Anki captures the field.
    let overlays = [];

    function clearHighlights() {
      overlays.forEach(function (o) {
        if (o.parentNode) o.parentNode.removeChild(o);
      });
      overlays = [];
    }

    function overlayCell(cell, kind) {
      if (!cell || !cell.isConnected) return;
      const rect = cell.getBoundingClientRect();
      let css =
        "position:fixed;pointer-events:none;z-index:99997;box-sizing:border-box;" +
        "left:" + rect.left + "px;top:" + rect.top + "px;" +
        "width:" + rect.width + "px;height:" + rect.height + "px;";
      if (kind === "active") {
        css += "border:2px solid " + SEL_COLOR + ";";
      } else if (kind === "sel") {
        css += "border:2px dashed " + SEL_COLOR + ";";
      } else {
        css += "border:2px solid " + DEL_COLOR + ";background:rgba(224,102,102,0.18);";
      }
      const div = document.createElement("div");
      div.style.cssText = css;
      sr.appendChild(div);
      overlays.push(div);
    }

    function highlightSelected() {
      clearHighlights();
      selectedCells.forEach(function (cell) {
        overlayCell(cell, cell === activeCell ? "active" : "sel");
      });
    }

    function highlightRow(cell) {
      clearHighlights();
      if (!cell) return;
      Array.prototype.forEach.call(cell.parentElement.children, function (sibling) {
        overlayCell(sibling, "del");
      });
    }

    function highlightCol(cell) {
      clearHighlights();
      if (!cell) return;
      const colIdx = Array.prototype.indexOf.call(cell.parentElement.children, cell);
      const table = cell.closest("table");
      Array.prototype.forEach.call(table.rows, function (row) {
        overlayCell(row.children[colIdx], "del");
      });
    }

    let resizing = null;

    function getResizeType(cell, clientX, clientY) {
      const rect = cell.getBoundingClientRect();
      if (Math.abs(clientX - rect.right) < RESIZE_HIT) return "col";
      if (Math.abs(clientX - rect.left) < RESIZE_HIT) return "col-left";
      if (Math.abs(clientY - rect.bottom) < RESIZE_HIT) return "row";
      return null;
    }

    sr.addEventListener("mousemove", function (e) {
      if (resizing) return;
      if (dragging) {
        e.preventDefault(); // prevent browser text-selection while dragging cells
        const cell = e.target.closest && e.target.closest("td,th");
        if (!cell) return;
        if (!dragMoved) {
          // First actual move: commit the drag and initialize selection
          dragMoved = true;
          if (!dragExtend) selectedCells.clear();
          if (dragStartCell) {
            selectedCells.add(dragStartCell);
            activeCell = dragStartCell;
          }
        }
        if (!selectedCells.has(cell)) {
          selectedCells.add(cell);
          activeCell = cell;
          highlightSelected();
          if (tb.style.display === "none") tb.style.display = "block";
          position(activeCell);
        }
        return;
      }
      const cell = e.target.closest && e.target.closest("td,th");
      const overToolbar = e.target.closest && e.target.closest(".anki-table-toolbar");
      if (!cell) {
        if (!selectionPinned && !overToolbar && tb.style.display !== "none") hide();
        return;
      }
      const resizeType = getResizeType(cell, e.clientX, e.clientY);
      cell.style.cursor = resizeType
        ? resizeType === "row"
          ? "row-resize"
          : "col-resize"
        : "";
      if (!selectionPinned && activeCell !== cell) {
        show(cell, false, true);
      }
    });

    sr.addEventListener("mouseleave", function () {
      if (!selectionPinned) hide();
    });

    sr.addEventListener("mousedown", function (e) {
      const cell = e.target.closest && e.target.closest("td,th");
      if (!cell) return;
      const resizeType = getResizeType(cell, e.clientX, e.clientY);
      if (resizeType) {
        e.preventDefault();
        e.stopPropagation();
        if (resizeType === "row") {
          resizing = {
            type: "row",
            startY: e.clientY,
            startSize: cell.parentElement.getBoundingClientRect().height,
            target: cell.parentElement,
          };
        } else {
          const table = cell.closest("table");
          const row = cell.parentElement;
          let colIdx = Array.prototype.indexOf.call(row.children, cell);
          if (resizeType === "col-left" && colIdx > 0) colIdx -= 1;
          const targets = [];
          Array.prototype.forEach.call(table.rows, function (currentRow) {
            if (currentRow.children[colIdx]) targets.push(currentRow.children[colIdx]);
          });
          resizing = {
            type: "col",
            startX: e.clientX,
            startSize: cell.getBoundingClientRect().width,
            targets: targets,
          };
        }
        return;
      }
      // Issue: start drag-select when pressing on a cell (non-resize area)
      dragging = true;
      dragMoved = false;
      dragStartCell = cell;
      dragExtend = e.shiftKey || e.ctrlKey || e.metaKey;
      selectionPinned = true;
    });

    const ownerDoc = sr.host ? sr.host.ownerDocument : document;
    ownerDoc.addEventListener("mousemove", function (e) {
      if (dragging) {
        e.preventDefault(); // prevent text-selection outside shadow root during drag
        return;
      }
      if (!resizing) return;
      if (resizing.type === "row") {
        resizing.target.style.height =
          Math.max(18, resizing.startSize + (e.clientY - resizing.startY)) + "px";
      } else {
        const newWidth = Math.max(20, resizing.startSize + (e.clientX - resizing.startX));
        resizing.targets.forEach(function (cell) {
          cell.style.width = newWidth + "px";
        });
      }
    });

    // Overlays are position:fixed — keep them glued to the cells when the
    // fields area scrolls or the window resizes.
    function refreshOverlays() {
      clearHint();
      if (selectedCells.size && activeCell && activeCell.isConnected) {
        highlightSelected();
        if (tb.style.display !== "none") position(activeCell);
      } else {
        clearHighlights();
      }
    }
    ownerDoc.addEventListener("scroll", refreshOverlays, true);
    if (ownerDoc.defaultView) {
      ownerDoc.defaultView.addEventListener("resize", refreshOverlays);
    }

    ownerDoc.addEventListener("mouseup", function () {
      if (dragging) {
        dragging = false;
        // If drag ended outside shadow root and toolbar is hidden, restore it
        if (dragMoved && selectedCells.size > 0 && activeCell && tb.style.display === "none") {
          tb.style.display = "block";
          position(activeCell);
        }
        return;
      }
      if (!resizing) return;
      resizing = null;
      notifyChange();
    });

    function position(cell) {
      const rect = cell.closest("table").getBoundingClientRect();
      tb.style.display = "block";
      const toolbarRect = tb.getBoundingClientRect();
      let top = rect.top - toolbarRect.height - 4;
      if (top < 4) top = rect.bottom + 4;
      let left = rect.left;
      const maxLeft = window.innerWidth - toolbarRect.width - 4;
      if (left > maxLeft) left = maxLeft;
      if (left < 4) left = 4;
      tb.style.top = top + "px";
      tb.style.left = left + "px";
    }

    function show(cell, addToSelection, fromHover) {
      if (!fromHover) selectionPinned = true;
      if (addToSelection) {
        if (selectedCells.has(cell)) {
          selectedCells.delete(cell);
          if (activeCell === cell) {
            activeCell = selectedCells.size ? selectedCells.values().next().value : null;
          }
        } else {
          selectedCells.add(cell);
          activeCell = cell;
        }
        if (selectedCells.size === 0) {
          hide();
          return;
        }
        position(activeCell);
        highlightSelected();
      } else {
        selectedCells.clear();
        selectedCells.add(cell);
        activeCell = cell;
        position(cell);
        highlightSelected();
      }
    }

    function hide() {
      activeCell = null;
      selectedCells.clear();
      selectionPinned = false;
      tb.style.display = "none";
      palette.style.display = "none";
      clearHighlights();
      clearHint();
    }

    sr.addEventListener("click", function (e) {
      if (resizing) return;
      // Issue: suppress the click event that fires at the end of a drag across cells
      if (dragMoved) { dragMoved = false; return; }
      const cell = e.target.closest && e.target.closest("td,th");
      if (cell) {
        // Support Ctrl/Cmd+Click in addition to Shift+Click for multi-cell selection
        show(cell, e.shiftKey || e.ctrlKey || e.metaKey, false);
      } else if (!e.target.closest || !e.target.closest(".anki-table-toolbar")) {
        hide();
      }
    });

    sr.addEventListener("keyup", function (e) {
      if (!e.key || e.key === "Shift" || e.key === "Control" || e.key === "Alt" || e.key === "Meta") {
        return;
      }
      const sel = sr.getSelection && sr.getSelection();
      if (!sel || !sel.anchorNode) return;
      let node = sel.anchorNode;
      if (node.nodeType === 3) node = node.parentElement;
      const cell = node && node.closest && node.closest("td,th");
      if (cell) show(cell, false, false);
    });

    tb.addEventListener("mousedown", function (e) {
      e.preventDefault();
    });

    tb.addEventListener("mouseover", function (e) {
      const btn = e.target.closest("[data-act]");
      if (!btn || !activeCell) return;
      const act = btn.dataset.act;
      if (act === "del-row") {
        clearHint();
        highlightRow(activeCell);
      } else if (act === "del-col") {
        clearHint();
        highlightCol(activeCell);
      } else if (act === "add-row-above") {
        highlightSelected();
        showInsertHint(activeCell, "above");
      } else if (act === "add-row-below") {
        highlightSelected();
        showInsertHint(activeCell, "below");
      } else if (act === "add-col-left") {
        highlightSelected();
        showInsertHint(activeCell, "left");
      } else if (act === "add-col-right") {
        highlightSelected();
        showInsertHint(activeCell, "right");
      } else {
        clearHint();
        highlightSelected();
      }
    });

    tb.addEventListener("mouseleave", function () {
      if (!activeCell) return;
      clearHint();
      highlightSelected();
    });

    function notifyChange() {
      const root = sr.querySelector("anki-editable") || sr.host;
      if (root && root.dispatchEvent) {
        root.dispatchEvent(new Event("input", { bubbles: true }));
      }
    }

    // Heal notes that were already saved with a stuck highlight by older
    // versions: strip our leftover class/outline styles from the loaded
    // content. Only touches outlines in the addon's own colors so user
    // styling is never affected. Runs from scan() so it also catches
    // content loaded after init (note switches in the browser).
    const STALE_RE = /__atb-hl|outline[^;"]*(2b8aef|43,\s*138,\s*239|e06666|224,\s*102,\s*102)/i;
    sr.__atbCleanStale = function () {
      let cleaned = false;
      sr.querySelectorAll("td,th").forEach(function (cell) {
        const inline = cell.getAttribute("style") || "";
        if (!cell.classList.contains("__atb-hl") && !STALE_RE.test(inline)) return;
        cell.classList.remove("__atb-hl");
        if (!cell.getAttribute("class")) cell.removeAttribute("class");
        cell.style.outline = "";
        cell.style.outlineOffset = "";
        if (/224,\s*102,\s*102/.test(cell.style.backgroundImage || "")) {
          cell.style.backgroundImage = "";
        }
        cleaned = true;
      });
      if (cleaned) notifyChange();
    };
    sr.__atbCleanStale();

    tb.addEventListener("click", function (e) {
      const btn = e.target.closest("[data-act]");
      if (!btn || !activeCell) return;
      const act = btn.dataset.act;
      selectionPinned = true;

      if (act === "bg-toggle") {
        const opening = palette.style.display === "none";
        palette.style.display = opening ? "block" : "none";
        // Issue #xxx: recalculate position after palette opens so the expanded
        // toolbar doesn't overlap table cells and intercept cell-click events
        if (opening && activeCell) position(activeCell);
        return;
      }
      if (act === "set-bg") {
        const color = btn.dataset.color;
        selectedCells.forEach(function (cell) {
          cell.style.backgroundColor = color;
        });
        palette.style.display = "none";
        notifyChange();
        highlightSelected();
        return;
      }
      if (act === "clear-bg") {
        selectedCells.forEach(function (cell) {
          cell.style.backgroundColor = "";
        });
        notifyChange();
        highlightSelected();
        return;
      }

      const row = activeCell.parentElement;
      const table = activeCell.closest("table");
      const colIdx = Array.prototype.indexOf.call(row.children, activeCell);

      if (act === "add-row-above" || act === "add-row-below") {
        const newRow = document.createElement("tr");
        for (let index = 0; index < row.children.length; index++) {
          const ref = row.children[index];
          const td = document.createElement("td");
          td.style.cssText = ref.style.cssText
            .replace(/font-weight:[^;]+;?/g, "")
            .replace(/outline:[^;]*;?/g, "")
            .replace(/outline-offset:[^;]*;?/g, "")
            .replace(/background-image:[^;]*;?/g, "")
            .replace(/background-color:[^;]*;?/g, "");
          if (!td.style.border) td.style.border = "1px solid #888";
          if (!td.style.padding) td.style.padding = "4px";
          td.innerHTML = "&nbsp;";
          newRow.appendChild(td);
        }
        if (act === "add-row-above") row.parentNode.insertBefore(newRow, row);
        else row.parentNode.insertBefore(newRow, row.nextSibling);
        const newCell = newRow.children[colIdx] || newRow.children[0];
        if (newCell) {
          show(newCell);
          notifyChange();
          return;
        }
      } else if (act === "add-col-left" || act === "add-col-right") {
        Array.prototype.forEach.call(table.rows, function (currentRow) {
          const refCell = currentRow.children[colIdx];
          const tag = refCell ? refCell.tagName : "TD";
          const nc = document.createElement(tag);
          if (refCell) {
            nc.style.cssText = refCell.style.cssText
              .replace(/outline:[^;]*;?/g, "")
              .replace(/outline-offset:[^;]*;?/g, "")
              .replace(/background-image:[^;]*;?/g, "")
              .replace(/background-color:[^;]*;?/g, "");
          }
          nc.innerHTML = "&nbsp;";
          if (act === "add-col-right") currentRow.insertBefore(nc, refCell || null);
          else currentRow.insertBefore(nc, refCell ? refCell.nextSibling : null);
        });
        const newColIdx = act === "add-col-right" ? colIdx : colIdx + 1;
        const newCell = row.children[newColIdx] || row.children[row.children.length - 1];
        if (newCell) {
          show(newCell);
          notifyChange();
          return;
        }
      } else if (act === "del-row") {
        if (table.rows.length > 1) row.remove();
        hide();
        notifyChange();
        return;
      } else if (act === "del-col") {
        if (table.rows[0] && table.rows[0].children.length > 1) {
          Array.prototype.forEach.call(table.rows, function (currentRow) {
            if (currentRow.children[colIdx]) currentRow.children[colIdx].remove();
          });
        }
        hide();
        notifyChange();
        return;
      } else if (act === "del-table") {
        table.remove();
        hide();
        notifyChange();
        return;
      }

      notifyChange();
      if (activeCell && activeCell.isConnected) highlightSelected();
    });
  }

  function scan() {
    document.querySelectorAll(".rich-text-editable").forEach(function (el) {
      if (el.shadowRoot) {
        initShadow(el.shadowRoot);
        if (el.shadowRoot.__atbCleanStale) el.shadowRoot.__atbCleanStale();
      }
    });
  }

  scan();
  const obs = new MutationObserver(scan);
  obs.observe(document.body, { childList: true, subtree: true });
  setInterval(scan, 1500);
})();
