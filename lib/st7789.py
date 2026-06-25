from machine import Pin
import time

# commands
SWRESET = 0x01
SLPOUT  = 0x11
COLMOD  = 0x3A
MADCTL  = 0x36
DISPON  = 0x29
CASET   = 0x2A
RASET   = 0x2B
RAMWR   = 0x2C

class ST7789:
    def __init__(self, spi, width, height, reset, cs, dc, rotation=0, xstart=0, ystart=0):

        self.spi = spi
        self.width = width
        self.height = height

        self.cs = cs
        self.dc = dc
        self.rst = reset

        self.xstart = xstart
        self.ystart = ystart
        self.rotation = rotation

        # FIX: poprawna inicjalizacja pinów
        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)

    def _write_cmd(self, cmd):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def _write_data(self, data):
        self.cs(0)
        self.dc(1)
        self.spi.write(data)
        self.cs(1)

    def reset(self):
        self.rst(0)
        time.sleep_ms(50)
        self.rst(1)
        time.sleep_ms(150)

    def init(self):
        self.reset()

        self._write_cmd(SWRESET)
        time.sleep_ms(150)

        self._write_cmd(SLPOUT)
        time.sleep_ms(120)

        # 16-bit color
        self._write_cmd(COLMOD)
        self._write_data(bytearray([0x55]))
        time.sleep_ms(10)

        # MADCTL (ważne!)
        self._write_cmd(MADCTL)
        self._write_data(bytearray([0x00]))  # możesz zmienić później rotację

        self._write_cmd(DISPON)
        time.sleep_ms(100)

    def _set_window(self, x0, y0, x1, y1):

        x0 += self.xstart
        x1 += self.xstart
        y0 += self.ystart
        y1 += self.ystart

        self._write_cmd(CASET)
        self._write_data(bytearray([
            (x0 >> 8) & 0xFF, x0 & 0xFF,
            (x1 >> 8) & 0xFF, x1 & 0xFF
        ]))

        self._write_cmd(RASET)
        self._write_data(bytearray([
            (y0 >> 8) & 0xFF, y0 & 0xFF,
            (y1 >> 8) & 0xFF, y1 & 0xFF
        ]))

        self._write_cmd(RAMWR)

    def fill(self, color):

        hi = color >> 8
        lo = color & 0xFF

        self._set_window(0, 0, self.width-1, self.height-1)

        # mały bufor (stabilny na ESP32-S2)
        buf = bytearray(512)
        for i in range(0, 512, 2):
            buf[i] = hi
            buf[i+1] = lo

        pixels = self.width * self.height

        self.cs(0)
        self.dc(1)

        while pixels > 0:
            n = min(256, pixels)
            self.spi.write(buf[:n*2])
            pixels -= n

        self.cs(1)