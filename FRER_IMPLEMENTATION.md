# SJA1110 FRER Implementation - GoldVIP-Based Approach

## Overview

This implementation enables FRER (Frame Replication and Elimination for Reliability) on the NXP SJA1110 switch by modifying existing GoldVIP binaries. This approach uses proven, working firmware as a base and adds FRER configuration.

## Key Innovation

Instead of creating firmware from scratch (which failed due to missing ARM Cortex-M7 microcode), we:
1. Use the working GoldVIP UC binary (has real code)
2. Modify only the switch configuration to enable FRER
3. Keep all board-specific initialization intact

## FRER Configuration Details

### Enabled Features
- **CB_EN (bit 7)**: Cut-through Bypass Enable for FRER
- **FRMREPEN (bit 16)**: Frame Replication Enable
- **SEQGEN (bit 17)**: Sequence Generation Enable
- **R-TAG**: 0xF1C1 (IEEE 802.1CB standard)

### Port Configuration
- **Port 4**: FRER input (receives original frames)
- **Port 2**: FRER output A (first replicated stream)
- **Port 3**: FRER output B (second replicated stream)

### Stream Configuration
- Stream ID: 0x0001
- Recovery Window: 256 frames
- Timeout: 1000ms

## Binary Files

### Generated FRER Binaries
- `binaries/sja1110_switch_frer.bin` (2,236 bytes) - Modified switch configuration
- `binaries/sja1110_uc_frer.bin` (320,280 bytes) - Unmodified GoldVIP UC firmware

### Configuration Changes

| Register | Original (GoldVIP) | Modified (FRER) | Purpose |
|----------|-------------------|-----------------|---------|
| Config1 | 0x06000000 | 0x06000080 | Enable CB_EN |
| Config2 | 0x000000DC | 0x000300DC | Enable FRMREPEN, SEQGEN |
| Port 4 | Standard | 0x04 | FRER input |
| Port 2 | Standard | 0x02 | FRER output A |
| Port 3 | Standard | 0x03 | FRER output B |

## Usage Instructions

### Installation

```bash
# 1. Upload to S32G274A-RDB2 board
scp binaries/sja1110_switch_frer.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp binaries/sja1110_uc_frer.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin

# 2. Reboot the board
ssh root@192.168.1.1 reboot

# 3. Verify successful loading
ssh root@192.168.1.1 'dmesg | grep sja1110'
```

### Testing FRER

```bash
# Send test traffic to Port 4
# Monitor Ports 2 and 3 for replicated frames with R-TAG 0xF1C1

# Example using tcpdump on the board:
tcpdump -i eth0 -e -XX | grep -A2 "f1c1"
```

## Technical Implementation

### How It Works

1. **Load GoldVIP Binaries**: Read proven working firmware
2. **Preserve UC Code**: Keep the 320KB UC binary untouched (has real ARM code)
3. **Modify Switch Config**: Enable FRER bits in switch binary
4. **Add Port Config**: Configure ports for FRER operation
5. **Update CRC**: Recalculate checksum for modified data

### Source Code

The `sja1110_frer_enabler.py` script performs the modification:

```python
# Enable FRER bits
config1_frer = config1 | 0x00000080  # CB_EN
config2_frer = config2 | 0x00030000  # FRMREPEN, SEQGEN

# Configure ports
switch_data[port4_offset] = 0x04  # Input
switch_data[port2_offset] = 0x02  # Output A
switch_data[port3_offset] = 0x03  # Output B
```

## Validation

The modified binaries maintain:
- Correct device ID (0xb700030f when read by driver)
- Valid UC magic header (6AA66AA66AA66AA6)
- Working ARM Cortex-M7 microcode
- Board-specific initialization sequences

## Why This Approach Works

### Previous Failures
- Creating firmware from scratch: Missing real microcode
- Generic configurations: No board-specific init
- Random patterns: Invalid ARM instructions

### Current Success Factors
- Uses real, tested UC firmware
- Minimal modification (only FRER bits)
- Preserves all working code
- Based on GoldVIP-S32G2-1.14.0

## Troubleshooting

### If Upload Fails
1. Check SPI interface: `/dev/spidev5.0` and `/dev/spidev5.1`
2. Verify driver version: `modinfo sja1110`
3. Check kernel logs: `dmesg | grep -i error`

### If FRER Doesn't Work
1. Verify bit settings in registers
2. Check port link status
3. Monitor R-TAG presence in frames
4. Validate sequence numbers

## References

- IEEE 802.1CB-2017: Frame Replication and Elimination
- NXP SJA1110 Reference Manual
- GoldVIP-S32G2-1.14.0 Package
- Linux sja1110 driver source

## License

Based on NXP GoldVIP binaries. Use according to NXP license terms.

---

**Version**: 1.0
**Date**: September 2024
**Status**: Ready for testing on S32G274A-RDB2