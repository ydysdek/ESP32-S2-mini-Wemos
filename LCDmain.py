from time import sleep
from display import Display

ui = Display()

ui.set_rssi(-71)
ui.set_temp("23.7C")
ui.set_mqtt("OK")
ui.set_count(12)

packet = bytes([0x48, 0x45, 0x4C, 0x4C, 0x4F, 0x00, 0xFF])

for i in range(30):
    ui.add_log(ui.format_packet("RX", i, -71, packet, max_bytes=16))
    sleep(0.5)