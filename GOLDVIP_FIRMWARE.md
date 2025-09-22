# GoldVIP-Compatible Firmware for S32G274A-RDB2

## ⚠️ EXPERIMENTAL - Testing Required

These firmware files are based on GoldVIP binary structure analysis but **have not been tested on actual hardware**.

## Problem Analysis

From the boot log, we identified two critical issues:

### 1. Device ID Mismatch
```
sja1110 spi5.1: Device id (0xb700030f) does not match that of the static config (0xf0300b7)
```
- Board reads: `0xb700030f`
- Firmware had: `0xf0300b7` (wrong byte order)
- Fixed to: `0x0f0300b7` (correct little-endian)

### 2. UC Upload Error
```
sja1110 spi5.0: Upload error detected in status message 8 (status=0x33,err=0x57)
```
- Missing proper magic header
- Invalid firmware structure

## GoldVIP Firmware Structure

Based on analysis of working GoldVIP binaries:

### Switch Firmware (2,236 bytes)
```
Offset  Size  Description
------  ----  -----------
0x00    4     Device ID (0x0f0300b7)
0x04    4     CB_EN flags (0x00000086)
0x08    4     FRMREPEN config (0xDD100000)
0x0C    4     CRC/Features (0x86E02CE8)
0x10    48    Port configurations
0x40    var   L2 forwarding tables
...           FRER configuration
```

### UC Firmware (320,280 bytes)
```
Offset  Size  Description
------  ----  -----------
0x00    8     Magic (6AA66AA66AA66AA6)
0x08    4     Entry point (0x00000024)
0x0C    4     Size field (0x12120000)
0x10    4     Version (0x00001200)
0x14    4     Checksum (0xF8E20400)
0x18    64    ARM Cortex-M vector table
...           Firmware code
```

## Files Included

### Firmware Files
- `sja1110_switch_goldvip.bin` - Switch configuration with correct device ID
- `sja1110_uc_goldvip.bin` - UC firmware with valid header

### Tools
- `sja1110_goldvip_fix.py` - Generator script
- `upload_goldvip.sh` - Upload script for S32G board

## Installation

### Method 1: Automatic Upload
```bash
chmod +x upload_goldvip.sh
./upload_goldvip.sh
```

### Method 2: Manual Upload
```bash
# Backup existing firmware
ssh root@192.168.1.1 "cp /lib/firmware/sja1110_*.bin /root/"

# Upload new firmware
scp sja1110_switch_goldvip.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp sja1110_uc_goldvip.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin

# Reboot
ssh root@192.168.1.1 "sync && reboot"
```

## Verification

After reboot, check the kernel log:

```bash
ssh root@192.168.1.1 'dmesg | grep sja1110'
```

### Expected Success Messages:
```
sja1110 spi5.0: probing uc
sja1110 spi5.1: probing switch
sja1110 spi5.1: [sja1110_init_hw] loaded fw 'sja1110_switch.bin'
sja1110 spi5.1: Device id (0xb700030f) matches configuration
sja1110 spi5.0: [sja1110_init_hw] loaded fw 'sja1110_uc.bin'
sja1110 spi5.0: [sja1110_pre_uc_upload] firmware appears to be valid
sja1110 spi5.0: Uploading firmware... [SUCCESS]
```

### If It Still Fails:

1. **Capture detailed logs:**
```bash
ssh root@192.168.1.1 'dmesg | grep -A5 -B5 sja1110 > /tmp/sja1110.log'
scp root@192.168.1.1:/tmp/sja1110.log .
```

2. **Check SPI communication:**
```bash
ssh root@192.168.1.1 'ls -la /dev/spidev5.*'
```

3. **Verify firmware files:**
```bash
ssh root@192.168.1.1 'hexdump -C /lib/firmware/sja1110_switch.bin | head -20'
```

## Technical Notes

### Why This Might Work:
1. Device ID now matches exactly what the driver expects
2. UC firmware has proper magic header from GoldVIP
3. All byte orders are corrected
4. FRER configuration included

### Why It Might Not Work:
1. UC firmware code section may need actual GoldVIP code
2. Configuration tables might need board-specific values
3. CRC/checksum values might be validated
4. Driver version differences

## Need Help?

If these firmware files don't work:

1. **Provide full boot log:**
   - Serial console output from U-Boot to Linux login
   - Complete dmesg output

2. **Check if you have working GoldVIP binaries:**
   - Location: `C:\Users\parksik\Downloads\GoldVIP-S32G2-1.14.0 (1)\binaries`
   - We can extract and analyze the working firmware

3. **Driver version:**
```bash
modinfo sja1110
```

## Disclaimer

These firmware files are experimental and based on reverse engineering. Use at your own risk. Always backup original firmware before testing.

---

**Version**: 0.1-experimental
**Status**: UNTESTED - Requires validation on actual hardware
**Based on**: GoldVIP-S32G2-1.14.0 structure analysis