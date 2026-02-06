import numpy as np
import time
import adi
import asyncio
import threading

from utils import current_utc_timestamp, ensure_dir

class PlutoSDRCapture:

    def __init__(self, center_freq, sample_rate, num_samples, duration, save_path):
        self.center_freq = center_freq
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.running = False
        self.duration = duration
        ensure_dir(save_path)
        self.save_path = save_path
        self.save_threads = []

    def save(self, path, data):
        np.save(path,data)
        pass

    def _capture(self):
        sdr = adi.Pluto()
        sdr.rx_lo = int(self.center_freq)
        sdr.sample_rate = int(self.sample_rate)
        sdr.rx_rf_bandwidth = int(self.sample_rate)
        sdr.rx_buffer_size = int(self.num_samples)
        sdr.rx() # Wait for the first sample before saving the start time
        start_time = time.time()
        
        print(f"SDR: Starting capture  | Time: {current_utc_timestamp()}")

        while time.time() - start_time < self.duration:
            data = np.array(sdr.rx())
            timestamp = current_utc_timestamp()
            self.save_threads.append(threading.Thread(target=self.save, args=(f"{self.save_path}/burst_{timestamp}.npy", data)))
            self.save_threads[-1].start()

        print(f"SDR: Ended capture     | Time: {current_utc_timestamp()}")

    def cleanup_threads(self):
        dead_threads = []
        for index in range(0, len(self.save_threads)):
            if not self.save_threads[index].is_alive():
                dead_threads.append(index)
        for dead_thread in dead_threads[::-1]:
            self.save_threads.pop(dead_thread)

    async def capture(self):
        ensure_dir(self.save_path)
        capture_thread = threading.Thread(target=self._capture)
        capture_thread.start()

        while capture_thread.is_alive():
            self.cleanup_threads()
            await asyncio.sleep(1.0)

        print(f"SDR: Saving...")

        while len(self.save_threads):
            self.cleanup_threads()
            await asyncio.sleep(1.0)
        
        print(f"SDR: Saving finished   | Time: {current_utc_timestamp()}")
            
