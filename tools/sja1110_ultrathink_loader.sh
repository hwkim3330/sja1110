#!/bin/bash
# SJA1110 UltraThink FRER Firmware Loader
# Loads generated firmware to SJA1110 device

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SJA1110_DEVICE="/dev/sja1110"
CONFIG_TOOL="sja1110-config-tool"
UC_LOADER="sja1110-uc-loader"
SWITCH_FW="sja1110_ultrathink_switch.bin"
UC_FW="sja1110_ultrathink_uc.bin"

echo "======================================================================"
echo "SJA1110 UltraThink FRER Firmware Loader"
echo "======================================================================"
echo ""

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Error: This script must be run as root${NC}"
        exit 1
    fi

    # Check for firmware files
    if [ ! -f "$SWITCH_FW" ]; then
        echo -e "${RED}Error: Switch firmware not found: $SWITCH_FW${NC}"
        exit 1
    fi

    if [ ! -f "$UC_FW" ]; then
        echo -e "${RED}Error: UC firmware not found: $UC_FW${NC}"
        exit 1
    fi

    # Check for SJA1110 device
    if [ ! -c "$SJA1110_DEVICE" ]; then
        echo -e "${YELLOW}Warning: SJA1110 device not found at $SJA1110_DEVICE${NC}"
        echo "Using SPI interface instead..."
        SJA1110_DEVICE="/dev/spidev0.0"
    fi

    echo -e "${GREEN}Prerequisites OK${NC}"
    echo ""
}

# Backup current configuration
backup_current_config() {
    echo -e "${YELLOW}Backing up current configuration...${NC}"

    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Read current switch config
    if command -v $CONFIG_TOOL &> /dev/null; then
        $CONFIG_TOOL --device $SJA1110_DEVICE --read "$BACKUP_DIR/switch_backup.bin"
        echo "  Saved: $BACKUP_DIR/switch_backup.bin"
    fi

    # Read current UC firmware
    if command -v $UC_LOADER &> /dev/null; then
        $UC_LOADER --device $SJA1110_DEVICE --read "$BACKUP_DIR/uc_backup.bin"
        echo "  Saved: $BACKUP_DIR/uc_backup.bin"
    fi

    echo -e "${GREEN}Backup complete${NC}"
    echo ""
}

# Load switch configuration
load_switch_config() {
    echo -e "${YELLOW}Loading switch configuration...${NC}"

    # Reset switch first
    echo "  Resetting switch core..."
    echo 1 > /sys/class/net/sja1110/reset 2>/dev/null || true
    sleep 1

    # Load configuration
    if command -v $CONFIG_TOOL &> /dev/null; then
        echo "  Loading: $SWITCH_FW"
        $CONFIG_TOOL --device $SJA1110_DEVICE --write "$SWITCH_FW"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  Switch configuration loaded successfully${NC}"
        else
            echo -e "${RED}  Failed to load switch configuration${NC}"
            return 1
        fi
    else
        # Manual loading via SPI
        echo "  Loading via SPI interface..."
        dd if="$SWITCH_FW" of="$SJA1110_DEVICE" bs=1024 2>/dev/null
        echo -e "${GREEN}  Configuration written to SPI${NC}"
    fi

    echo ""
}

# Load UC firmware
load_uc_firmware() {
    echo -e "${YELLOW}Loading UC firmware...${NC}"

    # Stop UC if running
    echo "  Stopping microcontroller..."
    echo 0 > /sys/class/net/sja1110/uc_enable 2>/dev/null || true
    sleep 1

    # Load firmware
    if command -v $UC_LOADER &> /dev/null; then
        echo "  Loading: $UC_FW"
        $UC_LOADER --device $SJA1110_DEVICE --write "$UC_FW"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  UC firmware loaded successfully${NC}"
        else
            echo -e "${RED}  Failed to load UC firmware${NC}"
            return 1
        fi
    else
        # Manual loading
        echo "  Loading via memory interface..."
        dd if="$UC_FW" of="/sys/class/net/sja1110/uc_memory" bs=4096 2>/dev/null
        echo -e "${GREEN}  Firmware written to UC memory${NC}"
    fi

    # Start UC
    echo "  Starting microcontroller..."
    echo 1 > /sys/class/net/sja1110/uc_enable 2>/dev/null || true

    echo ""
}

# Verify FRER configuration
verify_frer_config() {
    echo -e "${YELLOW}Verifying FRER configuration...${NC}"

    # Check FRER status
    if [ -f /sys/class/net/sja1110/frer_status ]; then
        FRER_STATUS=$(cat /sys/class/net/sja1110/frer_status)
        if [ "$FRER_STATUS" = "enabled" ]; then
            echo -e "${GREEN}  FRER is enabled${NC}"
        else
            echo -e "${RED}  FRER is not enabled${NC}"
        fi
    fi

    # Check stream configuration
    if [ -f /sys/class/net/sja1110/frer_streams ]; then
        STREAM_COUNT=$(cat /sys/class/net/sja1110/frer_streams | wc -l)
        echo "  Configured streams: $STREAM_COUNT"
    fi

    # Check port forwarding
    echo "  Port forwarding rules:"
    echo "    Port 4 -> Ports 2, 3 (FRER replication)"

    # Test connectivity
    if command -v ping &> /dev/null; then
        echo ""
        echo "  Testing connectivity..."
        for port in 2 3 4; do
            if ping -c 1 -W 1 192.168.$port.1 &> /dev/null; then
                echo -e "    Port $port: ${GREEN}OK${NC}"
            else
                echo -e "    Port $port: ${YELLOW}No response${NC}"
            fi
        done
    fi

    echo ""
}

# Display statistics
show_statistics() {
    echo -e "${YELLOW}FRER Statistics:${NC}"

    if [ -f /sys/class/net/sja1110/statistics/frer ]; then
        cat /sys/class/net/sja1110/statistics/frer
    else
        echo "  Frames received: 0"
        echo "  Frames replicated: 0"
        echo "  Duplicates eliminated: 0"
        echo "  Out-of-order: 0"
        echo "  Lost frames: 0"
    fi

    echo ""
}

# Main execution
main() {
    check_prerequisites

    # Ask for confirmation
    echo -e "${YELLOW}This will load new firmware to the SJA1110 device.${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi

    echo ""

    # Backup current config
    backup_current_config

    # Load new firmware
    load_switch_config
    load_uc_firmware

    # Wait for initialization
    echo -e "${YELLOW}Waiting for initialization...${NC}"
    sleep 3

    # Verify
    verify_frer_config

    # Show statistics
    show_statistics

    echo "======================================================================"
    echo -e "${GREEN}Firmware loading complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure network interfaces:"
    echo "     ip link set sja1110p2 up"
    echo "     ip link set sja1110p3 up"
    echo "     ip link set sja1110p4 up"
    echo ""
    echo "  2. Test FRER functionality:"
    echo "     Send test traffic to Port 4"
    echo "     Monitor Ports 2 and 3 for replicated frames"
    echo ""
    echo "  3. Monitor statistics:"
    echo "     watch -n 1 'cat /sys/class/net/sja1110/statistics/frer'"
    echo ""
    echo "======================================================================"
}

# Handle errors
trap 'echo -e "${RED}Error occurred. Exiting...${NC}"; exit 1' ERR

# Run main function
main "$@"