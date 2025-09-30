## ?? Lab Notebook: BLE Device Fingerprinting & Spoofing Resistance with PlutoSDR

### ?? Experiment Title
**RF Fingerprinting of BLE Devices using PlutoSDR: Evaluating Uniqueness and Spoofing Resistance**

---

### ?? Goal
To evaluate whether BLE transmitters can be uniquely identified from their physical-layer RF signatures captured via PlutoSDR, and to explore the resilience of such identification against replay-based spoofing attacks.

---

### ? Research Question
Can we reliably authenticate BLE devices using RF fingerprints extracted from their I/Q bursts, and how resistant is this method to spoofing through IQ sample replay?

---

###  Value Hypothesis
RF front-end imperfections (e.g., I/Q imbalance, spectral leakage, nonlinearities) are sufficiently unique and stable to act as a **device fingerprint**, providing a lightweight alternative to cryptographic authentication, particularly for resource-constrained or legacy IoT systems.

---

### ?? Implementation Steps

#### 1. **Setup**
- Configure PlutoSDR for BLE band (e.g., 2402 MHz � Channel 37)
- Ensure synchronized system clocks (for accurate timestamping)

#### 2. **Data Collection**
- Capture raw I/Q bursts using PlutoSDR triggered by power threshold
- Log BLE MAC and RSSI in parallel using `bluepy` on Raspberry Pi

#### 3. **Data Alignment**
- Match I/Q bursts with nearby BLE logs based on UTC timestamps (�1�2 sec window)
- Store pairs of `(burst, MAC, RSSI)` as labeled dataset

### 4. **Feature Extraction**
- Compute per-burst features:
  - I/Q imbalance
  - RMS power envelope
  - FFT spectrum
  - Signal entropy

### 5. **Fingerprinting**
- Train CNN or other classifier to predict device MAC from burst features
- Measure fingerprint accuracy and reproducibility across sessions

### 6. **Spoofing Simulation (Outlined)**
- Re-transmit captured I/Q bursts with PlutoSDR in TX mode
- Log and compare:
  - Classifier confusion
  - Signal artifacts
  - ROC curve for spoof detection

---

## ?? Future Extensions
- Add real-time challenge-response simulation
- Include adversarial perturbation scenarios
- Expand to multiple environments (indoor/outdoor, mobility)

---

## ?? Data Folders
- `data/raw/` � Captured I/Q bursts (.npy)
- `data/ble_log.csv` � BLE MAC + RSSI logs
- `data/processed/` � Features extracted for ML

---

## ? Status
- [x] Burst collection & BLE logging synchronized  
- [x] Matching logic tested  
- [ ] Classifier training in progress  
- [ ] Spoofing module prepared (not yet tested)

---