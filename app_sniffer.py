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
    print("RUN BOARD DISPLAY:", board["display"])
    print("RUN BOARD CC1101:", board["cc1101"])
    
    if board.get("display") is None:
        raise ValueError("Sniffer needs a board with display config")

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
    count = 0
    last_packet = ticks_ms()
    last_recover = ticks_ms()
    wdg_count = 0
    
    while True:
        pkt = radio.read_packet()

        if pkt:
            count += 1
            last_packet = ticks_ms()
            rssi = int(pkt["rssi"])

            print("RX", count, "RSSI", rssi)

            ui.set_count(count)
            ui.set_rssi(rssi)
            #ui.add_log("DIRECT RX {}".format(count))
            frame = parse_frame(pkt["data"])

            if frame:
                ui.add_log(format_frame(frame))
            else:
                ui.add_log(ui.format_packet("RX", count, rssi, pkt["data"], max_bytes=8))

        now = ticks_ms()

        if ticks_diff(now, last_packet) > 3000 and ticks_diff(now, last_recover) > 3000:
            wdg_count += 1
            state, rxbytes = radio.recover_rx()
            reason = radio.marcstate_name(state)

            print("RX watchdog reset", wdg_count, "state", reason, "rxbytes", rxbytes)
            ui.add_log("WDG {} {} rb={}".format(wdg_count, reason, rxbytes))

            last_recover = now
            last_packet = now
            
        sleep_ms(5)

