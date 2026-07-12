from boards import BOARDS
from settings import APP, BOARD

board = BOARDS[BOARD]

if APP == "sniffer":
    from app_sniffer import run
elif APP == "tx_ccp":
    from app_tx_ccp import run
elif APP == "tx_legacy":
    from app_tx_legacy import run
elif APP == "bridge":
    from app_bridge import run
else:
    raise ValueError("Unknown APP: {}".format(APP))

print("APP:", APP)
print("BOARD:", BOARD)

run(board)