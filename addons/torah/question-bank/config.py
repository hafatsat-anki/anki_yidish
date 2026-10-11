from aqt import mw


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    try:
        return conf[arg]
    except KeyError:
        return fail


def wc(key, val, second_key=None):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        if second_key is not None:
            conf[key][second_key] = val
        else:
            conf[key] = val
        mw.addonManager.writeConfig(__name__, conf)
    else:
        mw.addonManager.writeConfig(__name__, {key: val})
