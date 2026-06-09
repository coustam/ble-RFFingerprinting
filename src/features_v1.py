import numpy as np
from scipy.fft import fft
from scipy.stats import entropy, skew, kurtosis

class IQFeatureExtractor:
    """
    Extract rich physical-layer features from I/Q signal bursts.

    This extractor is designed for RF fingerprinting and device
    authentication. Features are derived from time-domain and 
    frequency-domain characteristics of the signal.

    Parameters:
    -----------
    fft_peaks : int
        Number of FFT peak magnitudes to extract (default=5).
    sample_rate : float
        Sampling rate in Hz for CFO estimation (default=2.5e6).
    """

    def __init__(self, fft_peaks=5, sample_rate=2_500_000):
        self.fft_peaks = fft_peaks
        self.sample_rate = sample_rate

    def _iq_imbalance(self, i, q):
        """Compute I/Q imbalance as the mean offset between I and Q components.

        Returns:
            float: Mean I/Q offset in volts.
        """
        return np.mean(i) - np.mean(q)

    def _rms_power(self, samples):
        return np.sqrt(np.mean(np.abs(samples) ** 2))

    def _spectral_entropy(self, spectrum):
        return entropy(spectrum + 1e-10)

    def _fft_peaks(self, samples):
        spectrum = np.abs(fft(samples))
        spectrum = spectrum[:len(spectrum) // 2]
        spectrum /= np.sum(spectrum) + 1e-10
        top_indices = np.argsort(spectrum)[-self.fft_peaks:][::-1]
        return spectrum, top_indices

    def _iq_correlation(self, i, q):
        return np.corrcoef(i, q)[0, 1]

    def _phase_noise(self, samples):
        phase = np.unwrap(np.angle(samples))
        return np.std(np.diff(phase))

    def _cfo_estimate(self, samples):
        """
        Estimate carrier frequency offset (CFO) in Hz.
        """
        phase = np.unwrap(np.angle(samples))
        dphi = np.diff(phase)
        avg_rad = np.mean(dphi)
        return (avg_rad / (2 * np.pi)) * self.sample_rate

    def _time_entropy(self, samples):
        hist, _ = np.histogram(np.abs(samples), bins=100, density=True)
        return entropy(hist + 1e-10)

    def _transient_rise(self, envelope):
        diff = np.diff(envelope)
        threshold = 0.1 * np.max(envelope)
        rise_indices = np.where(diff > threshold)[0]
        return rise_indices[0] if len(rise_indices) > 0 else 0

    def _iq_gain_phase_imbalance(self, i, q):
        """
        Compute gain and phase imbalance.
        Gain imbalance = 20log10(std(I)/std(Q)) [dB]
        Phase imbalance = acos(corr(I,Q)) [radians]
        """
        gain_imbalance = 20 * np.log10(np.std(i) / (np.std(q) + 1e-10))
        corr = np.corrcoef(i, q)[0, 1]
        phase_imbalance = np.arccos(np.clip(corr, -1, 1))
        return gain_imbalance, phase_imbalance

    def compute_features(self, samples):
        """
        Extract a feature vector from a complex I/Q burst.

        Returns:
        --------
        dict : A dictionary of extracted feature names and values.
        """
        i = np.real(samples)
        q = np.imag(samples)
        envelope = np.abs(samples)

        spectrum, peak_indices = self._fft_peaks(samples)
        gain_db, phase_rad = self._iq_gain_phase_imbalance(i, q)

        features = {
            "iq_imbalance": self._iq_imbalance(i, q),
            "iq_gain_imbalance_db": gain_db,
            "iq_phase_imbalance_rad": phase_rad,
            "rms_power": self._rms_power(samples),
            "spectral_entropy": self._spectral_entropy(spectrum),
            "cfo_estimate_hz": self._cfo_estimate(samples),
            "iq_corr": self._iq_correlation(i, q),
            "phase_noise": self._phase_noise(samples),
            "time_entropy": self._time_entropy(samples),
            "rise_index": self._transient_rise(envelope),
            "i_skew": skew(i),
            "q_skew": skew(q),
            "i_kurtosis": kurtosis(i),
            "q_kurtosis": kurtosis(q),
        }

        for rank, idx in enumerate(peak_indices):
            features[f"fft_peak_{rank}"] = spectrum[idx]

        return features
