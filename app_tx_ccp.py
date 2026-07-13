from machine import Pin
from time import sleep_ms

from settings import NODE_ID, TX_INTERVAL_MS
from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG
from ccp import make_frame, MSG_HELLO, MSG_SENSOR, BROADCAST
from sensors import DS18B20Sensor, BatteryADC

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


def panic_blink(led):
    while True:
        led.blink(60)
        sleep_ms(60)


def run(board):
    led = Led(board["led"], active_high=True)

    sensors = board.get("sensors", {})
    print(sensors)

    temp = None
    battery = None
    if temp and not temp.available():
        print("DS18B20 not found")
    
    if sensors.get("ds18b20") is not None:
        temp = DS18B20Sensor(sensors["ds18b20"])

    if sensors.get("battery_adc") is not None:
        battery = BatteryADC(
            sensors["battery_adc"],
            sensors.get("battery_k", 0.67)
        )
    
    radio = CC1101(**board["cc1101"], debug=False)

    led.blink(100)

    radio.reset()
    radio.configure(CC1101_CONFIG)

    errors = radio.verify(CC1101_CONFIG)
    print("VERIFY ERRORS:", errors)

    if errors:
        panic_blink(led)

    seq = 0

    while True:
        #payload = "HELLO {}".format(seq).encode()
        t = temp.read_c() if temp else None
        v = battery.read_v() if battery else None

        if t is None:
            t_text = "NA"
        else:
            t_text = "{:.1f}C".format(t)

        if v is None:
            v_text = "NA"
        else:
            v_text = "{:.2f}V".format(v)

        payload = "T={} V={}".format(t_text, v_text).encode()
        
        frame = make_frame(
            MSG_SENSOR,
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
        sleep_ms(TX_INTERVAL_MS)