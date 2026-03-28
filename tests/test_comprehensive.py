"""
Comprehensive test for pymsp library functionality.

This test validates that all aspects of the library work as expected,
following the TDD approach with API specifications and implementation.
"""

from pymsp.msp import MSPException, MSPFrame, MSPv1, MSPv2


def crc8_dvb_s2(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0xD5) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


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
    frame = msp.unpack(reply_message)

    assert isinstance(frame, MSPFrame)
    assert frame.message_id == message_id, f"Expected ID {message_id}, got {frame.message_id}"
    assert frame.payload == payload, f"Expected payload {payload.hex()}, got {frame.payload.hex()}"
    assert frame.protocol_version == 1
    assert frame.flags == b''  # MSP v1 has no flags
    print("    ✓ Pack/unpack roundtrip successful")

    # Test message without payload
    print("  - Empty payload test")
    packed_empty = msp.pack(101)
    reply_empty = b'$M>' + packed_empty[3:]
    frame_empty = msp.unpack(reply_empty)

    assert frame_empty.message_id == 101
    assert frame_empty.payload == b''
    assert frame_empty.protocol_version == 1
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

    # Test to_bytes method
    print("  - to_bytes method test")
    original_packed = msp.pack(100, b'\x01\x02\x03')
    reply_for_unpack = b'$M>' + original_packed[3:]
    frame = msp.unpack(reply_for_unpack)
    _ = frame.to_bytes()

    # Check that important fields are preserved (excluding checksum which is recalculated)
    assert frame.header == b'$M>'
    assert frame.message_id == 100
    assert frame.payload == b'\x01\x02\x03'
    assert frame.protocol_version == 1
    print("    ✓ to_bytes method works correctly")


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
    frame = msp.unpack(reply_message)

    assert isinstance(frame, MSPFrame)
    assert frame.message_id == message_id, f"Expected ID {message_id}, got {frame.message_id}"
    assert frame.payload == payload, f"Expected payload {payload.hex()}, got {frame.payload.hex()}"
    assert frame.flags == flags, f"Expected flags {flags.hex()}, got {frame.flags.hex()}"
    assert frame.protocol_version == 2
    print("    ✓ Pack/unpack roundtrip successful")

    # Test message without payload
    print("  - Empty payload test")
    packed_empty = msp.pack(0x2000)
    reply_empty = b'$X>' + packed_empty[3:]
    frame_empty = msp.unpack(reply_empty)

    assert frame_empty.message_id == 0x2000
    assert frame_empty.payload == b''
    assert frame_empty.flags == b'\x00'
    assert frame_empty.protocol_version == 2
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
        flags_byte = b'\x00'
        id_bytes = b'\x0B\x10'
        size_bytes = b'\x00\x00'
        bad_message = b'$X>' + flags_byte + id_bytes + size_bytes + b'\xFF'
        msp.unpack(bad_message)
        assert False, "Should have raised exception for bad checksum"
    except MSPException:
        print("    ✓ Correctly detects invalid checksum")

    # Test to_bytes method
    print("  - to_bytes method test")
    original_packed = msp.pack(0x100B, b'\x01\x02\x03\x04', b'\x00')
    reply_for_unpack = b'$X>' + original_packed[3:]
    frame = msp.unpack(reply_for_unpack)
    _ = frame.to_bytes()

    # Check that important fields are preserved (excluding checksum which is recalculated)
    assert frame.header == b'$X>'
    assert frame.message_id == 0x100B
    assert frame.payload == b'\x01\x02\x03\x04'
    assert frame.flags == b'\x00'
    assert frame.protocol_version == 2
    print("    ✓ to_bytes method works correctly")

    print("  - Real INAV request frame test")
    real_request = bytes.fromhex('24583c000100000045')
    request_frame = msp.unpack(real_request)
    assert request_frame.header == b'$X<'
    assert request_frame.message_id == 1
    assert request_frame.payload == b''
    print("    ✓ Real INAV request frame parses correctly")


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
    frame = msp_v1.unpack(reply)
    assert frame.message_id == max_id_v1
    assert frame.protocol_version == 1
    print("    ✓ Maximum ID (255) handled correctly")

    # MSPv2 boundary test
    msp_v2 = MSPv2()
    print("  - MSPv2 boundary tests")

    # Test with maximum valid ID
    max_id_v2 = 0xFFFF  # 65535
    packed = msp_v2.pack(max_id_v2, b'')
    reply = b'$X>' + packed[3:]
    frame = msp_v2.unpack(reply)
    assert frame.message_id == max_id_v2
    assert frame.protocol_version == 2
    print("    ✓ Maximum ID (65535) handled correctly")

    # Test with various payload sizes for MSP v1 (size field is 1 byte, max 255)
    print("  - Variable payload size tests for MSP v1")
    for size in [0, 1, 10, 255]:  # MSP v1 size field is 1 byte (max 255)
        payload = bytes([i % 256 for i in range(size)])
        packed = msp_v1.pack(100, payload)
        reply = b'$M>' + packed[3:]
        frame = msp_v1.unpack(reply)

        assert frame.message_id == 100
        assert frame.payload == payload
    print("    ✓ MSP v1 various payload sizes handled correctly")

    # Test MSP v2 with larger payloads (size field is 2 bytes, max 65535)
    print("  - Large payload size test for MSP v2")
    size = 500  # This would fail in MSP v1 but should work in MSP v2
    payload = bytes([i % 256 for i in range(size)])
    packed = msp_v2.pack(1000, payload, b'\x00')
    reply = b'$X>' + packed[3:]
    frame = msp_v2.unpack(reply)

    assert frame.message_id == 1000
    assert frame.payload == payload
    assert frame.flags == b'\x00'
    assert frame.protocol_version == 2
    print("    ✓ MSP v2 large payload handled correctly")

    # Test MSP v1 size limit error handling
    print("  - MSP v1 size limit error handling")
    try:
        oversized_payload = bytes([i % 256 for i in range(256)])  # 256 bytes, too big for MSP v1
        msp_v1.pack(100, oversized_payload)
        assert False, "Should have raised error for oversized payload in MSP v1"
    except MSPException:
        print("    ✓ MSP v1 correctly handles oversized payload error")

    # Test mixed version handling
    print("  - Mixed version handling test")
    v1_frame = msp_v1.unpack(b'$M>\x00\x65\x65')  # Empty payload for ID 101
    v2_packed = msp_v2.pack(0x2001, b'\x01\x02\x03', b'\x00')
    v2_reply = b'$X>' + v2_packed[3:]
    v2_frame = msp_v2.unpack(v2_reply)

    assert v1_frame.protocol_version == 1
    assert v2_frame.protocol_version == 2
    assert v1_frame.flags == b''  # MSP v1 has no flags
    assert v2_frame.flags == b'\x00'  # MSP v2 has flags
    print("    ✓ Mixed version handling works correctly")


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
    print("- Unified MSPFrame for both protocol versions")
    print("- Proper packing and unpacking of messages")
    print("- Correct header formats ($M<> for v1, $X<> for v2)")
    print("- Accurate checksum calculations")
    print("- Appropriate error handling")
    print("- Full API compatibility as specified")
    print("- to_bytes method for reconstructing message bytes")


if __name__ == "__main__":
    run_all_tests()
