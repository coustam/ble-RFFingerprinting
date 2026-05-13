import os
from datetime import datetime, timedelta
import numpy as np
from datetime import datetime
import pandas as pd

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def current_utc_timestamp():
    return datetime.utcnow().isoformat() + "Z"

def parse_timestamp(ts_str):
    return datetime.fromisoformat(ts_str.replace("Z", ""))

def is_within_time_window(ts1, ts2, window_sec):
    delta = abs((ts1 - ts2).total_seconds())
    return delta <= window_sec

def list_npys_by_timestamp(folder):
    files = sorted([f for f in os.listdir(folder) if f.endswith('.npy')])
    return [(f, parse_timestamp(f.split('_')[2].replace('.npy', '')), f.split('_')[1]) for f in files]

def load_iq_burst(file_path):
    return np.load(file_path)



def parse_timestamp(ts):
    if isinstance(ts, (datetime, pd.Timestamp)):
        return ts  # Already parsed
    if isinstance(ts, str):
        ts = ts.strip()
        if ts.endswith("Z"):
            ts = ts[:-1]
        return datetime.fromisoformat(ts)
    raise ValueError(f"Unsupported timestamp format: {type(ts)} -> {ts}")
