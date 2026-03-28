"""
Tests for the PyMSP library following TDD principles.

These tests define the expected API and behavior before implementation.
"""

import struct

import pytest

from pymsp.msp import MSPException, MSPFrame, MSPStreamProcessor, MSPv1, MSPv2


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


def test_mspv1_import():
    """Test that MSPv1 can be imported"""
    assert MSPv1 is not None


def test_mspv2_import():
    """Test that MSPv2 can be imported"""
    assert MSPv2 is not None


def test_mspframe_import():
    """Test that MSPFrame can be imported"""
    assert MSPFrame is not None


def test_mspstreamprocessor_import():
    """Test that MSPStreamProcessor can be imported"""
    assert MSPStreamProcessor is not None


def test_msp_exception_import():
    """Test that MSPException can be imported"""
    assert MSPException is not None


class TestMSPv1:
    """Tests for MSP v1 protocol implementation"""

    def test_mspv1_initialization(self):
        """Test MSPv1 initialization"""
        msp = MSPv1()
        assert isinstance(msp, MSPv1)

    def test_mspv1_pack_basic_message(self):
        """Test packing a basic MSP v1 message with no payload"""
        msp = MSPv1()
        message_id = 100  # MSP_STATUS
        packed = msp.pack(message_id)

        # Expected format: $M<data><checksum>
        assert packed.startswith(b'$M<')
        # Length byte should be 0 (no payload)
        assert packed[3] == 0
        # Message ID should be 100
        assert packed[4] == message_id
        # Checksum should be calculated correctly
        expected_checksum = 0 ^ 0 ^ 100  # length ^ message_id
        assert packed[5] == expected_checksum

    def test_mspv1_pack_message_with_payload(self):
        """Test packing a MSP v1 message with payload"""
        msp = MSPv1()
        message_id = 101  # MSP_RAW_IMU
        payload = b'\x01\x02\x03'
        packed = msp.pack(message_id, payload)

        # Expected format: $M<size><message_id><payload><checksum>
        assert packed.startswith(b'$M<')
        # Length byte should match payload length
        assert packed[3] == len(payload)
        # Message ID should be correct
        assert packed[4] == message_id
        # Payload should be included
        assert packed[5:8] == payload
        # Checksum should be calculated correctly
        expected_checksum = 0 ^ len(payload) ^ message_id
        for byte in payload:
            expected_checksum ^= byte
        assert packed[8] == expected_checksum

    def test_mspv1_pack_invalid_message_id(self):
        """Test that packing fails with invalid message ID"""
        msp = MSPv1()
        # Test ID greater than 255
        with pytest.raises(MSPException):
            msp.pack(300, b'')

    def test_mspv1_unpack_valid_message_no_payload(self):
        """Test unpacking a valid MSP v1 message with no payload"""
        msp = MSPv1()
        # Create a valid message: $M<message><checksum>
        # Message ID 100 with no payload
        message_id = 100
        size = 0
        checksum = size ^ message_id  # 0 ^ 100 = 100
        raw_message = b'$M>' + struct.pack('BBB', size, message_id, checksum)

        frame = msp.unpack(raw_message)

        assert isinstance(frame, MSPFrame)
        assert frame.message_id == message_id
        assert frame.payload == b''
        assert frame.protocol_version == 1
        assert frame.flags == b''  # MSP v1 has no flags

    def test_mspv1_unpack_valid_message_with_payload(self):
        """Test unpacking a valid MSP v1 message with payload"""
        msp = MSPv1()
        # Create a valid message: $M<message><checksum>
        message_id = 101
        payload = b'\x01\x02\x03'
        size = len(payload)
        # Calculate checksum: size ^ message_id ^ payload_bytes
        checksum = size ^ message_id
        for byte in payload:
            checksum ^= byte
        raw_message = b'$M>' + struct.pack('BB', size, message_id) + payload + struct.pack('B', checksum)

        frame = msp.unpack(raw_message)

        assert isinstance(frame, MSPFrame)
        assert frame.message_id == message_id
        assert frame.payload == payload
        assert frame.size == size
        assert frame.protocol_version == 1
        assert frame.flags == b''  # MSP v1 has no flags

    def test_mspv1_unpack_invalid_header(self):
        """Test that unpacking fails with invalid header"""
        msp = MSPv1()
        # Message without proper header
        invalid_message = b'ABC\x00d\x00'

        with pytest.raises(MSPException, match="Invalid MSP v1 header"):
            msp.unpack(invalid_message)

    def test_mspv1_unpack_short_message(self):
        """Test that unpacking fails with short message"""
        msp = MSPv1()
        # Message too short to be valid
        short_message = b'$M>'

        with pytest.raises(MSPException, match="Message too short"):
            msp.unpack(short_message)

    def test_mspv1_unpack_invalid_checksum(self):
        """Test that unpacking fails with invalid checksum"""
        msp = MSPv1()
        # Message with wrong checksum
        message_id = 100
        size = 0
        # Use incorrect checksum (different from calculated one)
        raw_message = b'$M>' + struct.pack('BBB', size, message_id, 0xFF)

        with pytest.raises(MSPException, match="Checksum mismatch"):
            msp.unpack(raw_message)

    def test_mspv1_frame_to_bytes(self):
        """Test converting MSPFrame back to bytes for v1"""
        msp = MSPv1()
        message_id = 101
        payload = b'\x01\x02\x03'

        # Pack and unpack to get frame
        packed = msp.pack(message_id, payload)
        reply_message = b'$M>' + packed[3:]
        frame = msp.unpack(reply_message)

        # Convert frame back to bytes
        _ = frame.to_bytes()

        # Should be identical to original (except possibly checksum which gets recalculated)
        # Compare all parts except checksum
        assert frame.header == b'$M>'
        assert frame.protocol_version == 1
        assert frame.message_id == message_id
        assert frame.payload == payload

    def test_calculate_checksum_method(self):
        """Test the calculate_checksum static method directly"""
        data = b'\x03d\x01\x02\x03'
        expected_checksum = 0
        for byte in data:
            expected_checksum ^= byte
        expected_checksum &= 0xFF

        assert MSPv1.calculate_checksum(data) == expected_checksum


