from ccp import *

pkt = make_frame(
    MSG_HELLO,
    FLAG_ACK_REQ,
    1,
    0x1234,
    BROADCAST,
    b"HELLO"
)

print(pkt)

frame = parse_frame(pkt)
print(format_frame(frame))
print(frame["payload"])