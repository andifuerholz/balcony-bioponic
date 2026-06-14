# state/runtime.py

import _thread
from config import (
    DEFAULT_SWITCH_DURATION_S,
    MIN_SWITCH_DURATION_S, MAX_SWITCH_DURATION_S,
    MAX_SWITCH_DURATION_AIR_S,
    DEFAULT_START_HOUR, DEFAULT_END_HOUR
)

# --- Ambient temperature (°C) -------------------------------------------------
_air_temp = None
_air_lock = _thread.allocate_lock()

def set_air_temp(value: float):
    global _air_temp
    with _air_lock:
        _air_temp = float(value)

def get_air_temp(default=None):
    with _air_lock:
        return _air_temp if _air_temp is not None else default


# --- Circuit durations --------------------------------------------------------

_c1_duration_s = DEFAULT_SWITCH_DURATION_S
_c2_duration_s = DEFAULT_SWITCH_DURATION_S
_c3_duration_s = DEFAULT_SWITCH_DURATION_S

_c1_lock = _thread.allocate_lock()
_c2_lock = _thread.allocate_lock()
_c3_lock = _thread.allocate_lock()


def _clamp_duration_water(v):
    return max(MIN_SWITCH_DURATION_S, min(int(v), MAX_SWITCH_DURATION_S))

def _clamp_duration_air(v):
    return max(MIN_SWITCH_DURATION_S, min(int(v), MAX_SWITCH_DURATION_AIR_S))


def set_c1_duration_s(v_s: int):
    global _c1_duration_s
    try:
        v = _clamp_duration(v_s)
        with _c1_lock:
            _c1_duration_s = v
    except:
        pass

def get_c1_duration_s() -> int:
    with _c1_lock:
        return int(_c1_duration_s)

def get_c1_duration_ms() -> int:
    with _c1_lock:
        return int(_c1_duration_s) * 1000


def set_c2_duration_s(v_s: int):
    global _c2_duration_s
    try:
        v = _clamp_duration(v_s)
        with _c2_lock:
            _c2_duration_s = v
    except:
        pass

def get_c2_duration_s() -> int:
    with _c2_lock:
        return int(_c2_duration_s)


def set_c3_duration_s(v_s: int):
    global _c3_duration_s
    try:
        v = _clamp_duration_air(v_s)
        with _c3_lock:
            _c3_duration_s = v
    except:
        pass

def get_c3_duration_s() -> int:
    with _c3_lock:
        return int(_c3_duration_s)


# --- Active day window --------------------------------------------------------

_start_minutes = DEFAULT_START_HOUR * 60
_end_minutes   = DEFAULT_END_HOUR   * 60
_win_lock = _thread.allocate_lock()

def set_active_window_minutes(start_m: int, end_m: int):
    global _start_minutes, _end_minutes
    try:
        s = int(start_m) % (24 * 60)
        e = int(end_m)   % (24 * 60)
        with _win_lock:
            _start_minutes, _end_minutes = s, e
    except:
        pass

def get_active_window_minutes():
    with _win_lock:
        return _start_minutes, _end_minutes


# --- Refill -------------------------------------------------------------------

_refill_request = False
_refill_time_s = 10
_refill_lock = _thread.allocate_lock()

def trigger_refill():
    global _refill_request
    with _refill_lock:
        _refill_request = True

def consume_refill_request():
    global _refill_request
    with _refill_lock:
        if _refill_request:
            _refill_request = False
            return True
    return False

def set_refill_time_s(v):
    global _refill_time_s
    try:
        v = max(1, min(int(v), 600))
        with _refill_lock:
            _refill_time_s = v
    except:
        pass

def get_refill_time_s():
    with _refill_lock:
        return _refill_time_s

