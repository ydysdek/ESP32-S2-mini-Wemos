# app_tx_legacy.py

from machine import Pin
from time import sleep_ms

from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG
try:
    from settings import TX_INTERVAL_MS
except ImportError:
    TX_INTERVAL_MS = 1000

def panic_blink(led, on=80, off=80):
    while True:
        led.on()
        sleep_ms(on)
        led.off()
        sleep_ms(off)
        
class Led:
    def __init__(self, pin, active_high=True):
        self.pin = Pin(pin, Pin.OUT)
        self.active_high = active_high
        self.off()

    def on(self):
        self.pin.value(1 if self.active_high else 0)

    def off(self):
        self.pin.value(0 if self.active_high else 1)

    def blink(self, ms=40):
        self.on()
        sleep_ms(ms)
        self.off()


def run(board):
    led = Led(board["led"], active_high=True)

    radio = CC1101(**board["cc1101"], debug=False)

    radio.reset()
    radio.configure(CC1101_CONFIG)

    errors = radio.verify(CC1101_CONFIG)
    print("VERIFY ERRORS:", errors)

    if errors:
        print("CC1101 VERIFY FAILED - STOP")
        panic_blink(led)

    led.blink(100)

    print("LEGACY TX READY")

    counter = 0

    while True:
        msg = "HELLO {:04d}".format(counter)
        pkt = msg.encode()

        radio.transmit(pkt)
        led.blink(40)

        print("TX:", msg)

        counter += 1
        sleep_ms(TX_INTERVAL_MS)