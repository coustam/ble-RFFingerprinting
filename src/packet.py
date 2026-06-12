"""
/src/packet.py

BLE packet utilities for PRISM6G.

This module contains conservative helpers for BLE packet handling:
packet containers, energy-region detection, BLE whitening/dewhitening,
bit-to-byte conversion, and address formatting.

Full packet decoding will be moved here from notebook 02 once validated.
Feature extraction belongs in features_v1.py.
CFO estimation belongs in cfo.py.
Dataset metadata export belongs in metadata.py.
"""

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np


# BLE advertising access address as conventionally displayed.
BLE_ADV_ACCESS_ADDRESS_HEX = "8e89bed6"
BLE_ADV_ACCESS_ADDRESS = bytes.fromhex(BLE_ADV_ACCESS_ADDRESS_HEX)

# Advertising PDU types containing AdvA / device address.
ADV_PDU_TYPES_WITH_ADDRESS = {0x00, 0x01, 0x02, 0x06}


@dataclass
class Packet:
    """
    Partially or fully decoded BLE packet.

    This class is deliberately permissive: fields may be None if decoding
    failed or has not yet been attempted.
    """

    raw_file: Optional[str] = None
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None

    preamble: Optional[bytes] = None
    access_address: Optional[bytes] = None
    pdu_header: Optional[bytes] = None
    pdu_data: Optional[bytes] = None

    preamble_score: Optional[float] = None
    decode_status: str = "unknown"

    @property
    def length_samples(self) -> Optional[int]:
        """Return packet length in samples if indices are available."""
        if self.start_idx is None or self.end_idx is None:
            return None
        return int(self.end_idx - self.start_idx)

    def pdu_type(self) -> Optional[int]:
        """Return BLE advertising PDU type if available."""
        if self.pdu_header is None or len(self.pdu_header) < 1:
            return None
        return self.pdu_header[0] & 0x0F

    def has_advertiser_address(self) -> bool:
        """Return True if this PDU type should contain AdvA."""
        pdu_type = self.pdu_type()
        return pdu_type in ADV_PDU_TYPES_WITH_ADDRESS

    def advertiser_address(self) -> Optional[str]:
        """
        Return advertiser address as AA:BB:CC:DD:EE:FF if available.

        BLE advertising payload carries AdvA little-endian relative to the
        common display convention, so bytes are reversed for presentation.
        """
        if not self.has_advertiser_address():
            return None

        if self.pdu_data is None or len(self.pdu_data) < 6:
            return None

        return format_ble_address(self.pdu_data[:6])

    def access_address_valid(self) -> Optional[bool]:
        """
        Check whether the decoded access address matches BLE advertising AA.

        This assumes access_address is stored in display byte order:
        8e89bed6.

        If the decoder stores raw on-air byte order, it must reverse bytes
        before assigning this field.
        """
        if self.access_address is None:
            return None
        return self.access_address == BLE_ADV_ACCESS_ADDRESS


def find_energy_regions(
    samples: np.ndarray,
    threshold: float,
    min_len: int = 16,
    pad: int = 0,
) -> list[tuple[int, int]]:
    """
    Find contiguous high-amplitude regions in complex I/Q samples.

    This is only a coarse packet candidate detector. It is not BLE packet
    synchronization.
    """
    samples = np.asarray(samples)
    active = np.abs(samples) > threshold

    if active.size == 0:
        return []

    transitions = np.diff(active.astype(np.int8))

    starts = list(np.where(transitions == 1)[0] + 1)
    ends = list(np.where(transitions == -1)[0] + 1)

    if active[0]:
        starts.insert(0, 0)

    if active[-1]:
        ends.append(len(active))

    regions = []

    for start, end in zip(starts, ends):
        if end - start < min_len:
            continue

        start = max(0, start - pad)
        end = min(len(samples), end + pad)

        regions.append((int(start), int(end)))

    return regions


def whiten_bits(bits: Sequence[int], channel: int = 37) -> np.ndarray:
    """
    Apply BLE whitening/dewhitening.

    BLE whitening is self-inverse. This function can therefore be used both
    for whitening and dewhitening.

    The LFSR initialization follows the BLE advertising/data channel index.
    """
    lfsr = 0x40 | (channel & 0x3F)
    out = []

    for bit in bits:
        bit = int(bit) & 1

        lsb = lfsr & 1
        lfsr >>= 1

        if lsb:
            lfsr ^= 0b01000100

        out.append(bit ^ lsb)

    return np.asarray(out, dtype=np.uint8)


def bits_to_bytes_lsb_first(bits: Sequence[int]) -> Optional[bytes]:
    """
    Convert BLE LSB-first bits to bytes.

    Returns None if len(bits) is not a multiple of 8.
    """
    bits = np.asarray(bits, dtype=np.uint8)

    if len(bits) % 8 != 0:
        return None

    bits = bits.reshape((-1, 8))
    weights = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)

    values = (bits * weights).sum(axis=1).astype(np.uint8)

    return bytes(values.tolist())


def format_ble_address(addr_little_endian: bytes) -> Optional[str]:
    """
    Format a BLE address carried in advertising payload.

    Input is expected in BLE payload order. Output is common display order.
    """
    if addr_little_endian is None or len(addr_little_endian) < 6:
        return None

    addr = addr_little_endian[:6][::-1]
    return ":".join(f"{byte:02X}" for byte in addr)


def bytes_to_hex(data: Optional[bytes], sep: str = "") -> str:
    """Format bytes for debugging."""
    if data is None:
        return ""
    return sep.join(f"{byte:02x}" for byte in data)


__all__ = [
    "BLE_ADV_ACCESS_ADDRESS",
    "BLE_ADV_ACCESS_ADDRESS_HEX",
    "ADV_PDU_TYPES_WITH_ADDRESS",
    "Packet",
    "find_energy_regions",
    "whiten_bits",
    "bits_to_bytes_lsb_first",
    "format_ble_address",
    "bytes_to_hex",
]