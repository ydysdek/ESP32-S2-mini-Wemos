from machine import Pin, ADC
import onewire
import ds18x20
from time import sleep_ms


class DS18B20Sensor:
    def __init__(self, pin):
        self.bus = ds18x20.DS18X20(onewire.OneWire(Pin(pin)))
        self.rom = None

        roms = self.bus.scan()

        if roms:
            self.rom = roms[0]

    def available(self):
        return self.rom is not None

    def read_c(self):
        if self.rom is None:
            return None

        self.bus.convert_temp()
        sleep_ms(750)
        return self.bus.read_temp(self.rom)

class BatteryADC:
    def __init__(self, pin, divider_k=0.67):
        self.adc = ADC(Pin(pin))
        self.divider_k = divider_k

        try:
            self.adc.atten(ADC.ATTN_11DB)
        except AttributeError:
            pass

    def read_v(self):
        raw = self.adc.read_u16()

        # MicroPython ADC read_u16: 0..65535. Przyjmujemy referencję ok. 3.3 V.
        vadc = raw * 3.3 / 65535
        return vadc / self.divider_k