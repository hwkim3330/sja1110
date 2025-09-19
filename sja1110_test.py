#!/usr/bin/env python3
"""
SJA1110 FRER Testing Script
Tests P4 to P2A/P2B frame replication
"""

import socket
import struct
import time
import sys

class FRERTester:
    def __init__(self):
        self.test_frames = []
        self.seq_num = 0

    def create_test_frame(self, data="Test Frame"):
        """Create an Ethernet test frame"""
        # Ethernet header
        dst_mac = b'\xff\xff\xff\xff\xff\xff'  # Broadcast
        src_mac = b'\x00\x11\x22\x33\x44\x55'  # Test source MAC
        eth_type = struct.pack('>H', 0x88F7)    # IEEE 1722 (TSN)

        # Payload
        payload = data.encode() + b'\x00' * (46 - len(data))  # Minimum frame size

        # Build frame
        frame = dst_mac + src_mac + eth_type + payload
        return frame

    def create_frer_frame(self, data="FRER Test"):
        """Create a frame with R-TAG for FRER"""
        # Ethernet header
        dst_mac = b'\x00\xaa\xbb\xcc\xdd\xee'
        src_mac = b'\x00\x11\x22\x33\x44\x55'

        # R-TAG (IEEE 802.1CB)
        r_tag_type = struct.pack('>H', 0xF1CD)  # R-TAG EtherType
        r_tag_reserved = struct.pack('>H', 0x0000)
        r_tag_seq_num = struct.pack('>H', self.seq_num)
        self.seq_num = (self.seq_num + 1) % 65536

        # Original EtherType and payload
        original_type = struct.pack('>H', 0x0800)  # IPv4
        payload = data.encode() + b'\x00' * (46 - len(data))

        # Build FRER frame
        frame = dst_mac + src_mac + r_tag_type + r_tag_reserved + r_tag_seq_num + original_type + payload
        return frame

    def send_to_port(self, interface, frame):
        """Send frame to specified network interface"""
        try:
            # Create raw socket
            s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
            s.bind((interface, 0))

            # Send frame
            s.send(frame)
            s.close()
            return True
        except Exception as e:
            print(f"Error sending to {interface}: {e}")
            return False

    def receive_from_port(self, interface, timeout=1):
        """Receive frame from specified network interface"""
        try:
            # Create raw socket
            s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
            s.bind((interface, 0))
            s.settimeout(timeout)

            # Receive frame
            data, addr = s.recvfrom(65535)
            s.close()
            return data
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error receiving from {interface}: {e}")
            return None

    def verify_replication(self):
        """Verify frame replication from P4 to P2A/P2B"""
        print("Testing FRER Frame Replication")
        print("===============================")
        print()

        test_data = "FRER_TEST_" + str(int(time.time()))

        # Create test frame
        frame = self.create_frer_frame(test_data)
        print(f"Sending test frame to P4 (sequence: {self.seq_num-1})")
        print(f"Frame size: {len(frame)} bytes")
        print(f"Payload: {test_data}")
        print()

        # Send to P4 (eth4 on Linux)
        if sys.platform == "linux":
            input_port = "eth4"
            output_ports = ["eth2a", "eth2b"]
        else:
            print("Note: This test should be run on the S32G2 Linux target")
            return

        # Send frame
        if self.send_to_port(input_port, frame):
            print(f"✓ Frame sent to {input_port}")
        else:
            print(f"✗ Failed to send frame to {input_port}")
            return

        # Check reception on output ports
        print("\nChecking replication on output ports...")
        time.sleep(0.1)

        received_frames = {}
        for port in output_ports:
            rx_frame = self.receive_from_port(port, timeout=0.5)
            if rx_frame:
                received_frames[port] = rx_frame
                print(f"✓ Frame received on {port} ({len(rx_frame)} bytes)")

                # Verify R-TAG presence
                if len(rx_frame) >= 18:
                    r_tag = struct.unpack('>H', rx_frame[12:14])[0]
                    if r_tag == 0xF1CD:
                        seq = struct.unpack('>H', rx_frame[16:18])[0]
                        print(f"  R-TAG detected, sequence: {seq}")
                    else:
                        print(f"  No R-TAG (EtherType: 0x{r_tag:04X})")
            else:
                print(f"✗ No frame received on {port}")

        # Verify both outputs received the frame
        if len(received_frames) == 2:
            print("\n✓ FRER replication successful!")
            print("  Frame successfully replicated to both output ports")

            # Check if frames are identical (except for possible modifications)
            if received_frames[output_ports[0]][:18] == received_frames[output_ports[1]][:18]:
                print("  Frames have matching headers")
        else:
            print("\n✗ FRER replication failed")
            print(f"  Only {len(received_frames)} of 2 output ports received the frame")

    def run_continuous_test(self, count=10, interval=1):
        """Run continuous replication test"""
        print(f"Running continuous test ({count} frames, {interval}s interval)")
        print("=" * 50)

        success_count = 0
        for i in range(count):
            print(f"\nTest {i+1}/{count}:")
            self.verify_replication()

            if i < count - 1:
                time.sleep(interval)

        print("\n" + "=" * 50)
        print("Test Summary:")
        print(f"  Frames sent: {count}")
        print(f"  Test completed")

def main():
    print("SJA1110 FRER Test Tool")
    print("======================")
    print("Configuration: P4 -> P2A, P2B (FRER replication)")
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        # Run continuous test
        tester = FRERTester()
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        tester.run_continuous_test(count)
    else:
        # Run single test
        tester = FRERTester()
        tester.verify_replication()

    print("\nFor detailed statistics, check:")
    print("  /sys/class/net/eth4/statistics/")
    print("  /sys/class/net/eth2a/statistics/")
    print("  /sys/class/net/eth2b/statistics/")

if __name__ == "__main__":
    main()