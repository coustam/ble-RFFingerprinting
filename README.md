# BLE Fingerprinting Using Analog RF Features  
**Toward Lightweight Physical Authentication for IoT**

## 1. Field of Research

This project lies at the intersection of:

- 🔒 Physical-layer security  
- 📡 Wireless device fingerprinting  
- 🔋 Lightweight authentication for constrained IoT devices  

It focuses on **RF fingerprinting**: uniquely identifying a transmitter based on **analog hardware imperfections** (e.g., I/Q imbalance, oscillator drift), extracted directly from raw I/Q samples — without relying on digital protocols, keys, or firmware.

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

## 4. Research Gap

Most existing work assumes:
- WiFi/OFDM-based fingerprinting
- Availability of decoded packets or demodulated signals
- BLE fingerprinting using packet-level statistics

📉 **We aim to close the gap** by:
- Working on **raw I/Q bursts** from BLE channels 37, 38, and 39.
- Extracting features **without packet decoding**
- Using only **low-complexity, analog-derived metrics**

## 5. Experimental Setup

**Hardware:**
- PlutoSDR (AD9363)
- Raspberry Pi for BLE scanning
- BLE devices broadcasting on **Channel 37 (2.402 GHz)**

**Data collected:**
- Raw I/Q bursts (threshold-triggered, ~100–500 samples per burst)
- BLE logs: MAC, RSSI, timestamp

**System architecture:**
[BLE Device] --> RF --> [PlutoSDR] --> [Python Feature Extractor]
↘ Timestamp sync ↙
[BLE Scanner on Raspberry Pi]

## 6. Feature Extraction Pipeline

We extract features **per burst**, using a custom pipeline designed for **raw I/Q data**, even without symbol synchronization.

| Feature Group          | Extracted Metrics                                                                 |
|------------------------|-----------------------------------------------------------------------------------|
| I/Q imperfections      | `iq_gain_imbalance_db`, `iq_phase_imbalance_rad`, `iq_offset_real/imag`          |
| Frequency offset       | `cfo_estimate_hz` *(via average phase drift)*                                     |
| Spectral shape         | `fft_peak_0` to `fft_peak_4`, `spectral_entropy`                                  |
| Time-domain stats      | `rms_power`, `time_entropy`, `rise_index`                                         |
| Statistical moments    | `i_skew`, `q_skew`, `i_kurtosis`, `q_kurtosis`                                    |

📁 Stored in: `features.csv`  
🕒 Each row corresponds to one burst, timestamp-aligned with BLE logs.

# 6.1 Feature Definitions (with Equations and Physical Interpretation)

Each feature is extracted from a **burst of complex baseband I/Q samples**:
```math
s[n] = I[n] + jQ[n], \quad n = 0, \dots, N-1
```
Expectations `E[·]` are estimated using sample means.

## I/Q Imbalance and DC Offsets
These features stem from **imperfections in quadrature modulation**, often introduced by:

- **LO leakage**
- **DAC mismatch**
- **Mixer imbalance**
- **Phase splitter or quadrature generator non-idealities**

### 🧮 DC Offset (LO leakage / baseband mismatch)
```math
\text{Offset} = \mu_I + j \mu_Q \quad \text{with} \quad \mu_I = \mathbb{E}[I[n]],\ \mu_Q = \mathbb{E}[Q[n]]
```
💡 **Implication:** Strong DC offset suggests LO leakage or poor analog isolation in baseband.

### 🧮 Gain Imbalance
```math
\text{Gain Imbalance (dB)} = 20 \log_{10}\left( \frac{\sigma_I}{\sigma_Q} \right)
```
Where:
```math
\sigma_I^2 = \mathbb{E}[(I[n] - \mu_I)^2],\quad \sigma_Q^2 = \mathbb{E}[(Q[n] - \mu_Q)^2]
```
💡 **Implication:** Reveals DAC mismatch, VGA (variable gain amp) asymmetry, or LO phase imbalance. Typically calibrated in commercial transceivers.

### 🧮 Phase Imbalance
```math
\theta_{\text{IQ}} = \cos^{-1}\left( \frac{\text{Cov}(I, Q)}{\sigma_I \sigma_Q} \right)
```
Where:
```math
\text{Cov}(I,Q) = \mathbb{E}[(I[n] - \mu_I)(Q[n] - \mu_Q)]
```
💡 **Implication:** Deviation from ideal 90° implies LO phase skew or imbalance in analog quadrature signal generation.

## Carrier Frequency Offset (CFO)
```math
\hat{f}_{\text{CFO}} = \frac{f_s}{2\pi} \cdot \mathbb{E}[ \angle s[n+1] - \angle s[n] ]
```
💡 **Implication:** Proportional to the ppm offset in crystal oscillator — a key **hardware signature**. Stable across bursts but varies between devices.

## Spectral Features

Let `S[k] = FFT{s[n]}` be the normalized DFT of the burst (zero-padded if needed).

### 🧮 FFT Peaks
Top-5 magnitudes of `abs(S[k])`  
💡 **Implication:** Reflects imperfections in RF chain like PA non-linearity, filter roll-off, or harmonic distortion from analog baseband.

