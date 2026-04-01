Water Level Sensing Subsystem (PCF8574T + Reed Switches)
Overview
The main tank contains a vertical float with six embedded magnets, each positioned at a fixed height.
Along the tank wall, six reed switches are mounted at corresponding levels.
A PCF8574T I/O expander reads the reed switches via I²C, providing a simple and robust way to measure the tank fill level.

Channel 0 = lowest water level
Channel 5 = highest water level
Reeds are normally open
A reed closes (logic 0) when the float’s magnet is at its height
Up to two sensors can be closed simultaneously, which represents the float being between two levels

The goal is to convert the reed states into a 0–100% fill level, rounded to 10% steps.

System Diagram
Reed Sensor Subsystem Architecture
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
                 └──────────────────────────┘   │  │
                                                │  │
PCF8574T Input Pins 0..5  <─────────────────────┘  │
                                                │
SDA (GPIO6)  <──────────────────────────────────┘
SCL (GPIO5)


Electrical Characteristics

PCF8574T inputs are quasi‑bidirectional and feature weak pull‑ups
Reed switches pull the line to GND when closed → logic 0
Open reed → line stays HIGH

This means:




















Reed StatePCF8574 BitInterpretationclosed0level reachedopen1above float

Fill‑Level Algorithm
Rules defined for this system

Reed positions are linearly spaced.
If no reeds are closed → return −1 (tank empty / sensor out of range).
If one or two reeds are closed:

Compute the average of their channel numbers.


Convert the averaged level L to percentage:

percent = (L / 5) * 100


Round to nearest 10%:

rounded = round(percent / 10) * 10


MicroPython Implementation
Reading closed reeds (channels 0..5)
Pythonfrom machine import Pin, I2CADDR = 0x20i2c = I2C(0, scl=Pin(5), sda=Pin(6), freq=100000)def get_closed_reeds():    """Return list of reed channels (0..5) that are closed."""    val = i2c.readfrom(ADDR, 1)[0]    return [pin for pin in range(6) if ((val >> pin) & 1) == 0]Weitere Zeilen anzeigen
Computing the tank fill percentage
Pythondef get_fill_percent():    closed = get_closed_reeds()    if not closed:        return -1  # No reed closed    # Compute average channel (handles 1 or 2 closed sensors)    level = sum(closed) / len(closed)    percent = (level / 5) * 100    percent_10 = int(round(percent / 10) * 10)    return percent_10Weitere Zeilen anzeigen
Example usage
Pythonimport timewhile True:    print("Weitere Zeilen anzeigen

Example Interpretation















































Closed reedsLevel (avg)PercentRoundedOutput{}———−1{0}00%0%0{2}240%40%40{3,4}3.570%70%70{5}5100%100%100

Integration Into the System
Later, the output of get_fill_percent() will be:
