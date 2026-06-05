# hw/relay.py
from machine import Pin
from config import RELAY_ACTIVE_LOW

def make_relay(pin_number: int):
    """Create relay pin, OFF by default."""
    p = Pin(pin_number, Pin.OUT)
    if RELAY_ACTIVE_LOW:
        p.value(1)  # OFF
    else:
        p.value(0)  # OFF
    return p

def set_relay(pin, on: bool):
    """Switch relay ON/OFF respecting polarity."""
    if RELAY_ACTIVE_LOW:
        pin.value(0 if on else 1)
    else:
        pin.value(1 if on else 0)
