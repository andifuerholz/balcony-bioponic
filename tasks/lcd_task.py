from time import sleep, ticks_ms, ticks_diff
from time_zh import localtime_ch
from cloud.callbacks import seconds_for_temp
from state.runtime import get_air_temp
import tankReeds


# -------------------------------------------------
# Helper: Countdown bis zum nächsten Trigger
# -------------------------------------------------
def seconds_until_next_trigger(current_sec, active_secs):
    if not active_secs:
        return 99

    future = sorted(s for s in active_secs if s > current_sec)

    if future:
        return future[0] - current_sec

    return (60 - current_sec) + min(active_secs)


# -------------------------------------------------
# Helper: Padding auf 16 Zeichen
# -------------------------------------------------
def pad(s, n=16):
    if len(s) >= n:
        return s[:n]
    return s + " " * (n - len(s))


# -------------------------------------------------
# Formatierung
# -------------------------------------------------
def format_line1(c1_cd, hh, mm, ss):
    return f"K1:{c1_cd:02d} {hh:02d}:{mm:02d}:{ss:02d}"


def format_line2(c2_cd, temp, tank):
    # Tank
    if tank is not None and tank >= 0:
        tank_str = f"{int(tank):02d}%"
    else:
        tank_str = "--%"

    # Temperatur
    if temp is not None:
        temp_str = f"{int(temp):02d}C"
    else:
        temp_str = "--C"

    return f"K2:{c2_cd:02d} {tank_str}  {temp_str}"


# -------------------------------------------------
# LCD Task
# -------------------------------------------------
def lcd_task(lcd, i2c, period_s=1):
    last_init = 0

    while True:
        now = ticks_ms()

        # --- Re-Init alle 5 Sekunden ---
        if ticks_diff(now, last_init) > 5000:
            try:
                lcd._init_lcd()
                print("[LCD] periodic reinit")
            except Exception:
                pass
            last_init = now

        try:
            # --- Zeit ---
            t_local, _, _ = localtime_ch()
            hh, mm, ss = t_local[3], t_local[4], t_local[5]

            # --- Temperatur ---
            temp = get_air_temp()

            # --- Trigger-Sekunden ---
            secs_c1 = seconds_for_temp('c1', temp)
            secs_c2 = seconds_for_temp('c2', temp)

            # --- Countdown ---
            c1_cd = seconds_until_next_trigger(ss, secs_c1)
            c2_cd = seconds_until_next_trigger(ss, secs_c2)

            c1_cd = min(99, c1_cd)
            c2_cd = min(99, c2_cd)

            # --- Tank ---
            tank = tankReeds.get_fill_percent()

            # --- Formatierung ---
            line1 = format_line1(c1_cd, hh, mm, ss)
            line2 = format_line2(c2_cd, temp, tank)

            # --- Ausgabe ---
            lcd.setCursor(0, 0)
            lcd.printout(pad(line1))

            lcd.setCursor(0, 1)
            lcd.printout(pad(line2))

        except Exception as e:
            print("[LCD] error:", e)

        sleep(period_s)
