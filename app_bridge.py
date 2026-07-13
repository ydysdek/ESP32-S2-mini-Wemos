from time import sleep_ms, ticks_ms, ticks_diff
from cc1101 import CC1101
from cc1101_config import CC1101_CONFIG
from ccp import parse_frame, payload_text
try:
    import ujson as json
except ImportError:
    import json
    
import settings
import network
from umqtt.simple import MQTTClient


BRIDGE_SERIAL = getattr(settings, "BRIDGE_SERIAL", True)
BRIDGE_MQTT = getattr(settings, "BRIDGE_MQTT", False)

WIFI_SSID = getattr(settings, "WIFI_SSID", "")
WIFI_PASSWORD = getattr(settings, "WIFI_PASSWORD", "")

MQTT_HOST = getattr(settings, "MQTT_HOST", "")
MQTT_PORT = getattr(settings, "MQTT_PORT", 1883)
MQTT_USER = getattr(settings, "MQTT_USER", None)
MQTT_PASSWORD = getattr(settings, "MQTT_PASSWORD", None)
MQTT_CLIENT_ID = getattr(settings, "MQTT_CLIENT_ID", "cc1101-bridge")
mqtt_topic_base = getattr(settings, "MQTT_TOPIC_BASE", "cc1101")

def to_bytes(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    return str(value).encode()


def wifi_connect(ssid, password, timeout_ms=15000):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(ssid, password)

        waited = 0
        while not wlan.isconnected() and waited < timeout_ms:
            sleep_ms(250)
            waited += 250

    if not wlan.isconnected():
        raise RuntimeError("WiFi connect failed")

    print("WIFI", wlan.ifconfig())
    return wlan


class BridgeOutput:
    def __init__(self, serial=True, mqtt_client=None, topic_base="cc1101"):
        self.serial = serial
        self.mqtt = mqtt_client
        self.topic_base = topic_base
        self.mqtt_ok = mqtt_client is not None

    def emit(self, obj):
        payload = json.dumps(obj)

        if self.serial:
            print(payload)

        if self.mqtt and self.mqtt_ok:
            topic = "{}/{}".format(self.topic_base, obj["kind"])

            try:
                self.mqtt.publish(to_bytes(topic), to_bytes(payload))
                #print("MQTT PUB", topic)
            except Exception as e:
                self.mqtt_ok = False
                print("MQTT publish failed:", e)
                
                
def hex_text(data):
    return " ".join("{:02X}".format(b) for b in data)


def hex_text(data):
    return " ".join("{:02X}".format(b) for b in data)


def emit(obj):
    print(json.dumps(obj))


def emit_ccp(out, count, pkt, frame):
    payload = payload_text(frame["payload"])

    out.emit({
        "kind": "ccp",
        "ts_ms": ticks_ms(),
        "count": count,
        "radio": {
            "rssi": int(pkt["rssi"]),
            "lqi": pkt["lqi"],
            "crc_ok": pkt["crc_ok"],
            "packet_len": pkt["length"],
        },
        "ccp": {
            "seq": frame["seq"],
            "type": frame["type"],
            "flags": frame["flags"],
            "src": "{:04X}".format(frame["src"]),
            "dst": "{:04X}".format(frame["dst"]),
            "payload_len": len(frame["payload"]),
            "payload": payload,
        },
    })


def emit_raw(out, count, pkt):
    out.emit({
        "kind": "raw",
        "ts_ms": ticks_ms(),
        "count": count,
        "radio": {
            "rssi": int(pkt["rssi"]),
            "lqi": pkt["lqi"],
            "crc_ok": pkt["crc_ok"],
            "packet_len": pkt["length"],
        },
        "raw": {
            "hex": hex_text(pkt["data"]),
            "ascii": payload_text(pkt["data"]),
        },
    })


def emit_wdg(out, wdg_count, state, rxbytes):
    out.emit({
        "kind": "watchdog",
        "ts_ms": ticks_ms(),
        "count": wdg_count,
        "watchdog": {
            "state": state,
            "rxbytes": rxbytes,
        },
    })
    
    
def run(board):
    bridge_serial = getattr(settings, "BRIDGE_SERIAL", True)
    bridge_mqtt = getattr(settings, "BRIDGE_MQTT", False)
    mqtt_topic_base = getattr(settings, "MQTT_TOPIC_BASE", "cc1101")
    mqtt_client = None

    print("APP:", APP)
    print("BOARD:", BOARD)
    print("MQTT connected")
    print("BRIDGE_SERIAL:", bridge_serial)
    print("BRIDGE_MQTT:", bridge_mqtt)

    if bridge_mqtt:
        wifi_connect(
            getattr(settings, "WIFI_SSID", ""),
            getattr(settings, "WIFI_PASSWORD", "")
        )

        mqtt_client = MQTTClient(
            to_bytes(getattr(settings, "MQTT_CLIENT_ID", "cc1101-bridge")),
            getattr(settings, "MQTT_HOST", ""),
            port=getattr(settings, "MQTT_PORT", 1883),
            user=to_bytes(getattr(settings, "MQTT_USER", None)),
            password=to_bytes(getattr(settings, "MQTT_PASSWORD", None))
        )

        mqtt_client.connect()
        print("MQTT connected")
    
    out = BridgeOutput(
        serial=bridge_serial,
        mqtt_client=mqtt_client,
        topic_base=mqtt_topic_base
    )

    radio = CC1101(**board["cc1101"], debug=False)
    radio.reset()
    radio.configure(CC1101_CONFIG)

    errors = radio.verify(CC1101_CONFIG)
    print("VERIFY ERRORS:", errors)

    if errors:
        while True:
            print("BRIDGE VERIFY ERRORS", errors)
            sleep_ms(1000)

    radio.enter_rx()

    count = 0
    last_packet = ticks_ms()
    last_recover = ticks_ms()
    wdg_count = 0

    #print("BRIDGE READY")
    out.emit({
        "kind": "status",
        "ts_ms": ticks_ms(),
        "status": {
            "app": "bridge",
            "board": "esp32_c6",
            "ready": True,
            "verify_errors": errors,
            "mqtt": bridge_mqtt,
            "topic_base": mqtt_topic_base,
            },
        })
    while True:
        pkt = radio.read_packet()

        if pkt:
            count += 1
            last_packet = ticks_ms()

            frame = parse_frame(pkt["data"])

            if frame:
                '''
                payload = payload_text(frame["payload"])

                print("CCP count={} seq={} type={} src={:04X} dst={:04X} rssi={} lqi={} crc={} len={} payload={}".format(
                    count,
                    frame["seq"],
                    frame["type"],
                    frame["src"],
                    frame["dst"],
                    int(pkt["rssi"]),
                    pkt["lqi"],
                    pkt["crc_ok"],
                    len(frame["payload"]),
                    payload
                ))
            else:
                hex_data = " ".join("{:02X}".format(b) for b in pkt["data"])
                ascii_data = payload_text(pkt["data"])

                print("RAW count={} rssi={} lqi={} crc={} len={} hex={} ascii={}".format(
                    count,
                    int(pkt["rssi"]),
                    pkt["lqi"],
                    pkt["crc_ok"],
                    pkt["length"],
                    hex_data,
                    ascii_data
                ))
                '''
            if frame:
                emit_ccp(out, count, pkt, frame)
            else:
                emit_raw(out, count, pkt)
                
        now = ticks_ms()
        '''
        if ticks_diff(now, last_packet) > 3000 and ticks_diff(now, last_recover) > 3000:
            wdg_count += 1
            state, rxbytes = radio.recover_rx()
            reason = radio.marcstate_name(state)

            print("WDG count={} state={} rxbytes={}".format(
                wdg_count,
                reason,
                rxbytes
            ))

            last_recover = now
            last_packet = now
        '''
        if ticks_diff(now, last_packet) > 3000 and ticks_diff(now, last_recover) > 3000:
            wdg_count += 1
            state, rxbytes = radio.recover_rx()
            reason = radio.marcstate_name(state)

            emit_wdg(out, wdg_count, reason, rxbytes)

            last_recover = now
            last_packet = now

        sleep_ms(5)
