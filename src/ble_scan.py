import argparse
import os
import time
from datetime import datetime
from bluepy.btle import Scanner

parser = argparse.ArgumentParser()
parser.add_argument("--duration", type=int, required=True)
parser.add_argument("--log", type=str, required=True)
parser.add_argument("--interval", type=int, default=5)
args = parser.parse_args()

scanner = Scanner()
start = time.time()

if not os.path.exists(args.log):
    with open(args.log, "w") as f:
        f.write("timestamp,mac,rssi\n")

print("READY", flush=True)

while time.time() - start < args.duration:
    devices = scanner.scan(args.interval)
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with open(args.log, "a") as f:
        for dev in devices:
            f.write(f"{timestamp},{dev.addr},{dev.rssi}\n")
    print(f"??? Logged {len(devices)} devices")