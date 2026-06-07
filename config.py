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

