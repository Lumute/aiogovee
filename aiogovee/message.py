# message.py
# Author: Gonzalo Parra

import json

class Message(object):
    def __init__(
        self,
        msg_type,
        cmd,
        data
    ):

        self.msg_type = msg_type  # String, type of Message
        self.cmd = cmd  # Command
        self.data = data  # tuples of ("label", value)

    def __str__(self):
        indent = "  "
        s = self.__class__.__name__ + "\n"
        s += indent + "MessageType: {}\n".format(self.msg_type)
        s += indent + "Data:"
        for attribute, value in self.data.items():
            s += "\n" + indent * 2 + "{}: {}".format(attribute, value)
            
        return s


def govee_message_to_json(msg):
    json_msg = {
        "msg": {
            "cmd": msg.cmd,
            "data": msg.data
        }
    }

    return json.dumps(json_msg)