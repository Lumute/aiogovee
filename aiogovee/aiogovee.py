# This application is a bridge for communication with Govee devices using their local API 
#
# It Containds code from MIT licensed aiolifx
# 
#    Copyright (c) 2016 François Wautier
#    Copyright (c) 2022 Michael Farrell <micolous+git@gmail.com>
#
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#    of the Software, and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in all copies
#    or substantial portions of the Software.
#
# Copyright (c) 2022 Gonzalo Parra <gaparra@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import asyncio as aio
import random, datetime, socket, ifaddr
from .msgtypes import *
from .message import govee_message_to_json

LISTEN_IP = "0.0.0.0"
UDP_LISTEN_PORT = 4002
UDP_BROADCAST_IP = "239.255.255.250"
UDP_BROADCAST_PORT = 4001
UDP_DEVICECONTROL_PORT = 4003
DEFAULT_TIMEOUT = 0.5  # How long to wait for a response
DEFAULT_ATTEMPTS = 1  # How many time should we try to send to the device
DISCOVERY_INTERVAL = 180
DISCOVERY_STEP = 5


class Device(aio.DatagramProtocol):
    """Connection to a given Govee device.
    :param loop: The asyncio loop being used
    :type loop: asyncio.AbstractEventLoop
    :param: deviceId: The device Govee ID 71:2b:C5:39:32:26:15:34
    :type deviceId: string
    :param ip_addr: The devie IP address
    :type ip_addr: string
    :param port: The port used by the unicast connection
    :type port: into
    :param parent: Parent object with register/unregister methods
    :type parent: object
    :returns: an asyncio DatagramProtocol to handle communication with the device
    :rtype: DatagramProtocol
    """

    def __init__(self, loop, deviceId, sku, ip_addr, parent=None):
        self.loop = loop
        self.deviceId = deviceId
        self.sku = sku
        self.ip_addr = ip_addr
        self.parent = parent
        self.registered = False
        self.retry_count = DEFAULT_ATTEMPTS
        self.timeout = DEFAULT_TIMEOUT
        self.unregister_timeout = DEFAULT_TIMEOUT
        self.transport = None
        self.task = None
        # And the rest
        self.bleVersionHard = None
        self.bleVersionSoft = None
        self.wifiVersionHard = None
        self.wifiVersionSoft = None
        self.onOff = None
        self.brightness = None
        self.rgbColor = None
        self.colorTemInKelvin = None
        self.lastmsg = datetime.datetime.now()


    #
    #                            Protocol Methods
    #

    def connection_made(self, transport):
        """Method run when the connection to the device is established"""
        self.transport = transport
        self.register()


    def register(self):
        """Proxy method to register the device with the parent."""
        if not self.registered:
            self.registered = True
            if self.parent:
                self.parent.register(self)


    def unregister(self):
        """Proxy method to unregister the device with the parent."""
        if self.registered:
            # Only if we have not received any message recently.
            if (
                datetime.datetime.now()
                - datetime.timedelta(seconds=self.unregister_timeout)
                > self.lastmsg
            ):
                self.registered = False
                if self.parent:
                    self.parent.unregister(self)


    def cleanup(self):
        """Method to call to cleanly terminate the connection to the device."""
        if self.transport:
            self.transport.close()
            self.transport = None
        if self.task:
            self.task.cancel()
            self.task = None


    #
    #                            Workflow Methods
    #

    async def try_sending(self, msg, num_repeats):
        """Coroutine used to send message to the device when no response is needed.
        :param msg: Message to send
        :type msg: aiogovee.
        :param num_repeats: number of times the message is to be sent.
        :returns: The coroutine that can be scheduled to run
        :rtype: coroutine
        """
        if num_repeats is None:
            num_repeats = self.retry_count
        sent_msg_count = 0
        sleep_interval = 0.05
        while sent_msg_count < num_repeats:
            if self.transport:
                payload = govee_message_to_json(msg).encode('utf-8')
                self.transport.sendto(payload)
            sent_msg_count += 1
            await aio.sleep(
                sleep_interval
            )  # Max num of messages device can handle is 20 per second.


    #  Don't wait for Responses, just send the same message repeatedly as fast as possible
    def send_and_forget(
        self, msg, num_repeats=None
    ):
        """Method used to send message to the device when no response is needed.
        :param msg: The message to send
        :type msg: aiogovee.Message
        :param num_repeats: Number of times the message is to be sent.
        :type num_repeats: int
        :returns: Always True
        :rtype: bool
        """
        xx = self.loop.create_task(self.try_sending(msg, num_repeats))
        return True


    #
    #                            Attribute Methods
    #

    def resp_discovery(self, response):
        """Default callback for get_status"""
        self.ip = response.ip
        self.bleVersionHard = response.bleVersionHard
        self.bleVersionSoft = response.bleVersionSoft
        self.wifiVersionHard = response.wifiVersionHard
        self.wifiVersionSoft = response.wifiVersionSoft


    def resp_devstatus(self, response):
        """Default callback for get_status"""
        self.onOff = response.onOff
        self.brightness = response.brightness
        self.rgbColor = response.rgbColor
        self.colorTemInKelvin = response.colorTemInKelvin


    def turn_onoff(self, onOff):
        """Convenience method to turn a device On/Off
        This method will send a turn message to the device.
            :param value: The new state
            :type value: str/bool/int
            :returns: None
            :rtype: None
        """
        on = [True, 1, "on", "On", "ON"]
        off = [False, 0, "off", "OFF"]
        if onOff in on:
            msg = OnOffControl(1)
        elif onOff in off:
            msg = OnOffControl(0)

        response = self.send_and_forget(msg)


    def get_devstatus(self):
        """Convenience method to refresh a device status
        This method will send a devStatus query to the device.
            :returns: None
            :rtype: None
        """
        msg = DeviceStatusQuery()

        response = self.send_and_forget(msg)


    def set_brightness(self, brightness):
        """Convenience method to change a device's brightness
        This method will send a brightness message to the device.
            :param value: The new brightness
            :type value: int 0-100
            :returns: None
            :rtype: None
        """
        msg = LightBrightness(brightness)

        response = self.send_and_forget(msg)


    def set_rgbColor(self, rgbColor):
        """Convenience method to change a device's brightness
        This method will send a brightness message to the device.
            :param value: The new brightness
            :type value: int 0-100
            :returns: None
            :rtype: None
        """
        msg = ColorColorTemperature(rgbColor, 0)

        response = self.send_and_forget(msg)


    def set_colorTemperature(self, colorTemInKelvin):
        """Convenience method to change a device's brightness
        This method will send a brightness message to the device.
            :param value: The new brightness
            :type value: int 0-100
            :returns: None
            :rtype: None
        """

        rgbColor = {'r': 0, 'g': 0, 'b': 0}
        msg = ColorColorTemperature(rgbColor, colorTemInKelvin)

        response = self.send_and_forget(msg)


