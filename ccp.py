# ccp.py
# CC1101 Control Protocol v0

PROTO = 0xC1
VERSION = 0x00

BROADCAST = 0xFFFF

MSG_PING    = 0x01
MSG_PONG    = 0x02
MSG_HELLO   = 0x03
MSG_ACK     = 0x04
MSG_SENSOR  = 0x10
MSG_STATE   = 0x11
MSG_COMMAND = 0x20
MSG_CONFIG  = 0x30
MSG_ERROR   = 0x7F

FLAG_ACK_REQ   = 0x01
FLAG_ACK       = 0x02
FLAG_ERROR     = 0x04
FLAG_ENCRYPTED = 0x80


def make_frame(msg_type, flags, seq, src, dst, payload=b""):
    if payload is None:
        payload = b""

    return bytes([
        PROTO,
        VERSION,
        msg_type & 0xFF,
        flags & 0xFF,
        seq & 0xFF,
        (src >> 8) & 0xFF,
        src & 0xFF,
        (dst >> 8) & 0xFF,
        dst & 0xFF,
    ]) + payload


def parse_frame(data):
    if data is None:
        return None

    if len(data) < 9:
        return None

    if data[0] != PROTO:
        return None

    return {
        "version": data[1],
        "type": data[2],
        "flags": data[3],
        "seq": data[4],
        "src": (data[5] << 8) | data[6],
        "dst": (data[7] << 8) | data[8],
        "payload": data[9:],
    }


def is_ack(frame):
    return frame is not None and frame["type"] == MSG_ACK


def wants_ack(frame):
    return frame is not None and (frame["flags"] & FLAG_ACK_REQ) != 0


def make_ack(frame, src):
    return make_frame(
        MSG_ACK,
        FLAG_ACK,
        frame["seq"],
        src,
        frame["src"],
        b""
    )


def msg_name(msg_type):
    names = {
        MSG_PING: "PING",
        MSG_PONG: "PONG",
        MSG_HELLO: "HELLO",
        MSG_ACK: "ACK",
        MSG_SENSOR: "SENSOR",
        MSG_STATE: "STATE",
        MSG_COMMAND: "COMMAND",
        MSG_CONFIG: "CONFIG",
        MSG_ERROR: "ERROR",
    }

    return names.get(msg_type, "0x{:02X}".format(msg_type))


def payload_text(payload):
    chars = []

    for b in payload:
        if 32 <= b <= 126:
            chars.append(chr(b))
        else:
            chars.append(".")

    return "".join(chars)


def format_frame(frame):
    if frame is None:
        return "INVALID"

    text = "{} s={} {:04X}>{:04X} n={}".format(
        msg_name(frame["type"]),
        frame["seq"],
        frame["src"],
        frame["dst"],
        len(frame["payload"])
    )

    if frame["payload"]:
        text += " " + payload_text(frame["payload"])

    return text