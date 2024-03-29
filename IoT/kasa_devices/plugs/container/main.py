# Markham Lee (C) 2023
# Productivity, Weather, Personal, et al dashboard:
# https://github.com/MarkhamLee/productivity-music-stocks-weather-IoT-dashboard
# Python script for receiving energy data from a TP Link
# Kasa TP25P4 smart plug and writing the data to InfluxDB.

import asyncio
import os
import json
import gc
from kasa import SmartPlug
from kasa_utilities import DeviceUtilities
from logging_util import logger


async def get_plug_data(client: object, topic: str,
                        device_ip: str, interval: int):

    try:
        dev = SmartPlug(device_ip)
        logger.info(f'Connected to Kasa smart plug at: {device_ip}')

    except Exception as e:
        logger.debug(f'device connection unsuccessful with error: {e}')

    while True:

        # poll device for update
        try:
            await dev.update()

        except Exception as e:
            logger.debug(f'connection error: {e}')

        # split out data

        payload = {
            "power_usage": dev.emeter_realtime.power,
            "voltage": dev.emeter_realtime.voltage,
            "current": dev.emeter_realtime.current,
            "device_id": dev.device_id
        }

        payload = json.dumps(payload)
        result = client.publish(topic, payload)
        status = result[0]

        if status != 0:
            logger.debug(f'data failed to publish to MQTT topic, status code:\
                          {status}')

        # clean up RAM, container metrics show RAM usage creeping up daily
        del payload, result, status
        gc.collect()

        # wait 30 seconds
        await asyncio.sleep(interval)  # Sleep some time between updates


def main():

    # instantiate utilities class
    deviceUtilities = DeviceUtilities()

    # Load operating parameters
    INTERVAL = int(os.environ['INTERVAL'])
    DEVICE_IP = os.environ['DEVICE_IP']
    TOPIC = os.environ['TOPIC']

    # Load connection variables
    MQTT_BROKER = os.environ['MQTT_BROKER']
    MQTT_USER = os.environ['MQTT_USER']
    MQTT_SECRET = os.environ['MQTT_SECRET']
    MQTT_PORT = int(os.environ['MQTT_PORT'])

    # get unique client ID
    clientID = deviceUtilities.getClientID()

    # get mqtt client
    client, code = deviceUtilities.mqttClient(clientID, MQTT_USER,
                                              MQTT_SECRET, MQTT_BROKER,
                                              MQTT_PORT)

    # start device monitoring
    try:
        asyncio.run(get_plug_data(client, TOPIC, DEVICE_IP, INTERVAL))

    finally:
        client.loop_stop()


if __name__ == "__main__":
    main()
