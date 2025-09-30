#!/bin/bash

echo "?? Testing BLE-RFF Development Environment"
echo "------------------------------------------"

# ---- Python Version ----
echo -n "?? Python version: "
python3 --version || echo "? Python not found"

# ---- Python Modules ----
echo "?? Verifying Python modules..."
missing_python=0
for module in adi numpy scipy matplotlib torch bluepy pandas; do
    python3 -c "import $module" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "  ? $module"
    else
        echo "  ? $module (missing)"
        missing_python=1
    fi
done

# ---- System Tools ----
echo "?? Verifying system tools..."
missing_tools=0
tools=(hcitool hcidump iio_info rfkill hciconfig)
for tool in "${tools[@]}"; do
    if command -v $tool &> /dev/null; then
        echo "  ? $tool"
    else
        echo "  ? $tool (not found)"
        missing_tools=1
    fi
done

# ---- Bluetooth Interface Check & Reset ----
echo "?? Checking Bluetooth interface (hci0)..."
if hciconfig | grep -q hci0; then
    echo "  ? hci0 interface is available"
    
    echo "  ?? Resetting Bluetooth interface..."
    sudo rfkill block bluetooth
    sleep 1
    sudo rfkill unblock bluetooth
    sudo hciconfig hci0 down
    sleep 1
    sudo hciconfig hci0 up
    sleep 2

    if hciconfig hci0 | grep -q UP; then
        echo "  ? hci0 is UP after reset"
    else
        echo "  ? hci0 failed to come UP after reset"
    fi
else
    echo "  ? hci0 not found (check USB or onboard BLE adapter)"
fi

# ---- BLE Device Scan Summary ----
echo "?? Scanning for nearby BLE devices..."
if command -v hcitool &> /dev/null; then
    sudo timeout 5 hcitool lescan > /tmp/ble_scan_result 2>/dev/null
    num_devices=$(grep -v "LE Scan" /tmp/ble_scan_result | awk '{print $1}' | sort | uniq | wc -l)
    echo "  ? Found $num_devices unique BLE advertising device(s)"
else
    echo "  ? hcitool not found, skipping BLE scan"
fi

# ---- Final Summary ----
echo "------------------------------------------"
echo "? Environment test complete."
if [ $missing_python -eq 0 ] && [ $missing_tools -eq 0 ]; then
    echo "?? All required components are installed and working!"
else
    echo "?? Some components are missing or misconfigured. Please check the logs above."
fi
