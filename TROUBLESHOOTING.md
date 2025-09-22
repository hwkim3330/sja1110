# 🔧 SJA1110 FRER Troubleshooting Guide

## Current Status: CRC Investigation

### Issue Description

Despite extensive reverse engineering of the NXP SJA1110 binary format and implementing the exact CRC algorithm from the [sja1105-tool](https://github.com/nxp-archive/openil_sja1105-tool) repository, we are still encountering CRC validation failures:

```
sja1110 spi5.1: Configuration failed: LocalCRCfail=1,DevIDunmatched=0,GlobalCRCfail=1
sja1110 spi5.1: verify firmware failed with -22
```

### Investigation Summary

#### ✅ What We've Verified

1. **Correct Device ID**: `0xb700030f` (little-endian) ✓
2. **Proper Binary Structure**: 16-byte header + 220-byte config ✓
3. **NXP CRC Algorithm**: Implemented exact `ether_crc32_le` from sja1105-tool ✓
4. **Multiple CRC Methods Tested**: 7 different calculation approaches ✓
5. **Exhaustive Range Search**: Tested all possible data ranges ✓

#### ❌ What's Not Working

- **CRC Validation**: No method produces matching CRC `0x86e02ce8`
- **Hardware Acceptance**: Even minimal modifications cause CRC failure

### Technical Analysis

#### Original GoldVIP Binary Analysis
```
Device ID: 0xb700030f
Config1:   0x06000000
Config2:   0x000000dc (220 bytes)
CRC:       0x86e02ce8
```

#### CRC Methods Tested

| Method | Calculated CRC | Match |
|--------|----------------|-------|
| NXP ether_crc32_le (config only) | `0x345876f3` | ❌ |
| Standard CRC32 | `0x345876f3` | ❌ |
| Header + Config (CRC=0) | `0x55ec54e5` | ❌ |
| Header(12) + Config | `0xdce2975c` | ❌ |
| Inverted CRC | `0xcba7890c` | ❌ |
| No final bit reverse | `0xcf6e1a2c` | ❌ |

#### Exhaustive Search Results
- **Tested**: All data ranges 0-236 bytes with 4 different CRC algorithms
- **Result**: No matching CRC found
- **Conclusion**: Either using wrong algorithm or wrong data range

### Current Hypothesis

1. **Hardware Pre-processing**: The hardware might apply transformations before CRC calculation
2. **Different Algorithm**: NXP might use a proprietary CRC variant not documented
3. **Multiple CRCs**: There might be separate local and global CRC calculations
4. **Firmware Signing**: The CRC might be part of a cryptographic signature
5. **Version Mismatch**: Our GoldVIP binary might not match the expected hardware version

### Testing Strategy

#### Phase 1: Baseline Verification
Test if the original GoldVIP binary actually works:

```bash
# Upload exact GoldVIP binary
scp binaries/sja1110_switch_frer.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp binaries/sja1110_uc_frer.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin
ssh root@192.168.1.1 reboot

# Check boot log
ssh root@192.168.1.1 'dmesg | grep sja1110'
```

**Expected Results**:
- ✅ `LocalCRCfail=0, GlobalCRCfail=0` - GoldVIP works
- ❌ `LocalCRCfail=1, GlobalCRCfail=1` - Even GoldVIP fails (hardware/version issue)

#### Phase 2: Minimal Modifications
If GoldVIP works, test minimal changes:

1. **CB_EN Only**: Enable only the CB_EN bit, keep original CRC
2. **Ports Only**: Modify only port configurations, keep original config1/CRC
3. **Progressive**: Add one change at a time

#### Phase 3: Alternative Approaches
If CRC issues persist:

1. **Hardware Analysis**: Oscilloscope/logic analyzer on SPI bus
2. **Driver Modification**: Bypass CRC check in Linux driver
3. **NXP Support**: Contact NXP for official FRER configuration
4. **Alternative Tools**: Use NXP's official configuration tools

### Files for Testing

| File | Description | Modifications |
|------|-------------|---------------|
| `sja1110_switch_frer.bin` | Original GoldVIP | None (baseline test) |
| `sja1110_uc_frer.bin` | UC firmware | None (unmodified) |

### Error Interpretation

#### LocalCRCfail=1
- **Meaning**: Switch configuration CRC validation failed
- **Scope**: Local to switch configuration data
- **Data**: 16-byte header + 220-byte config

#### GlobalCRCfail=1
- **Meaning**: Global firmware CRC validation failed
- **Scope**: Entire firmware package
- **Possible**: Cross-validation between switch and UC firmware

#### DevIDunmatched=0
- **Meaning**: Device ID validation passed ✓
- **Confirms**: We have the correct device ID format

### Next Steps

1. **Immediate**: Test original GoldVIP binary to establish baseline
2. **Short-term**: If GoldVIP works, try minimal modifications
3. **Medium-term**: Investigate alternative FRER enablement methods
4. **Long-term**: Contact NXP or analyze hardware directly

### Alternative FRER Approaches

If CRC issues cannot be resolved:

1. **Runtime Configuration**: Enable FRER via register writes after boot
2. **Driver Patches**: Modify Linux driver to enable FRER features
3. **U-Boot Configuration**: Enable FRER during early boot process
4. **JTAG Programming**: Direct hardware register configuration

### Tools Used

- **sja1105-tool**: NXP's reference CRC implementation
- **Custom analyzers**: Binary structure analysis
- **Exhaustive search**: All possible CRC combinations
- **Hardware logs**: S32G274A-RDB2 boot output

### References

- [NXP SJA1105 Tool](https://github.com/nxp-archive/openil_sja1105-tool)
- [SJA1110 Linux Driver](https://github.com/nxp-archive/autoivnsw_sja1110_linux)
- [IEEE 802.1CB-2017](https://standards.ieee.org/ieee/802.1CB/7032/) - FRER Standard

---

**Status**: Under Investigation
**Priority**: High - Blocking FRER implementation
**Last Updated**: September 2024

For assistance, please review the [Binary Analysis Report](docs/BINARY_ANALYSIS.md) and check the latest boot logs.