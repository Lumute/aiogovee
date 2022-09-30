# msgtypes.py
# Author: Gonzalo Parra


from .message import Message
import json

##### DEVICE MESSAGES #####


class ScanRequest(Message):
    def __init__(
        self,
    ):
        data={"account_topic":"reserve"}
        super(ScanRequest, self).__init__(
            "ScanRequest",
            "scan",
            data,
        )
 

class ScanResponse(Message):
    def __init__(
        self,
        data,
    ):
        self.deviceId = data["device"]
        self.sku = data["sku"]
        self.ip = data["ip"]
        self.bleVersionHard = data["bleVersionHard"]
        self.bleVersionSoft = data["bleVersionSoft"]
        self.wifiVersionHard = data["wifiVersionHard"]
        self.wifiVersionSoft = data["wifiVersionSoft"]
        super(ScanResponse, self).__init__(
            "ScanResponse",
            "scan",
            data,
        )


class OnOffControl(Message):
    def __init__(
        self,
        onOff,
    ):
        data = {"value":onOff}
        super(OnOffControl, self).__init__(
            "OnOffControl",
            "turn",
            data,
        )


class LightBrightness(Message):
    def __init__(
        self,
        brightness,
    ):
        data = {"value":brightness}
        super(LightBrightness, self).__init__(
            "LightBrightness",
            "brightness",
             data,
       )


class DeviceStatusQuery(Message):
    def __init__(
        self,
    ):
        data={}
        super(DeviceStatusQuery, self).__init__(
            "DeviceStatusQuery",
            "devStatus",
            data,
        )


class DeviceStatusResponse(Message):
    def __init__(
        self,
        data,
    ):
        self.onOff = str_onoff(data["onOff"])
        self.brightness = data["brightness"]
        self.rgbColor = data["color"]
        self.colorTemInKelvin = data["colorTemInKelvin"]
        super(DeviceStatusResponse, self).__init__(
            "DeviceStatusResponse",
            "devStatus",
             data,
       )


class ColorColorTemperature(Message):
    def __init__(
        self,
        rgbColor,
        colorTemInKelvin,
    ):
        data={"color":rgbColor,"colorTemInKelvin":colorTemInKelvin}
        super(ColorColorTemperature, self).__init__(
            "ColorColorTemperature",
            "colorwc",
            data,
        )


def datagram_to_govee_message(datagram):

    message = json.loads(datagram)

    govee_message = None
    if message["msg"]["cmd"] == 'scan':
        govee_message = ScanResponse(message["msg"]["data"])
    elif message["msg"]["cmd"] == 'devStatus':
        govee_message = DeviceStatusResponse(message["msg"]["data"])
    return govee_message


ONOFF_MAP = {1: "On", 0: "Off"}

def str_onoff(key):
    string_representation = "Unknown"
    if key == 1:
        string_representation = "On"
    elif key == 0:
        string_representation = "Off"
    return string_representation