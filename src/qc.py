"""
Packet-level quality-control utilities for PRISM6G.

QC flags are used to decide whether a packet is suitable for feature extraction
and dataset release. The goal is traceability: every accepted or rejected packet
should have explicit reasons.

This module intentionally avoids pretending to know true SNR unless a noise
floor/background measurement is provided.
"""

from typing import Optional

import numpy as np


def rms_power(samples: np.ndarray) -> float:
    """Return RMS magnitude of complex I/Q samples."""
    samples = np.asarray(samples)

    if len(samples) == 0:
        return float("nan")

    return float(np.sqrt(np.mean(np.abs(samples) ** 2)))


def peak_magnitude(samples: np.ndarray) -> float:
    """Return peak magnitude of complex I/Q samples."""
    samples = np.asarray(samples)

    if len(samples) == 0:
        return float("nan")

    return float(np.max(np.abs(samples)))


def clipping_flag(samples: np.ndarray, margin: float = 0.98) -> bool:
    """
    Heuristic clipping detector.

    For integer ADC-like arrays, clipping is checked against dtype limits.
    For complex floating-point arrays from PlutoSDR, absolute ADC scale is not
    always reliable, so this returns False unless the dtype is integer.
    """
    samples = np.asarray(samples)

    if len(samples) == 0:
        return False

    if not np.issubdtype(samples.real.dtype, np.integer):
        return False

    limit = np.iinfo(samples.real.dtype).max
    return bool(np.max(np.abs(samples)) >= margin * limit)


def snr_proxy_db(samples: np.ndarray, noise_floor_rms: Optional[float] = None) -> float:
    """
    Return a simple RMS-based SNR proxy in dB.

    If no noise_floor_rms is supplied, returns NaN. This avoids reporting a
    fake SNR when no background measurement exists.
    """
    if noise_floor_rms is None or noise_floor_rms <= 0:
        return float("nan")

    signal_rms = rms_power(samples)

    if not np.isfinite(signal_rms) or signal_rms <= 0:
        return float("nan")

    return float(20.0 * np.log10(signal_rms / noise_floor_rms))


def packet_length_valid(
    packet_len_samples: int,
    min_len_samples: int = 16,
    max_len_samples: Optional[int] = None,
) -> bool:
    """Check packet length against simple sample-count bounds."""
    if packet_len_samples < min_len_samples:
        return False

    if max_len_samples is not None and packet_len_samples > max_len_samples:
        return False

    return True


def compute_packet_qc(
    samples: np.ndarray,
    preamble_score: Optional[float] = None,
    access_address_valid: Optional[bool] = None,
    decode_status: str = "unknown",
    cfo_hz: Optional[float] = None,
    noise_floor_rms: Optional[float] = None,
    min_len_samples: int = 16,
    max_len_samples: Optional[int] = None,
) -> dict:
    """
    Compute packet-level QC metrics and flags.

    Returns
    -------
    dict
        Flat QC dictionary suitable for merging into packet metadata.
    """
    samples = np.asarray(samples)
    packet_len = int(len(samples))

    return {
        "qc_packet_len_samples": packet_len,
        "qc_packet_length_valid": packet_length_valid(
            packet_len,
            min_len_samples=min_len_samples,
            max_len_samples=max_len_samples,
        ),
        "qc_rms_power": rms_power(samples),
        "qc_peak_magnitude": peak_magnitude(samples),
        "qc_clipping": clipping_flag(samples),
        "qc_snr_proxy_db": snr_proxy_db(samples, noise_floor_rms=noise_floor_rms),
        "qc_preamble_score": preamble_score,
        "qc_access_address_valid": access_address_valid,
        "qc_decode_status": decode_status,
        "qc_cfo_valid": bool(cfo_hz is not None and np.isfinite(cfo_hz)),
    }


def packet_is_release_candidate(qc: dict) -> bool:
    """
    Conservative release-candidate decision.

    This is intentionally minimal for now. Tight thresholds should be added only
    after we inspect real chamber captures.
    """
    if not qc.get("qc_packet_length_valid", False):
        return False

    if qc.get("qc_clipping", False):
        return False

    if qc.get("qc_access_address_valid") is False:
        return False

    if qc.get("qc_decode_status") in {"failed", "invalid"}:
        return False

    return True


__all__ = [
    "rms_power",
    "peak_magnitude",
    "clipping_flag",
    "snr_proxy_db",
    "packet_length_valid",
    "compute_packet_qc",
    "packet_is_release_candidate",
]