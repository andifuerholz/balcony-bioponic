# boot.py

import network
import logging
from time import sleep

from secrets import WIFI_SSID, WIFI_PASSWORD


def wifi_connect():
    if not WIFI_SSID or not WIFI_PASSWORD:
        raise Exception("Network not configured. Set SSID and password in secrets.py")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        logging.info("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        while not wlan.isconnected():
            sleep(0.5)

    logging.info(f"WiFi connected: {wlan.ifconfig()}")


# Run WiFi connection immediately at boot
wifi_connect()
