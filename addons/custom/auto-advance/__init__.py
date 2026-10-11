from aqt import gui_hooks, mw
from aqt.qt import QApplication

from _shared_libs.haf_logging import get_logger

logger = get_logger("auto_advance")


# --- Config Management Class ---

class ConfigManager:
    def __init__(self):
        self.addon_name = mw.addonManager.addonFromModule(__name__)
        self.default_config = {"presets": {}}
        self._ensure_valid_config()

    def _ensure_valid_config(self):
        """Validate without overwriting unreadable user settings."""
        try:
            conf = mw.addonManager.getConfig(self.addon_name)
            if conf is not None and not isinstance(conf, dict):
                raise ValueError("די איינשטעלונגען פאר אויטאמאטיש ווייטערגיין זענען נישט אין א גילטיגן פארמאט")
        except Exception as e:
            raise RuntimeError("מען קען נישט לייענען די איינשטעלונגען פאר אויטאמאטיש ווייטערגיין. די ביז יעצטיגע איינשטעלונגען זענען נישט געטוישט געווארן.") from e

    def get_config(self):
        """Loads config with fail-safe mechanism."""
        conf = mw.addonManager.getConfig(self.addon_name)
        if conf is None:
            return self.default_config
        if "presets" not in conf:
            conf["presets"] = {}
        return conf

    def get_preset_status(self, conf_id):
        config = self.get_config()
        presets = config.get("presets", {})
        return presets.get(str(conf_id), False)

    def set_preset_status(self, conf_id, status: bool):
        config = self.get_config()
        config["presets"][str(conf_id)] = status
        mw.addonManager.writeConfig(self.addon_name, config)
        logger.debug(f"Saved status for {conf_id}: {status}")

        # --- NEW: Update Reviewer Immediately ---
        update_active_reviewer_if_needed(str(conf_id), status)



# יצירת מופע יחיד
config_manager = ConfigManager()


# --- Real-Time Updates Logic (NEW) ---

def update_active_reviewer_if_needed(modified_conf_id, new_status):
    """
    די פונקציע ווערט אויפגערופן גלייך נאכן אפזיכערן.
    זי קוקט צי דער באניצער איז יעצט ביים חזרן, און אויב יא, דערהיינטיגט זי דעם מצב גלייך.
    """
    # בדיקה שאנחנו במצב חזרה ויש כרטיסייה פעילה
    if mw.state != "review" or not mw.reviewer.card:
        return

    # בדיקה האם הכרטיסייה הנוכחית שייכת ל-Preset ששונה כרגע
    deck_id = mw.reviewer.card.current_deck_id()
    deck = mw.col.decks.get(deck_id)
    if not deck or 'conf' not in deck:
        return

    current_conf_id = str(deck['conf'])

    # אם השינוי רלוונטי לחפיסה הנוכחית
    if current_conf_id == modified_conf_id:
        logger.debug(f"Real-time update for active review session: {new_status}")

        # 1. עדכון המשתנה הבוליאני של אנקי (זה משפיע על ה"וי" בתפריט More)
        mw.reviewer.auto_advance_enabled = new_status

        # 2. עדכון הטיימר בפועל (התנהגות)
        if new_status:
            # אם הופעל - ננסה להפעיל את הטיימר לכרטיס הנוכחי
            if hasattr(mw.reviewer, "_auto_advance_to_answer_if_enabled"):
                mw.reviewer._auto_advance_to_answer_if_enabled()
        else:
            # אם כובה - ננקה טיימרים קיימים
            if hasattr(mw.reviewer, "_clear_auto_advance_timers"):
                mw.reviewer._clear_auto_advance_timers()

        # 3. רענון סרגל הכלים (כדי שהתפריט More יתעדכן ויזואלית בפעם הבאה שייפתח)
        if hasattr(mw, "toolbar"):
            mw.toolbar.redraw()


# --- Helpers ---

def find_conf_id_by_name(display_name):
    all_configs = mw.col.decks.all_config()
    clean_display = display_name.replace('\u2068', '').replace('\u2069', '')
    all_configs.sort(key=lambda c: len(c['name']), reverse=True)
    for conf in all_configs:
        if clean_display.startswith(conf['name']):
            return str(conf['id'])
    return None


def find_active_options_dialog():
    for widget in QApplication.topLevelWidgets():
        if "DeckOptionsDialog" in str(type(widget)) and hasattr(widget, "web") and widget.isVisible():
            return widget
    return None


# --- JavaScript Code ---

