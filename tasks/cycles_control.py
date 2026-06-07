# tasks/cycles_control.py
# Cyclic worker for trigger-on-second watering logic with:
# - dynamic pulse duration (seconds) via getter
# - active day window (start/end minutes) via getter
# - publication of the effective seconds set (optional)

from time import sleep, ticks_ms, ticks_diff
from time_zh import localtime_ch


def _minutes_since_midnight(local_tuple):
    """Return minutes since midnight from localtime tuple (Y,M,D,h,m,s,wd,yd)."""
    h, m = local_tuple[3], local_tuple[4]
    return (h * 60 + m) % (24 * 60)


def _within_window(now_m, start_m, end_m):
    """
    Check if now_m (minutes since midnight) lies within [start_m .. end_m),
    supporting windows that cross midnight (start > end).
    """
    if start_m == end_m:
        return False
    if start_m < end_m:
        return start_m <= now_m < end_m
    return (now_m >= start_m) or (now_m < end_m)


def cycles_control_task(
    set_led_fn,
    led_pin,
    poll_ms=100,
    get_temp_fn=None,
    select_secs_fn=None,
    client=None,
    effective_var_name=None,
    get_duration_s_fn=None,
    get_window_minutes_fn=None,
):
    """
    Poll current local second; if within the active window and configured, turn LED ON
    for the configured duration (seconds) on each trigger second. Non-blocking pulses.
    """
    led_active_until = 0
    last_fired_sec = -1
    last_effective = None

    while True:
        try:
            # --- Time ---
            t_local, _, _ = localtime_ch()
            sec = t_local[5]  # Development: seconds
            now_ms = ticks_ms()
            now_m = _minutes_since_midnight(t_local)

            # --- Turn OFF when duration elapsed ---
            if led_active_until and ticks_diff(led_active_until, now_ms) <= 0:
                set_led_fn(led_pin, False)
                led_active_until = 0

            # --- Determine active set ---
            temp_c = get_temp_fn() if get_temp_fn else None
            active_secs = select_secs_fn(temp_c) if select_secs_fn else set()

            # --- Publish effective set (if changed) ---
            if client and effective_var_name is not None:
                eff_tuple = tuple(sorted(active_secs))
                if eff_tuple != last_effective:
                    try:
                        client[effective_var_name] = ','.join(map(str, eff_tuple))
                    except Exception:
                        pass
                    last_effective = eff_tuple

            # --- Window check ---
            in_window = True
            if get_window_minutes_fn:
                try:
                    s_m, e_m = get_window_minutes_fn()
                    in_window = _within_window(now_m, s_m, e_m)
                except Exception:
                    in_window = True  # fail-open

            if not in_window:
                if led_active_until:
                    set_led_fn(led_pin, False)
                    led_active_until = 0
                sleep(poll_ms / 1000.0)
                continue

            # --- Resolve duration ---
            duration_ms = 2000  # fallback
            if get_duration_s_fn:
                try:
                    duration_ms = int(get_duration_s_fn()) * 1000
                except Exception:
                    pass

            # --- Trigger ---
            if (sec in active_secs) and (sec != last_fired_sec):
                set_led_fn(led_pin, True)
                led_active_until = now_ms + duration_ms
                last_fired_sec = sec
                print("[cycles] Fired at second", sec, "for", duration_ms, "ms")

        except Exception as e:
            print("cycles_blink_task error:", e)

        sleep(poll_ms / 1000.0)
