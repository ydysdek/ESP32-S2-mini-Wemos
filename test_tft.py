from machine import Pin, SPI
import st7789
import time

spi = SPI(
    1,
    baudrate=40_000_000,
    polarity=0,
    phase=0,
    sck=Pin(36),
    mosi=Pin(35)
)

tft = st7789.ST7789(
    spi,
    320,
    240,
    reset=Pin(7, Pin.OUT),
    cs=Pin(5, Pin.OUT),
    dc=Pin(6, Pin.OUT)
)

tft.init()

while True:
    tft.fill(0xFFFF)  # biały
    time.sleep(1)
    tft.fill(0x0000)  # czarny
    time.sleep(1)
    tft.fill(0xF800)  # czerwony
    time.sleep(1)
    tft.fill(0x07E0)  # zielony
    time.sleep(1)
    tft.fill(0x001F)  # niebieski
    time.sleep(1)