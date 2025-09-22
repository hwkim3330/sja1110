#!/bin/bash
# Upload fixed SJA1110 firmware to S32G274A-RDB2

echo "Uploading SJA1110 firmware to S32G274A-RDB2..."

# Copy files to board
scp sja1110_switch_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp sja1110_uc_s32g.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin

echo "Files uploaded. Rebooting board..."
ssh root@192.168.1.1 "sync && reboot"

echo "Done! Board will reboot with new firmware."
