# sensors_ds18b20.py
# Purpose: Read one or multiple DS18B20 sensors on a OneWire bus and publish
# named values to the Arduino IoT Cloud as individual variables (name_temp).

from machine import Pin
import onewire, ds18x20, time
from config import SENSOR_MAP, TEMP_MIN, TEMP_MAX, OFFSETS

SENSOR_PIN_DEFAULT = 4  # DQ on GPIO4, ~4.7–5 kΩ pull‑up to 3V3

def hex_rom(b):
    """Return hex-string representation of a ROM ID (bytes)."""
    return ':'.join(f'{x:02X}' for x in b)

class DS18B20Manager:
    """
    Manage multiple DS18B20 sensors on a OneWire bus and publish named readings
    to the Arduino IoT Cloud as {name}_temp variables.

    Parameters
    ----------
    client : ArduinoCloudClient-like
        Object supporting dict-like assignment: client['var'] = value
    pin : int
        GPIO pin number for the OneWire data line (DQ).
    interval_s : int/float
        Publish interval in seconds.
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
            print("⚠️  No DS18B20 sensors found.")
        else:
            print("DS18B20 ROMs (hex):", [hex_rom(r) for r in self.roms])

    def _read_all(self):
        """
        Convert all sensors, read them individually, filter implausible values,
        and apply per-sensor offsets.

        Returns
        -------
        dict
            {sensor_name: temperature} for mapped sensors;
            hex-keys for unknown sensors (logged only, not published).
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

            # Skip None and out-of-range values
            if t is None or not (TEMP_MIN <= t <= TEMP_MAX):
                continue

            # Map ROM to a friendly name
            name = SENSOR_MAP.get(rom)  # bytes key expected
            if name:
                t = t + OFFSETS.get(name, 0.0)
                vals[name] = round(t, 2)
            else:
                # Unknown sensor: log with hex key (not published)
                vals[hex_rom(rom)] = round(t, 2)

        return vals

    def loop(self):
        """
        Endless loop: read values and publish to cloud variables named {name}_temp.
        Notes:
        - Only mapped (named) sensors are published.
        - Consider checking client connectivity before publishing if the
          cloud client exposes a 'connected' flag.
        """
        while True:
            vals = self._read_all()
            if vals:
                for name, value in vals.items():
                    # Publish only named sensors (str keys); hex keys are logs only.
                    if not isinstance(name, str):
                        continue
                    var_name = f"{name}_temp"
                    try:
                        # Optionally guard with: if getattr(self.client, "connected", False):
                        self.client[var_name] = value
                        # Debug: print(f"{var_name} -> {value}")
                    except Exception as e:
                        # Variable not registered or cloud not ready yet
                        print(f"Publish {var_name} error:", e)
            time.sleep(self.interval_s)
