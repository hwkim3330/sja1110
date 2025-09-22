#!/bin/bash
# SJA1110 FRER Firmware Verification Script

echo "SJA1110 UltraThink FRER Firmware Verification"
echo "=============================================="

# Check firmware files
if [ ! -f sja1110_ultrathink_switch.bin ]; then
    echo "ERROR: Switch firmware not found!"
    exit 1
fi

if [ ! -f sja1110_ultrathink_uc.bin ]; then
    echo "ERROR: UC firmware not found!"
    exit 1
fi

echo "Firmware files found."
echo ""

# Verify switch firmware
echo "Analyzing switch firmware..."
SWITCH_SIZE=$(stat -c%s sja1110_ultrathink_switch.bin)
echo "  Size: $SWITCH_SIZE bytes"

# Check device ID
DEVICE_ID=$(xxd -s 0 -l 4 -e sja1110_ultrathink_switch.bin | awk '{print $2}')
if [ "$DEVICE_ID" = "b700030e" ]; then
    echo "  [OK] Device ID verified: SJA1110"
else
    echo "  [ERROR] Invalid device ID: $DEVICE_ID"
fi

# Check FRER tables
echo ""
echo "FRER Configuration Tables:"
xxd -s 48 -l 64 sja1110_ultrathink_switch.bin | head -4
echo ""

# Verify UC firmware
echo "Analyzing UC firmware..."
UC_SIZE=$(stat -c%s sja1110_ultrathink_uc.bin)
echo "  Size: $UC_SIZE bytes"

# Check vector table
RESET_VECTOR=$(xxd -s 4 -l 4 -e sja1110_ultrathink_uc.bin | awk '{print $2}')
echo "  Reset vector: 0x$RESET_VECTOR"

echo ""
echo "Verification complete."