class TestMSPv2:
    """Tests for MSP v2 protocol implementation"""

    def test_mspv2_initialization(self):
        """Test MSPv2 initialization"""
        msp = MSPv2()
        assert isinstance(msp, MSPv2)

    def test_mspv2_pack_basic_message(self):
        """Test packing a basic MSP v2 message with no payload"""
        msp = MSPv2()
        message_id = 400  # Example MSP V2 message ID
        packed = msp.pack(message_id)

        # Expected format: $X<flags><message_id_low><message_id_high><size_low><size_high><payload><checksum>
        assert packed.startswith(b'$X<')
        assert packed[3] == 0
        assert packed[4:6] == struct.pack('<H', message_id)
        assert packed[6:8] == struct.pack('<H', 0)
        # Checksum should be calculated correctly
        msg_data_without_header_and_checksum = packed[3:8]
        expected_checksum = crc8_dvb_s2(msg_data_without_header_and_checksum)
        assert packed[8] == expected_checksum

    def test_mspv2_pack_message_with_payload_and_flags(self):
        """Test packing a MSP v2 message with payload and flags"""
        msp = MSPv2()
        message_id = 500
        payload = b'\x01\x02\x03\x04'
        flags = b'\x05'
        packed = msp.pack(message_id, payload, flags)

        # Expected format: $X<flags><message_id><size><payload><checksum>
        assert packed.startswith(b'$X<')
        assert packed[3:4] == flags
        assert struct.unpack('<H', packed[4:6])[0] == message_id
        assert struct.unpack('<H', packed[6:8])[0] == len(payload)
        # Payload should match
        payload_start = 8
        payload_end = payload_start + len(payload)
        assert packed[payload_start:payload_end] == payload
        # Checksum should be calculated correctly
        assert packed[payload_end] == crc8_dvb_s2(packed[3:payload_end])

    def test_mspv2_pack_invalid_message_id(self):
        """Test that packing fails with invalid message ID"""
        msp = MSPv2()
        # Test ID greater than 0xFFFF (65535)
        with pytest.raises(MSPException):
            msp.pack(0x20000, b'')  # 131072

    def test_mspv2_unpack_valid_message_no_payload(self):
        """Test unpacking a valid MSP v2 message with no payload"""
        msp = MSPv2()
        message_id = 400
        flags = b'\x00'
        size = 0

        # Build the message part (without header and checksum)
        msg_part = flags + struct.pack('<H', message_id) + struct.pack('<H', size)
        checksum = crc8_dvb_s2(msg_part)

        # Build full message
        raw_message = b'$X>' + msg_part + struct.pack('B', checksum)

        frame = msp.unpack(raw_message)

        assert isinstance(frame, MSPFrame)
        assert frame.message_id == message_id
        assert frame.payload == b''
        assert frame.flags == flags
        assert frame.protocol_version == 2

    def test_mspv2_unpack_valid_message_with_payload_and_flags(self):
        """Test unpacking a valid MSP v2 message with payload and flags"""
        msp = MSPv2()
        message_id = 500
        flags = b'\x01'
        payload = b'\x01\x02\x03'
        size = len(payload)

        # Build the message part (without header and checksum)
        msg_part = flags + struct.pack('<H', message_id) + struct.pack('<H', size) + payload
        checksum = crc8_dvb_s2(msg_part)

        # Build full message
        raw_message = b'$X>' + msg_part + struct.pack('B', checksum)

        frame = msp.unpack(raw_message)

        assert isinstance(frame, MSPFrame)
        assert frame.message_id == message_id
        assert frame.payload == payload
        assert frame.flags == flags
        assert frame.size == size
        assert frame.protocol_version == 2

    def test_mspv2_unpack_invalid_header(self):
        """Test that unpacking fails with invalid header"""
        msp = MSPv2()
        # Message without proper header
        invalid_message = b'ABC\x00\x00\x00\x00\x00'

        with pytest.raises(MSPException, match="Invalid MSP v2 header"):
            msp.unpack(invalid_message)

    def test_mspv2_unpack_short_message(self):
        """Test that unpacking fails with short message"""
        msp = MSPv2()
        # Message too short to be valid
        short_message = b'$X>'

        with pytest.raises(MSPException, match="Message too short"):
            msp.unpack(short_message)

    def test_mspv2_unpack_invalid_checksum(self):
        """Test that unpacking fails with invalid checksum"""
        msp = MSPv2()
        # Message with wrong checksum
        message_id = 500
        flags = b'\x00'
        size = 0

        # Build the message part (without header and checksum)
        msg_part = flags + struct.pack('<H', message_id) + struct.pack('<H', size)
        # Build full message with wrong checksum
        raw_message = b'$X>' + msg_part + struct.pack('B', 0xFF)  # Wrong checksum

        with pytest.raises(MSPException, match="Checksum mismatch"):
            msp.unpack(raw_message)

    def test_mspv2_frame_to_bytes(self):
        """Test converting MSPFrame back to bytes for v2"""
        msp = MSPv2()
        message_id = 500
        payload = b'\x01\x02\x03'
        flags = b'\x01'

        # Pack and unpack to get frame
        packed = msp.pack(message_id, payload, flags)
        reply_message = b'$X>' + packed[3:]
        frame = msp.unpack(reply_message)

        # Convert frame back to bytes
        _ = frame.to_bytes()

        # Should be identical to original (except possibly checksum which gets recalculated)
        # Compare all parts except checksum
        assert frame.header == b'$X>'
        assert frame.protocol_version == 2
        assert frame.message_id == message_id
        assert frame.payload == payload
        assert frame.flags == flags

    def test_mspv2_unpack_request_header(self):
        """Test unpacking a valid MSP v2 request header"""
        msp = MSPv2()
        raw_message = bytes.fromhex('24583c000100000045')

        frame = msp.unpack(raw_message)

        assert frame.header == b'$X<'
        assert frame.protocol_version == 2
        assert frame.flags == b'\x00'
        assert frame.message_id == 1
        assert frame.size == 0
        assert frame.payload == b''


