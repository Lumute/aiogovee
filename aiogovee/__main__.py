# This application is an example on how to use aiogovee
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


import sys
import asyncio as aio

import aiogovee
import argparse
import ifaddr


# Simple device control from console
class devices:
    """A simple class with a register and unregister methods"""

    def __init__(self):
        self.devices = []
        self.doi = None  # Device of interest
        self.doiNeedsStatusRefresh = False  # Device of Interest Status needs to be Refreshed

    def register(self, device):
        global opts
        self.devices.append(device)
        self.devices.sort(key=lambda x: x.deviceId)
        if opts.extra:
            device.register_callback(lambda y: print("Unexpected message: %s" % str(y)))
 
    def unregister(self, device):
        idx = 0
        for x in list([y.deviceId for y in self.device]):
            if x == device.deviceId:
                del device.device[idx]
                break
            idx += 1


async def amain():
    global MyDevices

    discovery_interval = 5
    firs_discovery_await = .5
    command_await = .3

    # Avoid any asyncio error message
    await aio.sleep(0)

    MyDevices = devices()
    loop = aio.get_event_loop()

    adapters = ifaddr.get_adapters()
    ips = [
        ip.ip
        for adapter in ifaddr.get_adapters()
        for ip in adapter.ips
        if ip.is_IPv4 and ip.ip != '127.0.0.1'
    ]
    discoveries = {}
    for ip in ips:
        discoveries[ip] = aiogovee.GoveeListener(loop, MyDevices, discovery_interval=discovery_interval, listen_ip=ip)

    try:
        for ip in ips:
            discoveries[ip].start()
        await aio.sleep(firs_discovery_await)

        selection = ''
        invalidSelection = False
        while selection != 'x':
            MyDevices.devices.sort(key=lambda x: x.deviceId)
            lov = [x for x in selection.split(" ") if x != ""]
            
            if lov:
                if not any(char.isdigit() for char in lov[0]):
                    print("\nERROR: Not a valid selection.")
                    invalidSelection = True             

                if MyDevices.doi and not invalidSelection:
                    try:
                        if int(lov[0]) == 0:
                            MyDevices.doi = None
                        elif int(lov[0]) == 1:
                            MyDevices.doiNeedsStatusRefresh = True
                        elif int(lov[0]) == 2:
                            MyDevices.doi.turn_onoff("On")
                            await aio.sleep(command_await)
                            MyDevices.doiNeedsStatusRefresh = True
                        elif int(lov[0]) == 3:
                            MyDevices.doi.turn_onoff("off")
                            await aio.sleep(command_await)
                            MyDevices.doiNeedsStatusRefresh = True
                        elif int(lov[0]) == 4:
                            if len(lov) == 2: 
                                MyDevices.doi.set_brightness(int(lov[1]))
                                await aio.sleep(command_await)
                                MyDevices.doiNeedsStatusRefresh = True
                            else:
                                print("\nERROR: This option also requires entering the brightness value, for example: 4 99")
                                invalidSelection = True
                        elif int(lov[0]) == 5:
                            if len(lov) == 4: 
                                rgbColor = {'r':int(lov[1]),'g':int(lov[2]),'b':int(lov[3])}
                                await aio.sleep(command_await)
                                MyDevices.doi.set_rgbColor(rgbColor)
                                MyDevices.doiNeedsStatusRefresh = True
                            else:
                                print("\nERROR: This option also requires entering the RGB values, for example: 5 254 254 276")
                                invalidSelection = True
                        else:
                            print("\nERROR: Not a valid selection.")
                            invalidSelection = True               
                    except Exception as e:
                        print(e)
                elif not invalidSelection:
                    try:
                        if int(lov[0]) > 0:
                            if int(lov[0]) <= len(MyDevices.devices):
                                MyDevices.doi = MyDevices.devices[int(lov[0]) - 1]
                                MyDevices.doiNeedsStatusRefresh = True
                            else:
                                print("\nERROR: Not a valid selection.")
                                invalidSelection = True               
                    except Exception as e:
                        print(e)

            if MyDevices.doiNeedsStatusRefresh:
                MyDevices.doi.get_devstatus()
                await aio.sleep(command_await)   
                MyDevices.doiNeedsStatusRefresh = False

            if MyDevices.doi:
                print("\nSelect Function for Device: {}".format(MyDevices.doi.deviceId))

                print("\n                    SKU: {}".format(MyDevices.doi.sku))
                print("             IP Address: {}".format(MyDevices.doi.ip_addr))
                print("   Hardware BLE Version: {}".format(MyDevices.doi.bleVersionHard))
                print("   Software BLE Version: {}".format(MyDevices.doi.bleVersionSoft))
                print("  Hardware WiFi Version: {}".format(MyDevices.doi.wifiVersionHard))
                print("  Software WiFi Version: {}".format(MyDevices.doi.wifiVersionSoft))
                print("                  State: {}".format(MyDevices.doi.onOff))
                print("             Brightness: {}".format(MyDevices.doi.brightness))
                print("          color (R,G,B): {}".format(MyDevices.doi.rgbColor))
                print("  Color Temperature (K): {}".format(MyDevices.doi.colorTemInKelvin))
                print("  Last message received: {}".format(MyDevices.doi.lastmsg))

                print("\n\n\t[1]\tRefresh Status")
                print("\t[2]\tTurn On")
                print("\t[3]\tTurn Off")
                print("\t[4]\tChange Brightness (0-100)")
                print("\t[5]\tChange Color (R) (G) (B)")
                print("\t[6]\tChange ColorTemperature in Kelvin (0-9000)")

                print("\n\t[0]\tBack to device selection")
                print("\t[x]\tQuit")
            else:
                idx = 1
                print("\nSelect Device:\n")

                for x in MyDevices.devices:
                    print("\t[{}]\t{} - {} - {}".format(idx, x.ip_addr, x.deviceId, x.sku))
                    idx += 1

                print("\n\t[Enter]\tRefresh discovered deviced")
                print("\t[x]\tQuit")
            await aio.sleep(.1)
            selection = input("\nYour choice: ")
            invalidSelection = False
            
    finally:
        for ip in ips:
            discoveries[ip].cleanup()
        loop.remove_reader(sys.stdin)


def main():
    """Main entry point."""
    global opts

    parser = argparse.ArgumentParser(
        description="Track and interact with Govee Devices."
    )
    parser.add_argument(
        "-x",
        "--extra",
        action="store_true",
        default=False,
        help="Print unexpected messages.",
    )
    try:
        opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))
    try:
        aio.run(amain())
    except KeyboardInterrupt:
        print("\nExiting at user's request.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()