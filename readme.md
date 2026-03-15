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

## Hardware

The bioponics system is built from a set of components aiming for a balcony-scale food production. The hardware includes:

- **Two cultivation channels**, each equipped with six holes for net pots used to grow lettuces and other leafy greens.
- **Two planting containers** for larger crops such as tomatoes or chayote.
- **One 15l water tank** containing the nutrient solution.
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
(Files of Arduino IoT Cloud Python Library and its dependencies are not listed)

#### `secrets.py`
This file stores all credentials required for Wi‑Fi access and for authentication with the Arduino IoT Cloud.  
It is not part of the public repository and must be created locally by the user.
#### `boot.py`
...
#### `main.py`
...

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
2. Continuously reading temperature sensors and deriving 10‑minute average values  
3. Manual control of two water circuits for a defined duration  
4. Adding automatic control based on defined time intervals  
5. Measuring the water level in the main water tank  
6. Controlling a pump from the auxiliary tank to refill the main tank  
7. Automatic refilling from the auxiliary tank

### Learning Goals
1. Understanding how to set up and run the basic hardware and software components  
2. Learning how to design an appropriate control structure (e.g., a state machine) for reading sensors and controlling actuators  
3. Understanding how to integrate real‑world constraints (timing, temperature thresholds, water levels


## Appendix
### ESP32 Wiring
![Arduino Nano ESP32 wiring](https://github.com/andifuerholz/balcony-bioponic/blob/bc93deddbc6b00784411bc56c6c973a75ff1a4b9/img/Arduino%20Nano%20ESP32%20connection.jpg?raw=true)

#### Connecting a DS18B20 Temperature Sensor to the Arduino Nano ESP32

#### Getting ROMs
```python
import onewire, ds18x20
from machine import Pin
ow = onewire.OneWire(Pin(4))     # dein Bus-Pin
ds = ds18x20.DS18X20(ow)
print("Gefundene ROMs:", ds.scan())

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
