# state/runtime.py
# Thread-safe runtime state for ambient temperature, watering pulse duration,
# and the active day window (start/end time). Values are updated via cloud callbacks.

import _thread
from config import (
    DEFAULT_C1_SWITCH_DURATION_S,
    MIN_SWITCH_DURATION_S, MAX_SWITCH_DURATION_S,
    DEFAULT_START_HOUR, DEFAULT_END_HOUR
)

# --- Ambient temperature (°C) -------------------------------------------------
_air_temp = None
_air_lock = _thread.allocate_lock()

def set_air_temp(value: float):
    """Update last known ambient temperature (°C)."""
    global _air_temp
    with _air_lock:
        _air_temp = float(value)

def get_air_temp(default=None):
    """Get last known ambient temperature (°C) or default if unknown."""
    with _air_lock:
        return _air_temp if _air_temp is not None else default

# --- Circuit 1: watering pulse duration (seconds) -----------------------------
_c1_duration_s = DEFAULT_C1_SWITCH_DURATION_S
_c1_lock = _thread.allocate_lock()

def set_c1_duration_s(v_s: int):
    """
    Set watering pulse duration for circuit 1 in *seconds*.
    Value is clamped to [MIN_SWITCH_DURATION_S .. MAX_SWITCH_DURATION_S].
    """
    global _c1_duration_s
    try:
        v = int(v_s)
    except Exception:
        return
    v = max(MIN_SWITCH_DURATION_S, min(v, MAX_SWITCH_DURATION_S))
    with _c1_lock:
        _c1_duration_s = v

def get_c1_duration_s() -> int:
    """Get watering pulse duration for circuit 1 (seconds)."""
    with _c1_lock:
        return int(_c1_duration_s)

def get_c1_duration_ms() -> int:
    """Convenience: circuit 1 duration in milliseconds."""
    with _c1_lock:
        return int(_c1_duration_s) * 1000
    
# --- Circuit 2: watering pulse duration (seconds) -----------------------------

_c2_duration_s = DEFAULT_C1_SWITCH_DURATION_S   # gleicher Default ok
_c2_lock = _thread.allocate_lock()

def set_c2_duration_s(v_s: int):
    global _c2_duration_s
    try:
        v = int(v_s)
    except Exception:
        return
    v = max(MIN_SWITCH_DURATION_S, min(v, MAX_SWITCH_DURATION_S))
    with _c2_lock:
        _c2_duration_s = v

def get_c2_duration_s() -> int:
    with _c2_lock:
        return int(_c2_duration_s)
    
# --- Circuit 3: air pump pulse duration (seconds) -----------------------------
_c3_duration_s = DEFAULT_C1_SWITCH_DURATION_S   # gleicher Default ok
_c3_lock = _thread.allocate_lock()

def set_c3_duration_s(v_s: int):
    global _c3_duration_s
    try:
        v = int(v_s)
    except Exception:
        return
    v = max(MIN_SWITCH_DURATION_S, min(v, MAX_SWITCH_DURATION_S))
    with _c3_lock:
        _c3_duration_s = v

def get_c3_duration_s() -> int:
    with _c3_lock:
        return int(_c3_duration_s)
    

# --- Active day window (start/end minutes after midnight) ---------------------
# Stored as minutes since midnight [0..1439]. Default 07:00..21:00.
_start_minutes = DEFAULT_START_HOUR * 60
_end_minutes   = DEFAULT_END_HOUR   * 60
_win_lock = _thread.allocate_lock()

def set_active_window_minutes(start_m: int, end_m: int):
    """
    Update active window as minutes since midnight (0..1439).
    Values are normalized into the valid range; no constraint that start < end:
    if start > end, the window crosses midnight (e.g., 22:00..06:00).
    """
    global _start_minutes, _end_minutes
    try:
        s = int(start_m) % (24 * 60)
        e = int(end_m)   % (24 * 60)
    except Exception:
        return
    with _win_lock:
        _start_minutes, _end_minutes = s, e

def get_active_window_minutes():
    """Return (start_minutes, end_minutes), both in [0..1439]."""
    with _win_lock:
        return _start_minutes, _end_minutes
