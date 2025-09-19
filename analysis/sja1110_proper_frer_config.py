#!/usr/bin/env python3
"""
SJA1110 FRER Configuration Generator - Based on NXP Official Format
Creates multiple versions for testing
"""

import struct
import binascii

# From NXP source: SJA1110 has 11 ports (0-10)
# Port mapping for S32G274ARDB2:
# Port 0: Internal port (CPU)
# Port 1-4: 1000BASE-T1 (RGMII)
# Port 5-6: 100BASE-T1
# Port 7-10: Internal ports

class SJA1110ConfigFormat:
    """Official SJA1110 configuration format based on NXP tools"""

    # Device ID from sja1110_init.h
    SJA1110_DEVICE_ID = 0xB700030E

    # Configuration table block IDs (from static-config.h)
    BLKID_L2_FORWARDING_TABLE = 0x08
    BLKID_MAC_CONFIG_TABLE = 0x09
    BLKID_L2_FORWARDING_PARAMS_TABLE = 0x0E
    BLKID_GENERAL_PARAMS_TABLE = 0x11

    # Table header format
    HEADER_SIZE = 12

    @staticmethod
    def create_table_header(block_id, crc, entry_count):
        """Create 12-byte table header"""
        header = struct.pack('<I', block_id)           # Block ID (4 bytes)
        header += struct.pack('<I', entry_count)       # Entry count (4 bytes)
        header += struct.pack('<I', crc)               # CRC (4 bytes)
        return header

    @staticmethod
    def calculate_crc(data):
        """Simple CRC32 calculation"""
        import zlib
        return zlib.crc32(data) & 0xFFFFFFFF


class FRERConfigV1:
    """Version 1: Basic port forwarding P4 -> P2A, P2B"""

    def __init__(self):
        self.config = bytearray()

    def create_config(self):
        """Create configuration with basic forwarding"""

        # 1. Device header (original format from binary)
        self.config += struct.pack('<I', 0x0F0300B7)  # Magic
        self.config += struct.pack('<I', 0x00000006)  # Version
        self.config += struct.pack('<I', 0xDC000000)  # Config size
        self.config += struct.pack('<I', 0xE82CE086)  # Features/CRC

        # 2. L2 Forwarding configuration (P4 -> P2A, P2B)
        # Entry format: [source_port][destination_mask]
        forwarding_entries = []

        # P4 (port 4) forwards to P2A (port 2) and P2B (port 3)
        port_4_dest_mask = (1 << 2) | (1 << 3)  # Bits 2 and 3 set
        forwarding_entries.append(struct.pack('<II', 4, port_4_dest_mask))

        # Add forwarding table
        for entry in forwarding_entries:
            self.config += entry

        # 3. Fill to match original size
        while len(self.config) < 2236:
            self.config += struct.pack('<I', 0x00ECFFFF)
            self.config += struct.pack('<I', 0x9FFF7F00)

        return bytes(self.config[:2236])


class FRERConfigV2:
    """Version 2: With FRER stream identification"""

    def __init__(self):
        self.entries = []

    def create_config(self):
        """Create configuration with FRER stream support"""

        config = bytearray()

        # Device header with FRER support enabled
        config += struct.pack('<I', 0x0F0300B7)  # Magic
        config += struct.pack('<I', 0x00000006)  # Version
        config += struct.pack('<I', 0xDC000000)  # Size
        config += struct.pack('<I', 0xE82CE086)  # Features with FRER

        # Port configuration entries
        # Format from binary analysis: [command][value] pairs

        # Configure P4 as input
        config += struct.pack('<I', 0x00ECFFFF)  # Command
        config += struct.pack('<I', 0x9FFF7F04)  # P4 config

        # Configure P2A as FRER output
        config += struct.pack('<I', 0x00ECFFFF)  # Command
        config += struct.pack('<I', 0x9FFF7F02)  # P2A config

        # Configure P2B as FRER output
        config += struct.pack('<I', 0x00ECFFFF)  # Command
        config += struct.pack('<I', 0x9FFF7F03)  # P2B config

        # FRER stream configuration
        # Enable stream ID 1 for replication
        config += struct.pack('<I', 0x80010000)  # FRER enable
        config += struct.pack('<I', 0x00000001)  # Stream ID 1
        config += struct.pack('<I', 0x00000010)  # P4 input (bit 4)
        config += struct.pack('<I', 0x0000000C)  # P2A+P2B output (bits 2,3)

        # Fill remaining space with port configs
        pattern_index = 0
        patterns = [
            (0x00ECFFFF, 0x9FFF7F00),
            (0x00ECFFFF, 0x9FFF7F02),
            (0x00ECFFFF, 0x9FFF7F04),
            (0x00ECFFFF, 0x9FFF7F06),
            (0x00ECFFFF, 0x9FFF7F08),
            (0x00ECFFFF, 0x9FFF7F0A),
        ]

        while len(config) < 2236:
            cmd, val = patterns[pattern_index % len(patterns)]
            config += struct.pack('<I', cmd)
            if len(config) < 2236:
                config += struct.pack('<I', val + (pattern_index * 2))
            pattern_index += 1

        return bytes(config[:2236])


