# aiogovee

Python 3 /asyncio library for communication with Govee devices using their local API.

[![PyPI version](https://img.shields.io/pypi/v/aiogovee)](https://pypi.python.org/pypi/aiogovee)
[![PyPI version](https://img.shields.io/pypi/pyversions/aiogovee)](https://pypi.python.org/pypi/aiogovee)
[![license](https://img.shields.io/github/license/lumute/aiogovee)](https://github.com/Lumute/aiogovee/blob/master/LICENSE.txt)

This is my first time coding in Python, this library was written using François Wautier's [aiolifx](https://github.com/frawau/aiolifx) as sample / guide and adapted to communicate with the much simpler [Govee Local API](https://app-h5.govee.com/user-manual/wlan-guide?updateTime=181)


# Installation

This library is published on PyPi so:

     pip3 install aiogovee

or

     python3 -m pip install aiogovee


# How to control your Govee Devices

First, you need enable local API for each supported device: 

     - Open the Govee App
     - Click on the Device
     - Click on the Gear signs at the top right corner
     - Turn On "Lan Control"

![Enabling Lan Control](https://i.postimg.cc/x8ph7CzH/Screenshot-20220929-214827.png)

NOTE: If your don't see the "Lan Control" switch, most likely your device is not supported, you can check the Govee Local API documentation linked above to for the list of supported devices, they update this document as they add support for more devices. If your device is listed there then either your device does not have the latest firmware or its hardware version is too old and does not support this feature (I've sees reports of this from some users), at this point your best bet it to contact Govee Support about it, they are very responsive and helpful.

Once you have enabled "Lan Control" for your devices, you can test the library by using the example utility to fully manage your those Devices:

     python3 -m aiogovee

While the application is running, it will run discovery over each network interface available (including VLAN interfaces) every 5s (Library default is 180s but I configured it lower for this demo utility). Devices do not always respond to the discovery broadcast but they usually all show up after a couple of discovery attempts, just let the application run for a bit longer and hit enter to refresh the list of discovered devices.

At the moment the API is very limited, these are the only supported operations:

     - Get Status
     - Turn On/Off
     - Change Brightness (0-100)
     - Change Color (R) (G) (B)
     - Change ColorTemperature in Kelvin (0-9000)


# How to use the Library

Essentially, you create an object with at least 2 methods:

    - register
    - unregister

You then start the GoveeListener task in asyncio, passing the object created above, the IP of the desired network interface to run discovery on (you can start multiple GoveeListeners if you have multiple network interfaces to subnets with Govee devices) and the discovery interval in seconds (180s by default). It will register any new Device it finds.

Once a device is registered, there are attribute methods for any of the supported actions in the API.

The easiest way is to look at the __main__.py which is the demo utility included as an example of how to use the library.

# Thanks

Thanks to François Wautier, his aiolifx library which provided a great learning resource and base for this project.
