# Markham Lee (C) 2023 - 2024
# Productivity, Weather, Personal, et al dashboard:
# https://github.com/MarkhamLee/productivity-music-stocks-weather-IoT-dashboard
# This script retrieves air quality data from a Nova PM SDS011
# Air Quality sensor connected via USB and then sends the data off
# to a MQTT broker

import json
import time
import gc
import os
import requests
from air_quality import AirQuality
from logging_util import logger


def air(client: object, quality: object, topic: str, interval: int) -> str:

    error_count = 0
    ALERT_THRESHOLD = os.environ.get['ALERT_THRESHOLD']
    DEVICE_FAILURE_CHANNEL = os.environ['DEVICE_FAILURE_CHANNEL']
    NODE_DEVICE_ID = os.environ['DEVICE_ID_DATA']

    while True:

        try:
            # get air quality data
            pm2, pm10 = quality.getAirQuality()
            error_count = 0

        except Exception as e:
            error_count += 1
            logger.debug(f'device read error: {e}')
            if error_count == ALERT_THRESHOLD:
                message = (f'potential device failure on: {NODE_DEVICE_ID}, air quality sensor unreadable for {ALERT_THRESHOLD} consecutive attempts')  # noqa: E501
                logger.debug(message)
                send_slack_alert(message, DEVICE_FAILURE_CHANNEL)

        # round off air quality numbers
        pm2 = round(pm2, 2)
        pm10 = round(pm10, 2)

        payload = {
            "pm2": pm2,
            "pm10": pm10
        }

        payload = json.dumps(payload)
        result = client.publish(topic, payload)
        status = result[0]

        if status != 0:
            logger.debug(f'data failed to publish to MQTT topic, status code: {status}')  # noqa: E501

        # given that this is a RAM constrained device, let's delete
        # everything and do some garbage collection, watching things
        # on htop the RAM usage was creeping upwards...
        del payload, result, status, pm2, pm10
        gc.collect()

        time.sleep(interval)


# method for sending
def send_slack_alert(message: str, device_failure_channel):

    ALERT_ENDPOINT = os.environ['ALERT_ENDPOINT']
    payload = {
        "text": message,
        "slack_channel": device_failure_channel
    }

    headers = {'Content-type': 'application/json'}

    response = requests.post(ALERT_ENDPOINT, json=payload, headers=headers)
    logger.info(f'Device failure alert sent with code: {response.text}')


def main():

    # instantiate air quality class
    quality = AirQuality()

    # Load parameters
    INTERVAL = int(os.environ['INTERVAL'])
    TOPIC = os.environ['TOPIC']

    # Load Environmental Variables
    MQTT_BROKER = os.environ['MQTT_BROKER']
    MQTT_USER = os.environ['MQTT_USER']
    MQTT_SECRET = os.environ['MQTT_SECRET']
    MQTT_PORT = int(os.environ['MQTT_PORT'])

    # get unique client ID
    clientID = quality.getClientID()

    # get mqtt client
    client, code = quality.mqttClient(clientID, MQTT_USER, MQTT_SECRET,
                                      MQTT_BROKER, MQTT_PORT)

    # start data monitoring
    try:
        air(client, quality, TOPIC, INTERVAL)

    finally:
        client.loop_stop()


if __name__ == '__main__':
    main()
