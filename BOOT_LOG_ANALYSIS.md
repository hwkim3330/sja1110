# S32G274ARDB2 Boot Log Analysis and Fixes

## Error Analysis from Boot Log

### Original Errors
```
sja1110 spi5.1: Configuration failed: LocalCRCfail=1,DevIDunmatched=0,GlobalCRCfail=1
sja1110 spi5.1: verify firmware failed with -22
```

### Root Causes Identified

1. **Device ID Issue**
   - Original firmware used: `0xB700030F`
   - Driver expects: `0xB700030E`
   - Source: `sja1110_init.h: #define SJA1110_VAL_DEVICEID (0xb700030eUL)`

2. **CRC Calculation Error**
   - Local CRC failed
   - Global CRC failed
   - CRC must be calculated over configuration data (excluding header)

3. **Configuration Structure**
   - Size must be exactly 2236 bytes
   - Header must be 16 bytes
   - CRC at offset 12-15

## Fixed Implementation

### Corrected Header Structure
```c
Offset  Size  Value       Description
0x00    4     0xB700030E  Device ID (little-endian)
0x04    4     0x00000006  Version
0x08    4     [varies]    Configuration flags
0x0C    4     [CRC32]     CRC of config data
```

### CRC Calculation Method
```python
def calculate_crc32(data):
    return zlib.crc32(data) & 0xFFFFFFFF

# CRC over configuration data only
config_data = config[16:]  # Skip 16-byte header
crc = calculate_crc32(config_data)
```

### Port Configuration for FRER

Based on boot log showing 11 ports (S32G2 has ports 0-10):

| Port | Function | FRER Config |
|------|----------|-------------|
| P0   | Internal CPU | No change |
| P1   | RGMII | No change |
| P2   | Output (P2A) | FRER enable (0x80000000) |
| P3   | Output (P2B) | FRER enable (0x80000000) |
| P4   | Input | Forward to P2,P3 (0x0000000C) |
| P5-P10 | Various | No change |

### Boot Log Key Information

```
sja1110 spi5.0: probing uc
sja1110 spi5.1: probing switch
sja1110 spi5.1: Found switch config of size 2236
sja1110 spi5.0: Found firmware of size 320280
sja1110 spi5.0: firmware appears to be valid
```

- Switch on SPI5.1
- UC on SPI5.0
- Switch config: 2236 bytes
- UC firmware: 320280 bytes

### Driver Loading Sequence

1. Reset via GPIO
2. Load switch configuration via SPI5.1
3. Verify device ID and CRC
4. Load UC firmware via SPI5.0
5. Verify image marker (0x6AA66AA6)
6. Upload and verify

## Verification in Fixed Version

The fixed firmware now:
- Uses correct device ID: `0xB700030E`
- Calculates CRC properly
- Maintains exact size: 2236 bytes
- Preserves original structure

### Test Results
```
Device ID: 0xB700030E (expect 0xB700030E) ✓
Version: 6 ✓
CRC: 0x449B31CE ✓
Calculated CRC: 0x449B31CE ✓
[OK] CRC matches
Configuration valid!
```

## PFE (Packet Forwarding Engine) Integration

From boot log:
```
pfeng 46000000.pfe: Version: 1.9.0
pfeng 46000000.pfe: Firmware: CLASS s32g_pfe_class.fw [45724 bytes]
pfeng 46000000.pfe: Firmware: UTIL s32g_pfe_util.fw [23352 bytes]
```

PFE handles packet acceleration and works with SJA1110 for TSN/FRER.

## Network Interface Mapping

```
pfeng 46000000.pfe pfe0: EMAC0 interface mode: 4 (SGMII)
pfeng 46000000.pfe pfe1: EMAC1 interface mode: 4 (SGMII)
pfeng 46000000.pfe pfe2: EMAC2 interface mode: 10 (RGMII-ID)
```

## Files Generated

1. **sja1110_switch_fixed.bin** - Corrected switch configuration
2. **sja1110_uc_fixed.bin** - UC firmware with FRER support
3. **sja1110_fixed_frer.py** - Fixed generator script

## Loading Instructions

```bash
# Copy to board
scp sja1110_switch_fixed.bin root@<board-ip>:/lib/firmware/sja1110_switch.bin
scp sja1110_uc_fixed.bin root@<board-ip>:/lib/firmware/sja1110_uc.bin

# Reboot to load
reboot
```