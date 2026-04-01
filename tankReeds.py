# tankReeds.py
# Water level sensing using PCF8574T

from config import PCF8574_ADDR

_i2c = None
_last_valid = None


def init(i2c):
    """Initialize module with shared I2C bus."""
    global _i2c
    _i2c = i2c


def _read_raw():
    """Read raw byte from PCF8574T. Returns None on error."""
    global _i2c
    if _i2c is None:
        return None
    try:
        return _i2c.readfrom(PCF8574_ADDR, 1)[0]
    except Exception:
        return None


def get_closed_reeds():
    """Return list of reed channels (0..5) that are closed; None on read error."""
    raw = _read_raw()
    if raw is None:
        return None
    return [pin for pin in range(6) if ((raw >> pin) & 1) == 0]


def get_fill_percent():
    """
    Convert closed reed channels to tank fill percent (0..100).
    Returns last valid value if no valid reading is available.
    -1 means: do not publish.
    """
    global _last_valid

    reeds = get_closed_reeds()
    if reeds is None:
        return _last_valid

    if len(reeds) == 0:
        return _last_valid

    level = sum(reeds) / len(reeds)
    percent = (level / 5) * 100
    rounded = int(round(percent / 10) * 10)

    _last_valid = rounded
    return rounded

