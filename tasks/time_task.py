# tasks/time_task.py

import time
import network
from machine import reset

from time_zh import localtime_ch
from tankReeds import get_fill_percent


def _fmt_time_str(t_local, tz_str):
    Y, M, D, hh, mm, ss = (
        t_local[0],
        t_local[1],
        t_local[2],
        t_local[3],
        t_local[4],
        t_local[5],
    )
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} {}".format(
        Y, M, D, hh, mm, ss, tz_str
    )


def time_and_temp_task(client, ds18_manager, period_s=1):

    # Initial publish
    try:
        t_local, _, tz = localtime_ch()
        client["time_zh"] = _fmt_time_str(t_local, tz)
    except:
        pass

    wlan = network.WLAN(network.STA_IF)

    wifi_lost_since = None
    last_daily_reset_date = None

    while True:
        try:
            # 1) Zeit
            t_local, _, tz = localtime_ch()
            client["time_zh"] = _fmt_time_str(t_local, tz)

            # Täglicher Neustart um 06:00
            Y, M, D, hh, mm, ss = t_local[:6]

            if hh == 6 and mm == 0:
                today = (Y, M, D)

                if today != last_daily_reset_date:
                    print("Daily 06:00 reboot")
                    last_daily_reset_date = today
                    time.sleep(2)
                    reset()

            # 2) WLAN überwachen
            if wlan.isconnected():
                if wifi_lost_since is not None:
                    print("WiFi restored")
                wifi_lost_since = None

            else:
                if wifi_lost_since is None:
                    wifi_lost_since = time.time()
                    print("WiFi lost")

                else:
                    lost_seconds = int(time.time() - wifi_lost_since)

                    if lost_seconds % 60 == 0:
                        print("WiFi down for", lost_seconds, "seconds")

                    if lost_seconds >= 300:
                        print("WiFi down for 5 minutes -> reboot")
                        time.sleep(2)
                        reset()

            # 3) Sensoren
            ds18_manager.read_and_publish_once()

            # 4) Tanklevel
            lvl = get_fill_percent()
            if lvl is not None and lvl >= 0:
                client["tankLevel"] = lvl

        except Exception as e:
            print("time_and_temp_task error:", e)

        time.sleep(period_s if period_s and period_s > 0 else 1)

