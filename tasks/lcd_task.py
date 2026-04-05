#lcd_task.py

# tasks/lcd_task.py
# Minimal LCD task: show only current local time (Europe/Zurich).

import time
from time_zh import localtime_ch

def lcd_task(lcd, period_s=1):
    """
    Update the LCD every period_s seconds with local time.
    lcd: instance of LCD1602.
    """
    while True:
        try:
            t_local, _, tz = localtime_ch()  # (Y M D h m s wd yd)
            hh = t_local[3]
            mm = t_local[4]
            ss = t_local[5]

            # Build "HH:MM:SS" string
            timestr = f"{hh:02d}:{mm:02d}:{ss:02d}"

            lcd.clear()
            lcd.setCursor(0, 0)
            lcd.printout(timestr)

        except Exception as e:
            # Minimal fallback; avoid crashing the thread
            try:
                lcd.clear()
                lcd.setCursor(0, 0)
                lcd.printout("LCD error")
            except:
                pass

        time.sleep(period_s)

