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
- **Two to three planting containers** for larger crops such as tomatoes or chayote.
- **One 15 litres water tank** containing the nutrient solution.
- **A Biofilter** with cocos a clay balls which creates and maintains the microbial colonies needed to break down organic fertilizers so that nutrients become continuously available to the plants.
- **Two water pumps** responsible for circulating the nutrient solution through the cultivation channels and the planting containers.
- **One air pump** which supplies oxygen to keep the microbial communities active so they can efficiently break down organic nutrients
- **One Arduino Nano ESP32 S3**, serving as the central microcontroller for automation and pump control.
- **Additional electronic components**, including relays, voltage converters, a power supply, and supporting circuitry.
- **SH20 temperature/humidity sensor (I2C)** to measure ambient temperature and humidity.
- **SH20 temperature sensor (I2C)** to monitor the nutrient solution temperature.
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

### Software Architecture

The software architecture follows a **layered and modular design**, separating hardware access, application logic, state management, and cloud interaction. The system is structured to support **concurrent tasks** on a resource‑constrained ESP32 using MicroPython threads.

At a high level, the architecture consists of the following layers:

- **Boot Layer**
  - Handles Wi‑Fi connectivity and NTP time synchronization at startup
  - Ensures that secure cloud communication (TLS) is possible before other components initialize

- **Application Layer (main.py)**
  - Acts as the central orchestrator
  - Initializes hardware components (relays, I²C devices, sensors, LCD)
  - Registers Arduino Cloud variables and their callbacks
  - Starts background tasks (threads)
  - Runs the blocking cloud client loop

- **State Layer (`state/runtime.py`)**
  - Provides a **thread-safe shared state**
  - Stores dynamic values such as:
    - ambient temperature
    - watering durations per circuit
    - active time window
  - Ensures safe concurrent access via locks
  - Acts as the single source of truth between tasks and cloud callbacks

- **Task Layer (`tasks/`)**
  - Implements concurrent workers with different execution frequencies:
    - **Low-frequency task**: updates time, reads sensors, publishes values
    - **High-frequency task**: evaluates watering schedules and triggers relays
    - **UI task**: manages LCD output
  - Uses polling combined with non-blocking timing (`ticks_ms`) to achieve soft real-time behavior

- **Hardware Abstraction Layer (`hw/`)**
  - Encapsulates direct hardware interaction:
    - relays
    - sensors (SHT20, DS18B20)
    - LCD display
    - I²C devices
  - Provides simple, reusable interfaces for higher-level components

- **Cloud Integration Layer (`cloud/`)**
  - Manages communication with Arduino IoT Cloud
  - Uses a callback-driven model:
    - cloud variables update local runtime state
    - configuration changes are applied immediately
  - Supports both structured profiles and legacy configuration formats

---

The system follows a **hybrid control model**:

- **Event-driven behavior** via cloud callbacks updating runtime parameters
- **Time-driven polling loops** for evaluating schedules and triggering actions

The core watering logic is implemented as a **cycle-based trigger system**:

1. Read current time and temperature  
2. Determine active trigger seconds based on temperature profiles  
3. Check if the system is within the configured active time window  
4. Activate relays for a configurable duration when a trigger condition is met  

This approach avoids blocking delays and allows overlapping operations across multiple circuits.

---

Overall, the architecture provides:

- clear separation of concerns  
- high configurability via cloud variables  
- robustness through state encapsulation  
- flexibility for extending sensors, actuators, or control logic  

It is effectively a **lightweight, soft real-time control system** tailored for IoT-based environmental automation.

### Files

📄 boot.py<br>
📄 config.py<br>
📄 secrets.py<br>
📄 main.py<br>
📄 time_zh.py<br>
📄 tankReeds.py<br>
📄 lcd1602.py<br>
📁 cloud/<br>
	📄 cloud/client.py<br>
	📄 cloud/callbacks.py<br>
📁 tasks/<br>
	📄 tasks/time_task.py<br>
	📄 tasks/cycles_control.py<br>
	📄 tasks/lcd_task.py<br>
📁 hw/<br>
	📄 hw/pins.py<br>
	📄 hw/sensors_sht20.py<br>
	📄 hw/relay.py<br>
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
#LED_PIN = 48
ACTIVE_LOW = False

