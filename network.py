import time
from utils import get_state

def get_net_stats():
    """Enhanced network stats with interface breakdown."""
    net_state = get_state()["net"]
    interfaces = {}
    rx_total, tx_total = 0, 0
    
    try:
        with open('/proc/net/dev') as f:
            for line in f.readlines()[2:]:
                parts = line.split()
                if len(parts) > 9:
                    iface = parts[0].rstrip(':')
                    # Skip loopback
                    if iface == 'lo':
                        continue
                    rx = int(parts[1])
                    tx = int(parts[9])
                    interfaces[iface] = {"rx": rx, "tx": tx}
                    rx_total += rx
                    tx_total += tx
    except:
        pass

    now = time.time()
    dt = now - net_state["time"]
    if dt > 0:
        net_state["rx_s"] = (rx_total - net_state["rx"]) / dt / 1024
        net_state["tx_s"] = (tx_total - net_state["tx"]) / dt / 1024
    
    net_state.update({"rx": rx_total, "tx": tx_total, "time": now})
    return {
        "rx_total": rx_total / (1024**2),
        "tx_total": tx_total / (1024**2),
        "rx_speed": net_state["rx_s"],
        "tx_speed": net_state["tx_s"],
        "interfaces": interfaces
    }
