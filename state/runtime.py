# --- Circuit 3: watering pulse duration (seconds) -----------------------------
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
