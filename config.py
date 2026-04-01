# config.py
# Central configuration for pins, timing, and DS18B20 sensor mapping/calibration.

# ---------------------------------
# Hardware pins & timing parameters
# ---------------------------------
LED_PIN = 48
ACTIVE_LOW = False
DS18B20_PIN = 4


# I2C Pin setting
I2C_SCL_PIN = 5
I2C_SDA_PIN = 6

# I2C Addresses
PCF8574_ADDR = 0x20

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
