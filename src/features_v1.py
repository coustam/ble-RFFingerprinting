"""
PRISM6G FeatureSet V1.

This module defines the first frozen feature set used for BLE RF
fingerprinting experiments. The goal is reproducibility: feature names,
formulas, units, and known limitations are fixed here.

Important
---------
These are statistical features computed from observed I/Q packet segments.
They are not yet calibrated physical impairment estimates.

In particular, cfo_estimate_hz is the original exploratory phase-drift CFO
proxy. For BLE GFSK, this is affected by modulation and packet alignment.
Validated packet-aligned CFO estimators live in cfo.py and will be compared
separately in WP1.

Changing feature names, formulas, or units requires a new feature-set version.
"""

import numpy as np
from scipy.fft import fft
from scipy.stats import entropy, skew, kurtosis

from cfo import cfo_phase_drift_exploratory


FEATURE_SET_VERSION = "PRISM6G_FeatureSet_V1"


FEATURE_DEFINITIONS = {
    "iq_imbalance": "mean(I) - mean(Q), exploratory DC/IQ offset proxy",
    "iq_gain_imbalance_db": "20*log10(std(I)/std(Q)), statistical gain-asymmetry proxy",
    "iq_phase_imbalance_rad": "acos(corr(I,Q)), statistical I/Q correlation proxy",
    "rms_power": "RMS magnitude of complex I/Q samples",
    "spectral_entropy": "entropy of normalized one-sided FFT magnitude spectrum",
    "cfo_estimate_hz": "exploratory mean phase-drift CFO proxy; not packet-aligned",
    "iq_corr": "Pearson correlation coefficient between I and Q",
    "phase_noise": "standard deviation of phase increments",
    "time_entropy": "entropy of amplitude-envelope histogram",
    "rise_index": "first envelope-rise index above 10% of peak difference",
    "i_skew": "skewness of I samples",
    "q_skew": "skewness of Q samples",
    "i_kurtosis": "kurtosis of I samples",
    "q_kurtosis": "kurtosis of Q samples",
    "fft_peak_0..N": "ranked normalized FFT peak magnitudes",
}


class PRISM6GFeatureExtractor:
    """
    Extract PRISM6G FeatureSet V1 from a complex I/Q segment.

    Parameters
    ----------
    fft_peaks:
        Number of ranked FFT peak magnitudes to extract.
    sample_rate:
        Sample rate in Hz, used for the exploratory CFO proxy.
    """

    def __init__(self, fft_peaks=5, sample_rate=2_500_000):
        self.fft_peaks = int(fft_peaks)
        self.sample_rate = float(sample_rate)

    def _iq_imbalance(self, i, q):
        return float(np.mean(i) - np.mean(q))

    def _rms_power(self, samples):
        return float(np.sqrt(np.mean(np.abs(samples) ** 2)))

    def _spectral_entropy(self, spectrum):
        return float(entropy(spectrum + 1e-10))

    def _fft_peaks(self, samples):
        spectrum = np.abs(fft(samples))
        spectrum = spectrum[: len(spectrum) // 2]
        spectrum = spectrum / (np.sum(spectrum) + 1e-10)
        top_indices = np.argsort(spectrum)[-self.fft_peaks:][::-1]
        return spectrum, top_indices

    def _iq_correlation(self, i, q):
        corr = np.corrcoef(i, q)[0, 1]
        return float(corr) if np.isfinite(corr) else float("nan")

    def _phase_noise(self, samples):
        phase = np.unwrap(np.angle(samples))
        return float(np.std(np.diff(phase)))

    def _time_entropy(self, samples):
        hist, _ = np.histogram(np.abs(samples), bins=100, density=True)
        return float(entropy(hist + 1e-10))

    def _transient_rise(self, envelope):
        if len(envelope) < 2 or np.max(envelope) <= 0:
            return 0

        diff = np.diff(envelope)
        threshold = 0.1 * np.max(envelope)
        rise_indices = np.where(diff > threshold)[0]
        return int(rise_indices[0]) if len(rise_indices) > 0 else 0

    def _iq_gain_phase_imbalance(self, i, q):
        """
        Statistical I/Q asymmetry proxies.

        These are useful fingerprint features, but they are not calibrated
        transmitter-only impairment estimates. They can be affected by receiver
        imbalance, modulation content, CFO, packet alignment, and SNR.
        """
        gain_imbalance = 20 * np.log10(np.std(i) / (np.std(q) + 1e-10))

        corr = np.corrcoef(i, q)[0, 1]
        if not np.isfinite(corr):
            return float(gain_imbalance), float("nan")

        phase_imbalance = np.arccos(np.clip(corr, -1, 1))
        return float(gain_imbalance), float(phase_imbalance)

    def compute_features(self, samples):
        """
        Extract a flat feature dictionary from one I/Q segment.
        """
        samples = np.asarray(samples)

        if len(samples) < 4:
            raise ValueError("Feature extraction requires at least 4 I/Q samples.")

        i = np.real(samples)
        q = np.imag(samples)
        envelope = np.abs(samples)

        spectrum, peak_indices = self._fft_peaks(samples)
        gain_db, phase_rad = self._iq_gain_phase_imbalance(i, q)

        features = {
            "feature_set_version": FEATURE_SET_VERSION,
            "iq_imbalance": self._iq_imbalance(i, q),
            "iq_gain_imbalance_db": gain_db,
            "iq_phase_imbalance_rad": phase_rad,
            "rms_power": self._rms_power(samples),
            "spectral_entropy": self._spectral_entropy(spectrum),
            "cfo_estimate_hz": cfo_phase_drift_exploratory(samples, self.sample_rate),
            "iq_corr": self._iq_correlation(i, q),
            "phase_noise": self._phase_noise(samples),
            "time_entropy": self._time_entropy(samples),
            "rise_index": self._transient_rise(envelope),
            "i_skew": float(skew(i)),
            "q_skew": float(skew(q)),
            "i_kurtosis": float(kurtosis(i)),
            "q_kurtosis": float(kurtosis(q)),
        }

        for rank, idx in enumerate(peak_indices):
            features[f"fft_peak_{rank}"] = float(spectrum[idx])

        return features


# Backward-compatible alias for old notebooks.
IQFeatureExtractor = PRISM6GFeatureExtractor


__all__ = [
    "FEATURE_SET_VERSION",
    "FEATURE_DEFINITIONS",
    "PRISM6GFeatureExtractor",
    "IQFeatureExtractor",
]