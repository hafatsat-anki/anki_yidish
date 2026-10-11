# Copyright (C) 2020 Hyun Woo Park
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

from aqt import gui_hooks
from aqt.utils import showInfo
from _shared_libs.haf_notifications import show_failure

from .uuid import addonUUID


def JSCallable(func):
    """ Decorator for js-callable python function """
    funcName = func.__name__
    msgPrefix = "pyfunc:%s:%s:" % (addonUUID(), funcName)

    def _onBridgeMessage(handled, message: str, context):
        if not message.startswith(msgPrefix):
            return handled

        # Need to json decode on the input
        try:
            argList = json.loads(message[len(msgPrefix) :])
        except json.JSONDecodeError as exc:
            show_failure("מען קען נישט אויספירן די פעולה אין דער הפסקה דערמאנונג. עפנט איבער דעם פענצטער און פרובירט נאכאמאל.", exc)

            return (True, {"error": "malformed message"})

        ret = func(*argList)
        # json encoding is not needed on return - already handled by Anki.
        return (True, {"error": None, "payload": ret})

    gui_hooks.webview_did_receive_js_message.append(_onBridgeMessage)

    # return function as-is. We don't need to modify them really
    return func
