// 2021 - Matthias Metelka @kleinerpirat
// Modified to include custom menu options: Styles & Auto-save & RTL Support
// Updated to hide floating-arrow on click

var Hider = {
  hide: (config) => {
    // הפעלת המעקב אחר התפריט הצף
    Hider.customize_menu_observer();

    setTimeout(() => {
      const editor = require("anki/NoteEditor");
      editor.lifecycle.onMount(async () => {
        config.ids.forEach((id) => {
          let element = document.getElementById(id);
          if (element) element.setAttribute("hidden", "");
        });
        config.classes.forEach((className) => {
          for (let element of document.getElementsByClassName(className))
            element.setAttribute("hidden", "");
        });
        config.selectors.forEach((selector) => {
          for (let element of document.querySelectorAll(selector))
            element.setAttribute("hidden", "");
        });
      });

      // הסתרת כפתור המתמטיקה
      let cards = document.querySelector(
        "#notetype > div > div > div:nth-child(2) > button"
      );
      if (cards) cards.setAttribute("hidden", "");

      let element = document.getElementById("template");
      if (element) {
        let buttons = element.getElementsByClassName(
          "button-group-item svelte-1wfg5gy"
        );
        if (buttons.length > 2) {
          get_last = buttons[2];
          get_last.setAttribute("hidden", "");
          // עיגול לימין של הכפתור מיקרופון
          mic = buttons[1];
          mic.setAttribute(
            "style",
            "--border-left-radius: 0; --border-right-radius: 5px;"
          );
        }
      }

      // עיגול לימין של הכפתור שדות
      let notetypeelement = document.querySelector(
        "#notetype > div > div > div:nth-child(3) > button"
      );
      if (!notetypeelement) {
        fields = document.querySelector(
          "#notetype > div > div > div:nth-child(1) > button"
        );
        if (fields) {
          fields.setAttribute(
            "style",
            "--border-left-radius: 5px; --border-right-radius: 5px;"
          );
        }
      }
    }, 100);
  },

  hide_buttons: () => {
    setTimeout(() => {
      const boxes = document.querySelectorAll(".plain-text-badge");
      for (const element of boxes) {
        element.setAttribute("hidden", "");
      }
    }, 100);
  },

  // --- חלק חדש: טיפול בתפריט הצף ---
  customize_menu_observer: () => {
    if (Hider._menuObserverStarted) return;
    Hider._menuObserverStarted = true;

    const observer = new MutationObserver((mutations) => {
      for (let mutation of mutations) {
        for (let node of mutation.addedNodes) {
          if (
            node.nodeType === 1 &&
            (node.classList.contains("floating") ||
              node.querySelector(".popover"))
          ) {
            setTimeout(() => Hider.modify_popover_content(node), 1);
          }
        }
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  },

  is_field_options_popover: (items) => {
    return items.some((item) => {
      const text = (item.textContent || item.innerText || "").toLowerCase();
      return (
        (text.indexOf("כווץ") !== -1 || text.indexOf("איינציען") !== -1 || text.indexOf("פארקלענערן") !== -1) ||
        (text.indexOf("הרחב") !== -1 || text.indexOf("אויסברייטערן") !== -1 || text.indexOf("פארברייטערן") !== -1) ||
        text.indexOf("collapse") !== -1 ||
        text.indexOf("expand") !== -1
      );
    });
  },

  modify_popover_content: (container) => {
    const popoverList = container.querySelector('div[role="listbox"]');
    if (!popoverList) return;

    const items = Array.from(popoverList.querySelectorAll(".dropdown-item"));
    // #126 — אל תיגע בתפריטי תמונה/מחיקה וכפתורי עורך אחרים; רק תפריט אפשרויות של שדה עריכה מקבל את כפתורי ההגדרות.
    if (!Hider.is_field_options_popover(items)) return;

    // --- שינוי RTL למיכל הראשי ---
    popoverList.style.direction = "rtl";
    popoverList.style.textAlign = "right";
    // ----------------------------

    items.forEach((item) => {
      if (item.id === "custom-styles-btn" || item.id === "custom-autosave-btn")
        return;

      const text = item.textContent || item.innerText || "";

      if ((text.indexOf("כווץ") !== -1 || text.indexOf("איינציען") !== -1 || text.indexOf("פארקלענערן") !== -1)) {
        item.style.display = "flex";
        item.style.alignItems = "center";
      } else {
        item.style.display = "none";
      }
    });

    if (!popoverList.querySelector("#custom-styles-btn")) {
      Hider.add_custom_button(
        popoverList,
        "custom-styles-btn",
        "איינשטעלן סטילן",
        "styles_options"
      );
    }

    if (!popoverList.querySelector("#custom-autosave-btn")) {
      Hider.add_custom_button(
        popoverList,
        "custom-autosave-btn",
        "איינשטעלן צייט פאר אויטאמאטיש אפזיכערן",
        "autosave_options"
      );
    }
  },

  add_custom_button: (container, id, text, pycmdName) => {
    const newBtn = document.createElement("button");
    newBtn.className = "dropdown-item svelte-1ft3k22";
    newBtn.id = id;
    newBtn.setAttribute("aria-selected", "false");
    newBtn.setAttribute("tabindex", "-1");

    // --- הגדרות עיצוב ---
    newBtn.style.direction = "rtl";
    newBtn.style.textAlign = "right";
    newBtn.style.display = "flex";
    newBtn.style.alignItems = "center";
    newBtn.style.justifyContent = "flex-start";
    newBtn.style.width = "100%";
    // -------------------

    newBtn.innerHTML = `
          <label class="svelte-dvwibz" style="visibility: hidden; margin-left: 5px;"></label>
          <span style="margin-right: 0.5rem;">${text}</span>
      `;

    newBtn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation(); // מונע התנגשויות אירועים

      // 1. ביצוע הפקודה לפייתון
      if (typeof pycmd !== "undefined") {
        pycmd(pycmdName);
      } else {
        console.log(`pycmd('${pycmdName}') triggered`);
      }

      // 2. מציאת כפתור הגלגל שיניים (הטריגר) ולחיצה עליו
      // אנו מחפשים את האלמנט האב המשותף (button-group-item)
      // ואז מוצאים בתוכו את הכפתור המקורי
      const groupItem = newBtn.closest(".button-group-item");
      if (groupItem) {
        const triggerBtn = groupItem.querySelector("button.icon-button");
        if (triggerBtn) {
          triggerBtn.click(); // זה יגרום לאנקי לסגור את התפריט ולעדכן את הסטטוס שלו
        }
      } else {
        // גיבוי למקרה שהמבנה משתנה - ניסיון ללחוץ על id="options" ישירות
        const optionsBtn = document.querySelector(
          "#options button.icon-button"
        );
        if (optionsBtn) optionsBtn.click();
      }
    };

    container.appendChild(newBtn);
  },
};