# --- Relays / Actuators ---
RELAY1_PIN = 38   # D11
RELAY2_PIN = 18   # D09
RELAY3_PIN = 47   # D12

RELAY_ACTIVE_LOW = False  # falls Relais invertiert sind → True setzen


# I2C Pin setting
I2C_SCL_PIN = 5
I2C_SDA_PIN = 6

# I2C Addresses
PCF8574_ADDR = 0x20
LCD_ADDR = 0x3E

# Task periods / polling (seconds or milliseconds as noted)
TIME_UPDATE_PERIOD_S = 1
CYCLE_POLL_MS = 250

# Default pulse length used as fallback for all circuits
# until cloud values are received (seconds)
DEFAULT_SWITCH_DURATION_S = 10

# Default active day window used until cloud values arrive (local time Europe/Zurich)
DEFAULT_START_HOUR = 7   # 07:00
DEFAULT_END_HOUR   = 21  # 21:00

# Safety clamps for watering pulse duration (in seconds)
MIN_SWITCH_DURATION_S = 1
MAX_SWITCH_DURATION_S = 60


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
    DEFAULT_SWITCH_DURATION_S,
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
_c1_duration_s = DEFAULT_SWITCH_DURATION_S
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
    
# --- Circuit 2: watering pulse duration (seconds) -----------------------------

_c2_duration_s = DEFAULT_SWITCH_DURATION_S   # gleicher Default ok
_c2_lock = _thread.allocate_lock()

def set_c2_duration_s(v_s: int):
    global _c2_duration_s
    try:
        v = int(v_s)
    except Exception:
        return
    v = max(MIN_SWITCH_DURATION_S, min(v, MAX_SWITCH_DURATION_S))
    with _c2_lock:
        _c2_duration_s = v

def get_c2_duration_s() -> int:
    with _c2_lock:
        return int(_c2_duration_s)
    
# --- Circuit 3: air pump pulse duration (seconds) -----------------------------
_c3_duration_s = DEFAULT_SWITCH_DURATION_S   # gleicher Default ok
_c3_lock = _thread.allocate_lock()

def set_c3_duration_s(v_s: int):
    global _c3_duration_s
    try:
        v = int(v_s)
    except Exception:
        return
    v = max(MIN_SWITCH_DURATION_S, min(v, MAX_SWITCH_DURATION_S))
    with _c3_lock:
        _c3_duration_s = v

def get_c3_duration_s() -> int:
    with _c3_lock:
        return int(_c3_duration_s)
    

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
    TIME_UPDATE_PERIOD_S,
    CYCLE_POLL_MS,
    LCD_ADDR,
    I2C_SCL_PIN,
    I2C_SDA_PIN,
    RELAY1_PIN,
    RELAY2_PIN,
    RELAY3_PIN
)

from hw.relay import make_relay, set_relay
from cloud.client import create_client
from cloud.callbacks import (
    onCycles1Change, onCycles2Change, onCycles3Change,
    seconds_for_temp,
    onC1DurationChange, onC2DurationChange, onC3DurationChange,
    onStartHourChange, onEndHourChange,
)
from tasks.time_task import time_and_temp_task
from tasks.cycles_control import cycles_control_task
from hw.sensors_sht20 import SHT20Manager

