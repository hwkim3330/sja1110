# S32G274A-RDB2 Board Support for SJA1110 FRER

## Overview

This document provides specific instructions for using SJA1110 FRER firmware on the NXP S32G274A-RDB2 automotive processor board.

## Board Specifications

- **Processor**: NXP S32G274A (ARM Cortex-A53 @ 1GHz)
- **Memory**: 4GB DDR4
- **Ethernet**: PFE (Packet Forwarding Engine) with 3 ports
- **SJA1110 Interface**: SPI5 (spi5.0 for UC, spi5.1 for switch)
- **Linux BSP**: Auto Linux BSP 44.0

## Known Issues and Fixes

### 1. Device ID Mismatch

**Problem:**
```
sja1110 spi5.1: Device id (0xb700030f) does not match that of the static config (0xe0300b7)
```

**Solution:** Fixed in `sja1110_switch_s32g.bin` with correct endianness.

### 2. Invalid UC Firmware Header

**Problem:**
```
sja1110 spi5.0: Invalid firmware header
```

**Solution:** Fixed in `sja1110_uc_s32g.bin` with proper magic header (6AA66AA66AA66AA6).

## Installation Steps

### 1. Connect to Board

```bash
# Via serial console
minicom -D /dev/ttyUSB0 -b 115200

# Or via SSH (if network is configured)
ssh root@192.168.1.1
```

### 2. Upload Fixed Firmware

From your host machine:

```bash
# Method 1: Using provided script
./upload_to_s32g.sh

# Method 2: Manual upload
scp sja1110_switch_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp sja1110_uc_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin
```

### 3. Verify Firmware Location

On the S32G274A-RDB2:

```bash
ls -la /lib/firmware/sja1110*
# Should show:
# -rw-r--r-- 1 root root   2236 Jan 22 10:30 sja1110_switch.bin
# -rw-r--r-- 1 root root 320280 Jan 22 10:30 sja1110_uc.bin
```

### 4. Reboot Board

```bash
sync
reboot
```

### 5. Verify Successful Loading

After reboot:

```bash
dmesg | grep sja1110

# Expected output:
# sja1110 spi5.0: probing uc
# sja1110 spi5.1: probing switch
# sja1110 spi5.1: [sja1110_init_hw] loaded fw 'sja1110_switch.bin'
# sja1110 spi5.1: Device id matches: 0xb700030f
# sja1110 spi5.0: [sja1110_init_hw] loaded fw 'sja1110_uc.bin'
# sja1110 spi5.0: Valid firmware header found
# sja1110 spi5.0: UC firmware uploaded successfully
# sja1110 spi5.1: Switch configuration complete
```

## Network Configuration

### Configure PFE Interfaces

```bash
# Bring up interfaces
ip link set pfe0 up
ip link set pfe1 up
ip link set pfe2 up

# Assign IP addresses
ip addr add 192.168.2.1/24 dev pfe0
ip addr add 192.168.3.1/24 dev pfe1
ip addr add 192.168.4.1/24 dev pfe2
```

### Test FRER Functionality

```bash
# Monitor replication
# Terminal 1:
tcpdump -i pfe0 -n

# Terminal 2:
tcpdump -i pfe1 -n

# Send test traffic to pfe2
ping -I pfe2 192.168.255.255

# Both pfe0 and pfe1 should show replicated frames
```

## Boot Log Analysis

### Successful Boot Indicators

1. **U-Boot Detection:**
```
SoC:   NXP S32G274A rev. 2.1
Model: NXP S32G274A-RDB2
DRAM:  4 GiB
```

2. **Linux Kernel:**
```
Linux version 6.6.85-rt53
Machine model: NXP S32G2 Reference Design Board 2
```

3. **PFE Initialization:**
```
pfeng 46000000.pfe: PFEng ethernet driver loading
pfeng 46000000.pfe: Version: 1.9.0
pfeng 46000000.pfe pfe0: registered
pfeng 46000000.pfe pfe1: registered
pfeng 46000000.pfe pfe2: registered
```

4. **SJA1110 Driver:**
```
sja1110: loading out-of-tree module taints kernel
sja1110 spi5.0: probing uc
sja1110 spi5.1: probing switch
```

## Troubleshooting

### Issue: Firmware Not Loading

Check SPI device presence:
```bash
ls /dev/spidev*
# Should show spidev5.0 and spidev5.1
```

### Issue: Network Interfaces Missing

Check PFE status:
```bash
dmesg | grep pfeng
ip link show | grep pfe
```

### Issue: FRER Not Working

Verify switch configuration:
```bash
# Check if SJA1110 is responding
devmem2 0x46000000  # PFE base address
```

## Performance Tuning

### CPU Affinity

```bash
# Bind PFE interrupts to specific CPU
echo 2 > /proc/irq/67/smp_affinity_list  # PFE BMU IRQ
```

### Network Optimization

```bash
# Increase ring buffer sizes
ethtool -G pfe0 rx 4096 tx 4096
ethtool -G pfe1 rx 4096 tx 4096
ethtool -G pfe2 rx 4096 tx 4096

# Enable hardware offload
ethtool -K pfe0 rx-checksumming on
ethtool -K pfe1 rx-checksumming on
ethtool -K pfe2 rx-checksumming on
```

## Technical Details

### Memory Map

- **PFE CBUS**: 0x46000000 (16MB)
- **SJA1110 Access**: Via SPI5
- **DDR**: 0x80000000 - 0x8FFFFFFFF (4GB)

### Device Tree Bindings

```dts
&spi5 {
    sja1110-uc@0 {
        compatible = "nxp,sja1110-uc";
        reg = <0>;
        spi-max-frequency = <25000000>;
    };

    sja1110-switch@1 {
        compatible = "nxp,sja1110-switch";
        reg = <1>;
        spi-max-frequency = <25000000>;
    };
};
```

## References

- [NXP S32G2 Reference Manual](https://www.nxp.com/docs/en/reference-manual/S32G2RM.pdf)
- [Auto Linux BSP Documentation](https://www.nxp.com/docs/en/user-guide/AUTOLBSPUG.pdf)
- [SJA1110 Linux Driver](https://github.com/nxp-archive/autoivnsw_sja1110_linux)

---

**Version**: 1.0.0
**Last Updated**: January 2025
**Tested on**: S32G274A-RDB2 with Auto Linux BSP 44.0