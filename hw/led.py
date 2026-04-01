# hw/led.py
from machine import Pin
from config import LED_PIN, ACTIVE_LOW

def make_led():
    """Create and return the LED Pin object, OFF by default."""
    p = Pin(LED_PIN, Pin.OUT)
    p.value(1 if ACTIVE_LOW else 0)
    return p

def set_led(pin, on: bool):
    """Set LED ON/OFF respecting polarity."""
    if ACTIVE_LOW:
        pin.value(0 if on else 1)
    else:
        pin.value(1 if on else 0)
