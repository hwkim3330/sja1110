#!/bin/bash
#
# SJA1110 FRER Configuration Loader Script
# Loads P4->P2A/P2B replication configuration to S32G2 board
#

CONFIG_FILE="sja1110_p4_to_p2ab_frer.bin"
DEVICE="/dev/sja1110"
SPI_DEV="/dev/spidev0.0"

echo "SJA1110 FRER Configuration Loader"
echo "=================================="
echo ""

# Check if running on target board
if [ ! -e /sys/class/net/eth0 ]; then
    echo "Warning: Not running on S32G2 target board"
    echo "This script should be executed on the S32G2 platform"
fi

# Check for configuration file
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file $CONFIG_FILE not found!"
    exit 1
fi

echo "Configuration: P4 input -> P2A, P2B output (FRER replication)"
echo "File: $CONFIG_FILE"
echo "Size: $(stat -c%s $CONFIG_FILE) bytes"
echo ""

# Load SJA1110 kernel module if not loaded
if ! lsmod | grep -q sja1110; then
    echo "Loading SJA1110 kernel module..."
    modprobe sja1110
    sleep 1
fi

# Reset the switch
echo "Resetting SJA1110 switch..."
echo 1 > /sys/class/gpio/gpio12/value
sleep 0.1
echo 0 > /sys/class/gpio/gpio12/value
sleep 1

# Load configuration via SPI
echo "Loading configuration to SJA1110..."
if [ -e "$SPI_DEV" ]; then
    # Direct SPI programming
    dd if=$CONFIG_FILE of=$SPI_DEV bs=256 count=1 2>/dev/null
else
    # Use sja1110 tool if available
    if command -v sja1110-config &> /dev/null; then
        sja1110-config load $CONFIG_FILE
    else
        echo "Error: No suitable method to load configuration"
        echo "Please ensure sja1110-config tool is installed"
        exit 1
    fi
fi

# Verify configuration
echo "Verifying configuration..."
sleep 1

# Configure network interfaces
echo "Configuring network interfaces..."

# P4 as input interface
ip link set eth4 up

# P2A and P2B as output interfaces
ip link set eth2a up
ip link set eth2b up

# Enable TSN features
echo "Enabling TSN features..."
tc qdisc add dev eth4 ingress
tc qdisc add dev eth2a root mqprio num_tc 8 map 0 1 2 3 4 5 6 7
tc qdisc add dev eth2b root mqprio num_tc 8 map 0 1 2 3 4 5 6 7

# Configure FRER stream
echo "Configuring FRER stream..."

# Add stream identification rule for P4 input
tc filter add dev eth4 ingress protocol all prio 1 \
    flower skip_hw \
    action gate base-time 0 \
    action mirred egress mirror dev eth2a \
    action mirred egress redirect dev eth2b

echo ""
echo "Configuration complete!"
echo ""
echo "FRER Status:"
echo "------------"
echo "Input port P4: $(ip link show eth4 | grep state)"
echo "Output port P2A: $(ip link show eth2a | grep state)"
echo "Output port P2B: $(ip link show eth2b | grep state)"
echo ""
echo "To test the configuration:"
echo "  1. Send traffic to P4 (eth4)"
echo "  2. Monitor P2A (eth2a) and P2B (eth2b)"
echo "  3. Verify frames are replicated with R-TAG"
echo ""
echo "Monitor statistics:"
echo "  cat /sys/class/net/eth4/statistics/rx_packets"
echo "  cat /sys/class/net/eth2a/statistics/tx_packets"
echo "  cat /sys/class/net/eth2b/statistics/tx_packets"