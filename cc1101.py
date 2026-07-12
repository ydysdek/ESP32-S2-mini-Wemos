from machine import Pin, SPI
import time


class CC1101:
    SRES  = 0x30
    SRX   = 0x34
    STX = 0x35
    SIDLE = 0x36
    SFRX  = 0x3A
    SFTX  = 0x3B
    RXFIFO = 0x3F
    TXFIFO = 0x3F
    LQI = 0x33
    RSSI = 0x34
    MARCSTATE = 0x35
    PKTSTATUS = 0x38
    RXBYTES = 0x3B

    def __init__(self, spi_id, sck, mosi, miso, cs, gdo0=None, gdo2=None, baudrate=1000000, debug=False):
        self.debug = debug
        self.spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=0,
            phase=0,
            sck=Pin(sck),
            mosi=Pin(mosi),
            miso=Pin(miso)
        )

        self.cs = Pin(cs, Pin.OUT, value=1)
        self.gdo0 = Pin(gdo0, Pin.IN) if gdo0 is not None else None
        self.gdo2 = Pin(gdo2, Pin.IN) if gdo2 is not None else None
        
        self.debug = debug
        
        self.packet_ready = False
        self.irq_count = 0

        if self.gdo0 is not None:
            self.gdo0.irq(trigger=Pin.IRQ_RISING, handler=self._gdo0_irq)

    def _gdo0_irq(self, pin):
        self.packet_ready = True
        self.irq_count += 1

    def select(self):
        self.cs.value(0)

    def deselect(self):
        self.cs.value(1)

    def strobe(self, cmd):
        self.select()
        self.spi.write(bytes([cmd]))
        self.deselect()

    def write_reg(self, addr, val):
        self.select()
        self.spi.write(bytes([addr, val]))
        self.deselect()

    def read_reg(self, addr):
        self.select()
        self.spi.write(bytes([addr | 0x80]))
        val = self.spi.read(1)[0]
        self.deselect()
        return val

    def read_status(self, addr):
        self.select()
        self.spi.write(bytes([addr | 0xC0]))
        val = self.spi.read(1)[0]
        self.deselect()
        return val

    def burst_read(self, addr, n):
        self.select()
        self.spi.write(bytes([addr | 0xC0]))
        data = self.spi.read(n)
        self.deselect()
        return data

    def reset(self):
        self.deselect()
        time.sleep_ms(10)
        self.select()
        time.sleep_ms(10)
        self.deselect()
        time.sleep_ms(60)

        self.strobe(self.SRES)
        time.sleep_ms(100)

    def configure(self, table):
        self.strobe(self.SIDLE)
        time.sleep_ms(10)

        for addr, val in enumerate(table):
            self.write_reg(addr, val)

        time.sleep_ms(50)

    def verify(self, table):
        errors = 0

        for addr, expected in enumerate(table):
            got = self.read_reg(addr)

            if got != expected:
                print("ERR 0x{:02X}: exp {:02X} got {:02X}".format(
                    addr, expected, got
                ))
                errors += 1

        return errors

    def enter_rx(self):
        self.strobe(self.SIDLE)
        self.strobe(self.SFRX)
        time.sleep_ms(2)
        self.strobe(self.SRX)

    def reset_rx(self):
        self.strobe(self.SIDLE)
        time.sleep_ms(1)
        self.strobe(self.SFRX)
        time.sleep_ms(1)
        self.strobe(self.SRX)
        time.sleep_ms(1)

    def rxbytes(self):
        return self.read_status(self.RXBYTES) & 0x7F

    def marcstate(self):
        return self.read_status(self.MARCSTATE)

    def pktstatus(self):
        return self.read_status(self.PKTSTATUS)

    def rssi_to_dbm(self, raw):
        if raw >= 128:
            return (raw - 256) / 2 - 74
        return raw / 2 - 74

    def read_packet(self):
        if not self.packet_ready:
            return None

        self.packet_ready = False

        rxbytes = self.rxbytes()

        self.log("")
        self.log("packet_ready = True, rxbytes = {}, gdo0_irqs = {}".format(
            rxbytes,
            self.irq_count
        ))
        self.log("marcstate = {}".format(hex(self.marcstate())))
        self.log("pktstatus = {}".format(hex(self.pktstatus())))

        if self.gdo0 is not None:
            self.log("GDO0 = {}".format(self.gdo0.value()))

        if rxbytes < 3:
            self.log("RX FIFO empty/too short, reset RX")
            self.reset_rx()
            return None

        fifo = self.burst_read(self.RXFIFO, rxbytes)
        self.log("len(fifo) = {}".format(len(fifo)))

        length = fifo[0]
        needed = 1 + length + 2

        if len(fifo) < needed:
            self.log("FIFO too short: len {}, needed {}".format(len(fifo), needed))
            self.reset_rx()
            return None

        data = fifo[1:1 + length]
        rssi_raw = fifo[1 + length]
        lqi_raw = fifo[1 + length + 1]

        packet = {
            "data": data,
            "length": length,
            "rssi": self.rssi_to_dbm(rssi_raw),
            "lqi": lqi_raw & 0x7F,
            "crc_ok": bool(lqi_raw & 0x80),
            "irq_count": self.irq_count,
        }

        self.log("--- Pakiet ---")
        self.log("Dlugosc: {} bajtow, RSSI: {:.1f} dBm, LQI: {}, CRC: {}".format(
            len(data),
            packet["rssi"],
            packet["lqi"],
            packet["crc_ok"]
        ))
        self.hexdump(data)

        self.reset_rx()
        return packet

    def log(self, msg=""):
        if self.debug:
            print(msg)
            
    def hexdump(self, data):
        if not self.debug:
            return

        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = " ".join("{:02X}".format(b) for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            print("{:04X}  {:<48}  {}".format(i, hex_part, ascii_part))
            
    def write_burst(self, addr, data):
        self.select()
        self.spi.write(bytes([addr | 0x40]))
        self.spi.write(data)
        self.deselect()

    def transmit(self, data):
        self.strobe(self.SIDLE)
        self.strobe(self.SFTX)
        time.sleep_ms(1)

        self.write_burst(self.TXFIFO, bytes([len(data)]) + data)

        self.strobe(self.STX)
