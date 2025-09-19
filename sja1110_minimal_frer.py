#!/usr/bin/env python3
"""
SJA1110 Minimal FRER Addition
Keep original working configuration, add minimal FRER changes
"""

import struct
import zlib

class SJA1110MinimalFRER:
    """
    Minimal approach: Keep original binary working, add only essential FRER bits
    """

    def __init__(self):
        self.original_path = r"C:\Users\parksik\Downloads\GoldVIP-S32G2-1.14.0 (1)\binaries\sja1110_switch.bin"

    def analyze_original_detailed(self):
        """Detailed analysis of original binary"""
        with open(self.original_path, 'rb') as f:
            data = f.read()

        print("Detailed Original Binary Analysis")
        print("=" * 50)
        print(f"Size: {len(data)} bytes")

        # Header
        device_id = struct.unpack('<I', data[0:4])[0]
        field1 = struct.unpack('<I', data[4:8])[0]
        field2 = struct.unpack('<I', data[8:12])[0]
        field3 = struct.unpack('<I', data[12:16])[0]

        print(f"Device ID: 0x{device_id:08X}")
        print(f"Field 1: 0x{field1:08X}")
        print(f"Field 2: 0x{field2:08X}")
        print(f"Field 3: 0x{field3:08X}")

        # Check if field3 might be CRC
        # Calculate CRC of data[16:] to see if it matches field3
        config_data = data[16:]
        calc_crc = zlib.crc32(config_data) & 0xFFFFFFFF

        print(f"Config data size: {len(config_data)} bytes")
        print(f"Calculated CRC: 0x{calc_crc:08X}")

        if calc_crc == field3:
            print("[OK] Field 3 is valid CRC!")
            crc_method = "data[16:]"
        else:
            # Try other CRC methods
            calc_crc2 = zlib.crc32(data[12:]) & 0xFFFFFFFF
            calc_crc3 = zlib.crc32(data[4:12]) & 0xFFFFFFFF

            print(f"CRC method 2: 0x{calc_crc2:08X}")
            print(f"CRC method 3: 0x{calc_crc3:08X}")

            if calc_crc2 == field3:
                print("[OK] Field 3 is CRC of data[12:]!")
                crc_method = "data[12:]"
            elif calc_crc3 == field3:
                print("[OK] Field 3 is CRC of data[4:12]!")
                crc_method = "data[4:12]"
            else:
                print("[WARNING] No matching CRC method found")
                crc_method = "unknown"

        # Look for port configuration patterns
        print("\nPort Configuration Analysis:")
        port_configs = []

        for offset in range(16, len(data), 8):
            if offset + 8 <= len(data):
                cmd = struct.unpack('<I', data[offset:offset+4])[0]
                val = struct.unpack('<I', data[offset+4:offset+8])[0]

                if cmd == 0xFFFFEC00:  # Common port config command
                    port = (val >> 1) & 0xFF  # Try different port extraction
                    port_configs.append((offset, port, val))

        if port_configs:
            print(f"Found {len(port_configs)} port configurations:")
            for offset, port, val in port_configs[:5]:
                print(f"  0x{offset:04X}: Port {port}, val=0x{val:08X}")

        return data, crc_method

    def create_conservative_frer(self):
        """Create FRER config with minimal changes"""
        data, crc_method = self.analyze_original_detailed()

        print("\nCreating Conservative FRER Configuration...")

        # Start with exact original
        config = bytearray(data)

        # Make minimal changes for FRER
        modified = False

        # Only modify if we found clear port patterns
        for offset in range(16, len(config), 8):
            if offset + 8 <= len(config):
                cmd = struct.unpack('<I', config[offset:offset+4])[0]
                val = struct.unpack('<I', config[offset+4:offset+8])[0]

                if cmd == 0xFFFFEC00:
                    # Check if this might be port 2, 3, or 4
                    port_indicator = val & 0xFF

                    # Very conservative modifications
                    if port_indicator == 0x04:  # Might be port 2 (P2A)
                        print(f"  Modifying P2A at 0x{offset:04X}")
                        # Set bit 31 for FRER enable
                        new_val = val | 0x80000000
                        config[offset+4:offset+8] = struct.pack('<I', new_val)
                        modified = True

                    elif port_indicator == 0x06:  # Might be port 3 (P2B)
                        print(f"  Modifying P2B at 0x{offset:04X}")
                        # Set bit 31 for FRER enable
                        new_val = val | 0x80000000
                        config[offset+4:offset+8] = struct.pack('<I', new_val)
                        modified = True

        if not modified:
            print("  No clear port patterns found, keeping original")
            return data

        # Recalculate CRC using discovered method
        if crc_method == "data[16:]":
            new_crc = zlib.crc32(config[16:]) & 0xFFFFFFFF
            config[12:16] = struct.pack('<I', new_crc)
        elif crc_method == "data[12:]":
            new_crc = zlib.crc32(config[12:]) & 0xFFFFFFFF
            # CRC might be stored elsewhere
            pass

        print(f"  Modified {2 if modified else 0} port configurations")
        return bytes(config)

    def create_original_plus_frer_table(self):
        """Keep original + add FRER table at end"""
        with open(self.original_path, 'rb') as f:
            original = f.read()

        print("\nCreating Original + FRER Table...")

        # Keep original completely unchanged
        config = bytearray(original)

        # Find a safe place to add FRER configuration
        # Look for padding area
        padding_start = None
        for i in range(len(config) - 16):
            if config[i:i+16] == b'\x00' * 16:
                padding_start = i
                break

        if padding_start:
            print(f"  Found padding at 0x{padding_start:04X}")

            # Add FRER configuration in padding area
            frer_config = [
                0x46524552,  # "FRER" marker
                0x00000001,  # Stream ID 1
                0x00000010,  # P4 input (bit 4)
                0x0000000C,  # P2A|P2B output (bits 2,3)
                0xF1CD0100,  # R-TAG EtherType + window
            ]

            offset = padding_start
            for val in frer_config:
                if offset + 4 <= len(config):
                    config[offset:offset+4] = struct.pack('<I', val)
                    offset += 4

        # Don't modify CRC - keep original valid
        return bytes(config)

    def create_backup_methods(self):
        """Try multiple backup methods"""
        methods = []

        # Method 1: Conservative
        try:
            config1 = self.create_conservative_frer()
            methods.append(("conservative", config1))
        except Exception as e:
            print(f"Conservative method failed: {e}")

        # Method 2: Original + FRER table
        try:
            config2 = self.create_original_plus_frer_table()
            methods.append(("original_plus", config2))
        except Exception as e:
            print(f"Original plus method failed: {e}")

        # Method 3: Exact original (fallback)
        with open(self.original_path, 'rb') as f:
            original = f.read()
        methods.append(("exact_original", original))

        return methods


def main():
    print("SJA1110 Minimal FRER Implementation")
    print("=" * 50)
    print("Strategy: Minimal changes to working configuration")
    print()

    generator = SJA1110MinimalFRER()

    # Try multiple methods
    methods = generator.create_backup_methods()

    print(f"\nGenerated {len(methods)} configuration variants:")

    for i, (name, config) in enumerate(methods):
        filename = f"sja1110_switch_{name}.bin"
        with open(filename, 'wb') as f:
            f.write(config)

        print(f"  {i+1}. {filename} ({len(config)} bytes)")

        # Quick verification
        device_id = struct.unpack('<I', config[0:4])[0]
        if device_id == 0xB700030F:
            print(f"     Device ID: OK (0x{device_id:08X})")
        else:
            print(f"     Device ID: ERROR (0x{device_id:08X})")

    print("\nRecommended testing order:")
    print("1. Try exact_original first (should work)")
    print("2. Try conservative (minimal FRER changes)")
    print("3. Try original_plus (FRER table added)")
    print("\nCopy one at a time to board and check boot log")

if __name__ == "__main__":
    main()