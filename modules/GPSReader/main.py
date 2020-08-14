# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
import json
import pprint
from datetime import datetime
from datetime import timezone

from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

import pynmea2
import serial

import pyudev

# import ptvsd
# ptvsd.enable_attach(('192.168.8.103',  5678))

# for example GPS vendor and device ublox GPS receiver
GPS_DEVICE_VENDOR = '1546'
GPS_DEVICE_ID = '01a8'

def is_usb_serial(device, vid=None, pid=None):
    # Checks device to see if its a USB Serial device.
    # The caller already filters on the subsystem being 'tty'.
    # If serial_num or vendor is provided, then it will further check to
    # see if the serial number and vendor of the device also matches.

    #pprint.pprint(dict(device.properties))

    # cannot be right if no vendor id
    if 'ID_VENDOR' not in device.properties:
        return False
    # searcing for right vendor
    if vid is not None:
        if device.properties['ID_VENDOR_ID'] != vid:
            print(vid + ' not found  ' + device.properties['ID_VENDOR_ID'])
            return False

    if pid is not None:
        if device.properties['ID_MODEL_ID'] != pid:
            print('not found')
            return False
    return True

def list_devices(vid=None, pid=None):
    devs = []
    context = pyudev.Context()
    for device in context.list_devices(subsystem='tty'):
        if is_usb_serial(device, vid= vid,  pid = pid):
            devs.append(device.device_node)
    return devs

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception(
                "The sample requires python 3.7+. Current version of Python: %s" % sys.version)
        print("IoT Hub Client Module for Python: GPS reader")

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()
        # connect the client
        await module_client.connect()

        # define behavior for halting the application
        def stdin_listener():
            while True:
                try:
                    selection = input("Press Q to quit\n")
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        break
                except:
                    time.sleep(10)

        async def receiveGPS(module_client, ser):
            # ptvsd.break_into_debugger()
            gps_message_types = ["$GNRMC", "$GPRMC", "$GLRMC", "$GARMC"]

            while True:
                try: 
                    data = ser.readline().decode('ascii', errors='replace')
                    data = data.strip()

                    if len(data) > 6 and data[0:6] in gps_message_types:
                        gps_data = pynmea2.parse(data)
                    
                        msg = {
                            "latitude": gps_data.latitude,
                            "longitude": gps_data.longitude,
                            "lat_dir": gps_data.lat_dir,
                            "lon_dir": gps_data.lon_dir,
                            "speed": gps_data.spd_over_grnd,
                            "deviceId": os.environ["IOTEDGE_DEVICEID"],
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }

                        payload = Message(json.dumps(msg), content_encoding="utf-8", content_type="application/json")
                        payload.custom_properties["type"] = "location" # needed for routing message to event grid

                        await module_client.send_message_to_output(payload, "output1")
                        
                    await asyncio.sleep(60)

                except Exception as e:
                    print("GPS reader errored: %s" % e)
                    await asyncio.sleep(10)

        # define port for GPS USB module
        gps_port = "/dev/ttyGPS"
        GPS_PORTS = list_devices(GPS_DEVICE_VENDOR, GPS_DEVICE_ID)
        print(GPS_PORTS)
        if GPS_PORTS != []:
            print('GPS DEVICE FOUND')
            gps_port = GPS_PORTS[0] # select first device
        else:
            print('NO RIGHT GPS DEVICE FOUND')

        # GPS receiver
        gps_ser = serial.Serial(gps_port, baudrate=9600, timeout=0.5)

        # Schedule task for C2D Listener
        listeners = asyncio.gather(receiveGPS(module_client, gps_ser))
        print("The GPSreader is now waiting for messages. ")

        # Run the stdin listener in the event loop
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print("Unexpected error %s " % e)
        raise

if __name__ == "__main__":
    # If using Python 3.7 or above, you can use following code instead:
     asyncio.run(main())
