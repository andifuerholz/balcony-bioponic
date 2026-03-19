# main.py
# Purpose: Initialize Arduino IoT Cloud client, register variables/callbacks,
# start background tasks (local time updater, DS18B20 manager), and run the
# client loop. Wi‑Fi and NTP are handled in boot.py.

from machine import Pin
from time import sleep
import logging
import _thread
from arduino_iot_cloud import ArduinoCloudClient

# Secrets (provided locally; do NOT commit)
from secrets import DEVICE_ID, CLOUD_PASSWORD

# Local Zurich time util → returns (t_local, tz_name, tz_offset)
from time_zh import localtime_ch

# DS18B20 multi-sensor manager
from sensors_ds18b20 import DS18B20Manager

# Hardware: Onboard LED (ESP32)
led_pin = Pin(2, Pin.OUT)

def onLedChange(client, value):
    """
    Cloud on_write callback for variable 'led_state'.
    Turns the onboard LED on/off.
    """
    led_pin.value(1 if value else 0)
    print("LED ON!" if value else "LED OFF!")

def time_update_task(client):
    """
    Background thread: update 'time_zh' every minute with local time (Europe/Zurich).
    Note: Publishes only once per minute. Consider guarding with client.connected.
    """
    while True:
        try:
            t_local, _, _ = localtime_ch()
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(
                t_local[0], t_local[1], t_local[2], t_local[3], t_local[4]
            )
            # Optional: if not getattr(client, "connected", False): sleep(1); continue
            client["time_zh"] = timestamp
            print("Updated time_zh:", timestamp)
        except Exception as e:
            print("Time thread error:", e)
        sleep(60)

if __name__ == "__main__":
    # Configure root logger (MicroPython may ignore some advanced formatting)
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO
    )

    # Wi‑Fi & NTP are handled in boot.py

    # Create Arduino IoT Cloud client
    client = ArduinoCloudClient(
        device_id=DEVICE_ID,
        username=DEVICE_ID,
        password=CLOUD_PASSWORD
        # Optionally: ssl_params={'cadata': ARDUINO_CA}
    )

    # Register cloud variables
    client.register('led_state', on_write=onLedChange)
    client.register('time_zh')      # write-only timestamp
    client.register('air_temp')     # for sensor named 'air'
    # Optional: register additional named sensors
    # client.register('water_temp')
    # client.register('biofilter_temp')

    # Start background threads after client creation
    _thread.start_new_thread(time_update_task, (client,))

    manager = DS18B20Manager(client, pin=4, interval_s=2)
    _thread.start_new_thread(manager.loop, ())

    # Blocking cloud loop (keeps the client alive)
    client.start()
