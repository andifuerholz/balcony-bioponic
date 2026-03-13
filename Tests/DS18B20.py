from machine import Pin
import onewire, ds18x20, time

ow_pin = 4  # DQ an GPIO4 (anpassen, falls anderer Pin)
ow = onewire.OneWire(Pin(ow_pin))
ds = ds18x20.DS18X20(ow)

roms = ds.scan()
print("Gefundene Sensoren:", roms)

if not roms:
    print("Kein DS18B20 gefunden – Verkabelung prüfen.")
else:
    ds.convert_temp()
    time.sleep_ms(750)  # Messzeit
    for r in roms:
        print("Temp:", ds.read_temp(r), "°C")