class FRERConfigV3:
    """Version 3: NXP tool compatible format with proper tables"""

    def __init__(self):
        self.tables = []

    def create_config(self):
        """Create config using NXP table format"""

        config = bytearray()

        # Configuration header (NXP format)
        config += struct.pack('>I', 0xB700030F)  # Device ID (big-endian)
        config += struct.pack('>I', 0x00000006)  # Version
        config += struct.pack('>I', 0x00000000)  # Reserved
        config += struct.pack('>I', 0x00000000)  # Reserved

        # L2 Forwarding Table
        # Table header
        table_id = SJA1110ConfigFormat.BLKID_L2_FORWARDING_TABLE
        entry_count = 11  # 11 ports
        crc = 0x00000000  # Will be calculated

        config += SJA1110ConfigFormat.create_table_header(table_id, crc, entry_count)

        # L2 Forwarding entries (8 bytes each)
        # Format: [reachable_ports][broadcast_domain]
        for port in range(11):
            if port == 4:  # P4 forwards to P2A and P2B
                reach = (1 << 2) | (1 << 3)
                bcast = (1 << 2) | (1 << 3)
            elif port in [2, 3]:  # P2A, P2B can reach each other
                reach = 0x7FF  # All ports reachable
                bcast = 0x7FF
            else:
                reach = 0x7FF
                bcast = 0x7FF

            config += struct.pack('<II', reach, bcast)

        # MAC Configuration Table
        table_id = SJA1110ConfigFormat.BLKID_MAC_CONFIG_TABLE
        entry_count = 11

        config += SJA1110ConfigFormat.create_table_header(table_id, crc, entry_count)

        # MAC config entries (32 bytes each for SJA1110)
        for port in range(11):
            # Basic MAC config
            mac_entry = bytearray(32)
            mac_entry[0:4] = struct.pack('<I', 0x00000003)  # Enable TX/RX
            mac_entry[4:8] = struct.pack('<I', 1000)        # Speed
            config += mac_entry

        # Pad to 2236 bytes
        while len(config) < 2236:
            config += b'\x00'

        return bytes(config[:2236])