class GoveeListener(aio.DatagramProtocol):
    """UDP Listener for Govee Local API Protocol
    The object will listen for messages sent from Govee Devices (Discovery or Status responses)
    It will also bradcast a discovery message every discovery_interval second. Sometimes it
    may be necessary to speed up this process. So discovery uses self.discovery_countdown, initially
    set to discovery_interval. It will then sleep for discovery_step seconds and decrease discovery_countdown
    by that amount. When discovery_countdown is <= 0, discovery is triggered. To hasten the process, one can set
    discovery_countdown = 0.
        :param parent: Parent object to register/unregister discovered device
        :type parent: object
        :param loop: The asyncio loop being used
        :type loop: asyncio.AbstractEventLoop
        :param discovery_interval: How often, in seconds, to broadcast a discovery messages
        :type discovery_interval: int
        :param discovery_step: How often, in seconds, will the discovery process check if it is time to broadcast
        :type discovery_step: int
        :returns: an asyncio DatagramProtocol to handle communication with the device
        :rtype: DatagramProtocol
    """

    def __init__(
        self,
        loop,
        parent=None,
        discovery_interval=DISCOVERY_INTERVAL,
        discovery_step=DISCOVERY_STEP,
        listen_ip=LISTEN_IP,
        listen_port=UDP_LISTEN_PORT,
        broadcast_ip=UDP_BROADCAST_IP,
        broadcast_port=UDP_BROADCAST_PORT,
        devicecontrol_port=UDP_DEVICECONTROL_PORT,
    ):
        self.devices = {}  # Known devices indexed by deviceId
        self.devicesByIP = {}  # Known deviceId's indexed by IP Address
        self.parent = parent  # Where to register new devices
        self.transport = None
        self.loop = loop
        self.task = None
        self.source_id = random.randint(0, (2 ** 32) - 1)
        self.discovery_interval = discovery_interval
        self.discovery_step = discovery_step
        self.discovery_countdown = 0
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.broadcast_ip = broadcast_ip
        self.broadcast_port = broadcast_port
        self.devicecontrol_port = devicecontrol_port

    def start(self):
        """Start discovery task."""

        coro = self.loop.create_datagram_endpoint(
            lambda: self, local_addr=(self.listen_ip, self.listen_port)
        )

        self.task = self.loop.create_task(coro)
        return self.task

    def connection_made(self, transport):
        """Method run when the UDP broadcast server is started"""
        # print('started')
        self.transport = transport
        sock = self.transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.loop.call_soon(self.discover)

    def datagram_received(self, data, addr):
        """Method run when data is received from the devices
        This method will parse the data according to the Govee protocol.
        If a new device is found, the device will be created and started and
        a DatagramProtocol and will be registered with the parent.
            :param data: raw data
            :type data: bytestring
            :param addr: sender IP address 2-tuple for IPv4, 4-tuple for IPv6
            :type addr: tuple
        """

        response = datagram_to_govee_message(data)
        dev_ip_addr = addr[0]

        # If the message received is a Discovery Response
        if (type(response) == ScanResponse):

            deviceId = response.deviceId
            sku = response.sku
            self.devicesByIP[dev_ip_addr] = deviceId

            if deviceId in self.devices:
                # rediscovered
                device = self.devices[deviceId]

                device.resp_discovery(response)
                
                # nothing else to do
                if device.registered:
                    return

                device.cleanup()
            else:

                # newly discovered
                device = Device(self.loop, deviceId, sku, dev_ip_addr, parent=self)
                device.resp_discovery(response)
                self.devices[deviceId] = device

            coro = self.loop.create_datagram_endpoint(
                lambda: device, family=socket.AF_INET, remote_addr=(dev_ip_addr, self.devicecontrol_port),
            )

            device.task = self.loop.create_task(coro)

        # If the message received is a Device Status reponse, finds the devive who sent the response by its IP address an processes it
        elif (type(response) == DeviceStatusResponse):
            deviceId = self.devicesByIP[dev_ip_addr]
            device = self.devices[deviceId]

            device.resp_devstatus(response)

        else:
            print("aborting")
            return

    def discover(self):
        """Method to send a discovery message"""
        if self.transport:
            if self.discovery_countdown <= 0:
                self.discovery_countdown = self.discovery_interval
                msg = ScanRequest()
                payload = govee_message_to_json(msg).encode('utf-8')
                self.transport.sendto(payload, (self.broadcast_ip, self.broadcast_port))
            else:
                self.discovery_countdown -= self.discovery_step
            self.loop.call_later(self.discovery_step, self.discover)

    def register(self, adevice):
        """Proxy method to register the device with the parent."""
        if self.parent:
            self.parent.register(adevice)

    def unregister(self, adevice):
        """Proxy method to unregister the device with the parent."""
        if self.parent:
            self.parent.unregister(adevice)

    def cleanup(self):
        """Method to call to cleanly terminate the connection to the device."""
        if self.transport:
            self.transport.close()
            self.transport = None
        if self.task:
            self.task.cancel()
            self.task = None
        for device in self.devices.values():
            device.cleanup()
        self.devices = {}
