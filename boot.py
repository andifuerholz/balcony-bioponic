# boot.py
import network, logging
from time import sleep, ticks_ms, ticks_diff
from secrets import WIFI_LIST   # NEW: list of dicts or tuples with ssid/pwd
# WIFI_LIST example in secrets.py:
# WIFI_LIST = [
#     {"ssid": "HomeAP", "pwd": "xxx"},
#     {"ssid": "LabAP",  "pwd": "yyy"},
#     {"ssid": "Phone",  "pwd": "zzz"},
# ]

CONNECT_TIMEOUT_MS = 5_000  # per SSID
RETRY_DELAY_S = 0.4

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    for idx, cred in enumerate(WIFI_LIST, 1):
        ssid = cred["ssid"]; pwd = cred["pwd"]
        if not ssid or not pwd:
            continue

        logging.info(f"[{idx}/{len(WIFI_LIST)}] Trying SSID '{ssid}' …")
        wlan.connect(ssid, pwd)

        t0 = ticks_ms()
        while not wlan.isconnected() and ticks_diff(ticks_ms(), t0) < CONNECT_TIMEOUT_MS:
            sleep(RETRY_DELAY_S)

        if wlan.isconnected():
            ip, mask, gw, dns = wlan.ifconfig()
            logging.info(f"WiFi connected to '{ssid}' → {ip} / gw {gw}")
            return

        # ensure clean state before next attempt
        try:
            wlan.disconnect()
        except Exception:
            pass
        sleep(0.5)

    raise Exception("No configured WiFi reachable. Check WIFI_LIST in secrets.py")

# Run WiFi connection immediately at boot
wifi_connect()

# Sync UTC Time
from time_zh import sync_ntp
sync_ntp()
