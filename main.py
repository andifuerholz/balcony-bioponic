# main.py
# Purpose:
# Initialize Arduino IoT Cloud client, register variables/callbacks,
# start background tasks (combined local time + DS18B20 readings, cycle-based actuator control),
# and run the client loop. Wi‑Fi and NTP are handled in boot.py.
#
# Enhancements:
# - switchDuration_circuit_1 (seconds) from cloud controls pulse length
# - startHour / endHour (Time) define active day window for triggering


import logging
import _thread
from machine import I2C, Pin
import tankReeds
from config import (
    DS18B20_PIN,
    TIME_UPDATE_PERIOD_S,
    CYCLE_POLL_MS,
    I2C_SCL_PIN,
    I2C_SDA_PIN,
    RELAY1_PIN,
    RELAY2_PIN,
    RELAY3_PIN
)

from hw.relay import make_relay, set_relay
from cloud.client import create_client
from cloud.callbacks import (
    onCycles1Change, onCycles2Change,
    seconds_for_temp,
    onC1DurationChange,
    onC2DurationChange,
    onStartHourChange, onEndHourChange,
)
from tasks.time_task import time_and_temp_task
from tasks.cycles_control import cycles_control_task
from hw.sensors_sht20 import SHT20Manager

from state.runtime import (
    get_air_temp,
    get_c1_duration_s,
    get_c2_duration_s,
    get_active_window_minutes,
)

from tasks.lcd_task import lcd_task
from hw.lcd1602 import LCD1602, SN3193

def main():
    # Basic logging setup
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO,
    )
    

    # --- Hardware setup ---
    relay1 = make_relay(RELAY1_PIN)
    relay2 = make_relay(RELAY2_PIN)
    relay3 = make_relay(RELAY3_PIN)

    
    # I2C BUS ERZEUGEN
    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=100000)
    

    # Tank‑Level Modul damit verbinden
    tankReeds.init(i2c)
    

    # --- LCD local display ----
    devices = i2c.scan()
    print("I2C devices:", [hex(d) for d in devices])

    lcd = None

    if 0x3e in devices:
        try:
            lcd = LCD1602(i2c, 16, 2)
            backlight = SN3193(i2c)
            backlight.set_brightness(20)

            # Background LCD thread
            _thread.start_new_thread(lcd_task, (lcd,))
            print("LCD initialized")
        except Exception as e:
            print("LCD init failed:", e)
    else:
        print("LCD not found on I2C bus")
        
        # Background LCD thread
        _thread.start_new_thread(lcd_task, (lcd,))
    
    # --- Cloud client & variables registration ---
    # Expect the following variables to exist in Arduino Cloud:
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
        'time_zh': {},
        'air_temp': {},
        'air_humidity': {},
        'cycles_circuit_1': {'on_write': onCycles1Change},
        'cycles_circuit_2': {'on_write': onCycles2Change},
        'cycles_circuit_3': {'on_write': onCycles2Change},
        'switchDuration_circuit_1': {'on_write': onC1DurationChange},
        'switchDuration_circuit_2': {'on_write': onC2DurationChange},
        'switchDuration_circuit_3': {'on_write': onC2DurationChange},
        'startHour': {'on_write': onStartHourChange},
        'endHour':   {'on_write': onEndHourChange},
        # Read-only mirrors (strings like "0,15,30,45" when the effective set changes):
        'cycles_circuit_1_effective': {},
        'cycles_circuit_2_effective': {},
        'tankLevel': {},
    })
    
    # --- Sensors manager (SHT20 over I2C) ---
    manager = SHT20Manager(client, i2c)

    # --- Background tasks ---
    # 1) Low-frequency combined task: local time string + temperature readings
    _thread.start_new_thread(
        time_and_temp_task,
        (client, manager, TIME_UPDATE_PERIOD_S)
    )

    # 2) High-frequency cycle workers
    # Circuit 1: temperature-driven schedule *and* cloud-driven pulse duration + active window
    _thread.start_new_thread(
        cycles_control_task,
        (
            set_relay, relay1,
            CYCLE_POLL_MS,
            get_air_temp,
            lambda t: seconds_for_temp('c1', t),
            client, 'cycles_circuit_1_effective',
            get_c1_duration_s,
            get_active_window_minutes,
        )
    )

    # Circuit 2: temperature-driven schedule *and* cloud-driven pulse duration + active window
    _thread.start_new_thread(
        cycles_control_task,
        (
            set_relay, relay2,
            CYCLE_POLL_MS,
            get_air_temp,
            lambda t: seconds_for_temp('c2', t),
            client, 'cycles_circuit_2_effective',
            get_c2_duration_s,
            get_active_window_minutes,
        )
    )
    
    # Circuit 3 (air pump): temperature-driven schedule *and* cloud-driven pulse duration + active window
    _thread.start_new_thread(
    cycles_control_task,
        (
            set_relay, relay3,
            CYCLE_POLL_MS,
            get_air_temp,
            lambda t: seconds_for_temp('c3', t),
            client, 'cycles_circuit_3_effective',

            # ✅ MINUTEN -> ms
            lambda: get_c3_duration_min() * 60 * 1000,

            get_active_window_minutes,
        )
    )
    
    

    # --- Blocking cloud loop ---
    client.start()
    

if __name__ == "__main__":
    main()
