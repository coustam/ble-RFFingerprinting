"""
Carrier-frequency-offset estimators for BLE RF fingerprinting.

BLE uses GFSK, so arbitrary phase drift over a burst is not a pure CFO estimate.
This module separates exploratory CFO proxies from packet-aligned estimators
used for PRISM6G validation.
"""

from typing import Optional

import numpy as np


def instantaneous_frequency_hz(samples: np.ndarray, sample_rate_hz: float) -> np.ndarray:
    """
    Estimate instantaneous frequency from complex baseband samples.

    Uses:
        f[n] = Fs / (2*pi) * angle(x[n] * conj(x[n-1]))

    This avoids explicit phase unwrapping and is usually more stable than
    unwrap(angle(x)) followed by diff(angle).
    """
    samples = np.asarray(samples)

    if len(samples) < 2:
        return np.asarray([], dtype=float)

    dphi = np.angle(samples[1:] * np.conj(samples[:-1]))
    return (float(sample_rate_hz) / (2.0 * np.pi)) * dphi


def cfo_phase_drift_exploratory(samples: np.ndarray, sample_rate_hz: float) -> float:
    """
    Exploratory CFO proxy from average phase drift.

    Warning
    -------
    For BLE GFSK this is not a pure oscillator CFO estimate. It is affected by
    modulation, packet alignment, SNR, clipping, and burst selection. Keep it
    only as a baseline for comparison with older exploratory results.
    """
    freq = instantaneous_frequency_hz(samples, sample_rate_hz)

    if len(freq) == 0:
        return float("nan")

    return float(np.mean(freq))


def cfo_packet_mean_frequency(
    packet_samples: np.ndarray,
    sample_rate_hz: float,
    start: Optional[int] = None,
    stop: Optional[int] = None,
    robust: bool = True,
) -> float:
    """
    Packet-aligned CFO proxy from instantaneous frequency.

    This should be used only on an aligned packet segment. For BLE advertising
    packets, the preamble and access-address region are preferable to an
    arbitrary energy burst because the segment definition is reproducible.

    Parameters
    ----------
    packet_samples:
        Complex I/Q samples containing a packet or packet segment.
    sample_rate_hz:
        SDR sample rate in Hz.
    start, stop:
        Optional sample indices selecting a segment inside packet_samples.
    robust:
        If True, use median frequency. If False, use mean frequency.
    """
    x = np.asarray(packet_samples)

    if start is not None or stop is not None:
        x = x[start:stop]

    freq = instantaneous_frequency_hz(x, sample_rate_hz)

    if len(freq) == 0:
        return float("nan")

    if robust:
        return float(np.median(freq))

    return float(np.mean(freq))


def cfo_known_sequence_least_squares(
    packet_samples: np.ndarray,
    sample_rate_hz: float,
    expected_freq_shape: np.ndarray,
) -> float:
    """
    Estimate CFO using a known GFSK frequency-shape template.

    Model:
        f_inst[n] = CFO + a * expected_freq_shape[n] + noise[n]

    The intercept estimates CFO, while the slope absorbs modulation deviation.

    This function is intentionally present as a release-candidate estimator, but
    it should only be used once packet alignment and the expected BLE symbol
    template are validated.
    """
    freq = instantaneous_frequency_hz(packet_samples, sample_rate_hz)
    expected_freq_shape = np.asarray(expected_freq_shape, dtype=float)

    n = min(len(freq), len(expected_freq_shape))

    if n < 4:
        return float("nan")

    y = freq[:n]
    s = expected_freq_shape[:n]

    design = np.column_stack([np.ones(n), s])
    coeff, *_ = np.linalg.lstsq(design, y, rcond=None)

    return float(coeff[0])


__all__ = [
    "instantaneous_frequency_hz",
    "cfo_phase_drift_exploratory",
    "cfo_packet_mean_frequency",
    "cfo_known_sequence_least_squares",
]
