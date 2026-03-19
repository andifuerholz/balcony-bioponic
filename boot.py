# boot.py
# Purpose: Connect to Wi‑Fi at boot and sync UTC time (for TLS).
# Notes:
# - Expects WIFI_LIST in secrets.py: [{'ssid': '...', 'pwd': '...'}, ...]
# - Must run before creating any TLS client (Arduino IoT Cloud, etc.)

import network, logging
from time import sleep, ticks_ms, ticks_diff
from secrets import WIFI_LIST  # list of dicts: {"ssid": "...", "pwd": "..."}

CONNECT_TIMEOUT_MS = 5_000   # timeout per SSID
RETRY_DELAY_S = 0.4          # poll interval during connection attempts

def wifi_connect():
    """
    Try connecting to the configured Wi‑Fi networks in order.
    Returns: network.WLAN instance when connected.
    Raises: Exception if no configured Wi‑Fi is reachable.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    for idx, cred in enumerate(WIFI_LIST, 1):
        ssid = cred.get("ssid")
        pwd = cred.get("pwd")
        if not ssid or not pwd:
            continue

        logging.info("[{}/{}] Trying SSID '{}' …".format(idx, len(WIFI_LIST), ssid))
        try:
            wlan.connect(ssid, pwd)
        except Exception as e:
            logging.warning("connect() error: {}".format(e))
            continue

        t0 = ticks_ms()
        # IMPORTANT: use '<', not HTML-escaped '&lt;'
        while (not wlan.isconnected()) and (ticks_diff(ticks_ms(), t0) < CONNECT_TIMEOUT_MS):
            sleep(RETRY_DELAY_S)

        if wlan.isconnected():
            ip, mask, gw, dns = wlan.ifconfig()
            logging.info("Wi‑Fi connected to '{}' → {} / gw {}".format(ssid, ip, gw))
            return wlan

        # Ensure a clean state before the next attempt
        try:
            wlan.disconnect()
        except Exception:
            pass
        sleep(0.5)

    raise Exception("No configured Wi‑Fi reachable. Check WIFI_LIST in secrets.py")

# 1) Connect to Wi‑Fi at boot
wlan = wifi_connect()

# 2) Sync UTC time (needed for TLS cert validation)
try:
    from time_zh import sync_ntp
    sync_ntp()  # should internally call ntptime.settime() and handle retries
except Exception as e:
    # Do not hard-fail; cloud/TLS may still reconnect later.
    logging.warning("NTP sync failed: {}".format(e))
