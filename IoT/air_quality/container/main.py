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
import signal
from air_quality import AirQuality
from logging_util import logger
from communications_utilities import IoTCommunications

com_utilities = IoTCommunications()
DEVICE_FAILURE_CHANNEL = os.environ['DEVICE_FAILURE_CHANNEL']
pid = 1


def air(client: object, quality: object, topic: str, interval: int) -> str:

    mqtt_error_count = 0

    while True:

        pm2, pm10 = quality.getAirQuality()

        payload = {
            "pm2": pm2,
            "pm10": pm10
        }

        payload = json.dumps(payload)
        result = client.publish(topic, payload)
        status = result[0]

        if status != 0:
            message = (f'data failed to publish to MQTT topic, status code: {status}')  # noqa: E501
            logger.debug(message)  # noqa: E501
            com_utilities.send_slack_alert(message, DEVICE_FAILURE_CHANNEL)
            mqtt_error_count += 1

            if mqtt_error_count == 20:
                # shut down due to a number of MQTT errors/broker is likely
                # down
                os.kill(pid, signal.SIGTERM)

        # given that this is a RAM constrained device, let's delete
        # everything and do some garbage collection, watching things
        # on htop the RAM usage was creeping upwards...
        del payload, result, status, pm2, pm10
        gc.collect()

        time.sleep(interval)


def main():

    # instantiate air quality class

    try:
        quality = AirQuality()
        logger.info('Air quality class instantiated successfully')

    except Exception as e:
        message = (f'Air Quality Class failed to instantiate, with error {e} shutting down...')  # noqa: E501
        logger.debug(message)
        com_utilities.send_slack_alert(message, DEVICE_FAILURE_CHANNEL)

    # Load parameters
    INTERVAL = int(os.environ['INTERVAL'])
    TOPIC = os.environ['TOPIC']

    # Load Environmental Variables
    MQTT_BROKER = os.environ['MQTT_BROKER']
    MQTT_USER = os.environ['MQTT_USER']
    MQTT_SECRET = os.environ['MQTT_SECRET']
    MQTT_PORT = int(os.environ['MQTT_PORT'])

    # get unique client ID
    clientID = com_utilities.getClientID()

    # get mqtt client
    client, code = com_utilities.mqttClient(clientID, MQTT_USER, MQTT_SECRET,
                                            MQTT_BROKER, MQTT_PORT)

    # start data monitoring
    try:
        air(client, quality, TOPIC, INTERVAL)

    finally:
        client.loop_stop()


if __name__ == '__main__':
    main()
