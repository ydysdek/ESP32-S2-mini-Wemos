from time import sleep
import st7789py as st7789
import tft_24inch_config as tft_config

tft = tft_config.config()

w = tft.width
h = tft.height

tft.fill(st7789.BLACK)

# Kolorowe pasy
tft.fill_rect(0, 0, w // 3, 30, st7789.RED)
tft.fill_rect(w // 3, 0, w // 3, 30, st7789.GREEN)
tft.fill_rect((w // 3) * 2, 0, w - (w // 3) * 2, 30, st7789.BLUE)

# Ramki
tft.rect(0, 0, w, h, st7789.WHITE)
tft.rect(5, 35, w - 10, h - 40, st7789.YELLOW)
tft.rect(15, 45, w - 30, h - 60, st7789.CYAN)

# Linie przekątne
tft.line(0, 0, w - 1, h - 1, st7789.WHITE)
tft.line(w - 1, 0, 0, h - 1, st7789.MAGENTA)

# Krzyż przez środek
tft.hline(0, h // 2, w, st7789.GREEN)
tft.vline(w // 2, 0, h, st7789.RED)

# Punkty w rogach
for x, y, color in (
    (0, 0, st7789.RED),
    (w - 1, 0, st7789.GREEN),
    (0, h - 1, st7789.BLUE),
    (w - 1, h - 1, st7789.YELLOW),
):
    for dx in range(4):
        for dy in range(4):
            xx = x - dx if x == w - 1 else x + dx
            yy = y - dy if y == h - 1 else y + dy
            tft.pixel(xx, yy, color)

# Małe kwadraty testowe
x = 20
y = h - 50
for color in (st7789.RED, st7789.GREEN, st7789.BLUE, st7789.WHITE, st7789.YELLOW):
    tft.fill_rect(x, y, 20, 20, color)
    x += 28

sleep(10)