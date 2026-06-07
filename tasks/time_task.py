# tasks/time_task.py

import time
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

    last_status = None   # ✅ NEU

    while True:
        try:
            # 1) Zeit
            t_local, _, tz = localtime_ch()
            client["time_zh"] = _fmt_time_str(t_local, tz)

            # 2) Sensoren
            ds18_manager.read_and_publish_once()

            # 3) Tanklevel
            lvl = get_fill_percent()
            if lvl is not None and lvl >= 0:
                client["tankLevel"] = lvl


        except Exception as e:
            print("time_and_temp_task error:", e)

        time.sleep(period_s if period_s and period_s > 0 else 1)
