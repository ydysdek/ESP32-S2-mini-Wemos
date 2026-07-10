import onewire
import ds18x20
import time
from machine import Pin

# GPIO do którego masz podłączony DATA (np. GPIO4)
dat = Pin(5)

# OneWire + DS18B20
ow = onewire.OneWire(dat)
ds = ds18x20.DS18X20(ow)

# skanujemy czujniki
roms = ds.scan()
print("Znalezione czujniki:", roms, (roms[0].hex()*))

while True:
    ds.convert_temp()
    time.sleep_ms(750)  # czas konwersji (12-bit)
    
    for rom in roms:
        temp = ds.read_temp(rom)
        print("Temp:", temp, "°C")
    
    time.sleep(2)
    