def get_js_code(initial_status, conf_id):
    js_bool = "true" if initial_status else "false"
    js_conf_id = str(conf_id)

    return f"""
    (async function() {{
        window.currentAutoAdvanceConfId = "{js_conf_id}";
        if (typeof window.pendingAutoAdvanceState === 'undefined') {{
            window.pendingAutoAdvanceState = {{}};
        }}

        const wrapperId = "custom-auto-advance-wrapper";
        const toggleId = "custom-auto-advance-toggle";

        function createOrUpdateToggle(isChecked, newConfId) {{
            window.currentAutoAdvanceConfId = newConfId;
            let wrapper = document.getElementById(wrapperId);
            let input = document.getElementById(toggleId);

            if (!wrapper) {{
                wrapper = document.createElement('div');
                wrapper.id = wrapperId;
                wrapper.style.padding = "15px";
                wrapper.style.margin = "10px 0";
                wrapper.style.backgroundColor = "var(--canvas-elevated)";
                wrapper.style.borderRadius = "5px";
                wrapper.style.border = "1px solid var(--border)";
                wrapper.style.display = "flex";
                wrapper.style.justifyContent = "space-between";
                wrapper.style.alignItems = "center";

                const textDiv = document.createElement('div');
                textDiv.id = "custom-auto-advance-text";
                textDiv.innerHTML = `
                    <div style="font-weight: bold; font-size: 1rem;">שאלט אן אויטאמאטיש ווייטערגיין</div>
                    <div style="font-size: 0.85em; color: var(--text-fg-faint); margin-top: 3px;">

                    </div>מען קען דאס צייטווייליג אן אדער אויסשאלטן אינעם מעניו נאך אפציעס
                `;

                const label = document.createElement('label');
                label.style.position = "relative";
                label.style.display = "inline-block";
                label.style.width = "40px";
                label.style.height = "20px";
                label.style.marginRight = "10px";

                input = document.createElement('input');
                input.id = toggleId;
                input.type = "checkbox";
                input.style.opacity = "0";
                input.style.width = "0";
                input.style.height = "0";

                const slider = document.createElement('span');
                slider.className = "slider-span";
                slider.style.position = "absolute";
                slider.style.cursor = "pointer";
                slider.style.top = "0";
                slider.style.left = "0";
                slider.style.right = "0";
                slider.style.bottom = "0";
                slider.style.backgroundColor = "#ccc";
                slider.style.transition = ".4s";
                slider.style.borderRadius = "34px";

                const circle = document.createElement('span');
                circle.id = "slider-circle";
                circle.style.position = "absolute";
                circle.style.content = "";
                circle.style.height = "16px";
                circle.style.width = "16px";
                circle.style.left = "2px";
                circle.style.bottom = "2px";
                circle.style.backgroundColor = "white";
                circle.style.transition = ".4s";
                circle.style.borderRadius = "50%";

                slider.appendChild(circle);
                label.appendChild(input);
                label.appendChild(slider);

                input.addEventListener('change', function() {{
                    window.pendingAutoAdvanceState[window.currentAutoAdvanceConfId] = this.checked;
                    updateVisuals(this.checked);
                }});

                wrapper.appendChild(textDiv);
                wrapper.appendChild(label);

                const target = findTargetElement();
                if (target) {{
                    if (target.querySelector('.setting-title')) {{
                        target.insertBefore(wrapper, target.children[1]);
                    }} else {{
                        target.prepend(wrapper);
                    }}
                }}
            }}

            if (input) {{
                input.checked = isChecked;
                setTimeout(() => updateVisuals(isChecked), 50);
            }}
            window.pendingAutoAdvanceState[newConfId] = isChecked;
        }}

        function updateVisuals(checked) {{
            const wrapper = document.getElementById(wrapperId);
            if (!wrapper) return;
            const circle = wrapper.querySelector("#slider-circle");
            const slider = wrapper.querySelector(".slider-span");
            if (!circle || !slider) return;

            if (checked) {{
                slider.style.backgroundColor = "#2196F3";
                circle.style.transform = "translateX(20px)";
            }} else {{
                slider.style.backgroundColor = "#ccc";
                circle.style.transform = "translateX(0px)";
            }}
        }}

        function findTargetElement() {{
            const headers = Array.from(document.querySelectorAll('h1, h2, h3, .setting-title'));
            for (let h of headers) {{
                if (h.textContent.includes("אויטאמאטיש ווייטערגיין") || h.textContent.includes("Auto Advance")) {{
                    return h.closest('.container') || h.parentElement;
                }}
            }}
            return null;
        }}

        function setupSaveButtonHook() {{
            const saveButtonDiv = document.querySelector('.button-bar .label-button.primary .save');
            if (!saveButtonDiv) {{
                setTimeout(setupSaveButtonHook, 500);
                return;
            }}
            const saveButton = saveButtonDiv.parentElement;
            if (saveButton.__autoAdvanceListenerAttached__) return;

            saveButton.addEventListener('click', function() {{
                const confId = window.currentAutoAdvanceConfId;
                const pendingState = window.pendingAutoAdvanceState[confId];
                if (confId !== undefined && pendingState !== undefined) {{
                    pycmd("save_auto_advance_state:" + confId + ":" + pendingState);
                }}
            }});
            saveButton.__autoAdvanceListenerAttached__ = true;
        }}

        let attempts = 0;
        const checkExist = setInterval(function() {{
            if (findTargetElement()) {{
                clearInterval(checkExist);
                createOrUpdateToggle({js_bool}, "{js_conf_id}");
                observePresetChange();
                setupSaveButtonHook();
            }}
            attempts++;
            if (attempts > 50) clearInterval(checkExist);
        }}, 100);

        function observePresetChange() {{
            const selectLabel = document.querySelector('.select-container .label');
            if (!selectLabel) {{
                setTimeout(observePresetChange, 500);
                return;
            }}
            const observer = new MutationObserver(function(mutations) {{
                mutations.forEach(function(mutation) {{
                    if (mutation.type === 'characterData' || mutation.type === 'childList') {{
                        const newName = selectLabel.textContent;
                        pycmd("preset_changed_by_name:" + newName);
                    }}
                }});
            }});
            observer.observe(selectLabel, {{ characterData: true, subtree: true, childList: true }});
        }}

        window.updateAutoAdvanceUI = function(status, newId) {{
            createOrUpdateToggle(status, newId);
        }}

    }})();
    """


