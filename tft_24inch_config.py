"""Generic ESP32 320x240

"""

from machine import Pin, SPI
import st7789py as st7789

TFA = 40
BFA = 40
WIDE = 1
TALL = 0
SCROLL = 0      # orientation for scroll.py
FEATHERS = 1    # orientation for feathers.py

PIN_SCK  = 36
PIN_MOSI = 35
PIN_MISO = 37
PIN_CS   = 34

ST7789_CS = 5
ST7789_DC = 6
ST7789_RST = 7
ST7789_BLK = 8

ROTATIONS_240x320 = (
    (0x00, 240, 320, 0, 0, True),
    (0x60, 320, 240, 0, 0, True),
    (0xC0, 240, 320, 0, 0, True),
    (0xA0, 320, 240, 0, 0, True),
)

def config(display_config=None):
    if display_config is None:
        display_config = {
            "spi_id": 1,
            "sck": PIN_SCK,
            "mosi": PIN_MOSI,
            "miso": None,
            "cs": ST7789_CS,
            "dc": ST7789_DC,
            "rst": ST7789_RST,
            "blk": ST7789_BLK,
            "rotation": 0,
        }

    rotation = display_config.get("rotation", 0)

    spi = SPI(
        display_config.get("spi_id", 1),
        baudrate=display_config.get("baudrate", 20000000),
        sck=Pin(display_config["sck"]),
        mosi=Pin(display_config["mosi"]),
        miso=Pin(display_config["miso"]) if display_config.get("miso") is not None else None
    )

    tft = st7789.ST7789(
        spi,
        240,
        320,
        reset=Pin(display_config["rst"], Pin.OUT) if display_config.get("rst") is not None else None,
        cs=Pin(display_config["cs"], Pin.OUT),
        dc=Pin(display_config["dc"], Pin.OUT),
        backlight=Pin(display_config["blk"], Pin.OUT),
        rotation=rotation,
        color_order=st7789.BGR,
        custom_rotations=ROTATIONS_240x320
    )

    tft.inversion_mode(False)
    return tft
