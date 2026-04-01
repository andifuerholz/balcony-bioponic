# Tests/test_i2c.py

from machine import Pin, I2C
import time

ADDR = 0x20

i2c = I2C(0, scl=Pin(5), sda=Pin(6), freq=100000)

def get_closed_reeds():
    """Gibt die Liste geschlossener Reeds auf Kanälen 0..5 zurück."""
    val = i2c.readfrom(ADDR, 1)[0]
    return [pin for pin in range(6) if ((val >> pin) & 1) == 0]


def get_fill_percent():
    closed = get_closed_reeds()

    if not closed:
        return -1   # kein Sensor geschlossen

    # Mittelwert der Kanäle
    level = sum(closed) / len(closed)

    # Umrechnen in Prozent
    percent = (level / 5) * 100

    # Auf 10% runden
    percent_10 = int(round(percent / 10) * 10)

    return percent_10


while True:
    value = get_fill_percent()
    print("Füllstand:", value, "%")
    time.sleep(0.5)