### 🧮 Spectral Entropy
```math
H_{\text{spec}} = - \sum_k P_k \log P_k, \quad P_k = \frac{|S[k]|^2}{\sum_j |S[j]|^2}
```
💡 **Implication:** Indicates how energy is distributed — low entropy = narrowband (e.g., single-tone), high entropy = spread (e.g., noisy modulator).

## Time-Domain Features

### 🧮 RMS Power
```math
P_{\text{RMS}} = \sqrt{ \frac{1}{N} \sum_{n=0}^{N-1} |s[n]|^2 }
```
💡 **Implication:** Measures burst energy; affected by path loss, amplifier gain, or TX power setting.

### 🧮 Time Entropy
Entropy of amplitude histogram of `|s[n]|`  
💡 **Implication:** Indicates signal variation or flatness — impacted by amplitude shaping or modulator state.

### 🧮 Rise Index
```math
A[n] = |s[n]|,\quad n_{\text{rise}} = \min \{ n : A[n] > 0.1 \cdot \max A \}
```
💡 **Implication:** Related to transient rise of burst — early rise → hard switching; slower rise → smoother ramp, e.g., analog ramp circuits.

## Higher-Order Moments (per channel)

### 🧮 Skewness
```math
\text{Skew}(x) = \frac{ \mathbb{E}[(x[n] - \mu)^3] }{ \sigma^3 }
```
💡 **Implication:** Non-zero skew indicates asymmetry due to clipping, poor DAC linearity or imbalance.

### 🧮 Kurtosis
```math
\text{Kurt}(x) = \frac{ \mathbb{E}[(x[n] - \mu)^4] }{ \sigma^4 }
```
💡 **Implication:** High kurtosis → bursty peaks or heavy tails (e.g., noise spikes); Low kurtosis → flatter distributions.

## 🔎 Summary Table

| Feature            | Approx Formula                                               | IC-Level Insight                                     |
|--------------------|--------------------------------------------------------------|------------------------------------------------------|
| DC Offset          | `E[I[n]] + j·E[Q[n]]`                                         | LO leakage, baseband coupling mismatch               |
| Gain Imbalance     | `20·log10(std(I) / std(Q))`                                   | VGA/DAC mismatch, analog gain imbalance              |
| Phase Imbalance    | `acos(Cov(I,Q) / (std(I)*std(Q)))`                            | LO skew, poor quadrature phase alignment             |
| CFO Estimate       | `fs/(2π) * mean(Δϕ)`                                          | Crystal oscillator drift, local clock mismatch       |
| FFT Peaks          | Top-5 `abs(S[k])`                                             | PA response, harmonic distortion, filtering          |
| Spectral Entropy   | `-∑ P_k log P_k` with `P_k = |S[k]|² / ∑ |S|²`                 | Spread vs. tone-like signature                       |
| RMS Power          | `sqrt(mean(|s[n]|²))`                                         | TX power, attenuation                                |
| Rise Index         | `min(n) where A[n] > 0.1 * max(A)`                            | PA attack time, envelope shaping                     |
| Time Entropy       | Entropy of `|s[n]|` histogram                                 | Randomness of envelope or modulator output           |
| I/Q Skewness       | `E[(x - μ)^3] / σ³`                                           | DAC clipping, asymmetry                              |
| I/Q Kurtosis       | `E[(x - μ)^4] / σ⁴`                                           | Tail behavior; high = outliers or bursty distortion  |

## 7. Results & Visualizations

Each feature was analyzed over time and across devices (MACs):

| Plot Title                       | Purpose                                                                 |
|----------------------------------|-------------------------------------------------------------------------|
| **I/Q Gain Imbalance Over Time** | Shows consistent per-device analog distortion                          |
| **CFO Drift Over Time**          | Reveals oscillator differences (ppm-level drift)                        |
| **FFT Peak Heatmap**             | Captures spectral energy distribution (device-specific)                |
| **PCA Scatter Plot (2D)**        | Shows MAC-wise clustering in feature space                             |
| **PCA Heatmap + Explained Var**  | Highlights top contributing features and variance retained             |

> 📊 These results demonstrate that BLE devices show **measurable and separable** hardware traits, despite GFSK limitations.

## 8. What’s Next?

| Area                    | Status / Need                                                                 |
|-------------------------|-------------------------------------------------------------------------------|
| Accurate CFO estimation | ✅ Implemented via phase drift — 🚧 needs packet-aware correction            |
| Time burst alignment    | ✅ Partial (via timestamps) — 🚧 rise time normalization not evaluated       |
| Feature validation      | 🚧 No cross-session or environmental robustness yet                           |
| Constellation plots     | 🚧 Not implemented — useful for debugging IQ/CFO estimation                   |
| Classification          | 🚧 No classifiers tested (e.g., k-NN, SVM)                                    |
| Packet-aware features   | 🚧 Preamble-based CFO or GFSK demod not implemented                           |

## 9. Why This Matters

This work supports the case for **hardware-rooted authentication**, especially in:

- 🔐 **Low-cost, low-power IoT environments**
- 🛰️ **Physically untrusted settings (e.g., asset tracking)**
- 🤖 **Autonomous pairing, device attestation**

And opens the door to **non-cryptographic identity primitives** derived from physics, not firmware.