from state.runtime import (
    get_air_temp,
    get_c1_duration_s, get_c2_duration_s, get_c3_duration_s,
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
            print("LCD initialized")
        except Exception as e:
            print("LCD init failed:", e)
    else:
        print("LCD not found on I2C bus")

    if lcd is not None:
        _thread.start_new_thread(lcd_task, (lcd, i2c))
    
    # --- Cloud client & variables registration ---
    client = create_client({
        'time_zh': {},
        'air_temp': {},
        'air_humidity': {},
        'cycles_circuit_1': {'on_write': onCycles1Change},
        'cycles_circuit_2': {'on_write': onCycles2Change},
        'cycles_circuit_3': {'on_write': onCycles3Change},
        'switchDuration_circuit_1': {'on_write': onC1DurationChange},
        'switchDuration_circuit_2': {'on_write': onC2DurationChange},
        'switchDuration_circuit_3': {'on_write': onC3DurationChange},
        'startHour': {'on_write': onStartHourChange},
        'endHour':   {'on_write': onEndHourChange},
        # Read-only mirrors (strings like "0,15,30,45" when the effective set changes):
        'cycles_circuit_1_effective': {},
        'cycles_circuit_2_effective': {},
        'cycles_circuit_3_effective': {},
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
            get_c3_duration_s,
            get_active_window_minutes,
        )
    )
    
    

    # --- Blocking cloud loop ---
    client.start()
    

if __name__ == "__main__":
    main()


```
#### hw/sensors_sht20.py

```python
# sensors_sht20.py
# Purpose:
# Read temperature and humidity from an SHT20 sensor over I2C
# and publish values to Arduino IoT Cloud.
#
# Published variables:
# - air_temp (°C)
# - air_humidity (% rF)

from machine import I2C
import time

SHT20_ADDR = 0x40

# Commands (no hold master)
CMD_TEMP = 0xF3
CMD_HUM  = 0xF5


class SHT20Manager:
    """
    Simple manager for a single SHT20 sensor on an I2C bus.
    Interface is compatible with the existing DS18B20Manager usage.
    """

    def __init__(self, client, i2c: I2C):
        self.client = client
        self.i2c = i2c

    # --- Low-level raw reads ----------------------------------------------

    def _read_temperature(self):
        self.i2c.writeto(SHT20_ADDR, bytes([CMD_TEMP]))
        time.sleep_ms(100)
        raw = self.i2c.readfrom(SHT20_ADDR, 2)
        val = (raw[0] << 8) | raw[1]
        val &= 0xFFFC  # mask status bits
        return -46.85 + 175.72 * val / 65536.0

    def _read_humidity(self):
        self.i2c.writeto(SHT20_ADDR, bytes([CMD_HUM]))
        time.sleep_ms(100)
        raw = self.i2c.readfrom(SHT20_ADDR, 2)
        val = (raw[0] << 8) | raw[1]
        val &= 0xFFFC  # mask status bits
        return -6.0 + 125.0 * val / 65536.0

    # --- Public API -------------------------------------------------------

    def read_and_publish_once(self):
        """
        Read temperature + humidity once and publish to the cloud.
        Also updates runtime temperature state.
        """
        try:
            temp = round(self._read_temperature(), 2)
            hum  = round(self._read_humidity(), 2)
        except Exception as e:
            print("SHT20 read error:", e)
            return

        # Publish to Arduino Cloud
        try:
            self.client["air_temp"] = temp
            self.client["air_humidity"] = hum
        except Exception as e:
            print("SHT20 publish error:", e)

        # Update runtime state for watering logic
        try:
            from state.runtime import set_air_temp
            set_air_temp(temp)
        except Exception:
            pass
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

####  tasks/cycles_control.py

```python
# tasks/cycles_control.py
# Cyclic worker for trigger-based watering logic with:
# - dynamic pulse duration (seconds) via getter
# - active day window (start/end minutes) via getter
# - publication of the effective trigger set (optional)

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
        return False
    if start_m < end_m:
        return start_m <= now_m < end_m
    return (now_m >= start_m) or (now_m < end_m)


def cycles_control_task(
    set_actuator_fn,
    actuator,
    poll_ms=100,
    get_temp_fn=None,
    select_secs_fn=None,
    client=None,
    effective_var_name=None,
    get_duration_s_fn=None,
    get_window_minutes_fn=None,
):
    """
    Poll current local second; if within the active window and configured,
    activate the actuator for the configured duration (seconds) on each trigger second.
    Uses non-blocking timing.
    """
    actuator_active_until = 0
    last_fired_sec = -1
    last_effective = None

    while True:
        try:
            # --- Time ---
            t_local, _, _ = localtime_ch()
            sec = t_local[5]  # Development: second-based triggering
            now_ms = ticks_ms()
            now_m = _minutes_since_midnight(t_local)

            # --- Turn OFF when duration elapsed ---
            if actuator_active_until and ticks_diff(actuator_active_until, now_ms) <= 0:
                set_actuator_fn(actuator, False)
                actuator_active_until = 0

            # --- Determine active trigger set ---
            temp_c = get_temp_fn() if get_temp_fn else None
            active_secs = select_secs_fn(temp_c) if select_secs_fn else set()

            # --- Publish effective set (if changed) ---
            if client and effective_var_name is not None:
                eff_tuple = tuple(sorted(active_secs))
                if eff_tuple != last_effective:
                    try:
                        client[effective_var_name] = ','.join(map(str, eff_tuple))
                    except Exception:
                        pass
                    last_effective = eff_tuple

            # --- Window check ---
            in_window = True
            if get_window_minutes_fn:
                try:
                    s_m, e_m = get_window_minutes_fn()
                    in_window = _within_window(now_m, s_m, e_m)
                except Exception:
                    in_window = True  # fail-open

            if not in_window:
                if actuator_active_until:
                    set_actuator_fn(actuator, False)
                    actuator_active_until = 0
                sleep(poll_ms / 1000.0)
                continue

            # --- Resolve duration ---
            duration_ms = 2000  # fallback
            if get_duration_s_fn:
                try:
                    duration_ms = int(get_duration_s_fn()) * 1000
                except Exception:
                    pass

            # --- Trigger ---
            if (sec in active_secs) and (sec != last_fired_sec):
                set_actuator_fn(actuator, True)
                actuator_active_until = now_ms + duration_ms
                last_fired_sec = sec
                print("[cycles] Trigger at", sec, "→ actuator active for", duration_ms, "ms")

        except Exception as e:
            print("cycles_control_task error:", e)

        sleep(poll_ms / 1000.0)

```

####  tasks/lcd_task.py
```python
from time import sleep, ticks_ms, ticks_diff
from time_zh import localtime_ch
from cloud.callbacks import seconds_for_temp
from state.runtime import get_air_temp
import tankReeds


# -------------------------------------------------
# Helper: Countdown bis zum nächsten Trigger
# -------------------------------------------------
def seconds_until_next_trigger(current_sec, active_secs):
    if not active_secs:
        return 99

    future = sorted(s for s in active_secs if s > current_sec)

    if future:
        return future[0] - current_sec

    return (60 - current_sec) + min(active_secs)


# -------------------------------------------------
# Helper: Padding auf 16 Zeichen
# -------------------------------------------------
def pad(s, n=16):
    if len(s) >= n:
        return s[:n]
    return s + " " * (n - len(s))


# -------------------------------------------------
# Formatierung
# -------------------------------------------------
def format_line1(c1_cd, hh, mm, ss):
    return f"K1:{c1_cd:02d} {hh:02d}:{mm:02d}:{ss:02d}"


def format_line2(c2_cd, temp, tank):
    # Tank
    if tank is not None and tank >= 0:
        tank_str = f"{int(tank):02d}%"
    else:
        tank_str = "--%"

    # Temperatur
    if temp is not None:
        temp_str = f"{int(temp):02d}C"
    else:
        temp_str = "--C"

    return f"K2:{c2_cd:02d} {tank_str}  {temp_str}"


# -------------------------------------------------
# LCD Task
# -------------------------------------------------
def lcd_task(lcd, i2c, period_s=1):
    last_init = 0

    while True:
        now = ticks_ms()

        # --- Re-Init alle 5 Sekunden ---
        if ticks_diff(now, last_init) > 5000:
            try:
                lcd._init_lcd()
                print("[LCD] periodic reinit")
            except Exception:
                pass
            last_init = now

        try:
            # --- Zeit ---
            t_local, _, _ = localtime_ch()
            hh, mm, ss = t_local[3], t_local[4], t_local[5]

            # --- Temperatur ---
            temp = get_air_temp()

            # --- Trigger-Sekunden ---
            secs_c1 = seconds_for_temp('c1', temp)
            secs_c2 = seconds_for_temp('c2', temp)

            # --- Countdown ---
            c1_cd = seconds_until_next_trigger(ss, secs_c1)
            c2_cd = seconds_until_next_trigger(ss, secs_c2)

            c1_cd = min(99, c1_cd)
            c2_cd = min(99, c2_cd)

            # --- Tank ---
            tank = tankReeds.get_fill_percent()

            # --- Formatierung ---
            line1 = format_line1(c1_cd, hh, mm, ss)
            line2 = format_line2(c2_cd, temp, tank)

            # --- Ausgabe ---
            lcd.setCursor(0, 0)
            lcd.printout(pad(line1))

            lcd.setCursor(0, 1)
            lcd.printout(pad(line2))

        except Exception as e:
            print("[LCD] error:", e)

        sleep(period_s)

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
    'c3': {'profiles': None, 'secs': set()},
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
            

def onCycles1Change(client, value):
    """on_write for 'cycles_circuit_1' (string)."""
    _update_circuit_from_text('c1', value if isinstance(value, str) else str(value))

def onCycles2Change(client, value):
    """on_write for 'cycles_circuit_2' (string)."""
    _update_circuit_from_text('c2', value if isinstance(value, str) else str(value))
    
def onCycles3Change(client, value):
    """on_write for 'cycles_circuit_3' (string)."""
    _update_circuit_from_text('c3', value if isinstance(value, str) else str(value))

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

# ---------- loud handlers for duration & time window ----------

import time

def _timestamp_to_minutes_since_midnight(ts_utc):
    """
    Convert POSIX timestamp (UTC) to local CH time (CET/CEST)
    and return minutes since midnight.
    """
    try:
        # In lokale Zeit wandeln (MicroPython kennt Zeitzone via time_zh)
        lt = time.localtime(int(ts_utc))

        hour = lt[3]
        minute = lt[4]
        return hour * 60 + minute
    except Exception as e:
        print("timestamp conversion error:", e)
        return None


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
        

def onC2DurationChange(client, value):
    try:
        from state.runtime import set_c2_duration_s
        set_c2_duration_s(int(value))
        print(f"[c2] switch duration set to {int(value)} s")
    except Exception as e:
        print("onC2DurationChange error:", e)
        
def onC3DurationChange(client, value):
    try:
        from state.runtime import set_c3_duration_s
        set_c3_duration_s(int(value))
        print(f"[c3] switch duration set to {int(value)} s")
    except Exception as e:
        print("onC3DurationChange error:", e)


def onStartHourChange(client, value):
    try:
        print("[DEBUG] raw startHour payload:", value)

        from state.runtime import get_active_window_minutes, set_active_window_minutes

        # POSIX-Zeitstempel in Minuten überführen
        m = _timestamp_to_minutes_since_midnight(value)
        if m is None:
            print("onStartHourChange: invalid timestamp:", value)
            return

        # Fenster aktualisieren
        _, end_m = get_active_window_minutes()
        set_active_window_minutes(m, end_m)

        print(f"[window] start set to {m//60:02d}:{m%60:02d}")

    except Exception as e:
        print("onStartHourChange error:", e)
        

def onEndHourChange(client, value):
    try:
        print("[DEBUG] raw endHour payload:", value)

        from state.runtime import get_active_window_minutes, set_active_window_minutes

        m = _timestamp_to_minutes_since_midnight(value)
        if m is None:
            print("onEndHourChange: invalid timestamp:", value)
            return

        start_m, _ = get_active_window_minutes()
        set_active_window_minutes(start_m, m)

        print(f"[window] end set to {m//60:02d}:{m%60:02d}")

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

#### hw/relay.py
```python

# hw/relay.py
from machine import Pin
from config import RELAY_ACTIVE_LOW

def make_relay(pin_number: int):
    """Create relay pin, OFF by default."""
    p = Pin(pin_number, Pin.OUT)
    if RELAY_ACTIVE_LOW:
        p.value(1)  # OFF
    else:
        p.value(0)  # OFF
    return p

def set_relay(pin, on: bool):
    """Switch relay ON/OFF respecting polarity."""
    if RELAY_ACTIVE_LOW:
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

hw/led.py
##
```pythom
# hw/lcd1602.py
# Clean integration of AiP31068L 1602 LCD + SN3193 backlight controller
# Uses shared I2C bus from main.py

import time

# LCD1602 I2C address (7-bit)
LCD_ADDRESS = 0x3E   # 0x7C >> 1

# Command prefixes
COMMAND_MODE = 0x80
DATA_MODE = 0x40

# LCD Commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME   = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT  = 0x10
LCD_FUNCTIONSET  = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# Flags
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTDECREMENT = 0x00

LCD_DISPLAYON = 0x04
LCD_CURSOROFF = 0x00
LCD_BLINKOFF = 0x00

LCD_4BITMODE = 0x00
LCD_1LINE    = 0x00
LCD_2LINE    = 0x08
LCD_5x8DOTS  = 0x00


class LCD1602:
    """
    1602 LCD with AiP31068L controller.
    Uses direct I2C commands (not PCF8574).
    """

    def __init__(self, i2c, cols=16, rows=2):
        self.i2c = i2c
        self.cols = cols
        self.rows = rows

        self._displayfunction = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS
        self._init_lcd()

    # --- Low-level writes ----------------------------------

    def _cmd(self, value):
        """Send command to LCD."""
        self.i2c.writeto_mem(LCD_ADDRESS, COMMAND_MODE, bytes([value]))

    def _data(self, value):
        """Send data byte."""
        self.i2c.writeto_mem(LCD_ADDRESS, DATA_MODE, bytes([value]))

    # --- LCD Initialization --------------------------------

    def _init_lcd(self):
        time.sleep(0.05)
        if self.rows > 1:
            self._displayfunction |= LCD_2LINE

        # Function set sequence
        self._cmd(LCD_FUNCTIONSET | self._displayfunction)
        time.sleep(0.005)
        self._cmd(LCD_FUNCTIONSET | self._displayfunction)
        time.sleep(0.005)
        self._cmd(LCD_FUNCTIONSET | self._displayfunction)

        # Display ON
        self._displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.display(True)

        # Clear screen
        self.clear()

        # Entry Mode: left-to-right
        self._entrymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        self._cmd(LCD_ENTRYMODESET | self._entrymode)

    # --- Public API ----------------------------------------

    def clear(self):
        self._cmd(LCD_CLEARDISPLAY)
        time.sleep(0.005)

    def home(self):
        self._cmd(LCD_RETURNHOME)
        time.sleep(0.005)

    def display(self, enable=True):
        if enable:
            self._cmd(LCD_DISPLAYCONTROL | self._displaycontrol)
        else:
            self._cmd(LCD_DISPLAYCONTROL | 0x00)

    def setCursor(self, col, row):
        if row >= self.rows:
            row = self.rows - 1

        addr = col + (0x80 if row == 0 else 0xC0)
        self._cmd(addr)

    def printout(self, text):
        if not isinstance(text, str):
            text = str(text)
        for ch in text:
            self._data(ord(ch))


# -----------------------------------------------------------------
# SN3193 LED Backlight Controller
# -----------------------------------------------------------------

SN3193_ADDR = 0x6B

# Registers
SHUTDOWN_REG = 0x00
LED_MODE_REG = 0x02
CURRENT_SETTING_REG = 0x03
PWM_1_REG = 0x04
PWM_UPDATE_REG = 0x07


class SN3193:
    """
    Simple wrapper for SN3193 LED backlight.
    """

    def __init__(self, i2c):
        self.i2c = i2c
        self._init_chip()

    def _write(self, reg, val):
        self.i2c.writeto_mem(SN3193_ADDR, reg, bytes([val]))

    def _init_chip(self):
        self._write(SHUTDOWN_REG, 0x20)
        self._write(LED_MODE_REG, 0x00)
        self._write(CURRENT_SETTING_REG, 0x00)
        time.sleep(0.01)
        self._write(PWM_1_REG, 0xFF)
        time.sleep(0.05)
        self._write(PWM_UPDATE_REG, 0x00)

    def set_brightness(self, percent):
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        pwm = int(percent * 2.55)  # 0..255
        self._write(PWM_1_REG, pwm)
        time.sleep(0.05)
        self._write(PWM_UPDATE_REG, 0x00)

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


### Water Level Sensing Subsystem (PCF8574T + Reed Switches)

#### Overview

The main tank contains a **vertical float with an embedded magnet**. Along the tank wall, **six reed switches** are mounted at corresponding levels.

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
