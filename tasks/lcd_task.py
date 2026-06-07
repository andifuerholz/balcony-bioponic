from time import sleep, ticks_ms, ticks_diff
from time_zh import localtime_ch
from config import LCD_ADDR

def lcd_present(i2c):
    try:
        return LCD_ADDR in i2c.scan()
    except Exception:
        return False


def lcd_task(lcd, i2c, period_s=1):
    alive = False
    last_try = 0

    while True:
        now = ticks_ms()

        present = lcd_present(i2c)

        if not present:
            alive = False
            sleep(period_s)
            continue

        # --- Reinit wenn nötig ---
        if not alive and ticks_diff(now, last_try) > 5000:
            try:
                lcd._init_lcd()
                alive = True
                print("[LCD] reinitialized")
            except Exception as e:
                print("[LCD] init failed:", e)
                last_try = now
                sleep(period_s)
                continue

        # --- Anzeige ---
        try:
            t_local, _, _ = localtime_ch()
            hh, mm, ss = t_local[3], t_local[4], t_local[5]

            timestr = f"{hh:02d}:{mm:02d}:{ss:02d}"

            lcd.clear()
            lcd.setCursor(0, 0)
            lcd.printout(timestr)

        except Exception as e:
            print("[LCD] error → will reinit:", e)
            alive = False

        sleep(period_s)