# --- Hooks & Bridge ---

def on_deck_options_did_load(options_dialog):
    deck = options_dialog._deck
    if 'conf' in deck:
        conf_id = deck['conf']
        current_status = config_manager.get_preset_status(conf_id)
        options_dialog.web.eval(get_js_code(current_status, conf_id))


def on_js_message(handled, message, context):
    if not isinstance(message, str):
        return handled

    if message.startswith("save_auto_advance_state:"):
        parts = message.split(":")
        if len(parts) == 3:
            conf_id = parts[1]
            state = (parts[2] == "true")
            config_manager.set_preset_status(conf_id, state)
        return (True, None)

    if message.startswith("preset_changed_by_name:"):
        display_name = message.replace("preset_changed_by_name:", "")
        new_id = find_conf_id_by_name(display_name)
        if new_id:
            status = config_manager.get_preset_status(new_id)
            js_bool = "true" if status else "false"
            dialog = find_active_options_dialog()
            if dialog and hasattr(dialog, 'web'):
                dialog.web.eval(f"window.updateAutoAdvanceUI({js_bool}, '{new_id}');")
        return (True, None)

    if message.startswith("open_url:"):
        url = message[9:]
        try:
            if hasattr(mw, 'open_pdf_file'):
                mw.open_pdf_file(url)
            else:
                from aqt.utils import openLink
                openLink(url)
        except Exception:
            from aqt.utils import openLink
            openLink(url)
        return (True, None)

    return handled


# --- REVIEWER LOGIC (Load New Card) ---

def apply_auto_advance_on_show_question(card):
    """
    Hook וואס ווערט אויפגערופן יעדעס מאל ווען א נייע קארטל ווערט געוויזן.
    """
    deck_id = card.current_deck_id()
    deck = mw.col.decks.get(deck_id)
    if not deck or 'conf' not in deck:
        return

    conf_id = str(deck['conf'])
    should_auto_advance = config_manager.get_preset_status(conf_id)

    # עדכון המצב הבוליאני
    mw.reviewer.auto_advance_enabled = should_auto_advance

    # הפעלה יזומה של הטיימר אם צריך
    if should_auto_advance and hasattr(mw.reviewer, "_auto_advance_to_answer_if_enabled"):
        mw.reviewer._auto_advance_to_answer_if_enabled()


# --- Registration ---

gui_hooks.deck_options_did_load.append(on_deck_options_did_load)
gui_hooks.webview_did_receive_js_message.append(on_js_message)
gui_hooks.reviewer_did_show_question.append(apply_auto_advance_on_show_question)
