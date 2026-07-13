import network
from time import sleep_ms
import settings

ssid = settings.WIFI_SSID
password = settings.WIFI_PASSWORD

def wifi_connect(ssid, password, timeout_ms=15000):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(ssid, password)

        waited = 0
        while not wlan.isconnected() and waited < timeout_ms:
            sleep_ms(250)
            waited += 250

    if not wlan.isconnected():
        raise RuntimeError("WiFi connect failed")

    print("WIFI", wlan.ifconfig())
    return wlan

wifi_connect(ssid, password)