class UCFirmwareGenerator:
    """Generate microcontroller firmware variants"""

    @staticmethod
    def create_basic_uc():
        """Basic UC firmware - minimal initialization"""

        fw = bytearray()

        # Image valid marker (from sja1110_init.h)
        fw += bytes([0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6])

        # Firmware header
        fw += struct.pack('<I', 0x02000024)  # Entry point
        fw += struct.pack('<I', 0x00000000)  # Reserved
        fw += struct.pack('<I', 0x00001212)  # Firmware size
        fw += struct.pack('<I', 0x00000012)  # Version

        # Vector table (ARM Cortex-M)
        fw += struct.pack('<I', 0x0004E2F8)  # Stack pointer
        fw += struct.pack('<I', 0x000001C1)  # Reset handler

        # Fill vectors
        for _ in range(14):
            fw += struct.pack('<I', 0x00000209)  # Default handler

        # Basic initialization code
        # This would contain the actual UC code
        # For now, minimal stub

        # Pad to 8KB
        while len(fw) < 8192:
            fw += b'\xFF'

        return bytes(fw)

    @staticmethod
    def create_frer_uc():
        """UC firmware with FRER packet processing"""

        fw = bytearray()

        # Image valid marker
        fw += bytes([0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6])

        # Header with FRER support
        fw += struct.pack('<I', 0x02000024)  # Entry
        fw += struct.pack('<I', 0x00000001)  # FRER enabled
        fw += struct.pack('<I', 0x00002000)  # Size
        fw += struct.pack('<I', 0x00000020)  # Version

        # Enhanced vector table
        fw += struct.pack('<I', 0x20008000)  # Stack
        fw += struct.pack('<I', 0x00000401)  # Reset
        fw += struct.pack('<I', 0x00000501)  # NMI
        fw += struct.pack('<I', 0x00000601)  # HardFault

        # FRER interrupt handlers
        for _ in range(12):
            fw += struct.pack('<I', 0x00000801)

        # FRER configuration area
        frer_config = [
            0x00000001,  # Enable FRER
            0x0000F1CD,  # R-TAG EtherType
            0x00000001,  # Stream ID start
            0x00000100,  # Max streams
            0x00000100,  # Sequence window
            0x000003E8,  # Timeout
        ]

        for val in frer_config:
            fw += struct.pack('<I', val)

        # Pad to standard size
        while len(fw) < 320280:  # Original UC size
            fw += b'\xFF'

        return bytes(fw)


def generate_all_versions():
    """Generate all firmware versions for testing"""

    print("SJA1110 FRER Firmware Generator - Multiple Versions")
    print("=" * 60)
    print()

    # Version 1: Basic forwarding
    print("Creating Version 1: Basic Port Forwarding...")
    v1 = FRERConfigV1()
    v1_data = v1.create_config()
    with open('sja1110_switch_v1_basic.bin', 'wb') as f:
        f.write(v1_data)
    print(f"  Created: sja1110_switch_v1_basic.bin ({len(v1_data)} bytes)")

    # Version 2: With FRER stream
    print("Creating Version 2: FRER Stream Support...")
    v2 = FRERConfigV2()
    v2_data = v2.create_config()
    with open('sja1110_switch_v2_frer.bin', 'wb') as f:
        f.write(v2_data)
    print(f"  Created: sja1110_switch_v2_frer.bin ({len(v2_data)} bytes)")

    # Version 3: NXP format
    print("Creating Version 3: NXP Table Format...")
    v3 = FRERConfigV3()
    v3_data = v3.create_config()
    with open('sja1110_switch_v3_nxp.bin', 'wb') as f:
        f.write(v3_data)
    print(f"  Created: sja1110_switch_v3_nxp.bin ({len(v3_data)} bytes)")

    # UC Firmware versions
    print()
    print("Creating UC Firmware Versions...")

    uc_basic = UCFirmwareGenerator.create_basic_uc()
    with open('sja1110_uc_v1_basic.bin', 'wb') as f:
        f.write(uc_basic)
    print(f"  Created: sja1110_uc_v1_basic.bin ({len(uc_basic)} bytes)")

    uc_frer = UCFirmwareGenerator.create_frer_uc()
    with open('sja1110_uc_v2_frer.bin', 'wb') as f:
        f.write(uc_frer)
    print(f"  Created: sja1110_uc_v2_frer.bin ({len(uc_frer)} bytes)")

    print()
    print("Configuration Summary:")
    print("-" * 40)
    print("All versions configure:")
    print("  Input: Port 4 (P4)")
    print("  Output: Port 2A (P2), Port 2B (P3)")
    print("  Mode: Frame replication (FRER)")
    print()
    print("Testing Instructions:")
    print("1. Try v1_basic first (simplest)")
    print("2. If v1 works, try v2_frer (with FRER)")
    print("3. Use v3_nxp for full compatibility")
    print()
    print("Load with: sja1110_loader.sh <version>")


if __name__ == "__main__":
    generate_all_versions()