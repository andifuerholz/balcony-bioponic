# Import Library
from machine import Pin
from time import sleep
import network
import logging
import _thread
from arduino_iot_cloud import ArduinoCloudClient

# Import Credentials
from secrets import WIFI_SSID
from secrets import WIFI_PASSWORD
from secrets import DEVICE_ID
from secrets import CLOUD_PASSWORD

# Time (Zurich)
from time_zh import localtime_ch

# Pin Setup
led_pin = Pin(2, Pin.OUT)

# Callback for Cloud → ESP32
def onLedChange(client, value):
    if value:
        led_pin.value(1)
        print("LED ON!")
    else:
        led_pin.value(0)
        print("LED OFF!")

# Background task to send Zurich time every minute
def time_update_task():
    while True:
        try:
            t_local, _, _ = localtime_ch()
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(
                t_local[0], t_local[1], t_local[2],
                t_local[3], t_local[4]
            )
            client["time_zh"] = timestamp
            print("Updated time_zh:", timestamp)
        except Exception as e:
            print("Time thread error:", e)

        sleep(60)  # update every minute

# Main Program
if __name__ == "__main__":
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO
    )

    # WiFi is already connected by boot.py → no wifi_connect() here

    # Cloud Client
    client = ArduinoCloudClient(
        device_id=DEVICE_ID,
        username=DEVICE_ID,
        password=CLOUD_PASSWORD
    )

    # Register Cloud variables
    client.register('led_state', on_write=onLedChange)
    client.register('time_zh')   # write-only variable

    # Start background thread AFTER client exists
    _thread.start_new_thread(time_update_task, ())

    # Main cloud loop — blocks forever
    client.start()
