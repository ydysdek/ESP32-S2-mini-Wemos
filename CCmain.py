from time import sleep_ms

from boards import BOARDS
from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG
from display import Display


BOARD = BOARDS["esp32_c6"]

ui = Display(BOARD["display"])
radio = CC1101(**BOARD["cc1101"], debug=True)

radio.reset()
radio.configure(CC1101_CONFIG)
radio.enter_rx()

count = 0

while True:
    pkt = radio.read_packet()

    if pkt:
        count += 1

        ui.set_rssi(int(pkt["rssi"]))
        ui.set_count(count)
        ui.add_log(ui.format_packet(
            "RX",
            count,
            int(pkt["rssi"]),
            pkt["data"],
            max_bytes=8
        ))

    sleep_ms(5)