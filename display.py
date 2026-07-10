import st7789py as st7789
import tft_24inch_config as tft_config
import vga1_8x16 as font


class Display:
    def __init__(self, display_config=None):
        self.tft = tft_config.config(display_config)

        self.width = self.tft.width
        self.height = self.tft.height

        self.header_h = 24
        self.status_h = 40

        self.log_line = 0
        self.line_h = font.HEIGHT

        self.log_y = self.header_h + self.status_h
        self.log_h = self.height - self.log_y
        self.max_lines = self.log_h // self.line_h
        self.log_cols = (self.width - 4) // font.WIDTH

        self.rssi = "---"
        self.temp = "--.-"
        self.mqtt = "OFF"
        self.count = 0

        self.clear()
        self.draw_frame()
        self.draw_header("CC1101 Sniffer")
        self.draw_status()

    def clear(self):
        self.tft.fill(st7789.BLACK)

    def draw_frame(self):
        self.tft.hline(0, self.header_h, self.width, st7789.WHITE)
        self.tft.hline(0, self.log_y, self.width, st7789.WHITE)

    def draw_header(self, title):
        self.tft.fill_rect(0, 0, self.width, self.header_h, st7789.BLUE)
        self.tft.text(font, title, 5, 4, st7789.WHITE, st7789.BLUE)

    def draw_status(self):
        y = self.header_h + 2

        self.tft.fill_rect(
            0,
            self.header_h + 1,
            self.width,
            self.status_h - 2,
            st7789.BLACK
        )

        self.tft.text(font, "RSSI : {}".format(self.rssi), 5, y, st7789.WHITE, st7789.BLACK)
        self.tft.text(font, "MQTT : {}".format(self.mqtt), 120, y, st7789.WHITE, st7789.BLACK)

        y += font.HEIGHT

        self.tft.text(font, "Temp : {}".format(self.temp), 5, y, st7789.WHITE, st7789.BLACK)
        self.tft.text(font, "Pkts : {}".format(self.count), 120, y, st7789.WHITE, st7789.BLACK)

    def wrap_text(self, text):
        lines = []
        line = ""

        for part in text.split(" "):
            if not line:
                line = part
            elif len(line) + 1 + len(part) <= self.log_cols:
                line += " " + part
            else:
                lines.append(line)
                line = part

        if line:
            lines.append(line)

        return lines

    def add_log(self, text):
        for line in self.wrap_text(text):
            self.draw_log_line(line)

    def draw_log_line(self, text):
        y = self.log_y + 2 + self.log_line * self.line_h

        self.tft.fill_rect(0, y, self.width, self.line_h, st7789.BLACK)
        self.tft.text(font, text, 2, y, st7789.GREEN, st7789.BLACK)

        self.log_line += 1

        if self.log_line >= self.max_lines:
            self.log_line = 0
            self.tft.fill_rect(
                0,
                self.log_y + 1,
                self.width,
                self.log_h - 1,
                st7789.BLACK
            )

    def format_packet(self, prefix, count, rssi, data, max_bytes=16):
        shown = data[:max_bytes]
        hex_data = " ".join("{:02X}".format(b) for b in shown)
        ascii_data = self.bytes_to_ascii(data, max_bytes)

        if len(data) > max_bytes:
            hex_data += " ..."

        return "{} {:03d} RSSI {} {} |{}".format(
            prefix,
            count,
            rssi,
            hex_data,
            ascii_data
        )

    def bytes_to_ascii(self, data, max_bytes=16):
        chars = []

        for b in data[:max_bytes]:
            if 32 <= b <= 126:
                chars.append(chr(b))
            else:
                chars.append(".")

        text = "".join(chars)

        if len(data) > max_bytes:
            text += "..."

        return text

    def set_rssi(self, value):
        self.rssi = value
        self.draw_status()

    def set_temp(self, value):
        self.temp = value
        self.draw_status()

    def set_mqtt(self, value):
        self.mqtt = value
        self.draw_status()

    def set_count(self, value):
        self.count = value
        self.draw_status()