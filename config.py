# config.py
# Purpose: Map DS18B20 ROM IDs to human-readable sensor names and define
# offsets and plausibility limits for temperature readings.

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
    # 'air': 0.0,
    # 'water': -0.2,
    # 'biofilter': +0.1,
}

# Plausibility limits in °C
# Values outside this range will be discarded.
TEMP_MIN = -20.0
TEMP_MAX =  60.0
