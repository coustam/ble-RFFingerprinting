"""
/src/capture_sdr.py
PlutoSDR capture utilities for PRISM6G BLE RF fingerprinting.

This module owns low-level I/Q capture from the PlutoSDR. It is used by the
capture notebook to record raw complex baseband buffers for later packet
detection, packet alignment, QC, and feature extraction.

Release rule
------------
Public PRISM6G datasets must be captured with fixed manual SDR gain. AGC-based
captures are allowed only for exploratory measurements and must not be mixed
with fixed-gain release data.
"""

import asyncio
import json
import os
import time

import adi
import numpy as np

from utils import current_utc_timestamp, ensure_dir


class PlutoSDRCapture:
    """
    PlutoSDR I/Q capture helper.

    Parameters
    ----------
    center_freq:
        Receiver center frequency in Hz.
    sample_rate:
        SDR sample rate in samples per second.
    num_samples:
        Number of I/Q samples per saved buffer.
    gain:
        Manual SDR gain in dB. Required unless allow_agc=True.
    duration:
        Capture duration in seconds.
    save_path:
        Folder where burst_<timestamp>.npy files are written.
    allow_agc:
        If True, allow PlutoSDR fast-attack AGC. This must be used only for
        exploratory captures, not release-grade PRISM6G data.
    """

    def __init__(
        self,
        center_freq,
        sample_rate,
        num_samples,
        gain,
        duration,
        save_path,
        allow_agc=False,
    ):
        self.center_freq = float(center_freq)
        self.sample_rate = float(sample_rate)
        self.num_samples = int(num_samples)
        self.gain = gain
        self.duration = float(duration)
        self.save_path = save_path
        self.allow_agc = bool(allow_agc)

        if self.gain is None and not self.allow_agc:
            raise ValueError(
                "Fixed SDR gain is required for PRISM6G release captures. "
                "Set gain=<value> or explicitly set allow_agc=True for exploratory captures."
            )

        ensure_dir(self.save_path)

    @property
    def gain_mode(self):
        """Return the active SDR gain mode as a metadata-friendly string."""
        return "fast_attack_agc" if self.gain is None else "manual"

    def _configure_sdr(self):
        """Configure and return a PlutoSDR receiver instance."""
        sdr = adi.Pluto()
        sdr.rx_lo = int(self.center_freq)
        sdr.sample_rate = int(self.sample_rate)
        sdr.rx_rf_bandwidth = int(self.sample_rate)
        sdr.rx_buffer_size = int(self.num_samples)

        if self.gain is None:
            sdr.gain_control_mode_chan0 = "fast_attack"
        else:
            sdr.gain_control_mode_chan0 = "manual"
            sdr.rx_hardwaregain_chan0 = float(self.gain)

        return sdr

    def _write_capture_config(self, start_timestamp):
        """
        Save SDR capture settings next to the raw .npy files.

        The canonical packet metadata table will be generated later, but this
        file prevents capture settings from being lost.
        """
        config = {
            "start_timestamp_utc": start_timestamp,
            "center_freq_hz": self.center_freq,
            "sample_rate_hz": self.sample_rate,
            "rx_rf_bandwidth_hz": self.sample_rate,
            "num_samples_per_buffer": self.num_samples,
            "duration_s": self.duration,
            "gain_mode": self.gain_mode,
            "sdr_gain_db": None if self.gain is None else float(self.gain),
            "allow_agc": self.allow_agc,
        }

        path = os.path.join(self.save_path, "capture_config.json")
        with open(path, "w") as f:
            json.dump(config, f, indent=2)

    def _capture_blocking(self):
        """
        Run the blocking SDR capture loop.

        This intentionally saves buffers synchronously. It is simpler and more
        reliable than spawning one process per saved file. If throughput becomes
        limiting later, replace this with a single writer queue.
        """
        sdr = self._configure_sdr()

        # Prime the SDR before starting the measurement clock.
        sdr.rx()

        start_timestamp = current_utc_timestamp()
        start_time = time.time()
        self._write_capture_config(start_timestamp)

        print(f"SDR: Starting capture  | Time: {start_timestamp}")
        print(f"SDR: Gain mode         | {self.gain_mode}")

        buffer_count = 0

        while time.time() - start_time < self.duration:
            samples = np.asarray(sdr.rx())
            timestamp = current_utc_timestamp()

            filename = f"burst_{timestamp}.npy"
            path = os.path.join(self.save_path, filename)

            np.save(path, samples)
            buffer_count += 1

        end_timestamp = current_utc_timestamp()
        print(f"SDR: Ended capture     | Time: {end_timestamp}")
        print(f"SDR: Saved buffers     | Count: {buffer_count}")

    async def capture(self):
        """
        Async wrapper so SDR capture can run together with BLE logging.

        The blocking SDR loop is moved to a worker thread. This keeps the
        notebook async orchestration simple without nested multiprocessing.
        """
        ensure_dir(self.save_path)
        await asyncio.to_thread(self._capture_blocking)