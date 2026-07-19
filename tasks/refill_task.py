# tasks/refill_task.py

from time import ticks_ms, ticks_diff, sleep
from tankReeds import get_fill_percent

def refill_task(
    set_actuator_fn,
    actuator,
    poll_ms,
    consume_request_fn,
    get_duration_s_fn,
    client=None
):
    active_until = 0

    while True:
        now = ticks_ms()

        # --- Stop bei >= 90% ---
        if active_until:
            lvl = get_fill_percent()

            if lvl is not None and lvl >= 90:
                set_actuator_fn(actuator, False)
                active_until = 0
                print("[REFILL] stopped at", lvl, "%")

                try:
                    if client:
                        client["refill_tank"] = False
                except Exception as e:
                    print("[REFILL] reset failed:", e)

        # --- OFF wenn Zeit vorbei ---
        if active_until and ticks_diff(active_until, now) <= 0:
            set_actuator_fn(actuator, False)
            active_until = 0
            print("[REFILL] completed")

            try:
                if client:
                    client["refill_tank"] = False
            except Exception as e:
                print("[REFILL] reset failed:", e)

        # --- Trigger prüfen ---
        if consume_request_fn():

            lvl = get_fill_percent()

            if lvl is not None and lvl >= 90:
                print("[REFILL] ignored, tank already at", lvl, "%")

                try:
                    if client:
                        client["refill_tank"] = False
                except Exception as e:
                    print("[REFILL] reset failed:", e)

            elif active_until:
                print("[REFILL] already running - ignoring trigger")

            else:
                duration_ms = int(get_duration_s_fn()) * 1000
                set_actuator_fn(actuator, True)
                active_until = now + duration_ms
                print("[REFILL] started for", duration_ms, "ms")

        sleep(poll_ms / 1000.0)
