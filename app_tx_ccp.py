from machine import Pin
from time import sleep_ms

from boards import BOARDS
from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG
from ccp import make_frame, MSG_HELLO, BROADCAST

# 1 mignięcie po utworzeniu radia,
# 2 mignięcia po poprawnym verify,
# krótkie mignięcie przy każdej transmisji.

class Led:
    def __init__(self, pin, active_high=True):
        self.pin = Pin(pin, Pin.OUT)
        self.active_high = active_high
        self.off()

    def on(self):
        self.pin.value(1 if self.active_high else 0)

    def off(self):
        self.pin.value(0 if self.active_high else 1)

    def blink(self, ms=60):
        self.on()
        sleep_ms(ms)
        self.off()


def run():

    BOARD = BOARDS["esp32_s2_mini"]
    NODE_ID = 0x2001

    led = Led(BOARD["led"], active_high=True)

    radio = CC1101(**BOARD["cc1101"], debug=False)

    led.blink(100)

    radio.reset()
    radio.configure(CC1101_CONFIG)

    errors = radio.verify(CC1101_CONFIG)
    print("VERIFY ERRORS:", errors)

    if errors == 0:
        led.blink(100)
        sleep_ms(100)
        led.blink(100)

    seq = 0

    while True:
        payload = "HELLO {}".format(seq).encode()

        frame = make_frame(
            MSG_HELLO,
            0,
            seq,
            NODE_ID,
            BROADCAST,
            payload
        )

        radio.transmit(frame)
        led.blink(40)

        print("TX seq={}, len={}".format(seq, len(frame)))

        seq = (seq + 1) & 0xFF
        sleep_ms(1370)


run()
