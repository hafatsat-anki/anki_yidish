"""Complete Yiddish settings while preserving preferences from Hebrew editions."""

import copy


def normalise_config_keys(config: dict) -> dict:
    result = copy.deepcopy(config)
    aliases = {
        "צבע טקסט סרגל": "סרגל טעקסט קאליר",
        "צבע מילוי": "פיל קאליר",
    }
    for old, new in aliases.items():
        if old in result:
            result.setdefault(new, result[old])
            del result[old]
    formatting = result.get("special_formatting")
    if isinstance(formatting, dict):
        for index in range(1, 7):
            old = f"צבע טקסט {index}"
            new = f"טעקסט קאליר {index}"
            if old in formatting:
                formatting.setdefault(new, formatting[old])
                del formatting[old]
    return result
