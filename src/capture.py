import numpy as np
import time
import os
import adi
from bluepy.btle import Scanner, BTLEManagementError
from utils import current_utc_timestamp, ensure_dir

class PlutoSDRCapture:
    def __init__(self, center_freq, sample_rate, num_samples, threshold):
        self.sdr = adi.Pluto()
        self.sdr.rx_lo = int(center_freq)
        self.sdr.sample_rate = int(sample_rate)
        self.sdr.rx_rf_bandwidth = int(sample_rate)
        self.num_samples = num_samples
        self.threshold = threshold
        self.running = False

    def capture_bursts(self, duration, save_path):
        ensure_dir(save_path)
        self.running = True
        start_time = time.time()
        while time.time() - start_time < duration:
            samples = self.sdr.rx()
            power = np.mean(np.abs(samples)**2)
            if power > self.threshold:
                timestamp = current_utc_timestamp()
                np.save(f"{save_path}/burst_{timestamp}.npy", samples)
                print(f"?? Captured burst at {timestamp} | Power: {power:.4f}")
        self.running = False
