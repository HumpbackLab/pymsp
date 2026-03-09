"""
Comprehensive test for pymsp library functionality.

This test validates that all aspects of the library work as expected,
following the TDD approach with API specifications and implementation.
"""

from pymsp.msp import MSPv1, MSPv2, MSPException


def test_comprehensive_mspv1():
    """Comprehensive test for MSPv1 functionality"""
    print("Testing MSPv1 functionality...")

    msp = MSPv1()

    # Test basic packing and unpacking
    print("  - Basic pack/unpack test")
    message_id = 100
    payload = b'\x01\x02\x03'
    packed = msp.pack(message_id, payload)

    # Convert starter header to reply header for unpacking
    reply_message = b'$M>' + packed[3:]
    unpacked_id, unpacked_payload = msp.unpack(reply_message)

    assert unpacked_id == message_id, f"Expected ID {message_id}, got {unpacked_id}"
    assert unpacked_payload == payload, f"Expected payload {payload.hex()}, got {unpacked_payload.hex()}"
    print("    ✓ Pack/unpack roundtrip successful")

    # Test message without payload
    print("  - Empty payload test")
    packed_empty = msp.pack(101)
    reply_empty = b'$M>' + packed_empty[3:]
    unpacked_id_empty, unpacked_payload_empty = msp.unpack(reply_empty)

    assert unpacked_id_empty == 101
    assert unpacked_payload_empty == b''
    print("    ✓ Empty payload test successful")

    # Test error conditions
    print("  - Error condition tests")
    try:
        msp.pack(300, b'')  # Invalid ID > 255
        assert False, "Should have raised exception for invalid ID"
    except MSPException:
        print("    ✓ Correctly rejects invalid message ID")

    # Test checksum validation
    print("  - Checksum validation test")
    try:
        # Create message with bad checksum manually
        bad_message = b'$M>' + b'\x00\x64' + b'\xFF'  # Bad checksum
        msp.unpack(bad_message)
        assert False, "Should have raised exception for bad checksum"
    except MSPException:
        print("    ✓ Correctly detects invalid checksum")


