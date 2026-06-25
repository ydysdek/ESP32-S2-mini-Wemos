from machine import Pin, SPI
import time

# =========================
# PINY
# =========================
PIN_SCK  = 12
PIN_MOSI = 11
PIN_MISO = 13
PIN_CS   = 10
PIN_LED  = 15

PIN_SCK  = 36
PIN_MOSI = 35
PIN_MISO = 37
PIN_CS   = 34
PIN_LED  = 15

spi = SPI(1,
          baudrate=500000,
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
def cs_low():
    cs.value(0)
    time.sleep_us(50)   # 🔴 KLUCZ

def cs_high():
    cs.value(1)
    time.sleep_us(50)

def strobe(cmd):
    cs_low()
    spi.write(bytearray([cmd]))
    cs_high()

def write(addr, val):
    cs_low()
    spi.write(bytearray([addr, val]))
    cs_high()

def read(addr):
    cs_low()
    spi.write(bytearray([addr | 0x80]))
    v = spi.read(1)[0]
    cs_high()
    return v

def burst_write(addr, data):
    cs_low()
    spi.write(bytearray([addr | 0x40]))
    spi.write(data)
    cs_high()

def spi_write_test():
    write(0x0B, 0xAA)
    v = read(0x0B)
    print("WRITE TEST:", hex(v))
# =========================
# STROBE
# =========================
SRES  = 0x30
SIDLE = 0x36
SFTX  = 0x3B
STX   = 0x35

# =========================
# RESET
# =========================
def reset():
    cs_high()
    time.sleep_ms(20)

    strobe(SRES)
    time.sleep_ms(100)
    for _ in range(10):
        read(0x30)
    print("RESET OK")

# =========================
# WRITE CONFIG SAFE
# =========================
def write_config(table):
    strobe(SIDLE)
    time.sleep_ms(5)

    strobe(SFTX)
    time.sleep_ms(5)

    for i, v in enumerate(table):
        write(i, v)

# =========================
# VERIFY
# =========================
def verify(table):
    print("\n--- VERIFY REGISTERS ---")
    errors = 0

    for i, exp in enumerate(table):
        got = read(i)

        if got != exp:
            print(f"ERR 0x{i:02X}: exp {exp:02X} got {got:02X}")
            errors += 1
        else:
            print(f"OK  0x{i:02X}: {got:02X}")

    print("------------------------")
    print("ERRORS:", errors)
    print("------------------------\n")

# =========================
# TX
# =========================
def send(pkt):

    strobe(SIDLE)
    strobe(SFTX)

    length = len(pkt)
    burst_write(0x3F, bytes([length]) + pkt)

    strobe(STX)

    time.sleep_ms(30)

# =========================
# MAIN
# =========================
reset()

print("SPI TEST:", hex(read(0x31)))
spi_write_test()

table = [
    0x07, 0x2E, 0x07, 0x03, 0xD3, 0x91, 0x3F, 0x0C,
    0x05, 0x64, 0x00, 0x08, 0x00, 0x21, 0x65, 0x6A,
    0xCA, 0x83, 0x8B, 0x22, 0xF8, 0x34, 0x07, 0x30,
    0x18, 0x16, 0x6D, 0x43, 0x40, 0x91, 0x87, 0x6B,
    0xF8, 0x56, 0x10, 0xE9, 0x2A, 0x00, 0x1F, 0x41,
    0x00, 0x59, 0x7F, 0x3F, 0x81, 0x35, 0x09
]

write_config(table)
verify(table)

print("TX READY")

counter = 0

while True:

    msg = "HELLO {:04d}".format(counter)
    pkt = msg.encode()

    print("TX:", msg)
    send(pkt)

    led.toggle()

    counter += 1
    time.sleep(1)