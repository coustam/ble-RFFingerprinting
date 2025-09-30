#!/bin/bash

echo "?? Starting BLE-RFF environment setup..."

echo "?? Updating system packages..."
sudo apt update && sudo apt upgrade -y

# ---- Python and Virtualenv Setup ----
echo "?? Checking Python and pip tools..."
if ! command -v python3 &> /dev/null; then
    echo "?? Python3 not found. Installing..."
    sudo apt install -y python3
fi

if ! command -v pip3 &> /dev/null; then
    echo "?? pip3 not found. Installing..."
    sudo apt install -y python3-pip
fi

if ! python3 -m venv --help &> /dev/null; then
    echo "?? venv module not available. Installing..."
    sudo apt install -y python3-venv
fi

# ---- Virtual Environment ----
if [ ! -d "ble-rff-env" ]; then
    echo "?? Creating Python virtual environment..."
    python3 -m venv ble-rff-env
else
    echo "?? Virtual environment already exists."
fi

echo "? Activating environment..."
source ble-rff-env/bin/activate

# ---- Python Dependencies ----
echo "Installing Python packages from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# ---- Bluetooth Tools ----
echo " Installing Bluetooth tools..."
sudo apt install -y bluez bluez-hcidump libglib2.0-dev libpcap-dev

# ---- SDR Support ----
echo " Installing PlutoSDR tools..."
sudo apt install -y libiio-utils

# ---- Bluetooth Activation ----
echo " Enabling and checking Bluetooth interface..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo rfkill unblock bluetooth

if hciconfig | grep -q hci0; then
    echo " Bringing up hci0..."
    sudo hciconfig hci0 up
else
    echo " No Bluetooth interface (hci0) found. Please check your adapter."
fi

echo "? Setup complete. your Python environment, run:"

