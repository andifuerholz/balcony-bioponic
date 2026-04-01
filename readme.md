## Table of Contents
- [Project description](#project-description)
- #hardware
- #software
  - [Core Watering Logic](#core-watering-logic)
  - #framework-description
  - [Files](#files)
    - [boot.py](#bootpy)
    - [config.py](#configpy)
    - #mainpy
    - #cloud
    - [tasks/](#tasks)
    - #hw
    - [state/](#state)
    - #sensors_ds18b20py
    - [time_zh.py](#time_zhpy)
    - #secretspy
  - [Arduino Cloud Setup](#arduino-cloud-setup)
    - [Cloud Variables](#cloud-variables)
    - #dashboard
- [Implementation Strategy](#implementation-strategy)
  - #preliminary-remarks
  - #automation-implementation
  - [Learning Goals](#learning-goals)
- #appendix
  - [ESP32 Wiring](#esp32-wiring)
  - [Connecting a DS18B20 Sensor](#connecting-a-ds18b20-sensor)
  - [Minimal MicroPython Test Script](#minimal-micropython-test-script)
  - [Tank swimmer (OpenSCAD)](#tank-swimmer-openscad)

## Project description

Project in development...hang on...

## Hardware

The bioponics system is built from a set of components aiming for a balcony-scale food production. The hardware includes:

- **Two cultivation channels**, each equipped with six holes for net pots used to grow lettuces and other leafy greens.
- **Two planting containers** for larger crops such as tomatoes or chayote.
- **One 15 litres water tank** containing the nutrient solution.
- **A Biofilter** with cocos a clay balls which creates and maintains the microbial colonies needed to break down organic fertilizers so that nutrients become continuously available to the plants.
- **One water pump** responsible for circulating the nutrient solution through the system.
- **Two water control valves** to regulate flow distribution between the cultivation channels and the planting containers.
- **One air pump** which supplies oxygen to keep the microbial communities active so they can efficiently break down organic nutrients
- **One Arduino Nano ESP32 S3**, serving as the central microcontroller for automation and pump control.
- **Additional electronic components**, including relays, voltage converters, a power supply, and supporting circuitry.
- **One outdoor temperature sensor (DS18B20)** to measure ambient temperature.
- **One water temperature sensor (DS18B20)** to monitor the nutrient solution temperature.
- **A custom-built water level sensing system**, consisting of six reed switches positioned at different heights.
- **An auxiliary tank with its own pump** to refill or stabilize the main reservoir when required.

## Software
### Core Watering Logic

The software controls the watering cycles within a defined daily time window (e.g., from 09:00 to 21:00).  
Within this active period, the pump of each watering circuit is triggered according to a schedule that specifies **at which minutes of the hour** the pump should run.

The configuration is independent for:

- the two watering circuits
- different ranges of outdoor temperature

Example:

If the outdoor temperature is **26 °C**, then at minutes **0, 20, and 40** of each hour, the pump of **circuit 1** is activated for **10 seconds**.

This logic allows the system to adapt its watering frequency to the current temperature conditions.

### Framework description

The software running on the Arduino Nano ESP32 is based on MicroPython.  
The system uses several components, libraries and external services:

- **MicroPython firmware on the ESP32**, installed using the  
  [Arduino MicroPython Installer](https://labs.arduino.cc/en/labs/micropython-installer)

- **Arduino Cloud**, which provides a graphical user interface (GUI) for monitoring and interaction.

- **Arduino IoT Cloud Python Library**, used to communicate with the Arduino Cloud:  
  https://github.com/arduino/arduino-iot-cloud-py

- A detailed setup guide and example for connecting the ESP32 with MicroPython to Arduino IoT Cloud is available here:  
  *How to Connect the ESP32 MicroPython to Arduino IoT Cloud*  
  https://forum.arduino.cc/t/how-to-connect-the-esp32-micropython-to-arduino-iot-cloud/1234953

### Files

📄 boot.py<br>
📄 config.py<br>
📄 secrets.py<br>
📄 main.py<br>
📄 sensors_ds18b20.py<br>
📄 time_zh.py<br>
📄 tankReeds.py<br>
📁 cloud/<br>
	📄 cloud/client.py<br>
	📄 cloud/callbacks.py<br>
📁 tasks/<br>
	📄 tasks/time_task.py<br>
	📄 tasks/cycles_led.py<br>
📁 hw/<br>
	📄 hw/led.py<br>
	📄 hw/pins.py<br>
📁 state/<br>
	📄 state/runtime.py<br>
📁 lib/<br>
	📄 ...<br>
	📄 ...<br>

#### `boot.py`

```python
# boot.py
# Purpose: Connect to Wi‑Fi at boot and sync UTC time (for TLS).
# Notes:
# - Expects WIFI_LIST in secrets.py: [{'ssid': '...', 'pwd': '...'}, ...]
# - Must run before creating any TLS client (Arduino IoT Cloud, etc.)

import network, logging
from time import sleep, ticks_ms, ticks_diff
from secrets import WIFI_LIST  # list of dicts: {"ssid": "...", "pwd": "..."}

CONNECT_TIMEOUT_MS = 5_000   # timeout per SSID
RETRY_DELAY_S = 0.4          # poll interval during connection attempts

def wifi_connect():
    """
    Try connecting to the configured Wi‑Fi networks in order.
    Returns: network.WLAN instance when connected.
    Raises: Exception if no configured Wi‑Fi is reachable.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    for idx, cred in enumerate(WIFI_LIST, 1):
        ssid = cred.get("ssid")
        pwd = cred.get("pwd")
        if not ssid or not pwd:
            continue

        logging.info("[{}/{}] Trying SSID '{}' …".format(idx, len(WIFI_LIST), ssid))
        try:
            wlan.connect(ssid, pwd)
        except Exception as e:
            logging.warning("connect() error: {}".format(e))
            continue

        t0 = ticks_ms()
        # IMPORTANT: use '<', not HTML-escaped '&lt;'
        while (not wlan.isconnected()) and (ticks_diff(ticks_ms(), t0) < CONNECT_TIMEOUT_MS):
            sleep(RETRY_DELAY_S)

        if wlan.isconnected():
            ip, mask, gw, dns = wlan.ifconfig()
            logging.info("Wi‑Fi connected to '{}' → {} / gw {}".format(ssid, ip, gw))
            return wlan

        # Ensure a clean state before the next attempt
        try:
            wlan.disconnect()
        except Exception:
            pass
        sleep(0.5)

    raise Exception("No configured Wi‑Fi reachable. Check WIFI_LIST in secrets.py")

# 1) Connect to Wi‑Fi at boot
wlan = wifi_connect()

# 2) Sync UTC time (needed for TLS cert validation)
try:
    from time_zh import sync_ntp
    sync_ntp()  # should internally call ntptime.settime() and handle retries
except Exception as e:
    # Do not hard-fail; cloud/TLS may still reconnect later.
    logging.warning("NTP sync failed: {}".format(e))

```

#### `secrets.py`

```python
# secrets.py

WIFI_LIST = [
    {"ssid": "[enter 1st SSID here]",   "pwd": "[enter 1st pw here]"},   # 1. Choice
    {"ssid": "[enter 2nd SSID here]", "pwd": "[enter 2nd pw here]"},   # 2. Choice
    {"ssid": "[enter 3rd SSID here]", "pwd": "[enter 3rd pw here]"},   # 3. Choice
]

DEVICE_ID = b"[enter ID here[" # b=Byte-String
CLOUD_PASSWORD = b[enter pw here]"  # b=Byte-String
```

#### `config.py`

```python
# config.py
# Central configuration for pins, timing, and DS18B20 sensor mapping/calibration.
# All comments are in English as requested.

# ---------------------------------
# Hardware pins & timing parameters
# ---------------------------------
LED_PIN = 48
ACTIVE_LOW = False
DS18B20_PIN = 4

# Task periods / polling (seconds or milliseconds as noted)
TIME_UPDATE_PERIOD_S = 1
LED_CYCLE_POLL_MS = 100

# Default pulse length used only as fallback; cloud overrides it (circuit 1).
# NOTE: Now expressed in *seconds* for conceptual alignment with cloud variable.
DEFAULT_C1_SWITCH_DURATION_S = 10  # used until 'switchDuration_circuit_1' arrives

# Default active day window used until cloud values arrive (local time Europe/Zurich)
DEFAULT_START_HOUR = 7   # 07:00
DEFAULT_END_HOUR   = 21  # 21:00

# Safety clamps for watering pulse duration (in seconds)
MIN_SWITCH_DURATION_S = 1
MAX_SWITCH_DURATION_S = 300  # 5 minutes

# ---------------------------------
# DS18B20 mapping & validation
# ---------------------------------
# DS18B20 ROM → friendly name
# IMPORTANT: Keys must be *bytes* (not bytearray; no HTML-escaped content).
SENSOR_MAP = {
    b'\x28\x8e\x01\x48\xf6\x75\x3c\xde': 'air',  # Main ambient sensor
    # Add more sensors as needed:
    # b'\x28\xaa\xbb\xcc\xdd\xee\xff\x01': 'water',
    # b'\x28\x11\x22\x33\x44\x55\x66\x77': 'biofilter',
}

# Optional per-sensor calibration offsets in °C
OFFSETS = {
    'air': 0.5,
    # 'water': -0.2,
    # 'biofilter': +0.1,
}

# Plausibility limits in °C
# Values outside this range will be discarded.
TEMP_MIN = -20.0
TEMP_MAX = 60.0

```
### state/runtime.py
```python
# state/runtime.py
# Thread-safe runtime state for ambient temperature, watering pulse duration,
# and the active day window (start/end time). Values are updated via cloud callbacks.

import _thread
from config import (
    DEFAULT_C1_SWITCH_DURATION_S,
    MIN_SWITCH_DURATION_S, MAX_SWITCH_DURATION_S,
    DEFAULT_START_HOUR, DEFAULT_END_HOUR
)

# --- Ambient temperature (°C) -------------------------------------------------
_air_temp = None
_air_lock = _thread.allocate_lock()

def set_air_temp(value: float):
    """Update last known ambient temperature (°C)."""
    global _air_temp
    with _air_lock:
        _air_temp = float(value)

def get_air_temp(default=None):
    """Get last known ambient temperature (°C) or default if unknown."""
    with _air_lock:
        return _air_temp if _air_temp is not None else default

# --- Circuit 1: watering pulse duration (seconds) -----------------------------
_c1_duration_s = DEFAULT_C1_SWITCH_DURATION_S
_c1_lock = _thread.allocate_lock()

def set_c1_duration_s(v_s: int):
    """
    Set watering pulse duration for circuit 1 in *seconds*.
    Value is clamped to [MIN_SWITCH_DURATION_S .. MAX_SWITCH_DURATION_S].
    """
    global _c1_duration_s
    try:
        v = int(v_s)
    except Exception:
        return
    v = max(MIN_SWITCH_DURATION_S, min(v, MAX_SWITCH_DURATION_S))
    with _c1_lock:
        _c1_duration_s = v

def get_c1_duration_s() -> int:
    """Get watering pulse duration for circuit 1 (seconds)."""
    with _c1_lock:
        return int(_c1_duration_s)

def get_c1_duration_ms() -> int:
    """Convenience: circuit 1 duration in milliseconds."""
    with _c1_lock:
        return int(_c1_duration_s) * 1000

# --- Active day window (start/end minutes after midnight) ---------------------
# Stored as minutes since midnight [0..1439]. Default 07:00..21:00.
_start_minutes = DEFAULT_START_HOUR * 60
_end_minutes   = DEFAULT_END_HOUR   * 60
_win_lock = _thread.allocate_lock()

def set_active_window_minutes(start_m: int, end_m: int):
    """
    Update active window as minutes since midnight (0..1439).
    Values are normalized into the valid range; no constraint that start < end:
    if start > end, the window crosses midnight (e.g., 22:00..06:00).
    """
    global _start_minutes, _end_minutes
    try:
        s = int(start_m) % (24 * 60)
        e = int(end_m)   % (24 * 60)
    except Exception:
        return
    with _win_lock:
        _start_minutes, _end_minutes = s, e

def get_active_window_minutes():
    """Return (start_minutes, end_minutes), both in [0..1439]."""
    with _win_lock:
        return _start_minutes, _end_minutes
```

#### `main.py`

```python
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
```
#### sensors_ds18b20.py

```python
# sensors_ds18b20.py
# Purpose: Read one or multiple DS18B20 sensors on a OneWire bus and publish
# named values to the Arduino IoT Cloud as individual variables (name_temp).
# Adds read_and_publish_once() for coordinated low-frequency tasks.

from machine import Pin
import onewire, ds18x20, time
from config import SENSOR_MAP, TEMP_MIN, TEMP_MAX, OFFSETS

SENSOR_PIN_DEFAULT = 4  # DQ on GPIO4, ~4.7–5 kΩ pull-up to 3V3

def hex_rom(b):
    """Return hex-string representation of a ROM ID (bytes)."""
    return ':'.join(f'{x:02X}' for x in b)

class DS18B20Manager:
    """
    Manage multiple DS18B20 sensors on a OneWire bus and publish named readings
    to the Arduino IoT Cloud as {name}_temp variables.
    """
    def __init__(self, client, pin=SENSOR_PIN_DEFAULT, interval_s=2):
        self.client = client
        self.interval_s = interval_s
        self.ow = onewire.OneWire(Pin(pin))
        self.ds = ds18x20.DS18X20(self.ow)

        # Scan at init and store ROMs as immutable bytes
        scan = self.ds.scan() or []
        self.roms = [bytes(r) for r in scan]
        if not self.roms:
            print("⚠️ No DS18B20 sensors found.")
        else:
            print("DS18B20 ROMs (hex):", [hex_rom(r) for r in self.roms])

    def _read_all(self):
        """
        Convert all sensors, read them, filter implausible raw values,
        and apply per-sensor offsets. Unknown sensors are returned with HEX keys.
        """
        vals = {}
        if not self.roms:
            return vals
        try:
            self.ds.convert_temp()
        except Exception as e:
            print("convert_temp error:", e)
            return vals

        # 12-bit resolution → 750 ms conversion time
        time.sleep_ms(750)

        for rom in self.roms:
            try:
                t = self.ds.read_temp(rom)
            except Exception as e:
                print("read_temp error:", e)
                continue

            # Raw plausibility check
            if t is None or not (TEMP_MIN <= t <= TEMP_MAX):
                continue

            name = SENSOR_MAP.get(rom)  # bytes key expected
            if name:
                t = t + OFFSETS.get(name, 0.0)
                vals[name] = round(t, 2)
            else:
                # Unknown sensor: log with hex key (not published in loop/once)
                vals[hex_rom(rom)] = round(t, 2)
        return vals

    def read_and_publish_once(self):
        """Perform one full DS18B20 read cycle and publish named sensors as {name}_temp."""
        vals = self._read_all()
        if not vals:
            return
        for name, value in vals.items():
            if not isinstance(name, str):
                continue  # skip hex keys (unknown sensors)
            var_name = f"{name}_temp"
            try:
                self.client[var_name] = value
            except Exception as e:
                print(f"Publish {var_name} error:", e)

            # Update runtime temperature state for 'air'
            if name == 'air':
                try:
                    from state.runtime import set_air_temp
                    set_air_temp(value)
                except Exception:
                    pass

    def loop(self):
        """
        Endless loop (legacy): read values and publish to {name}_temp.
        Kept for compatibility; not used in the combined time+temp approach.
        """
        while True:
            vals = self._read_all()
            if vals:
                for name, value in vals.items():
                    if not isinstance(name, str):
                        continue
                    var_name = f"{name}_temp"
                    try:
                        self.client[var_name] = value
                    except Exception as e:
                        print(f"Publish {var_name} error:", e)
            time.sleep(self.interval_s)

```
#### tasks/time_task.py
```python
# tasks/time_task.py
# Purpose:
#   Low-frequency task that (1) publishes a human-readable local time string
#   and (2) reads DS18B20 sensors once per cycle and publishes their values.

import time
from time_zh import localtime_ch
from tankReeds import get_fill_percent


def _fmt_time_str(t_local, tz_str):
    # t_local: (Y, M, D, hh, mm, ss, wd, yd)
    Y, M, D, hh, mm, ss = (
        t_local[0],
        t_local[1],
        t_local[2],
        t_local[3],
        t_local[4],
        t_local[5],
    )
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} {}".format(
        Y, M, D, hh, mm, ss, tz_str
    )


def time_and_temp_task(client, ds18_manager, period_s=1):
    """
    Publishes:
      - time_zh: local date-time string with TZ (CET/CEST)
      - {name}_temp: per-sensor temp readings via DS18B20Manager.read_and_publish_once()
    """

    # First immediate publish
    try:
        t_local, _, tz = localtime_ch()
        client["time_zh"] = _fmt_time_str(t_local, tz)
    except Exception:
        pass

    while True:
        try:
            # 1) Local time (Europe/Zurich)
            t_local, _, tz = localtime_ch()
            client["time_zh"] = _fmt_time_str(t_local, tz)

            # 2) DS18B20 readings
            ds18_manager.read_and_publish_once()

            # 3) TankLevel readings
            lvl = get_fill_percent()
            if lvl is not None and lvl >= 0:
                client["tankLevel"] = lvl

        except Exception as e:
            print("time_and_temp_task error:", e)

        time.sleep(period_s if period_s and period_s > 0 else 1)
```

####  tasks/cycles_led.py

```python
# tasks/cycles_led.py
# Cyclic worker for trigger-on-second watering logic with:
# - dynamic pulse duration (seconds) via getter
# - active day window (start/end minutes) via getter
# - publication of the effective seconds set (optional)

from time import sleep, ticks_ms, ticks_diff
from time_zh import localtime_ch

def _minutes_since_midnight(local_tuple):
    """Return minutes since midnight from localtime tuple (Y,M,D,h,m,s,wd,yd)."""
    h, m = local_tuple[3], local_tuple[4]
    return (h * 60 + m) % (24 * 60)

def _within_window(now_m, start_m, end_m):
    """
    Check if now_m (minutes since midnight) lies within [start_m .. end_m),
    supporting windows that cross midnight (start > end).
    """
    if start_m == end_m:
        # Degenerate: treat as closed window (nothing active)
        return False
    if start_m < end_m:
        return start_m <= now_m < end_m
    # Cross-midnight window, e.g., 22:00..06:00
    return (now_m >= start_m) or (now_m < end_m)

def cycles_blink_task(set_led_fn,
                      led_pin,
                      poll_ms=100,
                      get_temp_fn=None,
                      select_secs_fn=None,
                      client=None,
                      effective_var_name=None,
                      get_duration_s_fn=None,
                      get_window_minutes_fn=None):
    """
    Poll current local second; if within the active window and configured, turn LED ON
    for the configured duration (seconds) on each trigger second. Non-blocking pulses.

    Args:
      set_led_fn: function(pin, on_bool) -> None
      led_pin: Pin object for the LED/valve
      poll_ms: loop poll interval
      get_temp_fn: () -> float|None, returns current ambient temp in °C
      select_secs_fn: (temp_c: float|None) -> set[int], seconds 0..59 for given temp
      client: ArduinoCloudClient to publish effective set changes (optional)
      effective_var_name: cloud variable name (string) to publish comma-separated seconds
      get_duration_s_fn: () -> int, watering pulse length in seconds
      get_window_minutes_fn: () -> (start_m, end_m), minutes since midnight
    """
    led_active_until = 0
    last_fired_sec = -1
    last_effective = None

    while True:
        try:
            t_local, _, _ = localtime_ch()
            sec = t_local[5]  # 0..59
            now_ms = ticks_ms()
            now_m = _minutes_since_midnight(t_local)

            # Turn LED off when the pulse duration has elapsed
            if led_active_until and ticks_diff(led_active_until, now_ms) <= 0:
                set_led_fn(led_pin, False)
                led_active_until = 0

            # Determine active seconds set for current temperature
            active_secs = set()
            if select_secs_fn:
                temp_c = get_temp_fn() if get_temp_fn else None
                active_secs = select_secs_fn(temp_c)

            # Optionally publish the effective set whenever it changes
            if client and effective_var_name is not None:
                eff_tuple = tuple(sorted(active_secs))
                if eff_tuple != last_effective:
                    try:
                        client[effective_var_name] = ','.join(map(str, eff_tuple))
                    except Exception:
                        pass
                    last_effective = eff_tuple

            # Window check
            in_window = True
            if get_window_minutes_fn:
                try:
                    s_m, e_m = get_window_minutes_fn()
                    in_window = _within_window(now_m, s_m, e_m)
                except Exception:
                    in_window = True  # fail-open

            if not in_window:
                # Ensure LED is OFF outside the window
                if led_active_until:
                    set_led_fn(led_pin, False)
                    led_active_until = 0
                sleep(poll_ms / 1000.0)
                continue

            # Resolve duration (seconds -> ms)
            duration_ms = 2000  # default fallback
            if get_duration_s_fn:
                try:
                    duration_ms = int(get_duration_s_fn()) * 1000
                except Exception:
                    pass

            # Fire once per matching second
            if (sec in active_secs) and (sec != last_fired_sec):
                set_led_fn(led_pin, True)
                led_active_until = now_ms + duration_ms
                last_fired_sec = sec
                print("[cycles] Fired at second", sec, "for", duration_ms, "ms")

        except Exception as e:
            print("cycles_blink_task error:", e)

        sleep(poll_ms / 1000.0)

```

#### cloud/callbacks.py

```python
# cloud/callbacks.py
# Cloud variable on_write handlers and profile parsing utilities.
# Adds handlers for:
# - switchDuration_circuit_1 (seconds, integer)
# - startHour / endHour (Arduino Cloud "Time" type; robust parsing)

import _thread

# Per-circuit state for seconds selection
_state = {
    'c1': {'profiles': None, 'secs': set()},
    'c2': {'profiles': None, 'secs': set()},
}
_lock = _thread.allocate_lock()

# ---------- Utility: CSV "seconds" parser ----------
def parse_cycle_seconds(s: str):
    """Parse CSV '5, 10, 20' -> {5,10,20}; clamp to 0..59; ignore junk."""
    secs = set()
    if not s:
        return secs
    for part in str(s).split(','):
        part = part.strip()
        if not part:
            continue
        try:
            v = int(part)
            if 0 <= v <= 59:
                secs.add(v)
        except Exception:
            pass
    return secs

def _parse_profile_line(line: str):
    """
    One line '20°C: 0, 20, 40' or '25: 0,15,30,45'
    Returns (threshold:int, seconds:set[int]) or None on parse failure.
    """
    if ':' not in line:
        return None
    left, right = line.split(':', 1)
    left = left.strip().replace('°C', '').replace('°', '')
    try:
        thr = int(left)
    except Exception:
        return None
    secs = parse_cycle_seconds(right)
    return thr, secs

def parse_temp_profiles(text: str):
    """
    Multi-line string with threshold profiles.
    Returns sorted list of (threshold, seconds) by ascending threshold.
    If parse fails, returns None.
    """
    if not isinstance(text, str):
        text = str(text)
    items = []
    # Be tolerant: allow either newline or ';' as separators
    for chunk in text.replace(';', '\n').splitlines():
        line = chunk.strip()
        if not line:
            continue
        item = _parse_profile_line(line)
        if item:
            items.append(item)
    if not items:
        return None
    # Deduplicate thresholds: keep last occurrence of each threshold
    dedup = {}
    for thr, secs in items:
        dedup[thr] = set(secs)
    return sorted(((thr, dedup[thr]) for thr in dedup), key=lambda x: x[0])

def _update_circuit_from_text(c_key: str, text: str):
    prof = parse_temp_profiles(text)
    with _lock:
        if prof:
            _state[c_key]['profiles'] = prof
            _state[c_key]['secs'] = set()  # clear legacy
            print(f"[{c_key}] thresholds:", [thr for thr, _ in prof])
        else:
            _state[c_key]['profiles'] = None
            _state[c_key]['secs'] = parse_cycle_seconds(text)
            print(f"[{c_key}] legacy seconds:", sorted(_state[c_key]['secs']))

def onLedChange(client, set_led_fn, led_pin, value):
    """on_write for 'led_state'."""
    try:
        set_led_fn(led_pin, bool(value))
        print("LED ON!" if value else "LED OFF!")
    except Exception as e:
        print("onLedChange error:", e)

def onCycles1Change(client, value):
    """on_write for 'cycles_circuit_1' (string)."""
    _update_circuit_from_text('c1', value if isinstance(value, str) else str(value))

def onCycles2Change(client, value):
    """on_write for 'cycles_circuit_2' (string)."""
    _update_circuit_from_text('c2', value if isinstance(value, str) else str(value))

def seconds_for_temp(c_key: str, temp_c):
    """
    Return active seconds for given temperature for the given circuit key ('c1'/'c2').
    Rule: use the profile with the highest threshold <= temp_c.
    If no profile is configured, fall back to the legacy seconds set.
    If temp is None, use the lowest-threshold profile (if present).
    """
    with _lock:
        prof = _state[c_key]['profiles']
        if not prof:
            return set(_state[c_key]['secs'])
        if temp_c is None:
            return set(prof[0][1]) if prof else set()
        active = set()
        for thr, secs in prof:
            if temp_c >= thr:
                active = secs
            else:
                break
        return set(active)

# ---------- New: Cloud handlers for duration & time window ----------

def _parse_time_var_to_minutes(value):
    """
    Parse Arduino Cloud 'Time' variable into minutes since midnight [0..1439].
    Accepts:
      - "HH:MM" or "HH:MM:SS" strings
      - mapping with keys {'hour','minute'(,'second')}
      - tuple/list (h, m) or (h, m, s)
    Returns int minutes or None on failure.
    """
    h = m = None
    # String form
    if isinstance(value, str):
        parts = value.strip().split(':')
        if len(parts) >= 2:
            try:
                h = int(parts[0]); m = int(parts[1])
            except Exception:
                return None
    # Mapping form
    elif hasattr(value, 'get'):
        try:
            h = int(value.get('hour'))
            m = int(value.get('minute'))
        except Exception:
            return None
    # Sequence form
    elif isinstance(value, (tuple, list)):
        try:
            h = int(value[0]); m = int(value[1])
        except Exception:
            return None
    else:
        return None

    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return (h * 60 + m) % (24 * 60)

def onC1DurationChange(client, value):
    """
    on_write for 'switchDuration_circuit_1' (seconds, integer).
    Clamped in state layer.
    """
    try:
        from state.runtime import set_c1_duration_s
        set_c1_duration_s(int(value))
        print(f"[c1] switch duration set to {int(value)} s")
    except Exception as e:
        print("onC1DurationChange error:", e)

def onStartHourChange(client, value):
    """
    on_write for 'startHour' (Arduino Cloud Time).
    """
    try:
        from state.runtime import get_active_window_minutes, set_active_window_minutes
        start_m = _parse_time_var_to_minutes(value)
        if start_m is None:
            print("onStartHourChange: invalid time payload:", value)
            return
        _, end_m = get_active_window_minutes()
        set_active_window_minutes(start_m, end_m)
        print(f"[window] start set to {start_m//60:02d}:{start_m%60:02d}")
    except Exception as e:
        print("onStartHourChange error:", e)

def onEndHourChange(client, value):
    """
    on_write for 'endHour' (Arduino Cloud Time).
    """
    try:
        from state.runtime import get_active_window_minutes, set_active_window_minutes
        end_m = _parse_time_var_to_minutes(value)
        if end_m is None:
            print("onEndHourChange: invalid time payload:", value)
            return
        start_m, _ = get_active_window_minutes()
        set_active_window_minutes(start_m, end_m)
        print(f"[window] end set to {end_m//60:02d}:{end_m%60:02d}")
    except Exception as e:
        print("onEndHourChange error:", e)

```

#### cloud/client.py
```python
# cloud/client.py
from arduino_iot_cloud import ArduinoCloudClient
from secrets import DEVICE_ID, CLOUD_PASSWORD

def create_client(register_map: dict):
    """
    Create and return a configured ArduinoCloudClient.

    register_map: dict of variable_name -> kwargs for register(), e.g.:
      {
        'led_state': {'on_write': some_fn},
        'time_zh': {},
        ...
      }
    """
    client = ArduinoCloudClient(
        device_id=DEVICE_ID,
        username=DEVICE_ID,     # Arduino IoT Cloud uses deviceId as username for token auth
        password=CLOUD_PASSWORD
    )
    for var, kwargs in register_map.items():
        client.register(var, **kwargs)
    return client

```

#### hw/led.py
```python
# hw/led.py
from machine import Pin
from config import LED_PIN, ACTIVE_LOW

def make_led():
    """Create and return the LED Pin object, OFF by default."""
    p = Pin(LED_PIN, Pin.OUT)
    p.value(1 if ACTIVE_LOW else 0)
    return p

def set_led(pin, on: bool):
    """Set LED ON/OFF respecting polarity."""
    if ACTIVE_LOW:
        pin.value(0 if on else 1)
    else:
        pin.value(1 if on else 0)

```

#### tankReeds.py
```python
# tankReeds.py
# Water level sensing using PCF8574T

from config import PCF8574_ADDR

_i2c = None
_last_valid = None


def init(i2c):
    """Initialize module with shared I2C bus."""
    global _i2c
    _i2c = i2c


def _read_raw():
    """Read raw byte from PCF8574T. Returns None on error."""
    global _i2c
    if _i2c is None:
        return None
    try:
        return _i2c.readfrom(PCF8574_ADDR, 1)[0]
    except Exception:
        return None


def get_closed_reeds():
    """Return list of reed channels (0..5) that are closed; None on read error."""
    raw = _read_raw()
    if raw is None:
        return None
    return [pin for pin in range(6) if ((raw >> pin) & 1) == 0]


def get_fill_percent():
    """
    Convert closed reed channels to tank fill percent (0..100).
    Returns last valid value if no valid reading is available.
    -1 means: do not publish.
    """
    global _last_valid

    reeds = get_closed_reeds()
    if reeds is None:
        return _last_valid

    if len(reeds) == 0:
        return _last_valid

    level = sum(reeds) / len(reeds)
    percent = (level / 5) * 100
    rounded = int(round(percent / 10) * 10)

    _last_valid = rounded
    return rounded
```

### Arduino Cloud Setup
#### Cloud Variables
- time_zh: stored local time
- dayHourActive: Start hour with watering (e.g. 07:00)
- dayHourInactive:End hour stop watering (e.g. 21:00)
- AirTemp: Air temperature
- AirTempAvg: Air temperatur 10 min. Average
- ...

#### Dashboard
...

## Implementation Strategy

### Preliminary Remarks
Core parts of the system were used for two years — with a simple timer — before implementing this automation work. The main drivers were that high temperatures and strong sunlight caused some damage, especially to the lettuce.

### Automation Implementation
1. Getting the ESP32 running with MicroPython, Wi-Fi, and LED control  
2. Continuously reading temperature sensor(s) and update arduino cloud variables and dashboard
3. Implement low frequent thread for temperature values and higher frequent thread for checking time schedule of watering
4. Associate temperature ranges to different watering schedules  
5. Measuring the water level in the main water tank and controlling a pump from the auxiliary tank to refill the main tank  
6. ...

### Learning Goals
1. Understanding how to set up and run the basic hardware and software components  
2. Learning how to design an appropriate control structure (~ threads) for reading sensors and controlling actuators  
3. Understanding how to integrate real‑world constraints (timing, temperature thresholds, water levels


## Appendix
### ESP32 Wiring
![Arduino Nano ESP32 wiring](https://github.com/andifuerholz/balcony-bioponic/blob/bc93deddbc6b00784411bc56c6c973a75ff1a4b9/img/Arduino%20Nano%20ESP32%20connection.jpg?raw=true)

#### Connecting a DS18B20 Temperature Sensor to the Arduino Nano ESP32

#### Getting ROMs
```python
import onewire, ds18x20
from machine import Pin
ow = onewire.OneWire(Pin(4))     # Bus-Pin
ds = ds18x20.DS18X20(ow)
print("Gefundene ROMs:", ds.scan())
```


The **DS18B20** is a digital temperature sensor that communicates via the **OneWire bus**. It requires only one data pin on the Arduino Nano ESP32 (ESP32‑S3).

#### 🔌 Wiring Overview

| DS18B20 Pin | Arduino Nano ESP32 Pin | Description |
|-------------|-------------------------|-------------|
| **VDD**     | **3V3**                 | Power supply |
| **GND**     | **GND**                 | Ground |
| **DQ**      | **GPIO 4 / A3 ~D20**              | OneWire data line |

##### 📐 Pull‑Up Resistor

Add a **4.7 kΩ resistor between DQ and 3V3**.

The DS18B20 requires this pull‑up for a stable HIGH level on the OneWire bus.  
For very short wires (<10 cm, 1 sensor) it may work temporarily without it,  
but stable operation requires the resistor.

### 🧪 Minimal MicroPython Test Script

```python
from machine import Pin
import onewire, ds18x20, time

SENSOR_PIN = 4

ow = onewire.OneWire(Pin(SENSOR_PIN))
ds = ds18x20.DS18X20(ow)

roms = ds.scan()
print("Detected sensors:", roms)

while True:
    ds.convert_temp()
    time.sleep_ms(750)
    for r in roms:
        print("Temperature:", ds.read_temp(r), "°C")
    time.sleep(5)

```
### Water Level Sensing Subsystem (PCF8574T + Reed Switches)

#### Overview

The main tank contains a **vertical float with six embedded magnets**, each positioned at a fixed height.  
Along the tank wall, **six reed switches** are mounted at corresponding levels.

A **PCF8574T I/O expander** reads the reed switches via I²C, providing a simple and robust way to measure the tank fill level.

- **Channel 0 = lowest water level**  
- **Channel 5 = highest water level**  
- Reeds are **normally open**  
- A reed closes (logic **0**) when the float’s magnet is at its height  
- Up to **two sensors can be closed simultaneously**, representing the float being between two levels  

The system converts reed states into a **0–100% fill level**, rounded to **10%** steps.

---

#### System Diagram & Interpretation

Reed Sensor Subsystem Architecture

```
              (Top of Tank – 100%)
                 ┌──────────────────────────┐
                 │  Level 5 ──── Reed (CH5) ├─────┐
                 ├──────────────────────────┤     │
                 │  Level 4 ──── Reed (CH4) ├──┐  │
                 ├──────────────────────────┤  │  │
                 │  Level 3 ──── Reed (CH3) ├─┐│  │
Float with       ├──────────────────────────┤ ││  │
magnets          │  Level 2 ──── Reed (CH2) ├┐││  │
moves up/down →  ├──────────────────────────┤│││  │
                 │  Level 1 ──── Reed (CH1) ├┘││  │
                 ├──────────────────────────┤ ││  │
                 │  Level 0 ──── Reed (CH0) ├─┘│  │
                 └──────────────────────────┘   │ │
                                                │ │
PCF8574T Input Pins 0..5  <─────────────────────┘ │
                                                │
SDA (GPIO6)  <──────────────────────────────────┘
SCL (GPIO5)
```

Example Interpretation

| Closed reeds | Level (avg) | Percent | Rounded | Output |
|--------------|-------------|---------|---------|---------|
| `{}`         | —           | —       | —       | **−1** |
| `{0}`        | 0           | 0%      | 0%      | 0 |
| `{2}`        | 2           | 40%     | 40%     | 40 |
| `{3,4}`      | 3.5         | 70%     | 70%     | 70 |
| `{5}`        | 5           | 100%    | 100%    | 100 |

---


#### Tank swimmer
constructed with OpenSCAD:

/*
Construction of a tank swimmer with OpenSCAD
use of BOSL2-Library;
https://github.com/BelfrySCAD/BOSL2;
https://github.com/BelfrySCAD/BOSL2/wiki/CheatSheet
*/
include <BOSL2/std.scad>
$fn=100;


difference() {
	cyl(l=14, d=35, rounding=2);
	translate ([0,0,-1]) cyl(l=16, d=8);;
}
