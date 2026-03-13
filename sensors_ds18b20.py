# sensors_ds18b20.py
from machine import Pin
import onewire, ds18x20, time, json
from config import SENSOR_MAP, TEMP_MIN, TEMP_MAX  # dein Mapping/Grenzen

SENSOR_PIN = 4  # DQ an GPIO4 (A3 ~D20)

class DS18B20Manager:
    def __init__(self, client, pin=SENSOR_PIN, interval_s=2, publish_json_var='temps_json'):
        self.client = client
        self.interval_s = interval_s
        self.publish_json_var = publish_json_var
        self.ow = onewire.OneWire(Pin(pin))
        self.ds = ds18x20.DS18X20(self.ow)
        self.roms = self.ds.scan()
        print("DS18B20 ROMs:", self.roms)

    def _read_all(self):
        vals = {}
        if not self.roms:
            return vals
        self.ds.convert_temp()
        time.sleep_ms(750)
        for rom in self.roms:
            try:
                t = self.ds.read_temp(rom)
                if t is None:
                    continue
                if TEMP_MIN <= t <= TEMP_MAX:
                    name = SENSOR_MAP.get(rom, None)
                    key = name if name else rom  # ungemappt → ROM als Key
                    vals[key] = round(t, 2)
            except Exception as e:
                print("Read error:", e)
        return vals

    def loop(self):
        while True:
            vals = self._read_all()
            if vals:
                # Einzelvariablen (optional, wenn existieren)
                if 'air' in vals and 'air_temp' in self.client.vars:
                    self.client['air_temp'] = vals['air']
                if 'water' in vals and 'water_temp' in self.client.vars:
                    self.client['water_temp'] = vals['water']
                # Gesamtsicht als JSON (nur benannte Sensoren)
                named = {k: v for k, v in vals.items() if isinstance(k, str)}
                if named and self.publish_json_var in self.client.vars:
                    self.client[self.publish_json_var] = json.dumps(named)
            time.sleep(self.interval_s)
