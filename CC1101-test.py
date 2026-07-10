from machine import Pin, SPI
import time

# =========================
# PINY ESP32-S2
# =========================
PIN_SCK  = 12
PIN_MOSI = 11
PIN_MISO = 13
PIN_CS   = 10
PIN_LED  = 15

spi = SPI(1,
          baudrate=2000000,
          polarity=0,
          phase=0,
          sck=Pin(PIN_SCK),
          mosi=Pin(PIN_MOSI),
          miso=Pin(PIN_MISO))

cs = Pin(PIN_CS, Pin.OUT, value=1)
led = Pin(PIN_LED, Pin.OUT, value=0)

# =========================
# LOW LEVEL
# =========================
def cs_low(): cs.value(0)
def cs_high(): cs.value(1)

def spi_strobe(cmd):
    cs_low()
    spi.write(bytes([cmd]))
    cs_high()

def write_reg(addr, val):
    cs_low()
    spi.write(bytes([addr, val]))
    cs_high()

def read_reg(addr):
    cs_low()
    spi.write(bytes([addr | 0x80]))
    val = spi.read(1)[0]
    cs_high()
    return val

def read_status(addr):
    cs_low()
    spi.write(bytes([addr | 0xC0]))
    val = spi.read(1)[0]
    cs_high()
    return val

# =========================
# STROBE
# =========================
SRES  = 0x30
SRX   = 0x34
SIDLE = 0x36
SFRX  = 0x3A

# =========================
# RESET
# =========================
def reset_cc1101():
    cs_high()
    time.sleep_ms(10)

    cs_low()
    time.sleep_ms(10)
    cs_high()
    time.sleep_ms(50)

    spi_strobe(SRES)
    time.sleep_ms(100)

    print("CC1101 zresetowany.")

# =========================
# DUMP REJESTRÓW
# =========================
def dump_registers(title=""):
    print("\n======================================")
    print(title)
    print("======================================")

    for addr in range(0x2F):
        val = read_reg(addr)
        print(f"Reg 0x{addr:02X}: 0x{val:02X}")

    partnum = read_reg(0x30)
    version = read_reg(0x31)

    print("--------------------------------------")
    print(f"PARTNUM: 0x{partnum:02X}")
    print(f"VERSION: 0x{version:02X}")

    # status debug
    freq = read_reg(0x0D)
    chan = read_reg(0x0A)

    print(f"FREQ2: 0x{freq:02X}")
    print(f"CHAN:  0x{chan:02X}")
    print("======================================\n")

# =========================
# KONFIG
# =========================
def configure_cc1101():
    table = [
        0x07, 0x2E, 0x07, 0x03, 0xD3, 0x91, 0x3F, 0x0C,
        0x05, 0x64, 0x00, 0x08, 0x00, 0x21, 0x65, 0x6A,
        0xCA, 0x83, 0x8B, 0x22, 0xF8, 0x34, 0x07, 0x30,
        0x18, 0x16, 0x6D, 0x43, 0x40, 0x91, 0x87, 0x6B,
        0xF8, 0x56, 0x10, 0xE9, 0x2A, 0x00, 0x1F, 0x41,
        0x00, 0x59, 0x7F, 0x3F, 0x81, 0x35, 0x09
    ]

    spi_strobe(SIDLE)
    time.sleep_ms(10)

    for addr, val in enumerate(table):
        write_reg(addr, val)

    print("Konfiguracja CC1101 wgrana.")

# =========================
# RX
# =========================
def enter_rx():
    spi_strobe(SIDLE)
    spi_strobe(SFRX)
    spi_strobe(SRX)
    print("Tryb RX aktywny")

# =========================
# START
# =========================
reset_cc1101()

dump_registers("REJESTRY PRZED KONFIGURACJĄ")

configure_cc1101()

dump_registers("REJESTRY PO KONFIGURACJI")

enter_rx()

# =========================
# LOOP TESTOWY
# =========================
while True:
    rssi_raw = read_reg(0x34)
    lqi = read_reg(0x33)

    rssi_dbm = (rssi_raw - 256)/2 if rssi_raw > 127 else rssi_raw/2

    print(f"RSSI: {rssi_dbm:.1f} dBm | LQI: {lqi}")

    time.sleep(1)