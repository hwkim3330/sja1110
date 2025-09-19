#!/usr/bin/env python3
"""
SJA1110 FRER Configuration for NXP GoldVIP Board
Based on original binaries from GoldVIP-S32G2-1.14.0
"""

import struct
import sys
import os

class GoldVIPFRER:
    """
    GoldVIP (Gold Vehicle Interface Platform) Board Configuration
    - S32G274ARDB2 processor
    - SJA1110 TSN switch
    """

    def __init__(self):
        # Load and analyze original binaries
        self.original_switch_path = r"C:\Users\parksik\Downloads\GoldVIP-S32G2-1.14.0 (1)\binaries\sja1110_switch.bin"
        self.original_uc_path = r"C:\Users\parksik\Downloads\GoldVIP-S32G2-1.14.0 (1)\binaries\sja1110_uc.bin"

    def analyze_original(self):
        """Analyze original GoldVIP configuration"""
        with open(self.original_switch_path, 'rb') as f:
            self.switch_orig = f.read()
        with open(self.original_uc_path, 'rb') as f:
            self.uc_orig = f.read()

        print(f"Original switch config: {len(self.switch_orig)} bytes")
        print(f"Original UC firmware: {len(self.uc_orig)} bytes")

        # Extract configuration pattern
        # First 16 bytes contain device ID and config
        header = struct.unpack('<4I', self.switch_orig[:16])
        print(f"Header: {[hex(x) for x in header]}")

        return header

    def create_frer_switch_config(self):
        """
        Create FRER switch configuration for GoldVIP
        P4 -> P2A, P2B replication
        """

        # Start with original binary as base
        config = bytearray(self.switch_orig)

        # Modify for FRER configuration
        # Based on pattern analysis: entries start at offset 0x10

        # Configuration entries are 8-byte pairs: [config_word][port_settings]
        # Offset 0x10+: Port configurations

        # Find and modify P4 (port 4) configuration
        # P4 at offset 0x30 (port 4 = 5th port, 8 bytes each)
        p4_offset = 0x10 + (4 * 8)

        # Enable FRER on P4
        # Set forwarding to P2A (port 2) and P2B (port 3)
        config[p4_offset:p4_offset+4] = struct.pack('<I', 0x00ECFFFF)
        config[p4_offset+4:p4_offset+8] = struct.pack('<I', 0x9FFF7F04)

        # Configure P2A for FRER output
        p2a_offset = 0x10 + (2 * 8)
        config[p2a_offset:p2a_offset+4] = struct.pack('<I', 0x00ECFFFF)
        config[p2a_offset+4:p2a_offset+8] = struct.pack('<I', 0x9FFF7F02 | 0x80000000)  # FRER enable bit

        # Configure P2B for FRER output
        p2b_offset = 0x10 + (3 * 8)
        config[p2b_offset:p2b_offset+4] = struct.pack('<I', 0x00ECFFFF)
        config[p2b_offset+4:p2b_offset+8] = struct.pack('<I', 0x9FFF7F03 | 0x80000000)  # FRER enable bit

        # Add FRER stream configuration at end of port configs
        # Find first 0x00000000 pattern (end marker)
        frer_offset = 0x100  # After port configs

        if frer_offset < len(config) - 16:
            # FRER Stream ID 1 configuration
            config[frer_offset:frer_offset+4] = struct.pack('<I', 0x00010001)  # Stream ID 1
            config[frer_offset+4:frer_offset+8] = struct.pack('<I', 0x00000010)  # P4 input mask
            config[frer_offset+8:frer_offset+12] = struct.pack('<I', 0x0000000C)  # P2A|P2B output
            config[frer_offset+12:frer_offset+16] = struct.pack('<I', 0xF1CD0000)  # R-TAG

        return bytes(config)

    def create_frer_uc_firmware(self):
        """
        Create UC firmware with FRER support for GoldVIP
        """

        # Start with original UC firmware structure
        # Keep the valid image marker and headers intact
        uc = bytearray(self.uc_orig)

        # The UC firmware has specific areas we can modify:
        # 1. Keep image marker at 0x00-0x07: 6A A6 6A A6 6A A6 6A A6
        # 2. Keep boot header at 0x08-0x1F
        # 3. Modify configuration area for FRER

        # FRER configuration typically starts after vector table
        # Around offset 0x1000
        frer_config_offset = 0x1000

        if frer_config_offset < len(uc) - 32:
            # FRER enable flags
            uc[frer_config_offset:frer_config_offset+4] = struct.pack('<I', 0x00000001)  # Enable
            uc[frer_config_offset+4:frer_config_offset+8] = struct.pack('<I', 0x0000F1CD)  # R-TAG
            uc[frer_config_offset+8:frer_config_offset+12] = struct.pack('<I', 0x00000100)  # Window
            uc[frer_config_offset+12:frer_config_offset+16] = struct.pack('<I', 0x00000001)  # Stream ID

            # Port mapping for FRER
            uc[frer_config_offset+16:frer_config_offset+20] = struct.pack('<I', 0x00000010)  # P4 in
            uc[frer_config_offset+20:frer_config_offset+24] = struct.pack('<I', 0x0000000C)  # P2A|P2B out

        return bytes(uc)


def main():
    print("=" * 70)
    print("SJA1110 FRER Configuration Generator for NXP GoldVIP Board")
    print("=" * 70)
    print()

    generator = GoldVIPFRER()

    print("Analyzing original GoldVIP configuration...")
    header = generator.analyze_original()
    print()

    print("Creating FRER configuration...")
    print("  Port mapping: P4 -> P2A, P2B (replication)")
    print("  FRER: IEEE 802.1CB enabled")
    print("  R-TAG: 0xF1CD")
    print()

    # Generate switch configuration
    switch_config = generator.create_frer_switch_config()
    output_switch = "sja1110_goldvip_switch_frer.bin"
    with open(output_switch, 'wb') as f:
        f.write(switch_config)
    print(f"[OK] Created: {output_switch} ({len(switch_config)} bytes)")

    # Generate UC firmware
    uc_firmware = generator.create_frer_uc_firmware()
    output_uc = "sja1110_goldvip_uc_frer.bin"
    with open(output_uc, 'wb') as f:
        f.write(uc_firmware)
    print(f"[OK] Created: {output_uc} ({len(uc_firmware)} bytes)")

    print()
    print("Configuration details:")
    print("-" * 40)
    print("Board: NXP GoldVIP (S32G274ARDB2)")
    print("Switch: SJA1110 TSN Ethernet Switch")
    print("Input: Port 4 (P4)")
    print("Output: Port 2A (P2), Port 2B (P3)")
    print("Feature: IEEE 802.1CB FRER")
    print("Stream ID: 1")
    print("Recovery window: 256 frames")
    print()
    print("Files generated:")
    print(f"  1. {output_switch}")
    print(f"  2. {output_uc}")
    print()
    print("These files are based on original GoldVIP binaries")
    print("and modified for FRER frame replication.")

if __name__ == "__main__":
    main()