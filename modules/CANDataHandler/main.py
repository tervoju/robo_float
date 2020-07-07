# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
import json
from functools import wraps, partial
import struct
from six.moves import input
import threading
from message_types import message_types
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run 

@async_wrap
def parse_can_message(message):
    if message["identifier"] in message_types:
        values = []
        # get every parameter value
        for param in message_types[message["identifier"]]["parameters"]:
            payload = {}
            # key is "name unit"
            # https://docs.microsoft.com/en-us/azure/time-series-insights/time-series-insights-update-how-to-shape-events
            key = "{name} ({unit})".format(name=param["name"], unit=param["unit"])
            # get start and end indices
            indices = [int(idx) for idx in param["bytes"].split(":")]

            # multiple bytes
            if len(indices) == 2:
                # select and reverse the data bytes
                value = ''.join(reversed(message["data"][indices[0]:indices[1]]))
                # convert the hex into actual proper value
                payload[key] = (int(value, 16) + param["offset"]) * param["resolution"]
            # single byte
            else:
                payload[key] = (int(message["data"][indices[0]], 16) + param["offset"]) * param["resolution"]

            values.append(payload)
        return values

    return None

async def main():
    try:
        if not sys.version >= "3.7":
            raise Exception("The sample requires python 3.7+. Current version of Python: %s" % sys.version)

        module_client = IoTHubModuleClient.create_from_edge_environment()
        await module_client.connect()

        # define behavior for receiving an input message on simulatedInput
        async def simulatedInput_listener(module_client):
            while True:
                try:
                    input_message = await module_client.receive_message_on_input("simulatedInput")  
                    print("getting simulated message")
                    data = json.loads(input_message.data.decode('utf8'))
                    values = await parse_can_message(data)
                    if values != None:
                        msg = [{
                            "deviceId": data["deviceId"],
                            "timestamp": data["timestamp"],
                            "series": values
                        }]
                    message = Message(json.dumps(msg), content_encoding="utf-8", content_type="application/json")
                    message.custom_properties["type"] = "time-series"
                except Exception as ex:
                    print("Unexpected error in isimulatedInput_listener: %s" % ex)
        
        # define behavior for receiving an input message on input1
        async def input1_listener(module_client):
            while True:
                input_message = await module_client.receive_message_on_input("input1")  # blocking call
                data = json.loads(input_message.data.decode('utf8'))
                values = await parse_can_message(data)
                if values != None:
                    msg = [{
                        "deviceId": data["deviceId"],
                        "timestamp": data["timestamp"],
                        "series": values
                    }]
                    message = Message(json.dumps(msg), content_encoding="utf-8", content_type="application/json")
                    message.custom_properties["type"] = "time-series"
                    await module_client.send_message_to_output(message, "output1")

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

        listeners = asyncio.gather(input1_listener(module_client), simulatedInput_listener(module_client))
        print ("CANDataHandler Waiting for messages.")

        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        await user_finished
        listeners.cancel()
        await module_client.disconnect()

    except Exception as e:
        print("Unexpected error %s " % e)
        raise

if __name__ == "__main__":
    asyncio.run(main())
