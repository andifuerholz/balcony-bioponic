# time_zh.py
# NTP-Sync und Lokalzeit für Europe/Zurich (CET/CEST)

import time
import ntptime

def sync_ntp(retries=3, delay_s=1):
    """Setzt die Systemzeit via NTP (UTC). Gibt True/False zurück."""
    for _ in range(retries):
        try:
            ntptime.settime()
            return True
        except:
            time.sleep(delay_s)
    return False

def _last_sunday(year, month):
    """Letzter Sonntag im Monat (0=Mo..6=So)."""
    # Tag 0 des nächsten Monats ist letzter Tag des aktuellen Monats
    if month == 12:
        y2, m2 = year + 1, 1
    else:
        y2, m2 = year, month + 1
    last_day_tuple = time.localtime(
        time.mktime((y2, m2, 1, 0, 0, 0, 0, 0)) - 24 * 3600
    )
    d = last_day_tuple[2]
    wd = last_day_tuple[6]  # 0=Mo..6=So
    d -= (wd - 6) % 7
    return d

def _is_dst_europe_zh(t_utc):
    """Sommerzeitregel für Europe/Zurich. t_utc ist ein time.localtime()-Tuple (UTC)."""
    y, m, d, hh = t_utc[0], t_utc[1], t_utc[2], t_utc[3]
    if m < 3 or m > 10:
        return False
    if 4 <= m <= 9:
        return True
    # März/Oktober Grenztage (Wechsel 01:00 UTC)
    if m == 3:
        sw_day = _last_sunday(y, 3)
        if d > sw_day: return True
        if d < sw_day: return False
        return hh >= 1  # ab 01:00 UTC -> DST an
    if m == 10:
        sw_day = _last_sunday(y, 10)
        if d > sw_day: return False
        if d < sw_day: return True
        return hh < 1   # bis 00:59 UTC -> DST an
    return False

def localtime_ch():
    """
    Gibt (t_local, offset_hours, tz_str) zurück.
    t_local = time.localtime() in Lokalzeit (Europe/Zurich),
    offset_hours = 1 (CET) oder 2 (CEST),
    tz_str = "CET" oder "CEST".
    """
    t_utc = time.localtime()  # nach NTP ist das UTC
    offset = 2 if _is_dst_europe_zh(t_utc) else 1
    t_local = time.localtime(time.mktime(t_utc) + offset * 3600)
    tz = "CEST" if offset == 2 else "CET"
    return t_local, offset, tz
