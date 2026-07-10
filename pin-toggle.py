from machine import Pin
from time import sleep

p = Pin(8, Pin.OUT)

while True:
    p.value(1)
    sleep(0.5)
    p.value(0)
    sleep(0.5)