# Water Level Sensing Subsystem (PCF8574T + Reed Switches)

## Overview

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

## System Diagram

### Reed Sensor Subsystem Architecture

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
                 └──────────────────────────┘   │  │
                                                │  │
PCF8574T Input Pins 0..5  <─────────────────────┘  │
                                                │
SDA (GPIO6)  <──────────────────────────────────┘
SCL (GPIO5)
```

---

## Electrical Characteristics

- PCF8574T inputs are **quasi‑bidirectional** and include **weak pull‑ups**  
- Reed switches pull the line to **GND when closed → logic 0**  
- Open reed → line stays **HIGH**

Mapping:

| Reed State | PCF8574 Bit | Interpretation |
|-----------|--------------|----------------|
| closed    | 0            | level reached |
| open      | 1            | above float |

---

## Fill‑Level Algorithm

### Rules

1. Reed positions are **linearly spaced**.
2. If **no reeds** are closed → return **−1**.
3. One or two reeds may be closed.
4. Compute the **average** channel number.
5. Convert to percent:

```
percent = (level / 5) * 100
```

6. Round to **nearest 10%**:

```
rounded = round(percent / 10) * 10
```

---

## MicroPython Implementation

### Reading closed reeds (channels 0..5)

```python
from machine import Pin, I2C

ADDR = 0x20
i2c = I2C(0, scl=Pin(5), sda=Pin(6), freq=100000)

def get_closed_reeds():
    """Return list of reed channels (0..5) that are closed."""
    val = i2c.readfrom(ADDR, 1)[0]
    return [pin for pin in range(6) if ((val >> pin) & 1) == 0]
```

### Computing the tank fill percentage

```python
def get_fill_percent():
    closed = get_closed_reeds()

    if not closed:
        return -1  # No reed closed

    # Compute average channel (handles 1 or 2 closed sensors)
    level = sum(closed) / len(closed)

    percent = (level / 5) * 100
    percent_10 = int(round(percent / 10) * 10)

    return percent_10
```

### Example usage

```python
import time

while True:
    print("Fill level:", get_fill_percent(), "%")
    time.sleep(0.5)
```

---

## Example Interpretation

| Closed reeds | Level (avg) | Percent | Rounded | Output |
|--------------|-------------|---------|---------|---------|
| `{}`         | —           | —       | —       | **−1** |
| `{0}`        | 0           | 0%      | 0%      | 0 |
| `{2}`        | 2           | 40%     | 40%     | 40 |
| `{3,4}`      | 3.5         | 70%     | 70%     | 70 |
| `{5}`        | 5           | 100%    | 100%    | 100 |

---

## Integration Into the System

Later, the output of `get_fill_percent()` will be:

- added into the **runtime state layer**
- published to **Arduino Cloud** via a dedicated variable
- used by the **automation logic** to control refilling from the auxiliary tank

A dedicated module (e.g. `water_level.py`) can be generated on request.
