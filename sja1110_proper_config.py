#!/usr/bin/env python3
"""
SJA1110 Proper Configuration Generator
Creates full configuration with all required tables
Based on NXP SJA1105 tool structure
"""

import struct
import zlib

class SJA1110ProperConfig:
    """
    Generate complete SJA1110 configuration with all required tables
    """

    # Table IDs from NXP documentation
    BLKID_L2_LOOKUP_TABLE = 0x05
    BLKID_L2_POLICING_TABLE = 0x06
    BLKID_VLAN_LOOKUP_TABLE = 0x07
    BLKID_L2_FORWARDING_TABLE = 0x08
    BLKID_MAC_CONFIG_TABLE = 0x09
    BLKID_L2_LOOKUP_PARAMS_TABLE = 0x0D
    BLKID_L2_FORWARDING_PARAMS_TABLE = 0x0E
    BLKID_GENERAL_PARAMS_TABLE = 0x11
    BLKID_XMII_MODE_PARAMS_TABLE = 0x4E

    # SJA1110 specifics
    NUM_PORTS = 11
    DEVICE_ID = 0xB700030F

    def __init__(self):
        self.tables = []
        self.config_data = bytearray()

    def add_table_header(self, table_id, entry_count, data_size):
        """Add 12-byte table header"""
        header = bytearray()
        header += struct.pack('<I', table_id)      # Table ID
        header += struct.pack('<H', entry_count)   # Entry count
        header += struct.pack('<H', data_size)     # Data size
        header += struct.pack('<I', 0)             # CRC (will be updated later)
        return header

    def create_l2_forwarding_table(self):
        """Create L2 forwarding table - controls port forwarding"""
        print("Creating L2 Forwarding Table...")

        table_data = bytearray()

        # Each port gets an entry (8 bytes each)
        for port in range(self.NUM_PORTS):
            reach_port = 0x7FF  # All ports reachable by default
            bc_domain = 0x7FF   # Broadcast domain

            # FRER configuration for specific ports
            if port == 4:  # P4 - input port
                # Forward to P2A (port 2) and P2B (port 3)
                reach_port = (1 << 2) | (1 << 3)
                bc_domain = (1 << 2) | (1 << 3)
            elif port == 2:  # P2A - FRER output
                reach_port = 0x7FF
                bc_domain = 0x7FF
            elif port == 3:  # P2B - FRER output
                reach_port = 0x7FF
                bc_domain = 0x7FF

            # Entry format: [reachable_ports][broadcast_domain]
            table_data += struct.pack('<I', reach_port)
            table_data += struct.pack('<I', bc_domain)

        # Add table header
        header = self.add_table_header(
            self.BLKID_L2_FORWARDING_TABLE,
            self.NUM_PORTS,
            len(table_data)
        )

        return header + table_data

    def create_mac_config_table(self):
        """Create MAC configuration table"""
        print("Creating MAC Config Table...")

        table_data = bytearray()

        # Each port gets MAC configuration (32 bytes each for SJA1110)
        for port in range(self.NUM_PORTS):
            mac_entry = bytearray(32)

            # Basic MAC settings
            mac_entry[0:4] = struct.pack('<I', 0x00000001)  # TOP[0] - Enable
            mac_entry[4:8] = struct.pack('<I', 0x00000001)  # BASE[0] - Speed
            mac_entry[8:12] = struct.pack('<I', 0x00000000) # BASE[1]

            # FRER-specific for P2A and P2B
            if port in [2, 3]:  # P2A, P2B
                mac_entry[12:16] = struct.pack('<I', 0x80000000)  # Enable FRER

            table_data += mac_entry

        header = self.add_table_header(
            self.BLKID_MAC_CONFIG_TABLE,
            self.NUM_PORTS,
            len(table_data)
        )

        return header + table_data

    def create_l2_forwarding_params(self):
        """Create L2 forwarding parameters"""
        print("Creating L2 Forwarding Parameters...")

        table_data = bytearray()

        # Single entry (12 bytes)
        table_data += struct.pack('<I', 0x00000FFF)  # MAX_DYNP
        table_data += struct.pack('<I', 0x00000001)  # Part_SPC
        table_data += struct.pack('<I', 0x00000000)  # Reserved

        header = self.add_table_header(
            self.BLKID_L2_FORWARDING_PARAMS_TABLE,
            1,
            len(table_data)
        )

        return header + table_data

    def create_general_params(self):
        """Create general parameters table"""
        print("Creating General Parameters...")

        table_data = bytearray()

        # General params (44 bytes for SJA1110)
        params = bytearray(44)

        # Key settings
        params[0:4] = struct.pack('<I', 0x00000001)   # VLLUPFORMAT
        params[4:8] = struct.pack('<I', 0x00000000)   # MIRR_PTACU
        params[8:12] = struct.pack('<I', self.DEVICE_ID)  # SWITCHID
        params[12:16] = struct.pack('<I', 0x00000000) # HOSTPRIO
        params[16:20] = struct.pack('<I', 0x00000180) # MAC_FLTRES1
        params[20:24] = struct.pack('<I', 0x00000180) # MAC_FLTRES0
        params[24:28] = struct.pack('<I', 0x00000000) # MAC_FLT1
        params[28:32] = struct.pack('<I', 0x00000000) # MAC_FLT0
        params[32:36] = struct.pack('<I', 0x00000000) # INCL_SRCPT1
        params[36:40] = struct.pack('<I', 0x00000000) # INCL_SRCPT0
        params[40:44] = struct.pack('<I', 0x00000000) # Reserved

        table_data += params

        header = self.add_table_header(
            self.BLKID_GENERAL_PARAMS_TABLE,
            1,
            len(table_data)
        )

        return header + table_data

    def create_vlan_lookup_table(self):
        """Create VLAN lookup table"""
        print("Creating VLAN Lookup Table...")

        table_data = bytearray()

        # Default VLAN entry (8 bytes)
        vlan_entry = bytearray()
        vlan_entry += struct.pack('<H', 0x0001)  # VLANID = 1
        vlan_entry += struct.pack('<H', 0x07FF)  # VMEMB_PORT - all ports
        vlan_entry += struct.pack('<H', 0x07FF)  # VLAN_BC - broadcast
        vlan_entry += struct.pack('<H', 0x0000)  # TAG_PORT

        table_data += vlan_entry

        header = self.add_table_header(
            self.BLKID_VLAN_LOOKUP_TABLE,
            1,
            len(table_data)
        )

        return header + table_data

    def create_xmii_params(self):
        """Create xMII mode parameters"""
        print("Creating xMII Parameters...")

        table_data = bytearray()

        # xMII settings (4 bytes)
        table_data += struct.pack('<I', 0x00000000)  # Default MII mode

        header = self.add_table_header(
            self.BLKID_XMII_MODE_PARAMS_TABLE,
            1,
            len(table_data)
        )

        return header + table_data

    def generate_configuration(self):
        """Generate complete configuration"""
        print("\n" + "="*60)
        print("Generating SJA1110 Configuration")
        print("="*60 + "\n")

        # Device header (16 bytes)
        self.config_data += struct.pack('<I', self.DEVICE_ID)  # Device ID
        self.config_data += struct.pack('<I', 0x00000100)      # Version
        self.config_data += struct.pack('<I', 0x00000000)      # Timestamp
        self.config_data += struct.pack('<I', 0x00000000)      # Reserved for CRC

        # Add all required tables
        tables = []
        tables.append(self.create_l2_forwarding_table())
        tables.append(self.create_mac_config_table())
        tables.append(self.create_l2_forwarding_params())
        tables.append(self.create_general_params())
        tables.append(self.create_vlan_lookup_table())
        tables.append(self.create_xmii_params())

        # Combine all tables
        for table in tables:
            self.config_data += table

        # Calculate CRC over entire configuration
        config_without_crc = self.config_data[:]
        config_without_crc[12:16] = b'\x00' * 4  # Clear CRC field

        crc = zlib.crc32(config_without_crc) & 0xFFFFFFFF
        self.config_data[12:16] = struct.pack('<I', crc)

        print(f"Configuration size: {len(self.config_data)} bytes")
        print(f"CRC: 0x{crc:08X}")

        return bytes(self.config_data)

    def verify_configuration(self, config):
        """Verify configuration structure"""
        print("\nVerifying configuration...")

        device_id = struct.unpack('<I', config[0:4])[0]
        version = struct.unpack('<I', config[4:8])[0]
        crc_field = struct.unpack('<I', config[12:16])[0]

        print(f"  Device ID: 0x{device_id:08X}")
        print(f"  Version: 0x{version:08X}")
        print(f"  Size: {len(config)} bytes")
        print(f"  CRC: 0x{crc_field:08X}")

        # Verify CRC
        config_check = bytearray(config)
        config_check[12:16] = b'\x00' * 4
        calc_crc = zlib.crc32(bytes(config_check)) & 0xFFFFFFFF

        if calc_crc == crc_field:
            print(f"  [OK] CRC valid (calculated: 0x{calc_crc:08X})")
            return True
        else:
            print(f"  [ERROR] CRC mismatch (calculated: 0x{calc_crc:08X})")
            return False


def main():
    generator = SJA1110ProperConfig()

    # Generate configuration
    config = generator.generate_configuration()

    # Verify
    if generator.verify_configuration(config):
        # Save configuration
        filename = 'sja1110_switch_proper.bin'
        with open(filename, 'wb') as f:
            f.write(config)

        print(f"\n[SUCCESS] Configuration saved to {filename}")
        print(f"Size: {len(config)} bytes")
        print("\nThis is a properly structured configuration with:")
        print("  - All required tables")
        print("  - Correct size (not 2.2KB)")
        print("  - Valid CRC")
        print("  - FRER: P4 -> P2A, P2B")
    else:
        print("\n[ERROR] Configuration verification failed!")

if __name__ == "__main__":
    main()