from time import sleep_ms, ticks_ms, ticks_diff

from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG
from ccp import parse_frame, payload_text


def run(board):
    radio = CC1101(**board["cc1101"], debug=False)

    radio.reset()
    radio.configure(CC1101_CONFIG)

    errors = radio.verify(CC1101_CONFIG)
    print("VERIFY ERRORS:", errors)

    if errors:
        while True:
            print("BRIDGE VERIFY ERRORS", errors)
            sleep_ms(1000)

    radio.enter_rx()

    count = 0
    last_packet = ticks_ms()
    last_recover = ticks_ms()
    wdg_count = 0

    print("BRIDGE READY")

    while True:
        pkt = radio.read_packet()

        if pkt:
            count += 1
            last_packet = ticks_ms()

            frame = parse_frame(pkt["data"])

            if frame:
                payload = payload_text(frame["payload"])

                print("CCP count={} seq={} type={} src={:04X} dst={:04X} rssi={} lqi={} crc={} len={} payload={}".format(
                    count,
                    frame["seq"],
                    frame["type"],
                    frame["src"],
                    frame["dst"],
                    int(pkt["rssi"]),
                    pkt["lqi"],
                    pkt["crc_ok"],
                    len(frame["payload"]),
                    payload
                ))
            else:
                hex_data = " ".join("{:02X}".format(b) for b in pkt["data"])
                ascii_data = payload_text(pkt["data"])

                print("RAW count={} rssi={} lqi={} crc={} len={} hex={} ascii={}".format(
                    count,
                    int(pkt["rssi"]),
                    pkt["lqi"],
                    pkt["crc_ok"],
                    pkt["length"],
                    hex_data,
                    ascii_data
                ))

        now = ticks_ms()

        if ticks_diff(now, last_packet) > 3000 and ticks_diff(now, last_recover) > 3000:
            wdg_count += 1
            state, rxbytes = radio.recover_rx()
            reason = radio.marcstate_name(state)

            print("WDG count={} state={} rxbytes={}".format(
                wdg_count,
                reason,
                rxbytes
            ))

            last_recover = now
            last_packet = now

        sleep_ms(5)