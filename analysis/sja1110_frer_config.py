#!/usr/bin/env python3
"""
SJA1110 FRER Configuration Generator
Configures P4 input to replicate to P2A and P2B ports
"""

import struct
import sys

class SJA1110Config:
    # SJA1110 Port definitions
    PORT_P0 = 0
    PORT_P1 = 1
    PORT_P2A = 2
    PORT_P2B = 3
    PORT_P3 = 4
    PORT_P4 = 5

    # Register addresses (example offsets)
    REG_GENERAL_CFG = 0x100000
    REG_PORT_CFG = 0x200000
    REG_FRER_CFG = 0x400000
    REG_STREAM_ID = 0x500000
    REG_SEQ_RECOVERY = 0x600000

    def __init__(self):
        self.config_data = []

    def add_register(self, address, value):
        """Add a register configuration entry"""
        self.config_data.append((address, value))

    def configure_general(self):
        """General switch configuration"""
        # Enable TSN features
        self.add_register(self.REG_GENERAL_CFG + 0x00, 0x0F0300B7)  # Magic header
        self.add_register(self.REG_GENERAL_CFG + 0x04, 0x00000006)  # Version
        self.add_register(self.REG_GENERAL_CFG + 0x08, 0xDC000000)  # Feature enable
        self.add_register(self.REG_GENERAL_CFG + 0x0C, 0xE82CE086)  # TSN enable

    def configure_ports(self):
        """Configure port settings"""
        # P4 as input port
        self.add_register(self.REG_PORT_CFG + (self.PORT_P4 * 0x100), 0x00ECFFFF)
        self.add_register(self.REG_PORT_CFG + (self.PORT_P4 * 0x100) + 4, 0x9FFF7F00 | self.PORT_P4)

        # P2A as output port with FRER
        self.add_register(self.REG_PORT_CFG + (self.PORT_P2A * 0x100), 0x00ECFFFF)
        self.add_register(self.REG_PORT_CFG + (self.PORT_P2A * 0x100) + 4, 0x9FFF7F00 | self.PORT_P2A)

        # P2B as output port with FRER
        self.add_register(self.REG_PORT_CFG + (self.PORT_P2B * 0x100), 0x00ECFFFF)
        self.add_register(self.REG_PORT_CFG + (self.PORT_P2B * 0x100) + 4, 0x9FFF7F00 | self.PORT_P2B)

    def configure_frer_replication(self):
        """Configure FRER frame replication from P4 to P2A/P2B"""

        # Stream ID configuration - Map all P4 traffic to Stream ID 1
        stream_id = 1
        self.add_register(self.REG_STREAM_ID + 0x00, 0x80000001)  # Enable stream ID 1
        self.add_register(self.REG_STREAM_ID + 0x04, (1 << self.PORT_P4))  # Input port mask
        self.add_register(self.REG_STREAM_ID + 0x08, 0xFFFFFFFF)  # Match all frames
        self.add_register(self.REG_STREAM_ID + 0x0C, stream_id)    # Stream ID value

        # FRER configuration for Stream ID 1
        self.add_register(self.REG_FRER_CFG + 0x00, 0x80000001)   # Enable FRER for stream 1
        self.add_register(self.REG_FRER_CFG + 0x04, 0x00000003)   # Replication mode

        # Configure replication paths
        # Path 1: P4 -> P2A
        self.add_register(self.REG_FRER_CFG + 0x10, (1 << self.PORT_P2A))
        # Path 2: P4 -> P2B
        self.add_register(self.REG_FRER_CFG + 0x14, (1 << self.PORT_P2B))

        # Sequence generation configuration
        self.add_register(self.REG_FRER_CFG + 0x20, 0x00010000)   # Enable sequence generation
        self.add_register(self.REG_FRER_CFG + 0x24, 0x0000FFFF)   # Sequence number max

        # R-TAG configuration
        self.add_register(self.REG_FRER_CFG + 0x30, 0xF1CD0000)   # R-TAG EtherType
        self.add_register(self.REG_FRER_CFG + 0x34, 0x00000001)   # Insert R-TAG

    def configure_forwarding_table(self):
        """Configure L2 forwarding table"""
        # Forward all traffic from P4 to both P2A and P2B
        port_mask = (1 << self.PORT_P2A) | (1 << self.PORT_P2B)

        # Broadcast/Unknown unicast forwarding
        self.add_register(0x300000, port_mask)

        # Enable forwarding from P4
        self.add_register(0x300004, (1 << self.PORT_P4))

    def configure_sequence_recovery(self):
        """Configure sequence recovery for redundancy elimination (optional)"""
        # This would be used on the receiving end to eliminate duplicates

        # Sequence recovery window
        self.add_register(self.REG_SEQ_RECOVERY + 0x00, 0x80000001)  # Enable
        self.add_register(self.REG_SEQ_RECOVERY + 0x04, 0x00000100)  # Window size = 256
        self.add_register(self.REG_SEQ_RECOVERY + 0x08, 0x000003E8)  # Timeout = 1000ms

        # History buffer configuration
        self.add_register(self.REG_SEQ_RECOVERY + 0x10, 0x00001000)  # Buffer size
        self.add_register(self.REG_SEQ_RECOVERY + 0x14, 0x90000000)  # Buffer address

    def generate_binary(self):
        """Generate binary configuration file"""
        # Create configuration header
        header = struct.pack('>I', 0x0F0300B7)  # Magic
        header += struct.pack('>I', 0x00000006)  # Version
        header += struct.pack('>I', len(self.config_data))  # Entry count
        header += struct.pack('>I', 0xE82CE086)  # Checksum placeholder

        # Build configuration data
        config_bytes = bytearray()

        for addr, value in self.config_data:
            # Each entry is 8 bytes: 4 bytes address, 4 bytes value
            config_bytes += struct.pack('>I', addr)
            config_bytes += struct.pack('>I', value)

        # Pad to align
        while len(config_bytes) % 16 != 0:
            config_bytes += b'\x00'

        return header + bytes(config_bytes)

    def build_configuration(self):
        """Build complete FRER configuration"""
        self.configure_general()
        self.configure_ports()
        self.configure_frer_replication()
        self.configure_forwarding_table()
        self.configure_sequence_recovery()

        return self.generate_binary()

def main():
    print("SJA1110 FRER Configuration Generator")
    print("=====================================")
    print("Configuration: P4 input -> P2A, P2B output (replicated)")
    print()

    # Create configuration
    config = SJA1110Config()
    binary_data = config.build_configuration()

    # Save to file
    output_file = "sja1110_p4_to_p2ab_frer.bin"
    with open(output_file, 'wb') as f:
        f.write(binary_data)

    print(f"Configuration generated: {output_file}")
    print(f"Size: {len(binary_data)} bytes")
    print()
    print("Configuration summary:")
    print("  - Input port: P4")
    print("  - Output ports: P2A, P2B (FRER replicated)")
    print("  - Stream ID: 1")
    print("  - R-TAG insertion: Enabled")
    print("  - Sequence generation: Enabled")
    print("  - Recovery window: 256 frames")

    # Generate human-readable config
    with open("sja1110_config.txt", 'w') as f:
        f.write("SJA1110 FRER Configuration\n")
        f.write("==========================\n\n")
        f.write("Register Configuration:\n")
        for addr, value in config.config_data:
            f.write(f"  0x{addr:08X} = 0x{value:08X}\n")

    print("\nHuman-readable configuration saved to: sja1110_config.txt")

if __name__ == "__main__":
    main()