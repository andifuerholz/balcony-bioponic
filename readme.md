## Table of Contents
- [Table of Contents](#table-of-contents)
- [Project description](#project-description)
- #hardware
- [Software](#software)
  - [Core Watering Logic](#core-watering-logic)
  - #framework-description
  - [Files](#files)
  - [Arduino Cloud Setup](#arduino-cloud-setup)
    - #cloud-variables
    - [Dashboard](#dashboard)
- [Implementation Strategy](#implementation-strategy)
  - [Preliminary Remarks](#preliminary-remarks)
  - #automation-implementation
  - [Learning Goals](#learning-goals)

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
- **One Arduino Nano ESP32**, serving as the central microcontroller for automation and pump control.
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

├── boot.py
├── config.py
├── main.py
├── secrets.py
├── sensors_ds18b20.py
├── time_zh.py
│
├── lib/
│
├── cloud/
│   ├── client.py
│   └── callbacks.py
│
├── tasks/
│   ├── time_task.py
│   └── cycles_led.py
│
├── hw/
│   ├── led.py
│   └── pins.py
│
└── state/
    └── runtime.py

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

TIME_UPDATE_PERIOD_S = 1
LED_CYCLE_DURATION_MS = 1000
LED_CYCLE_POLL_MS = 100

# ---------------------------------
# DS18B20 mapping & validation
# ---------------------------------
# DS18B20 ROM → friendly name
# IMPORTANT: Keys must be *bytes* (not bytearray; no HTML-escaped content).
SENSOR_MAP = {
    b'\x28\x8e\x01\x48\xf6\x75\x3c\xde': 'air',   # Main ambient sensor
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
TEMP_MAX =  60.0

```
### state/runtime.py
```python
# state/runtime.py
import _thread

_air_temp = None
_lock = _thread.allocate_lock()

def set_air_temp(value: float):
    """Update last known ambient temperature (°C)."""
    global _air_temp
    with _lock:
        _air_temp = float(value)

def get_air_temp(default=None):
    """Get last known ambient temperature (°C) or default if unknown."""
    with _lock:
        return _air_temp if _air_temp is not None else default
```

#### `main.py`

```python
# main.py
# Purpose:
#   Initialize Arduino IoT Cloud client, register variables/callbacks,
#   start background tasks (combined local time + DS18B20 readings, cycle-based LED),
#   and run the client loop. Wi‑Fi and NTP are handled in boot.py.
#
# Notes:
#   - Development mode: the "watering" events are simulated by toggling the on-board LED.
#   - The cycle schedule is temperature-dependent and provided as a multi-line profile string
#     per circuit via Arduino Cloud variables `cycles_circuit_1` and `cycles_circuit_2`, e.g.:
#         0°C: 0, 30
#         20°C: 0, 20, 40
#         25°C: 0, 15, 30, 45
#   - Rule: for the current ambient temperature, select the seconds-set of the highest
#     threshold that is <= current temperature (0°C acts as default).
#   - Optional read-only mirrors `cycles_circuit_1_effective` / `_2_effective` publish
#     the currently active seconds (comma-separated) for dashboard visibility.

import logging
import _thread

from config import (
    LED_PIN, ACTIVE_LOW,
    DS18B20_PIN,
    TIME_UPDATE_PERIOD_S,
    LED_CYCLE_DURATION_MS, LED_CYCLE_POLL_MS,
)

from hw.led import make_led, set_led
from cloud.client import create_client
from cloud.callbacks import (
    onLedChange,
    onCycles1Change, onCycles2Change,
    seconds_for_temp,        # selector: seconds_for_temp(c_key, temp_c)
)
from tasks.time_task import time_and_temp_task
from tasks.cycles_led import cycles_blink_task
from sensors_ds18b20 import DS18B20Manager
from state.runtime import get_air_temp     # thread-safe getter for current ambient temp


def main():
    # Basic logging setup
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO,
    )

    # --- Hardware setup (LED as actuator placeholder) ---
    led_pin = make_led()  # respects ACTIVE_LOW/LED_PIN from config

    # --- Cloud client & variables registration ---
    # Expect the following variables to exist in Arduino Cloud:
    #   - led_state                  (bool; R/W)
    #   - time_zh                    (string; R/O)
    #   - air_temp                   (float; R/O)  → published by sensor task
    #   - cycles_circuit_1           (string; R/W) → profile text or legacy CSV seconds
    #   - cycles_circuit_2           (string; R/W) → profile text or legacy CSV seconds
    #   - cycles_circuit_1_effective (string; R/O) → comma-separated active seconds
    #   - cycles_circuit_2_effective (string; R/O) → comma-separated active seconds
    client = create_client({
        'led_state': {'on_write': lambda c, v: onLedChange(c, set_led, led_pin, v)},
        'time_zh': {},
        'air_temp': {},
        'cycles_circuit_1': {'on_write': onCycles1Change},
        'cycles_circuit_2': {'on_write': onCycles2Change},
        # Read-only mirrors (strings like "0,15,30,45" when the effective set changes):
        'cycles_circuit_1_effective': {},
        'cycles_circuit_2_effective': {},
    })

    # --- Sensors manager (DS18B20) ---
    #   Publishes named temps as {name}_temp (e.g., air_temp) and updates runtime state.
    manager = DS18B20Manager(client, pin=DS18B20_PIN)

    # --- Background tasks ---
    # 1) Low-frequency combined task: local time string + temperature readings
    _thread.start_new_thread(
        time_and_temp_task,
        (client, manager, TIME_UPDATE_PERIOD_S)
    )

    # 2) High-frequency cycle workers (development: both circuits use the same LED output)
    #    Later, replace set_led/led_pin per circuit with dedicated GPIOs for valves/pumps.
    _thread.start_new_thread(
        cycles_blink_task,
        (
            set_led, led_pin,
            LED_CYCLE_DURATION_MS, LED_CYCLE_POLL_MS,
            get_air_temp,                         # temperature getter
            lambda t: seconds_for_temp('c1', t),  # selector for circuit 1
            client, 'cycles_circuit_1_effective'  # publish effective set (optional)
        )
    )

    _thread.start_new_thread(
        cycles_blink_task,
        (
            set_led, led_pin,
            LED_CYCLE_DURATION_MS, LED_CYCLE_POLL_MS,
            get_air_temp,                         # temperature getter
            lambda t: seconds_for_temp('c2', t),  # selector for circuit 2
            client, 'cycles_circuit_2_effective'  # publish effective set (optional)
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

def _fmt_time_str(t_local, tz_str):
    # t_local: (Y, M, D, hh, mm, ss, wd, yd)
    Y, M, D, hh, mm, ss = t_local[0], t_local[1], t_local[2], t_local[3], t_local[4], t_local[5]
    # ISO-like "YYYY-MM-DD hh:mm:ss TZ"
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} {}".format(Y, M, D, hh, mm, ss, tz_str)

def time_and_temp_task(client, ds18_manager, period_s=1):
    """
    Publishes:
      - time_zh: local date-time string with TZ (CET/CEST)
      - {name}_temp: per-sensor temp readings via DS18B20Manager.read_and_publish_once()
    """
    # First immediate publish to avoid dashboard silence on boot
    try:
        t_local, _, tz = localtime_ch()
        client['time_zh'] = _fmt_time_str(t_local, tz)
    except Exception:
        pass

    while True:
        try:
            # 1) Local time (Europe/Zurich)
            t_local, _, tz = localtime_ch()
            client['time_zh'] = _fmt_time_str(t_local, tz)

            # 2) DS18B20 readings (also updates runtime air temperature state)
            ds18_manager.read_and_publish_once()

        except Exception as e:
            print("time_and_temp_task error:", e)

        time.sleep(period_s if period_s and period_s > 0 else 1)

```

####  tasks/cycles_led.py

```python
# tasks/cycles_led.py
from time import sleep, ticks_ms, ticks_diff
from time_zh import localtime_ch

def cycles_blink_task(set_led_fn,
                      led_pin,
                      duration_ms=2000,
                      poll_ms=100,
                      get_temp_fn=None,
                      select_secs_fn=None,
                      client=None,
                      effective_var_name=None):
    """
    Poll current local second; if configured, turn LED ON for duration_ms (non-blocking).

    Args:
        set_led_fn: function(pin, on_bool) -> None
        led_pin: Pin object for the LED/valve
        duration_ms: ON duration for each trigger event
        poll_ms: loop poll interval
        get_temp_fn: () -> float|None, returns current ambient temp in °C
        select_secs_fn: (temp_c: float|None) -> set[int], seconds active for given temperature
        client: ArduinoCloudClient to publish effective set changes (optional)
        effective_var_name: Cloud variable name (string) to publish comma-separated seconds
    """
    led_active_until = 0
    last_fired_sec = -1
    last_effective = None

    while True:
        try:
            t_local, _, _ = localtime_ch()
            sec = t_local[5]  # 0..59
            now = ticks_ms()

            # Turn LED off when the pulse duration has elapsed
            if led_active_until and ticks_diff(led_active_until, now) <= 0:
                set_led_fn(led_pin, False)
                led_active_until = 0

            # Determine active seconds set for current temperature
            if select_secs_fn:
                temp_c = get_temp_fn() if get_temp_fn else None
                active_secs = select_secs_fn(temp_c)
            else:
                active_secs = set()

            # Optionally publish the effective set whenever it changes
            if client and effective_var_name is not None:
                eff_tuple = tuple(sorted(active_secs))
                if eff_tuple != last_effective:
                    try:
                        client[effective_var_name] = ','.join(map(str, eff_tuple))
                    except Exception:
                        pass
                    last_effective = eff_tuple

            # Fire once per matching second
            if (sec in active_secs) and (sec != last_fired_sec):
                set_led_fn(led_pin, True)
                led_active_until = now + duration_ms
                last_fired_sec = sec
                print("[cycles] Fired at second", sec, "for", duration_ms, "ms")

        except Exception as e:
            print("cycles_blink_task error:", e)

        sleep(poll_ms / 1000.0)
```

#### cloud/callbacks.py

```python
# cloud/callbacks.py
import _thread

# Per-circuit state
_state = {
    'c1': {'profiles': None, 'secs': set()},
    'c2': {'profiles': None, 'secs': set()},
}
_lock = _thread.allocate_lock()

def parse_cycle_seconds(s: str):
    """Parse CSV '5, 10, 20' -> {5,10,20}; clamp to 0..59; ignore junk."""
    secs = set()
    if not s:
        return secs
    for part in s.split(','):
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
    """
    on_write for 'led_state'. Kept generic by passing set_led_fn and led_pin.
    """
    try:
        set_led_fn(led_pin, bool(value))
        print("LED ON!" if value else "LED OFF!")
    except Exception as e:
        print("onLedChange error:", e)

def onCycles1Change(client, value):
    """
    on_write for 'cycles_circuit_1' (string).
    Supports both legacy CSV and temperature-profile strings.
    """
    text = value if isinstance(value, str) else str(value)
    _update_circuit_from_text('c1', text)

def onCycles2Change(client, value):
    """
    on_write for 'cycles_circuit_2' (string).
    Supports both legacy CSV and temperature-profile strings.
    """
    text = value if isinstance(value, str) else str(value)
    _update_circuit_from_text('c2', text)

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

### Tank swimmer
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
