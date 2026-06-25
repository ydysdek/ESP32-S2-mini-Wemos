from machine import Pin, SPI
import time

# =========================
# PINY (ESP32-S2 WEMOS)
# =========================
PIN_SCK  = 36
PIN_MOSI = 35
PIN_MISO = 37
PIN_CS   = 34
PIN_LED  = 15
PIN_GDO0 = 4

spi = SPI(1, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(PIN_SCK),
          mosi=Pin(PIN_MOSI),
          miso=Pin(PIN_MISO))

cs = Pin(PIN_CS, Pin.OUT, value=1)
led = Pin(PIN_LED, Pin.OUT, value=0)
gdo0 = Pin(PIN_GDO0, Pin.IN)

# =========================
# SPI LOW LEVEL
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

def burst_read(addr, n):
    cs_low()
    spi.write(bytes([addr | 0xC0]))
    data = spi.read(n)
    cs_high()
    return data

# =========================
# STROBE
# =========================
SRES  = 0x30
SRX   = 0x34
SIDLE = 0x36
SFRX  = 0x3A
SFTX  = 0x3B

# =========================
# RESET
# =========================
def reset_cc1101():
    cs_high()
    time.sleep_ms(10)
    cs_low()
    time.sleep_ms(10)
    cs_high()
    time.sleep_ms(60)

    spi_strobe(SRES)
    time.sleep_ms(100)

    print("CC1101 zresetowany.\n")

# =========================
# KONFIGURACJA
# =========================
table = [
    0x07, 0x2E, 0x07, 0x03, 0xD3, 0x91, 0x3F, 0x0C,
    0x05, 0x64, 0x00, 0x08, 0x00, 0x21, 0x65, 0x6A,
    0xCA, 0x83, 0x8B, 0x22, 0xF8, 0x34, 0x07, 0x30,
    0x18, 0x16, 0x6D, 0x43, 0x40, 0x91, 0x87, 0x6B,
    0xF8, 0x56, 0x10, 0xE9, 0x2A, 0x00, 0x1F, 0x41,
    0x00, 0x59, 0x7F, 0x3F, 0x81, 0x35, 0x09
]

def configure_cc1101(table):

    spi_strobe(SIDLE)
    time.sleep_ms(10)

    for addr, val in enumerate(table):
        write_reg(addr, val)

    # 🔥 KLUCZOWE: GDO0 = packet end???
    #write_reg(0x02, 0x0D)

    print("Konfiguracja CC1101 wgrana.\n")
    time.sleep_ms(50)

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
        got = read_reg(i)

        if got != exp:
            print(f"ERR 0x{i:02X}: exp {exp:02X} got {got:02X}")
            errors += 1
        else:
            print(f"OK  0x{i:02X}: {got:02X}")

    print("------------------------")
    print("ERRORS:", errors)
    print("------------------------\n")


def read_regs():
    print("\n--- READ REGISTERS ---")
    table = []

    for i in range(0x2e):
        got = read_reg(i)
        table.append(got)
    print(f'table = {table}')

# =========================
# RX CONTROL
# =========================
def enter_rx():
    spi_strobe(SIDLE)
    spi_strobe(SFRX)
    time.sleep_ms(2)
    spi_strobe(SRX)
    print("Tryb RX aktywny\n")

def read_rxbytes():
    return read_status(0x3B) & 0x7F

def read_marcstate():
    return read_status(0x35)

def read_pktstatus():
    return read_status(0x38)

# =========================
# RSSI / LQI
# =========================
def get_rssi_lqi():
    rssi = read_reg(0x34)
    lqi  = read_reg(0x33)

    rssi_dbm = rssi/2 - 74 if rssi < 128 else (rssi - 256)/2 - 74
    lqi_val = lqi & 0x7F

    return rssi_dbm, lqi_val

# =========================
# HEXDUMP
# =========================
def hexdump(data):
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f"{b:02X}" for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"{i:04X}  {hex_part:<48}  {ascii_part}")

