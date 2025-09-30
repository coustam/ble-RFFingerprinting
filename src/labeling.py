import pandas as pd
from utils import parse_timestamp, is_within_time_window

    
def match_bursts_to_ble_devices(burst_timestamps, ble_log_path, time_window=1.0):
    """
    Match each burst timestamp to BLE MACs seen within a time window.

    Args:
        burst_timestamps (list of str): ISO format timestamps from IQ captures.
        ble_log_path (str): Path to BLE log CSV (timestamp, mac, rssi).
        time_window (float): Matching window in seconds.

    Returns:
        list of dict: Each item includes burst timestamp and matched MACs/RSSIs.
    """
    ble_log = pd.read_csv(ble_log_path)
    ble_log['timestamp'] = ble_log['timestamp'].apply(parse_timestamp)

    matched = []
    for ts_str in burst_timestamps:
        ts = parse_timestamp(ts_str)
        window = ble_log[ble_log['timestamp'].apply(lambda x: is_within_time_window(ts, x, time_window))]

        macs = window['mac'].unique().tolist()
        rssi_dict = window.groupby('mac')['rssi'].mean().to_dict()

        matched.append({
            'burst_timestamp': ts_str,
            'matched_macs': macs,
            'matched_rssi': rssi_dict
        })

    return matched
