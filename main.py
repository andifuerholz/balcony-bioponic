# main.py
# Purpose:
# Initialize Arduino IoT Cloud client, register variables/callbacks,
# start background tasks (combined local time + DS18B20 readings, cycle-based LED),
# and run the client loop. Wi‑Fi and NTP are handled in boot.py.
#
# Enhancements:
# - switchDuration_circuit_1 (seconds) from cloud controls pulse length
# - startHour / endHour (Time) define active day window for triggering
# - cycles_blink_task reads duration + window via thread-safe getters


import logging
import _thread
from machine import I2C, Pin
import tankReeds
from config import (
    DS18B20_PIN,
    TIME_UPDATE_PERIOD_S,
    LED_CYCLE_POLL_MS,
    I2C_SCL_PIN,
    I2C_SDA_PIN,
)
from hw.led import make_led, set_led
from cloud.client import create_client
from cloud.callbacks import (
    onLedChange,
    onCycles1Change, onCycles2Change,
    seconds_for_temp,
    onC1DurationChange,
    onStartHourChange, onEndHourChange,
)
from tasks.time_task import time_and_temp_task
from tasks.cycles_led import cycles_blink_task
from sensors_ds18b20 import DS18B20Manager
from state.runtime import (
    get_air_temp,
    get_c1_duration_s,
    get_active_window_minutes,
)


def main():
    # Basic logging setup
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO,
    )

    # --- Hardware setup (LED as actuator placeholder) ---
    led_pin = make_led()  # respects ACTIVE_LOW/LED_PIN from config
    
    
    # I2C BUS ERZEUGEN
    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=100000)

    # Tank‑Level Modul damit verbinden
    tankReeds.init(i2c)

    # --- Cloud client & variables registration ---
    # Expect the following variables to exist in Arduino Cloud:
    # - led_state (bool; R/W)
    # - time_zh (string; R/O)
    # - air_temp (float; R/O) → published by sensor task
    # - cycles_circuit_1 (string; R/W) → profile text or legacy CSV seconds
    # - cycles_circuit_2 (string; R/W) → profile text or legacy CSV seconds
    # - switchDuration_circuit_1 (int/number; R/W) → pulse length (seconds)
    # - startHour (time; R/W) → active window start (local time)
    # - endHour   (time; R/W) → active window end   (local time)
    # - cycles_circuit_1_effective (string; R/O) → comma-separated active seconds
    # - cycles_circuit_2_effective (string; R/O) → comma-separated active seconds
    client = create_client({
        'led_state': {'on_write': lambda c, v: onLedChange(c, set_led, led_pin, v)},
        'time_zh': {},
        'air_temp': {},
        'cycles_circuit_1': {'on_write': onCycles1Change},
        'cycles_circuit_2': {'on_write': onCycles2Change},
        'switchDuration_circuit_1': {'on_write': onC1DurationChange},  # NEW
        'startHour': {'on_write': onStartHourChange},                   # NEW
        'endHour':   {'on_write': onEndHourChange},                     # NEW
        # Read-only mirrors (strings like "0,15,30,45" when the effective set changes):
        'cycles_circuit_1_effective': {},
        'cycles_circuit_2_effective': {},
        'tankLevel': {},
    })

    # --- Sensors manager (DS18B20) ---
    # Publishes named temps as {name}_temp (e.g., air_temp) and updates runtime state.
    manager = DS18B20Manager(client, pin=DS18B20_PIN)

    # --- Background tasks ---
    # 1) Low-frequency combined task: local time string + temperature readings
    _thread.start_new_thread(
        time_and_temp_task,
        (client, manager, TIME_UPDATE_PERIOD_S)
    )

    # 2) High-frequency cycle workers (development: both circuits use the same LED output)
    # Circuit 1: temperature-driven schedule *and* cloud-driven pulse duration + active window
    _thread.start_new_thread(
        cycles_blink_task,
        (
            set_led, led_pin,
            LED_CYCLE_POLL_MS,
            get_air_temp,                                 # temperature getter
            lambda t: seconds_for_temp('c1', t),          # selector for circuit 1
            client, 'cycles_circuit_1_effective',
            get_c1_duration_s,
            get_active_window_minutes,
        )
    )

    # Circuit 2: keep existing behavior (no window/duration override yet)
    _thread.start_new_thread(
        cycles_blink_task,
        (
            set_led, led_pin,
            LED_CYCLE_POLL_MS,
            get_air_temp,                                 # temperature getter
            lambda t: seconds_for_temp('c2', t),          # selector for circuit 2
            client, 'cycles_circuit_2_effective',
            None,                                         # duration -> default
            None,                                         # window -> always active
        )
    )

    # --- Blocking cloud loop ---
    client.start()

if __name__ == "__main__":
    main()