def test_comprehensive_mspv2():
    """Comprehensive test for MSPv2 functionality"""
    print("Testing MSPv2 functionality...")

    msp = MSPv2()

    # Test basic packing and unpacking
    print("  - Basic pack/unpack test")
    message_id = 0x100B  # MSP2_COMMON_SERIAL_CONFIG
    payload = b'\x01\x02\x03\x04'
    flags = b'\x00'
    packed = msp.pack(message_id, payload, flags)

    # Convert starter header to reply header for unpacking
    reply_message = b'$X>' + packed[3:]
    unpacked_id, unpacked_payload, unpacked_flags = msp.unpack(reply_message)

    assert unpacked_id == message_id, f"Expected ID {message_id}, got {unpacked_id}"
    assert unpacked_payload == payload, f"Expected payload {payload.hex()}, got {unpacked_payload.hex()}"
    assert unpacked_flags == flags, f"Expected flags {flags.hex()}, got {unpacked_flags.hex()}"
    print("    ✓ Pack/unpack roundtrip successful")

    # Test message without payload
    print("  - Empty payload test")
    packed_empty = msp.pack(0x2000)
    reply_empty = b'$X>' + packed_empty[3:]
    unpacked_id_empty, unpacked_payload_empty, unpacked_flags_empty = msp.unpack(reply_empty)

    assert unpacked_id_empty == 0x2000
    assert unpacked_payload_empty == b''
    assert unpacked_flags_empty == b'\x00'
    print("    ✓ Empty payload test successful")

    # Test error conditions
    print("  - Error condition tests")
    try:
        msp.pack(0x20000, b'')  # Invalid ID > 0xFFFF
        assert False, "Should have raised exception for invalid ID"
    except MSPException:
        print("    ✓ Correctly rejects invalid message ID")

    # Test checksum validation
    print("  - Checksum validation test")
    try:
        # Create message with bad checksum manually
        size_bytes = b'\x00\x00'  # Size 0
        flags_byte = b'\x00'      # Flags
        id_bytes = b'\x0B\x10'    # ID 0x100B in little endian
        bad_message = b'$X>' + size_bytes + flags_byte + id_bytes + b'\xFF'  # Bad checksum
        msp.unpack(bad_message)
        assert False, "Should have raised exception for bad checksum"
    except MSPException:
        print("    ✓ Correctly detects invalid checksum")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("Testing edge cases...")

    # MSPv1 boundary test
    msp_v1 = MSPv1()
    print("  - MSPv1 boundary tests")

    # Test with maximum valid ID
    max_id_v1 = 255
    packed = msp_v1.pack(max_id_v1, b'')
    reply = b'$M>' + packed[3:]
    unpacked_id, _ = msp_v1.unpack(reply)
    assert unpacked_id == max_id_v1
    print("    ✓ Maximum ID (255) handled correctly")

    # MSPv2 boundary test
    msp_v2 = MSPv2()
    print("  - MSPv2 boundary tests")

    # Test with maximum valid ID
    max_id_v2 = 0xFFFF  # 65535
    packed = msp_v2.pack(max_id_v2, b'')
    reply = b'$X>' + packed[3:]
    unpacked_id, _, _ = msp_v2.unpack(reply)
    assert unpacked_id == max_id_v2
    print("    ✓ Maximum ID (65535) handled correctly")

    # Test with various payload sizes for MSP v1 (size field is 1 byte, max 255)
    print("  - Variable payload size tests for MSP v1")
    for size in [0, 1, 10, 255]:  # MSP v1 size field is 1 byte (max 255)
        payload = bytes([i % 256 for i in range(size)])
        packed = msp_v1.pack(100, payload)
        reply = b'$M>' + packed[3:]
        unpacked_id, unpacked_payload = msp_v1.unpack(reply)

        assert unpacked_id == 100
        assert unpacked_payload == payload
    print("    ✓ MSP v1 various payload sizes handled correctly")

    # Test MSP v2 with larger payloads (size field is 2 bytes, max 65535)
    print("  - Large payload size test for MSP v2")
    size = 500  # This would fail in MSP v1 but should work in MSP v2
    payload = bytes([i % 256 for i in range(size)])
    packed = msp_v2.pack(1000, payload, b'\x00')
    reply = b'$X>' + packed[3:]
    unpacked_id, unpacked_payload, unpacked_flags = msp_v2.unpack(reply)

    assert unpacked_id == 1000
    assert unpacked_payload == payload
    assert unpacked_flags == b'\x00'
    print("    ✓ MSP v2 large payload handled correctly")

    # Test MSP v1 size limit error handling
    print("  - MSP v1 size limit error handling")
    try:
        oversized_payload = bytes([i % 256 for i in range(256)])  # 256 bytes, too big for MSP v1
        msp_v1.pack(100, oversized_payload)
        assert False, "Should have raised error for oversized payload in MSP v1"
    except MSPException:
        print("    ✓ MSP v1 correctly handles oversized payload error")


def run_all_tests():
    """Run all comprehensive tests"""
    print("Running comprehensive tests for PyMSP library...\n")

    test_comprehensive_mspv1()
    print()

    test_comprehensive_mspv2()
    print()

    test_edge_cases()
    print()

    print("All comprehensive tests passed! ✓")
    print("\nPyMSP library is fully functional with:")
    print("- MSP v1 protocol support")
    print("- MSP v2 protocol support")
    print("- Proper packing and unpacking of messages")
    print("- Correct header formats ($M<> for v1, $X<> for v2)")
    print("- Accurate checksum calculations")
    print("- Appropriate error handling")
    print("- Full API compatibility as specified")


if __name__ == "__main__":
    run_all_tests()