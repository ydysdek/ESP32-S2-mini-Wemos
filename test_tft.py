from machine import Pin, SPI, PWM
import st7789
import time

BLK = 8
RES = 7
CS  = 5
DC  = 6

spi_tft = SPI(
    1,
    baudrate=30_000_000,
    polarity=0,
    phase=0,
    sck=Pin(36),
    mosi=Pin(35)
)

# backlight
bl = PWM(Pin(BLK))
bl.freq(1000)
bl.duty_u16(65535)

tft = st7789.ST7789(
    spi_tft,
    240,
    320,
    reset=Pin(RES, Pin.OUT),
    cs=Pin(CS, Pin.OUT),
    dc=Pin(DC, Pin.OUT),
    xstart=0,
    ystart=0
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