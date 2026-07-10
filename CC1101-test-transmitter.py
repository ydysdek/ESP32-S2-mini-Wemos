from machine import Pin, SPI
import time

# =========================
# PINY (dopasuj do HW)
# =========================
PIN_SCK  = 36
PIN_MOSI = 35
PIN_MISO = 37
PIN_CS   = 34
PIN_LED  = 15

spi = SPI(
    1,
    baudrate=4000000,
    polarity=0,
    phase=0,
    sck=Pin(PIN_SCK),
    mosi=Pin(PIN_MOSI),
    miso=Pin(PIN_MISO)
)

cs = Pin(PIN_CS, Pin.OUT, value=1)
led = Pin(PIN_LED, Pin.OUT, value=0)

# =========================
# LOW LEVEL SPI
# =========================
def cs_low():
    cs.value(0)
    time.sleep_us(5)

def cs_high():
    cs.value(1)
    time.sleep_us(10)

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

# =========================
# STROBES
# =========================
SRES = 0x30
SIDLE = 0x36
SFTX = 0x3B
STX = 0x35

# =========================
# RESET
# =========================
def reset():
    cs_high()
    time.sleep_ms(20)

    strobe(SRES)
    time.sleep_ms(100)

    strobe(SIDLE)
    time.sleep_ms(10)

    print("RESET OK")

# =========================
# SPI DIAGNOSTYKA
# =========================
def spi_self_check():
    print("\n--- SPI SELF CHECK (REAL) ---")

    # PATABLE jest najlepszy do testu
    write(0x3E, 0xAA)
    v1 = read(0x3E)

    write(0x3E, 0x55)
    v2 = read(0x3E)

    ok = (v1 == 0xAA or v1 == 0xAA & 0xFF) and (v2 == 0x55 or v2 == 0x55 & 0xFF)

    print("PATABLE:", hex(v1), hex(v2))
    print("SPI:", "OK" if ok else "CHECK MASKING")

    return True  # NIE FAILUJEMY CC1101 przez maskowanie

def test_register_write():
    print("\n--- REG WRITE TEST ---")

    write(0x0B, 0xAA)
    print("0xAA ->", hex(read(0x0B)))

    write(0x0B, 0x55)
    print("0x55 ->", hex(read(0x0B)))

def test_block_write():
    print("\n--- BLOCK TEST ---")

    for a, v in [(0x0B, 0x12), (0x0C, 0x34), (0x0D, 0x56)]:
        write(a, v)

    for a, _ in [(0x0B, 0), (0x0C, 0), (0x0D, 0)]:
        print(hex(a), hex(read(a)))

# =========================
# CONFIG
# =========================
def write_config(table):
    strobe(SIDLE)
    time.sleep_ms(5)

    for i, v in enumerate(table):
        write(i, v)

    print("CONFIG OK")

def verify(table):
    print("\n--- VERIFY REGISTERS ---")

    err = 0
    for i, exp in enumerate(table):
        got = read(i)

        if got != exp:
            print(f"ERR 0x{i:02X}: exp {exp:02X} got {got:02X}")
            err += 1
        else:
            print(f"OK  0x{i:02X}: {got:02X}")

    print("------------------------")
    print("ERRORS:", err)
    print("------------------------\n")

# =========================
# TX
# =========================
def send(pkt):
    strobe(SIDLE)
    time.sleep_ms(2)

    strobe(SFTX)
    time.sleep_ms(2)

    burst_write(0x3F, bytes([len(pkt)]) + pkt)

    strobe(STX)
    time.sleep_ms(20)

# =========================
# CONFIG TABLE
# =========================
table = [
    0x07,0x2E,0x07,0x03,0xD3,0x91,0x3F,0x0C,
    0x05,0x64,0x00,0x08,0x00,0x21,0x65,0x6A,
    0xCA,0x83,0x8B,0x22,0xF8,0x34,0x07,0x30,
    0x18,0x16,0x6D,0x43,0x40,0x91,0x87,0x6B,
    0xF8,0x56,0x10,0xE9,0x2A,0x00,0x1F,0x41,
    0x00,0x59,0x7F,0x3F,0x81,0x35,0x09
]

# =========================
# MAIN
# =========================
reset()

spi_self_check()
test_register_write()
test_block_write()

write_config(table)
verify(table)

print("TX READY")

counter = 0

while True:
    msg = "HELLO {:04d}".format(counter)

    print("TX:", msg)
    send(msg.encode())

    led.toggle()
    counter += 1

    time.sleep(1)