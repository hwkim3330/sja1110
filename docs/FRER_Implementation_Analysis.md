# S32G2 FRER (IEEE 802.1CB) Implementation Analysis

## Binary Files Overview

### 1. SJA1110 Switch Configuration
- **File**: `sja1110_switch.bin` (2,236 bytes)
- **Type**: Custom binary configuration format
- **Purpose**: TSN Ethernet switch configuration including FRER support

### 2. PFE (Packet Forwarding Engine) Firmware
- **Files**:
  - `s32g_pfe_class.fw` - ELF 32-bit MIPS executable
  - `s32g_pfe_util.fw` - ELF 32-bit MIPS executable
- **Architecture**: MIPS32 rel2
- **Purpose**: Hardware packet processing acceleration

### 3. SJA1110 Microcontroller Firmware
- **File**: `sja1110_uc.bin` (custom binary)
- **Purpose**: Switch microcontroller firmware

## FRER Implementation Architecture

### SJA1110 TSN Switch Features
The SJA1110 is an automotive Ethernet switch supporting:
- IEEE 802.1CB Frame Replication and Elimination for Reliability
- IEEE 802.1Qci Per-Stream Filtering and Policing
- IEEE 802.1AS-2020 Time Synchronization
- IEEE 802.1Qav Credit-Based Shaping
- IEEE 802.1Qbv Time-Aware Shaping

### FRER Configuration Structure

The switch binary contains configuration tables for:

1. **Stream Identification**
   - Maps incoming frames to stream IDs
   - Based on MAC addresses, VLAN tags, or other fields

2. **Sequence Recovery**
   - Maintains sequence number history per stream
   - Eliminates duplicate frames
   - Recovers original frame order

3. **Redundancy Tags**
   - R-TAG insertion for replicated frames
   - R-TAG removal after elimination

4. **Port Configuration**
   - Ingress/egress port stream handling
   - Member/non-member stream configuration

### Configuration Binary Analysis

```
Configuration Header:
  Magic: 0x0f0300b7
  Version: 0x00000006

Table Entries (pattern):
  - Entry format: [Config Word] [Mask/Value]
  - Repeating pattern: 0x00ecffff 0x9fff7fXX
  - Incremental indices in lower bytes
```

### FRER Operation Flow

1. **Frame Reception**
   - Stream identification based on configured rules
   - Check if frame belongs to FRER-protected stream

2. **Sequence Recovery (Elimination)**
   - Extract sequence number from R-TAG
   - Compare with history window
   - Drop duplicates, forward unique frames

3. **Frame Replication**
   - For egress FRER streams
   - Add R-TAG with sequence number
   - Replicate to configured redundant paths

4. **Statistics & Monitoring**
   - Lost frames counter
   - Duplicate frames counter
   - Out-of-order frames counter

## Implementation Details

### Register Configuration
The SJA1110 uses memory-mapped registers for FRER configuration:
- Stream identification tables at specific offsets
- Sequence recovery parameters (window size, timeout)
- Port-based FRER enable/disable flags

### PFE Integration
The PFE firmware handles:
- Fast-path packet processing
- Hardware acceleration for FRER operations
- Statistics collection and reporting

### Software Stack Integration
- Linux kernel TSN driver support
- User-space configuration via tc (traffic control)
- YANG models for standardized configuration

## Usage Example

To enable FRER on the S32G2 platform:

1. Load switch configuration binary
2. Configure stream identification rules
3. Set sequence recovery parameters
4. Enable FRER on specific ports
5. Monitor statistics for redundancy effectiveness

## Key Registers and Tables

- Stream ID table: Maps traffic to streams
- Sequence recovery table: Per-stream duplicate detection
- Port FRER control: Enable/disable per port
- Statistics counters: Monitor FRER performance

This implementation provides automotive-grade redundancy for critical Ethernet traffic, ensuring reliable communication even in the presence of link failures or interference.