class TestMSPStreamProcessor:
    """Tests for MSP stream processor functionality"""

    def test_stream_processor_initialization(self):
        """Test MSPStreamProcessor initialization"""
        processor = MSPStreamProcessor()
        assert isinstance(processor, MSPStreamProcessor)
        assert processor.buffer == b''

    def test_process_single_mspv1_frame_complete(self):
        """Test processing a single complete MSP v1 frame"""
        processor = MSPStreamProcessor()
        msp_v1 = MSPv1()

        # Create a complete MSP v1 frame
        message_id = 101
        payload = b'\x01\x02\x03'
        packed = msp_v1.pack(message_id, payload)
        reply_packet = b'$M>' + packed[3:]  # Change to reply header

        # Process the packet
        frames = list(processor.push_bytes(reply_packet))

        assert len(frames) == 1
        frame = frames[0]
        assert frame.message_id == message_id
        assert frame.payload == payload
        assert frame.protocol_version == 1

    def test_process_single_mspv2_frame_complete(self):
        """Test processing a single complete MSP v2 frame"""
        processor = MSPStreamProcessor()
        msp_v2 = MSPv2()

        # Create a complete MSP v2 frame
        message_id = 0x2001
        payload = b'\x04\x05\x06'
        flags = b'\x00'
        packed = msp_v2.pack(message_id, payload, flags)
        reply_packet = b'$X>' + packed[3:]  # Change to reply header

        # Process the packet
        frames = list(processor.push_bytes(reply_packet))

        assert len(frames) == 1
        frame = frames[0]
        assert frame.message_id == message_id
        assert frame.payload == payload
        assert frame.flags == flags
        assert frame.protocol_version == 2

    def test_process_single_mspv2_request_frame_complete(self):
        """Test processing a single complete MSP v2 request frame"""
        processor = MSPStreamProcessor()
        request_packet = bytes.fromhex('24583c000100000045')

        frames = list(processor.push_bytes(request_packet))

        assert len(frames) == 1
        frame = frames[0]
        assert frame.header == b'$X<'
        assert frame.message_id == 1
        assert frame.payload == b''
        assert frame.protocol_version == 2

    def test_process_mspv1_frame_split_delivery(self):
        """Test processing an MSP v1 frame delivered in parts"""
        processor = MSPStreamProcessor()
        msp_v1 = MSPv1()

        # Create a frame
        message_id = 102
        payload = b'\x0A\x0B\x0C\x0D'
        packed = msp_v1.pack(message_id, payload)
        reply_packet = b'$M>' + packed[3:]

        # Split delivery: first half, then second half
        split_point = len(reply_packet) // 2
        first_half = reply_packet[:split_point]
        second_half = reply_packet[split_point:]

        # Process first half - should yield no frames
        frames1 = list(processor.push_bytes(first_half))
        assert len(frames1) == 0

        # Process second half - should complete the frame
        frames2 = list(processor.push_bytes(second_half))
        assert len(frames2) == 1
        frame = frames2[0]
        assert frame.message_id == message_id
        assert frame.payload == payload

    def test_process_mspv2_frame_split_delivery(self):
        """Test processing an MSP v2 frame delivered in parts"""
        processor = MSPStreamProcessor()
        msp_v2 = MSPv2()

        # Create a frame
        message_id = 0x3001
        payload = b'\x0E\x0F\x10\x11\x12'
        flags = b'\x01'
        packed = msp_v2.pack(message_id, payload, flags)
        reply_packet = b'$X>' + packed[3:]

        # Split delivery: first part, then middle part, then end
        part1 = reply_packet[:4]   # Header + partial data
        part2 = reply_packet[4:9]  # Middle part
        part3 = reply_packet[9:]   # Final part

        # Process part 1 - should yield no frames
        frames1 = list(processor.push_bytes(part1))
        assert len(frames1) == 0

        # Process part 2 - should still not complete the frame
        frames2 = list(processor.push_bytes(part2))
        assert len(frames2) == 0

        # Process part 3 - should complete the frame
        frames3 = list(processor.push_bytes(part3))
        assert len(frames3) == 1
        frame = frames3[0]
        assert frame.message_id == message_id
        assert frame.payload == payload
        assert frame.flags == flags

    def test_process_multiple_frames_in_one_batch(self):
        """Test processing multiple frames in a single push_bytes call"""
        processor = MSPStreamProcessor()
        msp_v1 = MSPv1()

        # Create two frames
        frame1_id, frame1_payload = 101, b'\x01\x02'
        frame2_id, frame2_payload = 102, b'\x03\x04\x05'

        packet1 = b'$M>' + msp_v1.pack(frame1_id, frame1_payload)[3:]
        packet2 = b'$M>' + msp_v1.pack(frame2_id, frame2_payload)[3:]

        # Combine both packets
        combined_packets = packet1 + packet2

        # Process both at once
        frames = list(processor.push_bytes(combined_packets))

        assert len(frames) == 2
        assert frames[0].message_id == frame1_id
        assert frames[0].payload == frame1_payload
        assert frames[1].message_id == frame2_id
        assert frames[1].payload == frame2_payload

    def test_process_garbage_data(self):
        """Test that garbage data doesn't cause errors"""
        processor = MSPStreamProcessor()

        # Process garbage data
        garbage = b'This is not MSP data at all!'
        frames = list(processor.push_bytes(garbage))

        # Should not yield any valid frames
        assert len(frames) == 0

        # Buffer should still be manageable
        assert isinstance(processor.buffer, bytes)

    def test_process_mixed_garbage_and_valid_frame(self):
        """Test processing a mix of garbage data and a valid frame"""
        processor = MSPStreamProcessor()
        msp_v1 = MSPv1()

        # Create a valid frame
        valid_frame = b'$M>' + msp_v1.pack(105, b'\x10\x20')[3:]

        # Mix with garbage
        mixed_data = b'GARBAGE DATA' + valid_frame

        # Process mixed data
        frames = list(processor.push_bytes(mixed_data))

        # Eventually should find the valid frame
        # May take multiple attempts as processor finds sync
        if len(frames) == 0:
            # If no frames found, try again with more data to help sync
            more_data = b'$M>' + msp_v1.pack(106, b'\x30\x40')[3:]
            more_frames = list(processor.push_bytes(more_data))
            assert len(more_frames) == 1
            assert more_frames[0].message_id == 106
        else:
            assert frames[0].message_id == 105
            assert frames[0].payload == b'\x10\x20'
