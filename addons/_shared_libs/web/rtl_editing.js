// #161 — shared by both editors. Do not add independent arrow inversions in addons.
(() => {
    if (window.HafRtlEditing) return;

    function isBackward(selection) {
        // Chromium 122 reports isCollapsed=true for a real ShadowRoot range.
        // Anchor/focus equality works in both old and new engines.
        if (!selection || !selection.rangeCount ||
                (selection.anchorNode === selection.focusNode &&
                 selection.anchorOffset === selection.focusOffset)) return false;
        const range = selection.getRangeAt(0);
        return selection.anchorNode !== range.startContainer ||
            selection.anchorOffset !== range.startOffset;
    }

    // Range always has ordered start/end; only Selection retains the active end.
    function restoreRange(selection, range, backward) {
        const anchor = backward ? "end" : "start";
        const focus = backward ? "start" : "end";
        selection.setBaseAndExtent(
            range[anchor + "Container"], range[anchor + "Offset"],
            range[focus + "Container"], range[focus + "Offset"],
        );
    }

    function caretRect(node, offset) {
        const range = document.createRange();
        range.setStart(node, offset);
        range.collapse(true);
        return range.getClientRects()[0] || null;
    }

    function horizontalDelta(before, after) {
        // Different visual lines are wrapping, not evidence of reversed keys.
        if (!before || !after || Math.min(before.bottom, after.bottom) <=
                Math.max(before.top, after.top)) return 0;
        return after.left - before.left;
    }

    function stepDelta(before, node, offset, nextNode, nextOffset) {
        const range = document.createRange();
        range.setStart(node, offset);
        range.collapse(true);
        if (range.comparePoint(nextNode, nextOffset) < 0) {
            range.setStart(nextNode, nextOffset);
            range.setEnd(node, offset);
        } else {
            range.setEnd(nextNode, nextOffset);
        }
        // At a bidi boundary a collapsed caret has two possible positions.
        // The crossed grapheme's box identifies the local side unambiguously.
        if (before) {
            const boxes = Array.from(range.getClientRects()).filter(rect => rect.width > 0.5 &&
                Math.min(before.bottom, rect.bottom) > Math.max(before.top, rect.top));
            boxes.sort((a, b) => a.width - b.width);
            for (const box of boxes) {
                if (Math.abs(before.left - box.right) < 0.5) return -box.width;
                if (Math.abs(before.left - box.left) < 0.5) return box.width;
            }
        }
        return horizontalDelta(before, caretRect(nextNode, nextOffset));
    }

    function moveVisually(selection, key, field) {
        const node = selection.focusNode, offset = selection.focusOffset;
        const before = caretRect(node, offset);
        const right = key === "ArrowRight";
        selection.modify("move", right ? "right" : "left", "character");
        if (!field.contains(selection.focusNode)) return;
        const nativeNode = selection.focusNode, nativeOffset = selection.focusOffset;
        const delta = stepDelta(before, node, offset, nativeNode, nativeOffset);
        // Some bidi contexts reverse even Chromium's physical direction name.
        // Correct only an observed same-line move against the requested key.
        if ((right && delta < -0.5) || (!right && delta > 0.5)) {
            selection.collapse(node, offset);
            selection.modify("move", right ? "left" : "right", "character");
            const corrected = field.contains(selection.focusNode)
                ? stepDelta(before, node, offset, selection.focusNode, selection.focusOffset) : 0;
            if (!((right && corrected > 0.5) || (!right && corrected < -0.5))) {
                selection.collapse(nativeNode, nativeOffset);
            }
        }
    }

    function handleArrow(event) {
        if (event.defaultPrevented || event.isComposing || event.altKey || event.metaKey) return;
        const key = event.key === "ArrowLeft" || event.key === "ArrowRight"
            ? event.key : event.code;
        if ((key !== "ArrowLeft" && key !== "ArrowRight") ||
                (!event.ctrlKey && !event.shiftKey)) return;

        // composedPath reaches anki-editable inside its ShadowRoot. It also
        // reaches newly rendered reviewer fields without rebinding listeners.
        const path = event.composedPath();
        const field = path.find(node => node.matches &&
            node.matches('anki-editable, [data-EFDRCfield]') && node.isContentEditable);
        if (!field) return;
        // Embedded inputs and explicitly noneditable islands own their keys.
        if (path.slice(0, path.indexOf(field)).some(node => node.matches &&
                node.matches('input, textarea, select, [contenteditable="false"]'))) return;
        const root = field.getRootNode();
        const selection = typeof root.getSelection === "function"
            ? root.getSelection() : window.getSelection();
        if (!selection || !selection.rangeCount || !selection.modify ||
                !field.contains(selection.anchorNode) || !field.contains(selection.focusNode)) return;

        const anchorNode = selection.anchorNode, anchorOffset = selection.anchorOffset;
        const focusNode = selection.focusNode, focusOffset = selection.focusOffset;
        // #161 — CSS direction is not the resolved bidi direction: plaintext,
        // nested LTR/RTL runs and inline editing hosts can disagree with it in
        // the SAME installation. Ask this renderer at this caret, on each key.
        const origin = document.createRange();
        origin.setStart(focusNode, focusOffset);
        origin.collapse(true);
        selection.collapse(focusNode, focusOffset);
        moveVisually(selection, key, field);
        if (event.ctrlKey && field.contains(selection.focusNode)) {
            const order = origin.comparePoint(selection.focusNode, selection.focusOffset);
            // Reuse Chromium's word segmentation in the observed direction.
            // No version switch, Hebrew-text heuristic or global inversion.
            selection.collapse(focusNode, focusOffset);
            if (order) selection.modify("move", order < 0 ? "backward" : "forward", "word");
        }
        if (event.shiftKey) {
            selection.setBaseAndExtent(anchorNode, anchorOffset,
                selection.focusNode, selection.focusOffset);
        }
        // A navigation command must never select outside this editing field.
        if (!field.contains(selection.focusNode) || !field.contains(selection.anchorNode)) {
            selection.setBaseAndExtent(anchorNode, anchorOffset, focusNode, focusOffset);
        }
        event.preventDefault();
        event.stopImmediatePropagation();
    }

    window.HafRtlEditing = {isBackward, restoreRange};
    window.addEventListener("keydown", handleArrow, true);
})();
