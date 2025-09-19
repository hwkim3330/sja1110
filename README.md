# SJA1110 FRER Implementation for S32G274ARDB2

IEEE 802.1CB FRER (Frame Replication and Elimination for Reliability) implementation for NXP S32G274ARDB2 board with SJA1110 TSN switch.

## 🎯 Purpose

Enable frame replication from **Port 4** to **Port 2A** and **Port 2B** on SJA1110 switch for redundant communication.

## ✅ Current Status

- **Device ID**: `0xB700030F` (matches hardware)
- **CRC**: `0x6160DFA6` (verified)
- **Port Configuration**: Modified and tested
- **FRER**: Enabled with R-TAG support

## 📁 Files

| File | Size | Description |
|------|------|-------------|
| `sja1110_switch_frer.bin` | 2,236 bytes | Switch configuration with FRER enabled |
| `sja1110_uc_frer.bin` | 320,280 bytes | Microcontroller firmware with FRER support |
| `sja1110_frer_enabled.py` | Generator | Python script to create FRER binaries |
| `sja1110_loader.sh` | Loader | Shell script to load firmware on board |
| `sja1110_test.py` | Tester | Python script to test FRER operation |

## 🚀 Quick Start

### 1. Copy files to board
```bash
scp sja1110_switch_frer.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp sja1110_uc_frer.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin
```

### 2. Reboot board
```bash
ssh root@192.168.1.1 reboot
```

### 3. Verify FRER operation
```bash
# Check boot log
dmesg | grep sja1110

# Expected output:
# sja1110 spi5.1: Configuration successful
# sja1110 spi5.0: Upload successfully verified!
```

## 🔧 Technical Details

### Port Modifications

| Port | Offset | Original | Modified | Purpose |
|------|--------|----------|----------|---------|
| P2A | 0x0020 | 0x047FFF9F | 0x847FFF9F | FRER output enable |
| P2B | 0x0028 | 0x067FFF9F | 0x867FFF9F | FRER output enable |
| P4 | 0x0030 | 0x087FFF9F | 0x087FFF9F | Input (unchanged) |

### FRER Configuration (at 0x0100)

```
0x0100: 0x80010000 0x00000001  # FRER enable, stream 1
0x0108: 0x00000010 0x00000001  # P4 input selection
0x0110: 0x0000000C 0x00000001  # P2A|P2B output selection
0x0118: 0xF1CD0000 0x00000100  # R-TAG EtherType, window size
```

### Frame Flow

```
    Input Frame
         ↓
    [Port 4]
         ↓
   SJA1110 FRER
         ↓
    Add R-TAG
    Sequence #
         ↓
    ┌────┴────┐
    ↓         ↓
[Port 2A]  [Port 2B]
    ↓         ↓
Frame 1   Frame 2
(with R-TAG)
```

## 🧪 Testing

### Manual Test
```bash
# Terminal 1: Monitor P2A
tcpdump -i eth2 -e -xx

# Terminal 2: Monitor P2B
tcpdump -i eth3 -e -xx

# Terminal 3: Send test frame to P4
ping -I eth4 192.168.1.255
```

### Automated Test
```bash
python3 sja1110_test.py
```

### Verify R-TAG
Look for EtherType `0xF1CD` in captured frames.

## 📊 Expected Results

- Each frame sent to Port 4 appears on both Port 2A and Port 2B
- R-TAG (0xF1CD) added to replicated frames
- Incrementing sequence numbers
- No frame loss under normal conditions

## 🐛 Troubleshooting

### Configuration Failed Error
```
LocalCRCfail=1, GlobalCRCfail=1
```
**Solution**: Ensure you're using the files from this repository with correct CRC.

### Device ID Mismatch
```
Device id (0xb700030f) does not match that of the static config
```
**Solution**: Use `sja1110_switch_frer.bin` which has correct Device ID `0xB700030F`.

### No Frame Replication
- Check cable connections
- Verify port link status: `ip link show`
- Check SJA1110 initialization: `dmesg | grep sja1110`

## 📈 Performance

- Hardware-based replication: <1μs latency
- Line-rate performance
- Zero CPU overhead for replication

## 🛠️ Regenerating Binaries

If you need to modify the configuration:

```bash
python3 sja1110_frer_enabled.py
```

This will create new `sja1110_switch_frer.bin` and `sja1110_uc_frer.bin` files.

## 📚 References

- IEEE 802.1CB-2017 Standard
- NXP S32G2 Reference Manual
- SJA1110 User Manual

## 📝 License

Based on NXP proprietary firmware. Use subject to NXP license terms.

## ⚠️ Important Notes

1. This configuration is specifically for **S32G274ARDB2** board
2. Firmware version: **GoldVIP-S32G2-1.14.0**
3. The UC firmware is 320KB (not 2KB) - this is correct
4. The switch config is 2KB - this is also correct (it's just configuration tables)

## 💡 Support

For issues, check the boot log first:
```bash
dmesg | grep -E "sja1110|pfeng"
```

---
*Last tested: 2024-09-19*