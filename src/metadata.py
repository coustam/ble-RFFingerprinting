"""
/src/metadata.py
Metadata helpers for BLE RF fingerprinting captures.

This module will build the canonical packet-level metadata table used by the
PRISM6G dataset. During the transition from exploratory notebooks, it also
contains helper functions for matching SDR bursts to BLE scanner logs.

Release rule
------------
Every released packet must have one metadata row linking it to session,
capture settings, SDR gain, raw file, packet indices, decoded address, QC flags,
and feature-set version.
"""

import pandas as pd

from utils import is_within_time_window, parse_timestamp


def load_ble_log(ble_log_path):
    """
    Load a BLE scanner log.

    Expected columns:
        timestamp, mac, rssi
    """
    df = pd.read_csv(ble_log_path)
    df["timestamp"] = df["timestamp"].apply(parse_timestamp)
    return df


def match_bursts_to_ble_devices(burst_timestamps, ble_log_path, time_window=1.0):
    """
    Match burst timestamps to BLE advertisements observed by the BLE scanner.

    This is an auxiliary/exploratory labelling method. For release-grade
    PRISM6G data, packet labels should come from decoded SDR packets whenever
    possible.

    Parameters
    ----------
    burst_timestamps:
        Iterable of timestamps or timestamp strings.
    ble_log_path:
        Path to a CSV file with columns timestamp, mac, rssi.
    time_window:
        Matching window in seconds.

    Returns
    -------
    list[dict]
        One dictionary per burst timestamp.
    """
    ble_log = load_ble_log(ble_log_path)

    matched = []

    for ts_str in burst_timestamps:
        ts = parse_timestamp(ts_str)

        window = ble_log[
            ble_log["timestamp"].apply(
                lambda x: is_within_time_window(ts, x, time_window)
            )
        ]

        macs = window["mac"].unique().tolist()
        rssi_dict = window.groupby("mac")["rssi"].mean().to_dict()

        matched.append(
            {
                "burst_timestamp": ts_str,
                "matched_macs": macs,
                "matched_rssi": rssi_dict,
                "num_matches": len(macs),
            }
        )

    return matched