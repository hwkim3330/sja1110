#!/usr/bin/env python3
"""
Binary Hexdump Analysis Tool
Analyzes SJA1110 binaries and generates detailed hexdump reports
"""

import struct
import sys
import os

def hexdump_analysis(filepath, output_lines=100):
    """Generate detailed hexdump with analysis"""

    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"File: {os.path.basename(filepath)}")
    print(f"Size: {len(data)} bytes (0x{len(data):04X})")
    print("=" * 70)
    print()

    # Hexdump with interpretation
    print("Offset    00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  ASCII")
    print("-" * 70)

    for i in range(0, min(len(data), output_lines * 16), 16):
        # Hex bytes
        hex_bytes = ' '.join(f'{b:02X}' for b in data[i:i+8])
        if i+8 < len(data):
            hex_bytes += '  ' + ' '.join(f'{b:02X}' for b in data[i+8:i+16])
        else:
            hex_bytes += '  ' + ' '.join(f'{b:02X}' for b in data[i+8:])

        # ASCII representation
        ascii_str = ''
        for b in data[i:i+16]:
            if 32 <= b < 127:
                ascii_str += chr(b)
            else:
                ascii_str += '.'

        # Special markers for important offsets
        marker = ''
        if i == 0:
            marker = ' <- Header'
        elif i == 0x10:
            marker = ' <- Config Start'
        elif i == 0x100:
            marker = ' <- FRER Config'
        elif i == 0x1000:
            marker = ' <- Main Code'

        print(f"{i:08X}  {hex_bytes:<48}  {ascii_str:<16}{marker}")

    print()
    print("Analysis Summary:")
    print("-" * 40)

    # Detect patterns
    if len(data) >= 4:
        magic = struct.unpack('<I', data[0:4])[0]
        print(f"Magic/Device ID: 0x{magic:08X}")

        if magic == 0xB700030F:
            print("  -> Valid SJA1110 Device ID")
        elif (data[0:8] == bytes([0x6A, 0xA6] * 4)):
            print("  -> Valid UC Firmware Image Marker")

    # Check for specific patterns
    patterns = {
        b'\xF1\xCD': 'R-TAG EtherType',
        b'\x00\xEC\xFF\xFF': 'Port Config Command',
        b'\x9F\xFF\x7F': 'Port Settings Pattern',
        b'\xFF' * 16: 'Unprogrammed Flash',
        b'\x00' * 16: 'Zero Padding'
    }

    print("\nPattern Detection:")
    for pattern, description in patterns.items():
        count = data.count(pattern)
        if count > 0:
            print(f"  {description}: {count} occurrences")

    # Configuration entry analysis for switch binary
    if 'switch' in filepath.lower():
        print("\nSwitch Configuration Entries:")
        entries = []
        for i in range(0x10, min(len(data), 0x200), 8):
            if i+8 <= len(data):
                cmd = struct.unpack('<I', data[i:i+4])[0]
                val = struct.unpack('<I', data[i+4:i+8])[0]
                if cmd == 0xFFFFEC00:
                    port = (val >> 24) & 0xFF
                    entries.append((i, cmd, val, port))

        for offset, cmd, val, port in entries[:10]:
            print(f"  0x{offset:04X}: Port {port//2} config (0x{val:08X})")

    # UC firmware analysis
    if 'uc' in filepath.lower():
        print("\nUC Firmware Structure:")
        if len(data) >= 0x20:
            entry_point = struct.unpack('<I', data[0x08:0x0C])[0]
            stack_ptr = struct.unpack('<I', data[0x18:0x1C])[0]
            reset_handler = struct.unpack('<I', data[0x1C:0x20])[0]

            print(f"  Entry Point: 0x{entry_point:08X}")
            print(f"  Stack Pointer: 0x{stack_ptr:08X}")
            print(f"  Reset Handler: 0x{reset_handler:08X}")

def compare_binaries(file1, file2):
    """Compare two binary files and show differences"""

    with open(file1, 'rb') as f:
        data1 = f.read()
    with open(file2, 'rb') as f:
        data2 = f.read()

    print("Binary Comparison")
    print("=" * 70)
    print(f"File 1: {os.path.basename(file1)} ({len(data1)} bytes)")
    print(f"File 2: {os.path.basename(file2)} ({len(data2)} bytes)")
    print()

    if len(data1) != len(data2):
        print(f"Warning: File sizes differ by {abs(len(data1) - len(data2))} bytes")
        print()

    # Find differences
    differences = []
    min_len = min(len(data1), len(data2))

    for i in range(min_len):
        if data1[i] != data2[i]:
            differences.append(i)

    print(f"Found {len(differences)} byte differences")

    if differences:
        print("\nFirst 20 differences:")
        print("Offset    File1  File2  Description")
        print("-" * 40)

        for offset in differences[:20]:
            desc = ""
            if offset < 0x10:
                desc = "Header"
            elif offset < 0x100:
                desc = "Port Config"
            elif offset < 0x1000:
                desc = "FRER Config"
            else:
                desc = "Firmware Code"

            print(f"0x{offset:06X}  0x{data1[offset]:02X}   0x{data2[offset]:02X}   {desc}")

def extract_config_table(filepath):
    """Extract configuration table from switch binary"""

    with open(filepath, 'rb') as f:
        data = f.read()

    print("Configuration Table Extraction")
    print("=" * 70)
    print()

    # Parse configuration entries
    entries = []
    offset = 0x10  # Start after header

    while offset < len(data) - 8:
        cmd = struct.unpack('<I', data[offset:offset+4])[0]
        val = struct.unpack('<I', data[offset+4:offset+8])[0]

        # Check for valid command patterns
        if cmd in [0xFFFFEC00, 0x00000000, 0x80010000]:
            entries.append({
                'offset': offset,
                'command': cmd,
                'value': val,
                'type': 'port' if cmd == 0xFFFFEC00 else 'control'
            })

        offset += 8

        # Stop at padding
        if data[offset:offset+16] == b'\x00' * 16:
            break

    # Display entries
    print(f"Found {len(entries)} configuration entries")
    print()
    print("Offset    Command     Value       Type        Interpretation")
    print("-" * 70)

    for entry in entries[:30]:
        interp = ""
        if entry['type'] == 'port':
            port_num = ((entry['value'] >> 24) & 0xFF) // 2
            interp = f"Port {port_num} configuration"
        elif entry['command'] == 0x80010000:
            interp = "FRER/Stream configuration"

        print(f"0x{entry['offset']:04X}  0x{entry['command']:08X}  0x{entry['value']:08X}  {entry['type']:<10}  {interp}")

    return entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='SJA1110 Binary Analysis Tool')
    parser.add_argument('command', choices=['hexdump', 'compare', 'extract'],
                       help='Analysis command to run')
    parser.add_argument('file1', help='First binary file')
    parser.add_argument('file2', nargs='?', help='Second file for comparison')
    parser.add_argument('-n', '--lines', type=int, default=100,
                       help='Number of lines for hexdump')

    args = parser.parse_args()

    if args.command == 'hexdump':
        hexdump_analysis(args.file1, args.lines)
    elif args.command == 'compare':
        if not args.file2:
            print("Error: Compare requires two files")
            sys.exit(1)
        compare_binaries(args.file1, args.file2)
    elif args.command == 'extract':
        extract_config_table(args.file1)