#!/bin/bash
# Upload GoldVIP-compatible firmware to S32G274A-RDB2

echo "Uploading GoldVIP firmware to S32G274A-RDB2..."

# Backup existing
ssh root@192.168.1.1 "cp /lib/firmware/sja1110_switch.bin /lib/firmware/sja1110_switch.bin.bak 2>/dev/null"
ssh root@192.168.1.1 "cp /lib/firmware/sja1110_uc.bin /lib/firmware/sja1110_uc.bin.bak 2>/dev/null"

# Upload new firmware
scp sja1110_switch_goldvip.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp sja1110_uc_goldvip.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin

echo "Firmware uploaded. Rebooting..."
ssh root@192.168.1.1 "sync && reboot"

echo "Done! Check dmesg after boot:"
echo "  ssh root@192.168.1.1 'dmesg | grep sja1110'"
