/* 
Remove Clozes Add-on for Anki

Copyright (C) 2016-2022  Aristotelis P. <https//glutanimate.com/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version, with the additions
listed at the end of the accompanied license file.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

NOTE: This program is subject to certain additional terms pursuant to
Section 7 of the GNU Affero General Public License.  You should have
received a copy of these additional terms immediately following the
terms and conditions of the GNU Affero General Public License which
accompanied this program.

If not, please request a copy through one of the means of contact
listed here: <https://glutanimate.com/contact/>.

Any modifications to this file must keep this entire header intact.
*/

const getSelectedHTML = () => {
  if (!document.activeElement) {
    return null;
  }
  const fieldShadowRoot = document.activeElement.shadowRoot;
  if (!fieldShadowRoot) {
    return null;
  }

  let html;
  const selection = fieldShadowRoot.getSelection();
  if (selection.rangeCount) {
    const container = document.createElement("div");
    for (let i = 0, len = selection.rangeCount; i < len; ++i) {
      container.appendChild(selection.getRangeAt(i).cloneContents());
    }
    html = container.innerHTML;
  }
  return html;
};

function removeClozes() {
  let selectedHTML = getSelectedHTML();
  if (!selectedHTML) {
    return;
  }
  selectedHTML = selectedHTML.replace(
    /\{\{c(\d+)::(.*?)(::(.*?))?\}\}/gm,
    "$2"
  );
  // workaround for duplicate list items:
  selectedHTML = selectedHTML.replace(/^(<li>)/, "");
  document.execCommand("insertHTML", false, selectedHTML);
  globalThis.saveNow();
}

// #138 — קיצור מקשים בתוך WebView עוקף מצב שבו QShortcut לא מקבל אירועים משדה העריכה של Anki.
window.RemoveClozesShortcut = window.RemoveClozesShortcut || {};

(function () {
  const state = window.RemoveClozesShortcut;
  const specialCodes = {
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

  const normalizedMainKey = function (key) {
    key = (key || "").trim().toLowerCase();
    if (key.length === 1) {
      if (/\d/.test(key)) return "digit" + key;
      if (/[a-z]/.test(key)) return "key" + key;
      return specialCodes[key] || key;
    }
    return key;
  };

  state.setHotkey = function (hotkey) {
    // #138 — shortcut-manager יכול לשלוח ערך ריק/<nop>; במקרה כזה מאזין ה-JS נשאר טעון אך לא מפעיל פעולה.
    hotkey = (hotkey || "").trim();
    state.hotkey = hotkey.toLowerCase() === "<nop>" ? "" : hotkey;
    const parts = state.hotkey
      .toLowerCase()
      .split("+")
      .map((part) => part.trim())
      .filter(Boolean);
    state.shortcut = {
      ctrl: parts.includes("ctrl"),
      shift: parts.includes("shift"),
      alt: parts.includes("alt"),
      key: normalizedMainKey(parts[parts.length - 1]),
      rawKey: parts[parts.length - 1] || "",
    };
  };

  const matchesHotkey = function (event) {
    const shortcut = state.shortcut;
    if (!state.hotkey || !shortcut || !shortcut.key) return false;
    if (shortcut.ctrl !== (event.ctrlKey || event.metaKey)) return false;
    if (shortcut.shift !== event.shiftKey) return false;
    if (shortcut.alt !== event.altKey) return false;
    const eventCode = (event.code || "").toLowerCase();
    if (eventCode === shortcut.key) return true;
    return shortcut.rawKey.length === 1 && (event.key || "").toLowerCase() === shortcut.rawKey;
  };

  if (!state.installed) {
    state.installed = true;
    document.addEventListener(
      "keydown",
      function (event) {
        if (!matchesHotkey(event)) return;
        event.preventDefault();
        event.stopPropagation();
        removeClozes();
      },
      true
    );
  }

  state.setHotkey(window.RemoveClozesPendingHotkey || state.hotkey || "");
})();
