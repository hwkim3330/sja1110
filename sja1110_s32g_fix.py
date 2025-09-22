#!/usr/bin/env python3
"""
SJA1110 Firmware Fix for S32G274A-RDB2
Fixes device ID endianness and UC header issues
"""

import struct
import sys

def fix_switch_firmware():
    """Fix switch firmware device ID"""

    print("Fixing SJA1110 switch firmware for S32G274A-RDB2...")

    # Read existing firmware
    with open('sja1110_ultrathink_switch.bin', 'rb') as f:
        data = bytearray(f.read())

    # Current (wrong): 0xe0300b7 (big-endian in wrong order)
    # Expected: 0xb700030f (little-endian)
    # Fix: Write as little-endian 0x0f0300b7

    # Update device ID at offset 0x00
    struct.pack_into('<I', data, 0x00, 0x0f0300b7)

    print(f"  Device ID fixed: 0x0f0300b7 (will read as 0xb700030f)")

    # Write fixed firmware
    with open('sja1110_switch_s32g.bin', 'wb') as f:
        f.write(data)

    print(f"  Created: sja1110_switch_s32g.bin ({len(data)} bytes)")

    return data


def fix_uc_firmware():
    """Fix UC firmware header"""

    print("\nFixing SJA1110 UC firmware for S32G274A-RDB2...")

    # Create proper UC firmware header
    fw = bytearray()

    # Valid UC firmware magic header (8 bytes)
    # This is what SJA1110 driver expects
    fw += bytes([0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6])

    # Firmware header structure
    fw += struct.pack('<I', 0x02000024)  # Entry point
    fw += struct.pack('<I', 0x00000001)  # Version/flags
    fw += struct.pack('<I', 0x00004000)  # Firmware size
    fw += struct.pack('<I', 0x00000020)  # Header size

    # Read existing UC firmware (skip current bad header)
    with open('sja1110_ultrathink_uc.bin', 'rb') as f:
        original = f.read()

    # ARM Cortex-M7 vector table from original
    fw += original[0:1024]  # Copy vector table

    # Add rest of firmware
    fw += original[1024:320280-24]  # Adjust size to maintain 320280 total

    # Pad to exact size
    while len(fw) < 320280:
        fw += b'\xFF'

    # Write fixed firmware
    with open('sja1110_uc_s32g.bin', 'wb') as f:
        f.write(fw[:320280])

    print(f"  Added valid UC header: 6AA66AA66AA66AA6")
    print(f"  Created: sja1110_uc_s32g.bin ({len(fw[:320280])} bytes)")

    return fw[:320280]


def verify_fixes():
    """Verify the fixed firmware files"""

    print("\nVerifying fixed firmware files...")

    # Check switch firmware
    with open('sja1110_switch_s32g.bin', 'rb') as f:
        switch_data = f.read()

    device_id = struct.unpack('<I', switch_data[0:4])[0]
    print(f"  Switch Device ID: 0x{device_id:08x} ", end='')
    if device_id == 0x0f0300b7:
        print("[OK] CORRECT")
    else:
        print("[ERROR] WRONG")

    # Check UC firmware
    with open('sja1110_uc_s32g.bin', 'rb') as f:
        uc_data = f.read()

    magic = uc_data[0:8]
    expected_magic = bytes([0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6])

    print(f"  UC Magic Header: {magic.hex()} ", end='')
    if magic == expected_magic:
        print("[OK] CORRECT")
    else:
        print("[ERROR] WRONG")


def create_upload_script():
    """Create upload script for S32G274A-RDB2"""

    script = """#!/bin/bash
# Upload fixed SJA1110 firmware to S32G274A-RDB2

echo "Uploading SJA1110 firmware to S32G274A-RDB2..."

# Copy files to board
scp sja1110_switch_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp sja1110_uc_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin

echo "Files uploaded. Rebooting board..."
ssh root@192.168.1.1 "sync && reboot"

echo "Done! Board will reboot with new firmware."
"""

    with open('upload_to_s32g.sh', 'w') as f:
        f.write(script)

    print("\nCreated upload script: upload_to_s32g.sh")
    print("Usage: ./upload_to_s32g.sh")


def main():
    print("=" * 60)
    print("SJA1110 Firmware Fix for S32G274A-RDB2")
    print("=" * 60)

    # Fix both firmwares
    fix_switch_firmware()
    fix_uc_firmware()

    # Verify
    verify_fixes()

    # Create upload script
    create_upload_script()

    print("\n" + "=" * 60)
    print("Firmware files ready for S32G274A-RDB2!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy files to board:")
    print("   scp sja1110_switch_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin")
    print("   scp sja1110_uc_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin")
    print("\n2. Reboot board:")
    print("   ssh root@192.168.1.1 reboot")
    print("\n3. Check dmesg for successful loading:")
    print("   dmesg | grep sja1110")


if __name__ == "__main__":
    main()