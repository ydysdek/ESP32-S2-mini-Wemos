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
    def __init__(self, pin, divider_k=0.67, cal=1.0):
        self.adc = ADC(Pin(pin))
        self.divider_k = divider_k
        self.cal = cal

        try:
            self.adc.atten(ADC.ATTN_11DB)
        except AttributeError:
            pass

    def read_v(self):
        total = 0

        for _ in range(16):
            total += self.adc.read_uv()
            sleep_ms(2)

        uv = total // 16
        vadc = uv / 1000000

        return vadc / self.divider_k * self.cal
