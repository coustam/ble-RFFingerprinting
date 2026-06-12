"""
/src/utils.py

Small shared utilities for the PRISM6G BLE RF fingerprinting pipeline.

This module contains only generic helpers: timestamp handling, directory
creation, .npy loading, and simple filename parsing. Project-specific signal
processing, packet decoding, QC, and feature extraction should live in their
own modules.
"""

from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd


def ensure_dir(path):
    """
    Create a directory if it does not already exist.

    Empty paths are ignored so calls such as ensure_dir(os.path.dirname("file.csv"))
    do not fail.
    """
    if path is None or str(path).strip() == "":
        return

    Path(path).mkdir(parents=True, exist_ok=True)


def current_utc_timestamp(timespec="microseconds"):
    """
    Return a UTC timestamp string with a trailing Z.

    Example:
        2026-06-09T14:03:22.123456Z
    """
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec=timespec) + "Z"


def parse_timestamp(ts):
    """
    Parse timestamps produced by current_utc_timestamp().

    Accepts strings ending in Z, datetime objects, and pandas Timestamp objects.
    """
    if isinstance(ts, pd.Timestamp):
        return ts.to_pydatetime()

    if isinstance(ts, datetime):
        return ts

    if isinstance(ts, str):
        ts = ts.strip()
        if ts.endswith(".npy"):
            ts = ts[:-4]
        if ts.endswith("Z"):
            ts = ts[:-1]
        return datetime.fromisoformat(ts)

    raise ValueError(f"Unsupported timestamp format: {type(ts)} -> {ts}")


def is_within_time_window(ts1, ts2, window_sec):
    """Return True if two timestamps are within window_sec seconds."""
    delta = abs((parse_timestamp(ts1) - parse_timestamp(ts2)).total_seconds())
    return delta <= window_sec


def list_npys_by_timestamp(folder):
    """
    List .npy files and parse timestamps from known filename conventions.

    Supported:
        burst_<timestamp>.npy
        packet_<address>_<timestamp>.npy

    Returns:
        list of tuples: (filename, timestamp, address)

    For burst files, address is None.
    """
    files = sorted([f for f in Path(folder).iterdir() if f.suffix == ".npy"])
    records = []

    for path in files:
        filename = path.name
        stem = path.stem

        if stem.startswith("packet_"):
            _, address, ts_str = stem.split("_", 2)
            records.append((filename, parse_timestamp(ts_str), address))

        elif stem.startswith("burst_"):
            _, ts_str = stem.split("_", 1)
            records.append((filename, parse_timestamp(ts_str), None))

        else:
            raise ValueError(f"Unsupported .npy filename format: {filename}")

    return records


def load_iq_burst(file_path):
    """Load one complex I/Q burst or packet from disk."""
    return np.load(file_path)