from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff
from display import Display
from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG
from ccp import parse_frame, format_frame

def blink_bl(bl, n=1, on=80, off=80):
    for _ in range(n):
        bl.value(0)
        sleep_ms(off)
        bl.value(1)
        sleep_ms(on)

def panic_blink_bl(bl):
    while True:
        blink_bl(bl, 1, 60, 60)
        
        
def run(board):
    count = 0
    last_lcd = ticks_ms()
    pending_text = None
    pending_rssi = None

    bl = Pin(8, Pin.OUT)

    blink_bl(bl, 1)  # main.py start

    # Cold boot delay: wait for TFT and CC1101 power-up stabilization.
    sleep_ms(3000)

    ui = Display(board["display"])
    ui.set_mqtt("OFF")
    ui.set_temp("--.-")

    radio = CC1101(**board["cc1101"], debug=False)

    radio.reset()
    radio.configure(CC1101_CONFIG)

    errors = radio.verify(CC1101_CONFIG)
    print("VERIFY ERRORS:", errors)

    if errors:
        panic_blink_bl(bl)

    radio.enter_rx()
    
    while True:
        pkt = radio.read_packet()

        if pkt:
            count += 1
            rssi = int(pkt["rssi"])

            frame = parse_frame(pkt["data"])

            if frame:
                text = format_frame(frame)
            else:
                text = ui.format_packet("RX", count, rssi, pkt["data"], max_bytes=8)

            pending_text = text
            pending_rssi = rssi

            # krótki terminal, bez hexdumpa
            print("RX", count, "RSSI", rssi)

        now = ticks_ms()

        if pending_text and ticks_diff(now, last_lcd) > 200:
            ui.set_count(count)

            if pending_rssi is not None:
                ui.set_rssi(pending_rssi)

            ui.add_log(pending_text)

            pending_text = None
            pending_rssi = None
            last_lcd = now

        sleep_ms(1)
