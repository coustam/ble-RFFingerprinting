import os
import bleak
import bleak.args.bluez as bluez
import asyncio

from utils import current_utc_timestamp, ensure_dir


class BLECapture:
    def __init__(self, log_path, rssi_threshold, address_prefix):
        self.rssi_threshold = rssi_threshold
        self.address_prefix = address_prefix
        self.log_path = log_path
        
        # Event to stop the thread
        self.stop_event = asyncio.Event()
    
    async def capture(self):
        # Create ble log file
        ensure_dir(os.path.dirname(self.log_path))
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w") as f:
                f.write("timestamp,mac,rssi\n")

        print(f"BLE: Starting logging  | Time: {current_utc_timestamp()}")

        def ble_on_detect(device, data):
            with open(self.log_path, "a") as f:
                timestamp = current_utc_timestamp()
                f.write(f"{timestamp},{device.address},{data.rssi}\n")
                print(f"BLE: Got advertisement | Time: {timestamp} | Power: {data.rssi:3.4f}")

        scanner_args = bleak.BlueZScannerArgs(
            filters=bluez.BlueZDiscoveryFilters(
            RSSI=self.rssi_threshold,
            Pattern=self.address_prefix)
        )

        async with bleak.BleakScanner(
            detection_callback = ble_on_detect, 
            bluez = scanner_args
        ):
            await self.stop_event.wait()

        print(f"BLE: Ended logging     | Time: {current_utc_timestamp()}")

    def stop_capture(self):
        self.stop_event.set()