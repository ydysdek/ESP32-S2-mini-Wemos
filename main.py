from settings import APP

if APP == "app_sniffer":
    from app_sniffer import run
elif APP == "app_tx_ccp":
    from app_tx_ccp import run
elif APP == "app_tx_legacy":
    from app_tx_legacy import run
elif APP == "app_bridge":
    from app_bridge import run
else:
    raise ValueError("Unknown APP: {}".format(APP))

run()
