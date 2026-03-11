## Table of Contents
- [Hardware](#hardware)
- [Software](#software)
  - [Einleitung](#einleitung)
  - [Core Watering Logic](#core-watering-logic)
  - [Files](#files)
    - #secrets.py

## Hardware

The bioponics system is built from a compact set of components suitable for balcony-scale food production. The hardware includes:

- **Two cultivation channels**, each equipped with six holes for net pots used to grow lettuces and other leafy greens.
- **Two planting containers** for larger crops such as tomatoes or chayote.
- **One water pump** responsible for circulating the nutrient solution through the system.
- **Two water control valves** to regulate flow distribution between the cultivation channels and the planting containers.
- **One Arduino Nano ESP32**, serving as the central microcontroller for automation and pump control.
- **Additional electronic components**, including relays, voltage converters, a power supply, and supporting circuitry.
- **One outdoor temperature sensor (DS18B20)** to measure ambient conditions.
- **One water temperature sensor (DS18B20)** to monitor the nutrient solution temperature.
- **A custom-built water level sensing system**, consisting of six reed switches positioned at different heights.
- **An auxiliary tank with its own pump** to refill or stabilize the main reservoir when required.

## Software

The software running on the Arduino Nano ESP32 is based on MicroPython.  
The system uses several components and external services:

- **MicroPython firmware on the ESP32**, installed using the  
  [Arduino MicroPython Installer](https://labs.arduino.cc/en/labs/micropython-installer)

- **Arduino Cloud**, which provides a graphical user interface (GUI) for monitoring and interaction.

- **Arduino IoT Cloud Python Library**, used to communicate with the Arduino Cloud:  
  https://github.com/arduino/arduino-iot-cloud-py

- A detailed setup guide and example for connecting the ESP32 with MicroPython to Arduino IoT Cloud is available here:  
  *How to Connect the ESP32 MicroPython to Arduino IoT Cloud*  
  https://forum.arduino.cc/t/how-to-connect-the-esp32-micropython-to-arduino-iot-cloud/1234953

The software controls the essential components of the system:

- Reading the two DS18B20 temperature sensors  
- Reading the water‑level system with six reed switches  
- Controlling the main water pump  
- Controlling the auxiliary tank pump  
- Controlling the two water valves

### Einleitung
#### Core Watering Logic

The software controls the watering cycles within a defined daily time window (e.g., from 09:00 to 21:00).  
Within this active period, the pump of each watering circuit is triggered according to a schedule that specifies **at which minutes of the hour** the pump should run.

The configuration is independent for:

- the two watering circuits
- different ranges of outdoor temperature

Example:

If the outdoor temperature is **26 °C**, then at minutes **0, 20, and 40** of each hour, the pump of **circuit 1** is activated for **10 seconds**.

This logic allows the system to adapt its watering frequency to the current temperature conditions.

#### Files
#### `secrets.py`

This file stores all credentials required for Wi‑Fi access and for authentication with the Arduino IoT Cloud.  
It is not part of the public repository and must be created locally by the user.


