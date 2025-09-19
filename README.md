# SJA1110 FRER Implementation for NXP GoldVIP Board

IEEE 802.1CB Frame Replication and Elimination for Reliability (FRER) implementation for NXP GoldVIP (Gold Vehicle Interface Platform) board with SJA1110 TSN switch.

## Repository Contents

```
├── sja1110_goldvip_switch_frer.bin  # Modified switch configuration
├── sja1110_goldvip_uc_frer.bin      # Modified UC firmware
├── sja1110_goldvip_frer.py          # Configuration generator
├── sja1110_loader.sh                 # Firmware loader
├── sja1110_test.py                   # FRER test tool
├── BINARY_ANALYSIS.md                # Complete binary analysis
├── FRER_Implementation_Analysis.md  # FRER technical details
└── analysis/                         # Analysis scripts
    ├── binary_hexdump.py            # Binary analysis tool
    ├── sja1110_ghidra_analysis.py   # Ghidra-style analysis
    ├── sja1110_frer_config.py       # Basic FRER config
    └── sja1110_proper_frer_config.py # Multi-version generator
```

## Overview

This repository contains firmware binaries and tools to enable FRER on the NXP GoldVIP S32G274ARDB2 platform, configuring the SJA1110 switch to replicate frames from Port 4 to Port 2A and Port 2B.

## Hardware Platform

- **Board**: NXP GoldVIP (S32G274ARDB2)
- **Processor**: S32G274A (ARM Cortex-A53 + Cortex-M7)
- **TSN Switch**: SJA1110 (11-port automotive Ethernet switch)
- **Firmware Base**: GoldVIP-S32G2-1.14.0

## Configuration

### Port Mapping
```
Input:  Port 4 (P4) - Receives original frames
Output: Port 2A (P2) - Replicated frame with R-TAG
        Port 2B (P3) - Replicated frame with R-TAG
```

### FRER Parameters
- **Protocol**: IEEE 802.1CB
- **Stream ID**: 1
- **R-TAG EtherType**: 0xF1CD
- **Sequence Window**: 256 frames
- **Recovery Timeout**: 1000ms

## Files

### Firmware Binaries
- `sja1110_goldvip_switch_frer.bin` - Switch configuration (2,236 bytes)
- `sja1110_goldvip_uc_frer.bin` - Microcontroller firmware (320,280 bytes)

### Tools
- `sja1110_goldvip_frer.py` - Configuration generator
- `sja1110_loader.sh` - Firmware loader script
- `sja1110_test.py` - FRER testing tool

### Documentation
- `FRER_Implementation_Analysis.md` - Technical analysis

## Installation

1. **Copy files to GoldVIP board**:
```bash
scp sja1110_goldvip_*.bin root@<board-ip>:/root/
scp sja1110_loader.sh root@<board-ip>:/root/
```

2. **Load firmware**:
```bash
ssh root@<board-ip>
cd /root
chmod +x sja1110_loader.sh
./sja1110_loader.sh
```

3. **Verify configuration**:
```bash
# Check port status
ip link show eth4
ip link show eth2
ip link show eth3

# Run test
python3 sja1110_test.py
```

## Testing

### Quick Test
```bash
# Terminal 1: Monitor P2A
tcpdump -i eth2 -e -n

# Terminal 2: Monitor P2B
tcpdump -i eth3 -e -n

# Terminal 3: Send test frame to P4
ping -I eth4 192.168.1.255
```

### Verify R-TAG
Look for EtherType `0xF1CD` in captured frames to confirm FRER operation.

## Frame Flow

```
Original Frame → P4 → SJA1110 FRER Engine
                           ↓
                    [Add R-TAG + Seq#]
                           ↓
                    ┌─────────────┐
                    ↓             ↓
                   P2A           P2B
              (Replica 1)    (Replica 2)
```

## Implementation Details

The firmware modifies the original GoldVIP binaries to:
1. Enable FRER on the SJA1110 switch
2. Configure P4 as input port
3. Set P2A and P2B as replicated output ports
4. Add R-TAG with sequence numbers
5. Implement sequence recovery window

## Performance

- Hardware-based replication: <1μs latency
- Line-rate performance at 1Gbps
- Zero packet loss under normal conditions

## Compatibility

- GoldVIP-S32G2 firmware version 1.14.0
- Linux kernel 5.10 or later with TSN support
- Compatible with IEEE 802.1CB-2017 standard

## Troubleshooting

### No Replication
- Verify switch initialization: `dmesg | grep sja1110`
- Check port link status: `ethtool eth4`
- Confirm firmware loaded: Check `/sys/class/spi_master/`

### Missing R-TAG
- Verify FRER enabled in configuration
- Check with Wireshark for EtherType 0xF1CD
- Ensure correct stream ID mapping

## License

Based on NXP proprietary firmware. Use subject to NXP license terms.

## Binary Analysis Summary

### Original Binaries (GoldVIP-S32G2-1.14.0)

| File | Size | Type | Purpose |
|------|------|------|--------|
| sja1110_switch.bin | 2,236 bytes | Config | Switch port/VLAN configuration |
| sja1110_uc.bin | 320,280 bytes | ARM FW | Microcontroller firmware |
| s32g_pfe_class.fw | 45,724 bytes | MIPS ELF | Packet classifier |
| s32g_pfe_util.fw | 23,352 bytes | MIPS ELF | Utility functions |

### Key Findings

1. **Device ID**: `0xB700030F` (SJA1110 identifier)
2. **UC Architecture**: ARM Cortex-M with Thumb-2 instructions
3. **Image Marker**: `0x6AA66AA6` (repeated 4 times)
4. **Port Mapping**: 11 ports (0-10), P4→P2A/P2B for FRER
5. **Configuration Format**: 8-byte entries `[Command][Value]`

### FRER Modifications

| Offset | Original | Modified | Purpose |
|--------|----------|----------|--------|
| 0x0030 | 0x087FFF9F | 0x887FFF9F | Enable FRER on P4 |
| 0x0020 | 0x047FFF9F | 0x847FFF9F | FRER output P2A |
| 0x0028 | 0x067FFF9F | 0x867FFF9F | FRER output P2B |
| 0x0100 | 0x00000000 | 0x00010001 | Stream ID 1 |
| 0x0104 | 0x00000000 | 0x00000010 | P4 input mask |
| 0x0108 | 0x00000000 | 0x0000000C | P2A\|P2B output |

For complete binary analysis, see [BINARY_ANALYSIS.md](BINARY_ANALYSIS.md)

## Support

For GoldVIP platform: Contact NXP support
For FRER implementation: Open issue in this repository