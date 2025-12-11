# BLE Fingerprinting Using Analog RF Features  
**Toward Lightweight Physical Authentication for IoT**

---

## 1. Field of Research

This project lies at the intersection of:

- ?? Physical-layer security  
- ?? Wireless device fingerprinting  
- ?? Lightweight authentication for constrained IoT devices  

It focuses on **RF fingerprinting**: uniquely identifying a transmitter based on **analog hardware imperfections** (e.g., I/Q imbalance, oscillator drift), extracted directly from raw I/Q samples � without relying on digital protocols, keys, or firmware.

---

## 2. Motivation

Unlike digital IDs (e.g., MAC addresses), analog imperfections:
- Are **hard to spoof**
- Exist **naturally in all transmitters**
- Offer a **low-cost alternative** to full cryptographic stacks

These traits make them attractive for:
- **IoT security**
- **Zero-touch pairing**
- **Device integrity verification**

Especially in scenarios where:
- Cryptographic operations are **energy-expensive**
- Devices lack **secure key storage**

---

## 3. Why BLE is Challenging

BLE (Bluetooth Low Energy) fingerprinting is harder than WiFi because:

| BLE (GFSK)                        | WiFi (OFDM)                        |
|-----------------------------------|------------------------------------|
| No known pilots                   | Has pilots/training sequences      |
| Short preamble (8 bits)           | Long training fields               |
| Narrowband (1 MHz)                | Wideband (20 MHz)                  |
| No CSI available                  | Channel estimation available       |
| Lower power + fewer samples       | Higher power + dense burst stream  |

These limitations **prevent traditional methods** (e.g., pilot-based CFO estimation, CSI fingerprinting), and require more creative approaches.

---

## 4. Research Gap

Most existing work assumes:
- WiFi/OFDM-based fingerprinting
- Availability of decoded packets or demodulated signals
- BLE fingerprinting using packet-level statistics

?? **We aim to close the gap** by:
- Working on **raw I/Q bursts** from BLE channel 37
- Extracting features **without packet decoding**
- Using only **low-complexity, analog-derived metrics**

---

## 5. Experimental Setup

**Hardware:**
- PlutoSDR (AD9363)
- Raspberry Pi for BLE scanning
- BLE devices broadcasting on **Channel 37 (2.402 GHz)**

**Data collected:**
- Raw I/Q bursts (threshold-triggered, ~100 to 500 samples per burst)
- BLE logs: MAC, RSSI, timestamp

**System architecture:**

