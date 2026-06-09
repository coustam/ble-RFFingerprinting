# Test the throughput of the SDR interface.
# The result consists of a histogram of the sampling times plus 
# a comparison of the number of frames that should have been
# captured with how many were actually captured.
# The program runs until a keyboard interrupt is triggered.

import adi
import time
import matplotlib.pyplot as plt
import numpy as np
from utils import current_utc_timestamp, ensure_dir
import threading

# Parameters
fs = 2000000                # Sample rate
fc = 2402e6                 # Center frequency
buf_len = 2**20             # Number of samples per read operations
save_path = "../disk/raw"   # Storage location

# Pluto SDR setup
sdr = adi.Pluto()
sdr.rx_lo = int(fc)
sdr.sample_rate = int(fs)
sdr.rx_rf_bandwidth = int(fs)
sdr.rx_buffer_size = int(buf_len)

# Storage folder setup
ensure_dir(save_path)

# Run the SDR
print("SDR: Capture starting...")
sdr.rx() # Wait for the first sample before saving the start time
start_time = time.time()
rx_time = start_time
current_time = start_time
rx_periods = []

try: 
    # Continuously sample and launch threads to write the data to storage
    while True:
        data = np.array(sdr.rx())

        timestamp = current_utc_timestamp()
        t = threading.Thread(target=np.save, args=(f"{save_path}/burst_{timestamp}.npy", data,))
        t.start()

        # Save the sample intervals to create a histogram
        current_time = time.time()
        rx_periods.append(current_time-rx_time)
        rx_time = current_time

except KeyboardInterrupt as e:
    print(f"\nSDR: Num. samples should: {(time.time() - start_time) * fs / buf_len}, is: {len(rx_periods)}")
    plt.hist(rx_periods, range=(np.min(rx_periods), np.max(rx_periods)), log=True)
    plt.show()

