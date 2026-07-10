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

This project implements a compact **bioponics automation system** for balcony-scale food production using an **Arduino Nano ESP32** running **MicroPython**.

The controller manages watering cycles, aeration, environmental monitoring, tank level measurement, and automatic reservoir refilling. Watering schedules are basically temperature-dependent and can be configured remotely through **Arduino IoT Cloud**.

The software follows a modular architecture with separate layers for hardware access, cloud communication, shared runtime state, and concurrent background tasks. This enables reliable operation while remaining easy to extend and maintain.

To support unattended operation, the system continuously monitors sensors and actuators, synchronizes with the cloud, performs a daily automatic reboot at **06:00**, and automatically recovers from extended Wi‑Fi outages through a watchdog-based restart mechanism.

Besides providing a productive growing environment for lettuces and fruits, the project also serves as a practical learning platform for embedded systems, MicroPython, IoT integration, automation, and robust real-world control systems.

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
- **Planned: SH20 temperature sensor (I2C)** to monitor the nutrient solution temperature.
- **A custom-built water level sensing system**, consisting of six reed switches positioned at different heights.
- **An auxiliary tank with its own pump** to refill or stabilize the main reservoir when required.

## Software
### Core Watering Logic

#### Core Watering Logic

The software controls the watering cycles within a configurable daily time window (e.g. from 07:00 to 22:00).

Within this active period, each circuit follows a temperature-dependent schedule that defines **at which minutes of the hour** the actuator is activated. Different temperature ranges can be assigned different trigger schedules, allowing the watering frequency to adapt automatically to environmental conditions.

Example:

- Air temperature: **26 °C**
- Circuit 1 schedule: **0, 20, 40**
- Pulse duration: **15 seconds**

Result:

- Circuit 1 is activated at minute 0, 20, and 40 of every hour and remains active for 15 seconds.

To reduce noise during nighttime operation, the cultivation channel is normally restricted to a configurable active daytime window. This prevents the circulation pump from running too often during warm summer nights. It is assumed, thath water demand remains lower at night, but plants still continue nutrient uptake and are able to growth. Therefore, a safety mechanism ensures that the cultivation channel is not left inactive for excessive periods. So in addition to the scheduled triggers, a circuit can define a **maximum off-time**. If the actuator has not been activated for the configured period, the system performs a forced activation regardless of the current schedule or active time window.

Example:

- Active window: **07:00–22:00**
- Maximum off-time: **75 minutes**
- No regular activation occurs within 75 minutes

Result:

- The circuit is automatically activated using the configured pulse duration.
- The off-time counter is reset after the activation.

This approach combines three objectives:

- temperature-adaptive watering during the day,
- reduced noise emissions during the night,
- guaranteed minimum circulation and nutrient supply for the cultivation channel over a 24-hour period.

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
	📄 tasks/refill_task.py<br>
📁 hw/<br>
	📄 hw/pins.py<br>
	📄 hw/sensors_sht20.py<br>
	📄 hw/relay.py<br>
📁 state/<br>
	📄 state/runtime.py<br>
📁 lib/<br>
	📄 ...<br>
	📄 ...<br>

### Reliability & Recovery Strategy

The system is designed to operate unattended for long periods on a balcony installation where temporary network interruptions may occur.

To improve long-term reliability, two recovery mechanisms are implemented:

#### Daily Scheduled Reboot

The controller performs an automatic reboot every day at **06:00 local time**.

Purpose:

- Refresh network and cloud connections
- Reinitialize hardware peripherals
- Re-synchronize the system clock (NTP)
- Reduce the risk of long-term memory fragmentation or stale internal states

The reboot occurs once per day and only within the configured minute, preventing repeated restarts.

#### Wi‑Fi Loss Watchdog

A background monitoring function continuously checks the Wi‑Fi connection status.

Behaviour:

1. If the Wi‑Fi connection is lost, a timer is started.
2. Temporary outages are tolerated and reported via log messages.
3. If the connection is restored, the timer is reset.
4. If the Wi‑Fi connection remains unavailable for more than **5 minutes**, the controller automatically reboots.

This approach provides a simple and robust recovery mechanism for situations where:

- the access point becomes temporarily unavailable,
- DHCP renewal fails,
- cloud connectivity cannot be re-established after a network interruption,
- internal network components enter an undefined state.

#### Design Philosophy

The project deliberately prioritizes robustness and simplicity over complex reconnection logic.

For a small embedded automation system, a controlled reboot is often the most reliable recovery strategy. After reboot, the standard startup sequence is executed:

1. Connect to Wi‑Fi
2. Synchronize time via NTP
3. Initialize hardware
4. Reconnect to Arduino IoT Cloud
5. Resume normal operation

This strategy has proven effective during testing with simulated Wi‑Fi outages and ensures that the system can recover automatically without user intervention.


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
