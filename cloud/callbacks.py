# cloud/callbacks.py
# Cloud variable on_write handlers and profile parsing utilities.
# Adds handlers for:
# - switchDuration_circuit_1 (seconds, integer)
# - startHour / endHour (Arduino Cloud "Time" type; robust parsing)

import _thread

# Per-circuit state for seconds selection
_state = {
    'c1': {'profiles': None, 'secs': set()},
    'c2': {'profiles': None, 'secs': set()},
}
_lock = _thread.allocate_lock()

# ---------- Utility: CSV "seconds" parser ----------
def parse_cycle_seconds(s: str):
    """Parse CSV '5, 10, 20' -> {5,10,20}; clamp to 0..59; ignore junk."""
    secs = set()
    if not s:
        return secs
    for part in str(s).split(','):
        part = part.strip()
        if not part:
            continue
        try:
            v = int(part)
            if 0 <= v <= 59:
                secs.add(v)
        except Exception:
            pass
    return secs

def _parse_profile_line(line: str):
    """
    One line '20°C: 0, 20, 40' or '25: 0,15,30,45'
    Returns (threshold:int, seconds:set[int]) or None on parse failure.
    """
    if ':' not in line:
        return None
    left, right = line.split(':', 1)
    left = left.strip().replace('°C', '').replace('°', '')
    try:
        thr = int(left)
    except Exception:
        return None
    secs = parse_cycle_seconds(right)
    return thr, secs

def parse_temp_profiles(text: str):
    """
    Multi-line string with threshold profiles.
    Returns sorted list of (threshold, seconds) by ascending threshold.
    If parse fails, returns None.
    """
    if not isinstance(text, str):
        text = str(text)
    items = []
    # Be tolerant: allow either newline or ';' as separators
    for chunk in text.replace(';', '\n').splitlines():
        line = chunk.strip()
        if not line:
            continue
        item = _parse_profile_line(line)
        if item:
            items.append(item)
    if not items:
        return None
    # Deduplicate thresholds: keep last occurrence of each threshold
    dedup = {}
    for thr, secs in items:
        dedup[thr] = set(secs)
    return sorted(((thr, dedup[thr]) for thr in dedup), key=lambda x: x[0])

def _update_circuit_from_text(c_key: str, text: str):
    prof = parse_temp_profiles(text)
    with _lock:
        if prof:
            _state[c_key]['profiles'] = prof
            _state[c_key]['secs'] = set()  # clear legacy
            print(f"[{c_key}] thresholds:", [thr for thr, _ in prof])
        else:
            _state[c_key]['profiles'] = None
            _state[c_key]['secs'] = parse_cycle_seconds(text)
            print(f"[{c_key}] legacy seconds:", sorted(_state[c_key]['secs']))
            

def onCycles1Change(client, value):
    """on_write for 'cycles_circuit_1' (string)."""
    _update_circuit_from_text('c1', value if isinstance(value, str) else str(value))

def onCycles2Change(client, value):
    """on_write for 'cycles_circuit_2' (string)."""
    _update_circuit_from_text('c2', value if isinstance(value, str) else str(value))

def seconds_for_temp(c_key: str, temp_c):
    """
    Return active seconds for given temperature for the given circuit key ('c1'/'c2').
    Rule: use the profile with the highest threshold <= temp_c.
    If no profile is configured, fall back to the legacy seconds set.
    If temp is None, use the lowest-threshold profile (if present).
    """
    with _lock:
        prof = _state[c_key]['profiles']
        if not prof:
            return set(_state[c_key]['secs'])
        if temp_c is None:
            return set(prof[0][1]) if prof else set()
        active = set()
        for thr, secs in prof:
            if temp_c >= thr:
                active = secs
            else:
                break
        return set(active)

# ---------- loud handlers for duration & time window ----------

import time

def _timestamp_to_minutes_since_midnight(ts_utc):
    """
    Convert POSIX timestamp (UTC) to local CH time (CET/CEST)
    and return minutes since midnight.
    """
    try:
        # In lokale Zeit wandeln (MicroPython kennt Zeitzone via time_zh)
        lt = time.localtime(int(ts_utc))

        hour = lt[3]
        minute = lt[4]
        return hour * 60 + minute
    except Exception as e:
        print("timestamp conversion error:", e)
        return None


def _parse_time_var_to_minutes(value):
    """
    Parse Arduino Cloud 'Time' variable into minutes since midnight [0..1439].
    Accepts:
      - "HH:MM" or "HH:MM:SS" strings
      - mapping with keys {'hour','minute'(,'second')}
      - tuple/list (h, m) or (h, m, s)
    Returns int minutes or None on failure.
    """
    h = m = None
    # String form
    if isinstance(value, str):
        parts = value.strip().split(':')
        if len(parts) >= 2:
            try:
                h = int(parts[0]); m = int(parts[1])
            except Exception:
                return None
    # Mapping form
    elif hasattr(value, 'get'):
        try:
            h = int(value.get('hour'))
            m = int(value.get('minute'))
        except Exception:
            return None
    # Sequence form
    elif isinstance(value, (tuple, list)):
        try:
            h = int(value[0]); m = int(value[1])
        except Exception:
            return None
    else:
        return None

    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return (h * 60 + m) % (24 * 60)

def onC1DurationChange(client, value):
    """
    on_write for 'switchDuration_circuit_1' (seconds, integer).
    Clamped in state layer.
    """
    try:
        from state.runtime import set_c1_duration_s
        set_c1_duration_s(int(value))
        print(f"[c1] switch duration set to {int(value)} s")
    except Exception as e:
        print("onC1DurationChange error:", e)
        

def onC2DurationChange(client, value):
    try:
        from state.runtime import set_c2_duration_s
        set_c2_duration_s(int(value))
        print(f"[c2] switch duration set to {int(value)} s")
    except Exception as e:
        print("onC2DurationChange error:", e)


def onStartHourChange(client, value):
    try:
        print("[DEBUG] raw startHour payload:", value)

        from state.runtime import get_active_window_minutes, set_active_window_minutes

        # POSIX-Zeitstempel in Minuten überführen
        m = _timestamp_to_minutes_since_midnight(value)
        if m is None:
            print("onStartHourChange: invalid timestamp:", value)
            return

        # Fenster aktualisieren
        _, end_m = get_active_window_minutes()
        set_active_window_minutes(m, end_m)

        print(f"[window] start set to {m//60:02d}:{m%60:02d}")

    except Exception as e:
        print("onStartHourChange error:", e)
        

def onEndHourChange(client, value):
    try:
        print("[DEBUG] raw endHour payload:", value)

        from state.runtime import get_active_window_minutes, set_active_window_minutes

        m = _timestamp_to_minutes_since_midnight(value)
        if m is None:
            print("onEndHourChange: invalid timestamp:", value)
            return

        start_m, _ = get_active_window_minutes()
        set_active_window_minutes(start_m, m)

        print(f"[window] end set to {m//60:02d}:{m%60:02d}")

    except Exception as e:
        print("onEndHourChange error:", e)
