
"""
/src/capture_ble.py

BLE advertisement logging utilities.

This module records BLE advertisements observed by the host BLE interface using
Bleak/BlueZ. The BLE log is auxiliary metadata that can help compare decoded SDR
packets against independently observed advertisements.

Release rule
------------
Final packet labels should come from decoded SDR packets whenever possible. BLE
scanner logs are useful for validation and timing context, but timestamp-based
matching alone is considered exploratory.
"""

import asyncio
import os

import bleak
import bleak.args.bluez as bluez

from utils import current_utc_timestamp, ensure_dir


class BLECapture:
    """
    BLE advertisement logger using Bleak/BlueZ.

    Parameters
    ----------
    log_path:
        CSV file written with columns timestamp, mac, rssi.
    rssi_threshold:
        Optional BlueZ RSSI filter.
    address_prefix:
        Optional BlueZ address/pattern filter.
    """

    def __init__(self, log_path, rssi_threshold=None, address_prefix=""):
        self.log_path = log_path
        self.rssi_threshold = rssi_threshold
        self.address_prefix = address_prefix
        self.stop_event = None

    async def capture(self):
        """Start BLE scanning until stop_capture() is called."""
        ensure_dir(os.path.dirname(self.log_path))

        if not os.path.exists(self.log_path):
            with open(self.log_path, "w") as f:
                f.write("timestamp,mac,rssi\n")

        self.stop_event = asyncio.Event()

        print(f"BLE: Starting logging  | Time: {current_utc_timestamp()}")

        filter_kwargs = {}

        if self.rssi_threshold is not None:
            filter_kwargs["RSSI"] = self.rssi_threshold

        if self.address_prefix:
            filter_kwargs["Pattern"] = self.address_prefix

        scanner_kwargs = {}

        if filter_kwargs:
            scanner_args = bleak.BlueZScannerArgs(
                filters=bluez.BlueZDiscoveryFilters(**filter_kwargs)
            )
            scanner_kwargs["bluez"] = scanner_args

        with open(self.log_path, "a", buffering=1) as f:

            def ble_on_detect(device, data):
                timestamp = current_utc_timestamp()
                rssi = data.rssi
                f.write(f"{timestamp},{device.address},{rssi}\n")
                print(
                    f"BLE: Got advertisement | Time: {timestamp} | "
                    f"MAC: {device.address} | RSSI: {rssi}"
                )

            async with bleak.BleakScanner(
                detection_callback=ble_on_detect,
                **scanner_kwargs,
            ):
                await self.stop_event.wait()

        self.stop_event = None
        print(f"BLE: Ended logging     | Time: {current_utc_timestamp()}")

    def stop_capture(self):
        """Request BLE scanning to stop."""
        if self.stop_event is not None:
            self.stop_event.set()