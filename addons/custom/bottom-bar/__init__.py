#// auth_ Mohamad Janati
#// Copyright (c) 2019-2021 Mohamad Janati (freaking stupid, right? :|)

from anki import version
from aqt import mw

config = mw.addonManager.getConfig(__name__)

anki_version = int(version.replace('.', ''))
from . import Bottom_Bar as Bottom_Bar
from . import Tooltip as Tooltip
from . import answered_cards as answered_cards

