# config.py
# Zuordnung DS18B20-ROM → sprechender Name
# WICHTIG: Keys sind echte bytes (nicht bytearray, kein HTML-Müll wie &lt;)

SENSOR_MAP = {
    b'\x28\x8e\x01\x48\xf6\x75\x3c\xde': 'air',   # Hauptsensor (Luft)
    # Weitere Sensoren später ergänzbar, z.B.:
    # b'\x28\xaa\xbb\xcc\xdd\xee\xff\x01': 'water',
    # b'\x28\x11\x22\x33\x44\x55\x66\x77': 'biofilter',
}

# Optional: Kalibrier-Offsets in °C
OFFSETS = {
    # 'air': 0.0,
    # 'water': -0.2,
    # 'biofilter': +0.1,
}

# Plausibilitätsgrenzen in °C
TEMP_MIN = -20.0
TEMP_MAX =  60.0
