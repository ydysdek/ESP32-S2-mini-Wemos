from time import sleep_ms

from boards import BOARDS
from display import Display
from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG


BOARD = BOARDS["esp32_s2"]

'''
ui = Display(BOARD["display"])
ui.add_log("LCD TEST 01")
ui.add_log("LCD TEST 02")
sleep(10)
'''

ui = Display(BOARD["display"])
ui.set_mqtt("OFF")
ui.set_temp("--.-")

radio = CC1101(**BOARD["cc1101"], debug=False)

radio.reset()
radio.configure(CC1101_CONFIG)

errors = radio.verify(CC1101_CONFIG)
print("VERIFY ERRORS:", errors)

radio.enter_rx()

count = 0

while True:
    pkt = radio.read_packet()

    if pkt:
        count += 1

        rssi = int(pkt["rssi"])

        #print("MAIN: packet for LCD")
        print("RX #{}, len {}, RSSI {}, LQI {}, CRC {}".format(
            count,
            pkt["length"],
            rssi,
            pkt["lqi"],
            pkt["crc_ok"]
        ))

        ui.set_count(count)
        ui.set_rssi(rssi)
        ui.add_log(ui.format_packet(
            "RX",
            count,
            rssi,
            pkt["data"],
            max_bytes=12
        ))

    sleep_ms(5)