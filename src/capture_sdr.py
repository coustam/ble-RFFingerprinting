import numpy as np
import time
import adi
import asyncio
import multiprocessing

from utils import current_utc_timestamp, ensure_dir

class PlutoSDRCapture:

    def __init__(self, center_freq, sample_rate, num_samples, gain, duration, save_path):
        self.center_freq = center_freq
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.gain = gain
        self.running = False
        self.duration = duration
        ensure_dir(save_path)
        self.save_path = save_path
        self.save_processes = []

    def save(self, path, data):
        np.save(path,data)
        pass

    def _capture(self):
        sdr = adi.Pluto()
        sdr.rx_lo = int(self.center_freq)
        sdr.sample_rate = int(self.sample_rate)
        sdr.rx_rf_bandwidth = int(self.sample_rate)
        sdr.rx_buffer_size = int(self.num_samples)
        if self.gain != None:
            sdr.gain_control_mode_chan0 = "manual"
            sdr.rx_hardwaregain_chan0 = float(self.gain)
        else:
            sdr.gain_control_mode_chan0 = "fast_attack"
        sdr.rx() # Wait for the first sample before saving the start time
        start_time = time.time()
        
        print(f"SDR: Starting capture  | Time: {current_utc_timestamp()}")

        while time.time() - start_time < self.duration:
            data = np.array(sdr.rx())
            timestamp = current_utc_timestamp()
            self.save_processes.append(multiprocessing.Process(target=self.save, args=(f"{self.save_path}/burst_{timestamp}.npy", data)))
            self.save_processes[-1].start()

        print(f"SDR: Ended capture     | Time: {current_utc_timestamp()}")

    def cleanup_processes(self):
        dead_processes = []
        for index in range(0, len(self.save_processes)):
            if not self.save_processes[index].is_alive():
                dead_processes.append(index)
        for dead_thread in dead_processes[::-1]:
            self.save_processes.pop(dead_thread)

    async def capture(self):
        ensure_dir(self.save_path)
        capture_process = multiprocessing.Process(target=self._capture)
        capture_process.start()

        while capture_process.is_alive():
            self.cleanup_processes()
            await asyncio.sleep(1.0)

        print(f"SDR: Saving...")

        while len(self.save_processes):
            self.cleanup_processes()
            await asyncio.sleep(1.0)
        
        print(f"SDR: Saving finished   | Time: {current_utc_timestamp()}")
            
