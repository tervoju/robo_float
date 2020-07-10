# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
import json
from datetime import datetime
from datetime import timezone

from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

import pynmea2
import serial

import ptvsd
ptvsd.enable_attach(('0.0.0.0',  5678))

gps_port = "/dev/ttyGPS"

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
            while True:
                try: 
                    await asyncio.sleep(60)

                    gps_data = None
                    found = False

                    while not found:
                        data = ser.readline()
                        if data[0:6] == "$GPRMC":
                            gps_data = data
                            found = True

                    try:
                        gps_data = pynmea2.parse(data)
                    except pynmea2.ParseError as e:
                        print('Parse error: {}'.format(e))
                        continue

                    data = {
                        "latitude": gps_data.latitude,
                        "longitude": gps_data.longitude,
                        "lat_dir": gps_data.lat_dir,
                        "lon_dir": gps_data.lon_dir,
                        "speed": gps_data.spd_over_grnd,
                        "deviceId": os.environ["IOTEDGE_DEVICEID"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    payload = Message(json.dumps(data), content_encoding="utf-8", content_type="application/json")
                    payload.custom_properties["type"] = "location" # needed for routing message to event grid
                    await module_client.send_message_to_output(payload, "output1")

                except Exception as e:
                    print("no GPS data available: %s" % e)
                    await asyncio.sleep(10)

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