# =========================
# IRQ (STABILNY)
# =========================
packet_ready = False
irq_lock = False
gdo0_irqs = 0

def gdo0_irq(pin):
    global packet_ready, irq_lock, gdo0_irqs
    if irq_lock:
        return
    irq_lock = True
    packet_ready = True
    gdo0_irqs += 1

gdo0.irq(trigger=Pin.IRQ_RISING, handler=gdo0_irq)

# =========================
# RESET + INIT
# =========================
reset_cc1101()
configure_cc1101(table)
verify(table)
enter_rx()

packet_counter = 0
last_t = time.ticks_ms()

# =========================
# MAIN LOOP
# =========================
loop = 0
gdo0_mismatch = 0

loops=100
last_timestamp = None  # do obliczania różnicy czasu
while True:
    loops -= 1
    #print(f'\n[{loop}]')
    #loop += 1
    #rxbytes = read_rxbytes()

    if packet_ready:# or rxbytes > 0:
        rxbytes = read_rxbytes()
        print(f'\npacket_ready = {packet_ready}, rxbytes = {rxbytes}, gdo0_irqs = {gdo0_irqs}')

        marcstate = read_marcstate()
        print(f'marcstate = {hex(marcstate)}')

        pktstatus = read_pktstatus()
        print(f'pktstatus = {hex(pktstatus)}')
        
        gdo0_value = gdo0.value()
        if((pktstatus & 1) != gdo0_value):
            gdo0_mismatch += 1
        print(f'GDO0 = {gdo0.value()}, gdo0_mismatch = {gdo0_mismatch}')

        packet_ready = False

        if rxbytes <= 0:
            spi_strobe(SIDLE)
            spi_strobe(SFRX)
            spi_strobe(SRX)
            irq_lock = False
            continue

        fifo = burst_read(0x3F, rxbytes)
        print(f'len(fifo) = {len(fifo)}')
        
        if len(fifo) < 2:
            spi_strobe(SIDLE)
            spi_strobe(SFRX)
            spi_strobe(SRX)
            continue

        length = fifo[0]
        pkt = fifo[1:1+length]

        #rssi, lqi = get_rssi_lqi()
        # odczyt RSSI i LQI
        #rssi = read_reg(0x34)
        rssi = fifo[1+length]
        #lqi = read_reg(0x33)
        lqi = fifo[1+length+1]
        rssi_dbm = (rssi - 256)/2 if rssi >= 128 else rssi/2
        lqi_val  = lqi & 0x7F

        # timestamp z milisekundami
        timestamp = time.localtime()
        ms = int((time.ticks_ms() % 1000))  # milisekundy od startu
        ts_str = "{:04}-{:02}-{:02} {:02}:{:02}:{:02}.{:03}".format(
            timestamp[0], timestamp[1], timestamp[2],
            timestamp[3], timestamp[4], timestamp[5], ms
        )

        # Δt od poprzedniego pakietu
        if last_timestamp is not None:
            delta_ms = int(time.ticks_diff(time.ticks_ms(), last_timestamp))
            delta_str = f" (Δt: {delta_ms} ms)"
        else:
            delta_str = ""
        last_timestamp = time.ticks_ms()

        packet_counter += 1
        print(f"\n--- Pakiet #{packet_counter} --- {ts_str}{delta_str}")
        print(f"Długość: {len(pkt)} bajtów, RSSI: {rssi_dbm:.1f} dBm, LQI: {lqi_val}")

        #print(f"\nPACKET #{packet_counter} | {length} bytes")
        hexdump(pkt)

        # 🔥 HARD RX RESET (KLUCZ DO STABILNOŚCI)
        spi_strobe(SIDLE)
        time.sleep_ms(1)
        spi_strobe(SFRX)
        time.sleep_ms(1)
        spi_strobe(SRX)
        time.sleep_ms(1)

        packet_ready = False
        irq_lock = False

    time.sleep_ms(5)