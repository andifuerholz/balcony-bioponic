# main.py
# Purpose: Initialize Arduino IoT Cloud client, register variables/callbacks,
# start background tasks (local time updater, DS18B20 manager, cycle-based LED),
# and run the client loop. Wi‑Fi and NTP are handled in boot.py.
#
# Notes:
# - cycles_circuit_1 (String) defines second marks within a minute (e.g. "5, 10, 20, 40, 50")
#   at which the LED turns ON for 2 seconds.
# - LED pin and polarity are configurable below.
# - All comments are in English as requested.

from machine import Pin
from time import sleep, ticks_ms, ticks_diff
import logging
import _thread

from arduino_iot_cloud import ArduinoCloudClient
from secrets import DEVICE_ID, CLOUD_PASSWORD
from time_zh import localtime_ch
from sensors_ds18b20 import DS18B20Manager

# -----------------------------
# LED configuration
# -----------------------------
LED_PIN = 48          # <- your board's LED pin
ACTIVE_LOW = False     # set to True if LED lights when output is 0, else False

def _make_led():
    """Create and return the LED Pin object."""
    p = Pin(LED_PIN, Pin.OUT)
    # Ensure LED starts OFF
    p.value(1 if ACTIVE_LOW else 0)
    return p

led_pin = _make_led()

def set_led(on: bool):
    """
    Set LED ON/OFF respecting polarity.
    Active-low boards: ON -> 0, OFF -> 1.
    """
    led_pin.value(0 if (on and ACTIVE_LOW) else (1 if (not on and ACTIVE_LOW) else (1 if on else 0)))

# -----------------------------
# Cloud callbacks and utilities
# -----------------------------

def onLedChange(client, value):
    """
    Cloud on_write callback for variable 'led_state'.
    Turns the LED on/off immediately.
    """
    set_led(bool(value))
    print("LED ON!" if value else "LED OFF!")

# State & parser for cycle seconds
_cycle_seconds = set()
_cycle_lock = _thread.allocate_lock()

def _parse_cycle_seconds(s: str):
    """
    Parse a CSV string like '5, 10, 20, 40, 50' into a set {5,10,20,40,50}.
    Ignores invalid entries and clamps to 0..59.
    """
    secs = set()
    if not s:
        return secs
    for part in s.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            val = int(part)
            if 0 <= val <= 59:
                secs.add(val)
        except:
            # ignore non-integer tokens
            pass
    return secs

def onCyclesChange(client, value):
    """
    Cloud on_write callback for 'cycles_circuit_1' (string).
    Expected format: comma-separated seconds within a minute, e.g. '5, 10, 20, 40, 50'.
    """
    global _cycle_seconds
    try:
        text = value if isinstance(value, str) else str(value)
        new_secs = _parse_cycle_seconds(text)
        with _cycle_lock:
            _cycle_seconds = new_secs
        print("Updated cycles_circuit_1 seconds:", sorted(new_secs))
    except Exception as e:
        print("cycles_circuit_1 parse error:", e)

# -----------------------------
# Background tasks (threads)
# -----------------------------

def time_update_task(client):
    """
    Background thread: update 'time_zh' every minute with local time (Europe/Zurich).
    """
    while True:
        try:
            t_local, _, _ = localtime_ch()
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(
                t_local[0], t_local[1], t_local[2], t_local[3], t_local[4]
            )
            client["time_zh"] = timestamp
            print("Updated time_zh:", timestamp)
        except Exception as e:
            print("Time thread error:", e)
        sleep(60)

def cycles_blink_task(client, duration_ms=2000, poll_ms=100):
    """
    Background loop: every poll_ms, check current local second; if it's in the configured
    set (cycles_circuit_1), turn LED on for duration_ms. Non-blocking timing.
    """
    led_active_until = 0
    last_fired_sec = -1

    while True:
        try:
            # Current local time (Europe/Zurich)
            t_local, _, _ = localtime_ch()
            sec = t_local[5]  # 0..59

            # Non-blocking OFF handling
            now = ticks_ms()
            if led_active_until and ticks_diff(led_active_until, now) <= 0:
                set_led(False)
                led_active_until = 0
                # print("LED auto-OFF")

            # Check configured seconds
            with _cycle_lock:
                active_now = sec in _cycle_seconds

            # Fire once per second
            if active_now and sec != last_fired_sec:
                set_led(True)
                led_active_until = now + duration_ms
                last_fired_sec = sec
                print("[cycles] Fired at second", sec, "for", duration_ms, "ms")

        except Exception as e:
            print("cycles_blink_task error:", e)

        sleep(poll_ms / 1000.0)

# -----------------------------
# Main entry point
# -----------------------------

if __name__ == "__main__":
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO
    )

    # Create Arduino IoT Cloud client (Wi‑Fi & NTP via boot.py)
    client = ArduinoCloudClient(
        device_id=DEVICE_ID,
        username=DEVICE_ID,
        password=CLOUD_PASSWORD
    )

    # Register cloud variables
    client.register('led_state', on_write=onLedChange)
    client.register('time_zh')                 # write-only timestamp
    client.register('air_temp')                # DS1820 'air'
    client.register('cycles_circuit_1', on_write=onCyclesChange)

    # Start background threads
    _thread.start_new_thread(time_update_task, (client,))

    manager = DS18B20Manager(client, pin=4, interval_s=2)
    _thread.start_new_thread(manager.loop, ())

    # Start cycle-based LED worker
    _thread.start_new_thread(cycles_blink_task, (client,))

    # Blocking cloud loop
    client.start()
