# !/usr/bin/env python
# Markham 2023 - 2024
# Productivity, Weather, Personal, et al dashboard:
# https://github.com/MarkhamLee/productivity-music-stocks-weather-IoT-dashboard
# Python script for receiving Air Quality data from
# a Nova PM SDS011 air quality sensor and sending it to InfluxDB
# via an MQTT Broker
import serial
import os
import sys
from logging_util import logger
from communications_utilities import IoTCommunications


class AirQuality:

    def __init__(self):

        # create variables
        self.defineVariables()
        self.connect_to_sensor()

    def defineVariables(self):

        self.pm2Bytes = 2
        self.pm10Bytes = 4
        self.deviceID = 6
        self.error_count = 0
        self.NODE_DEVICE_ID = os.environ['DEVICE_ID_DATA']
        self.DEVICE_FAILURE_CHANNEL = os.environ['DEVICE_FAILURE_CHANNEL']

        self.com_utilities = IoTCommunications()

    def connect_to_sensor(self):

        USB = os.environ['USB_ADDRESS']

        try:
            self.serialConnection = serial.Serial(USB)
            logger.info(f'connected to Nova PM SDS011 Air Quality sensor at: {USB}')  # noqa: E501

        except Exception as e:
            message = (f'USB device connection failure for {self.NODE_DEVICE_ID} on {USB} with error message: {e}')  # noqa: E501
            logger.debug(message)
            self.com_utilities.send_slack_alert(message,
                                                self.DEVICE_FAILURE_CHANNEL)

    def getAirQuality(self):

        try:

            message = self.serialConnection.read(10)

            # outputs have to be scaled by 0.1 to properly capture the
            # sensor's precision as it returns integers that are actually
            # decimals I.e. 15 is really 1.5

            pm2 = round((self.parse_value(message, self.pm2Bytes) * 0.1), 4)
            pm10 = round((self.parse_value(message, self.pm10Bytes) * 0.1), 4)
            return pm2, pm10

        except Exception as e:
            message = (f'Potential Nova PM SDS011 device error/failure on: {self.NODE_DEVICE_ID}, with error {e}, exiting....')  # noqa: E501
            self.com_utilities.send_slack_alert(message,
                                                self.DEVICE_FAILURE_CHANNEL)
            logger.debug(message)
            # just shutdown if the device isn't reachable, as the fix probably
            # requires physical intervention.
            sys.exit()

    def parse_value(self, message, start_byte, num_bytes=2,
                    byte_order='little', scale=None):

        """Returns a number from a sequence of bytes."""
        value = message[start_byte: start_byte + num_bytes]
        value = int.from_bytes(value, byteorder=byte_order)
        value = value * scale if scale else value

        return value
