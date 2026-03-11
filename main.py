# Import Library
from machine import Pin
from time import sleep
import network
import logging
from arduino_iot_cloud import ArduinoCloudClient

# Import Credential 
from secrets import WIFI_SSID
from secrets import WIFI_PASSWORD
from secrets import DEVICE_ID
from secrets import CLOUD_PASSWORD

# Pin Setup
led_pin = Pin(2, Pin.OUT)

# Callback Function
def onLedChange(client, value):
    if value:
        led_pin.value(1)
        print('LED ON!')
    else:
        led_pin.value(0)
        print('LED OFF!')

# Main Program
if __name__ == "__main__":
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO
    )
    
    # WiFi is already connected by boot.py → no wifi_connect() here

    client = ArduinoCloudClient(
        device_id=DEVICE_ID,
        username=DEVICE_ID,
        password=CLOUD_PASSWORD
    )
    client.register('led_state', on_write=onLedChange)
    client.start()
