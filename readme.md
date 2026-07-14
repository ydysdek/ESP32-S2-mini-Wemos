# CC1101 Sensor Network

## Eksperymentalna sieć radiowa oparta o CC1101, ESP32 i MicroPython.

Projekt obejmuje:
- nadajniki legacy wysyłające surowe tekstowe pakiety,
- nadajniki CCP wysyłające ramki własnego protokołu,
- sniffer z LCD,
- bridge CC1101 -> JSONL -> MQTT dla Home Assistant / innych systemów.

## Architektura

```text
[TX legacy] ----\
                 \
[TX CCP sensor] ---> CC1101 radio ---> [Bridge ESP32-C6] ---> MQTT
                 /
[inne CC1101] --/

[Sniffer LCD] = terenowy monitor odbioru ```

Tryby aplikacji
Tryb wybierany jest w settings.py przez APP.
APP = "bridge"
BOARD = "esp32_c6"
Obsługiwane aplikacje:
APP	Opis
tx_legacy	Nadajnik starego formatu, wysyła tekst typu HELLO 1234
tx_ccp	Nadajnik CCP, np. sensor temperatury i baterii
sniffer	Sniffer z LCD, terenowy monitor CC1101
bridge	Odbiornik CC1101 publikujący JSON/JSONL i MQTT

Profile płytek
Profile sprzętowe są w boards.py.
Przykłady:
BOARD	Zastosowanie
esp32_s2	Sniffer z LCD i CC1101
esp32_s2_mini	Nadajnik CCP / sensor
esp32_s2_mini_legacy	Nadajnik legacy z innym pinoutem
esp32_c6	Bridge Wi-Fi/MQTT

boards.py opisuje fizyczne piny: SPI, CC1101, LCD, LED, sensory.
settings.py wybiera, co aktualnie uruchamia dana płytka.
Protokół CCP
Ramki CCP są tworzone i parsowane w ccp.py.
Aktualnie używane typy:
Typ	Stała	Opis
0x03	MSG_HELLO	Ramka powitalna/testowa
0x10	MSG_SENSOR	Dane sensora
0x20	MSG_COMMAND	Przyszłe komendy

Payload sensora jest obecnie tekstowy, np.:
T=22.8C V=3.03V
To jest celowo proste i czytelne podczas debugowania.
Bridge MQTT
Bridge odbiera ramki CC1101, parsuje CCP i publikuje JSON przez MQTT.
W settings.py:
APP = "bridge"
BOARD = "esp32_c6"

BRIDGE_SERIAL = False
BRIDGE_MQTT = True

WIFI_SSID = "..."
WIFI_PASSWORD = "..."

MQTT_HOST = "192.168.50.xxx"
MQTT_PORT = 1883
MQTT_USER = "..."
MQTT_PASSWORD = "..."
MQTT_CLIENT_ID = "cc1101-bridge-c6"
MQTT_TOPIC_BASE = "cc1101"
Tematy MQTT:
cc1101/status
cc1101/ccp
cc1101/raw
cc1101/watchdog

Przykład cc1101/ccp:
{
  "kind": "ccp",
  "ts_ms": 534382,
  "count": 1,
  "radio": {
    "rssi": -29,
    "lqi": 6,
    "crc_ok": true,
    "packet_len": 24
  },
  "ccp": {
    "seq": 126,
    "type": 16,
    "flags": 0,
    "src": "1001",
    "dst": "FFFF",
    "payload_len": 15,
    "payload": "T=22.1C V=3.01V"
  }
}

Przykład cc1101/raw:
{
  "kind": "raw",
  "ts_ms": 535554,
  "count": 2,
  "radio": {
    "rssi": -41,
    "lqi": 7,
    "crc_ok": true,
    "packet_len": 11
  },
  "raw": {
    "hex": "48 45 4C 4C 4F 20 32 30 33 32 38",
    "ascii": "HELLO 20328"
  }
}
Sniffer LCD
Sniffer z LCD jest traktowany jako terenowy monitor, nie pełny analizator.
Pokazuje:
RSSI,
licznik pakietów,
ostatnie ramki CCP/raw,
watchdog RX.
Pełny log i analiza powinny iść przez serial/MQTT.
Watchdog RX
CC1101 potrafi okresowo wypaść do IDLE.
Objaw:
state IDLE rxbytes 0
Bridge/sniffer wykrywają ciszę i wykonują odzysk RX:
watchdog -> marcstate/rxbytes -> reset_rx()
To jest normalna część działania projektu.
Sensory
Nadajnik CCP może mieć sekcję sensors w boards.py:
"sensors": {
    "ds18b20": 18,
    "battery_adc": 17,
    "battery_k": 0.67,
    "battery_cal": 1.015,
}
DS18B20:
brak czujnika nie powinien zatrzymywać nadajnika,
wtedy temperatura może być wysyłana jako NA.
Pomiar baterii:
dzielnik: Vadc = Vbat * battery_k,
na ESP32-S2/C6 używać ADC.read_uv(), nie ręcznego skalowania read_u16().
Home Assistant
Aktualnie bridge publikuje MQTT, ale encje HA nie tworzą się automatycznie.
Możliwe następne kroki:
ręczne sensory MQTT w HA,
MQTT Discovery,
rozbijanie payloadu sensora na pola JSON, np. temperature_c, battery_v.
Workflow z Thonny
Przy wielu płytkach łatwo edytować zły plik.
Zalecenia:
zamykać pliki przed zmianą płytki,
sprawdzać APP i BOARD na starcie,
po krytycznych zmianach robić hard reset / odłączyć USB,
Thonny może mieć timeout przy zatrzymywaniu programu z Wi-Fi/MQTT.

## Status
Działa:
1. legacy TX,
2. CCP TX,
3. DS18B20,
4. pomiar baterii przez ADC,
5. sniffer LCD,
6. bridge JSONL,
7. bridge MQTT,
8. watchdog RX po IDLE.

Do zrobienia:
1. README / dokumentacja pinów,
2. MQTT Discovery dla Home Assistant,
3. transmisja MQTT -> CC1101,
4. binarny payload MSG_SENSOR,
5. ACK/retry dla komend,
6. ograniczenie serial debug w trybie produkcyjnym.