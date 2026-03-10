"""
Example usage of the PyMSP library.

This script demonstrates how to use the PyMSP library to pack and unpack
MSP v1 and MSP v2 protocol messages using the new unified MSPFrame type.
"""
from pymsp.msp import MSPv1, MSPv2, MSPFrame, MSPException


def example_mspv1():
    """Example of MSP v1 usage with the new MSPFrame type"""
    print("=== MSP v1 Example with MSPFrame ===")

    # Create an MSP v1 instance
    msp_v1 = MSPv1()

    # Pack a message (e.g., MSP_STATUS with ID 101)
    message_id = 101  # MSP_STATUS
    payload = b'\x01\x02\x03\x04'  # Example payload
    packed_message = msp_v1.pack(message_id, payload)

    print(f"Packed message: {packed_message.hex()}")
    print(f"Packed message (readable): {packed_message}")

    # Change the header to reply format for unpacking
    reply_message = b'$M>' + packed_message[3:]

    # Unpack the message using the new MSPFrame type
    try:
        frame: MSPFrame = msp_v1.unpack(reply_message)

        print(f"Unpacked as MSPFrame:")
        print(f"  - Header: {frame.header}")
        print(f"  - Size: {frame.size}")
        print(f"  - Message ID: {frame.message_id}")
        print(f"  - Payload: {frame.payload.hex()}")
        print(f"  - Checksum: 0x{frame.checksum:02x}")
        print(f"  - Protocol Version: {frame.protocol_version}")
        print(f"  - Flags: {frame.flags}")

        # Test the to_bytes method
        repacked = frame.to_bytes()
        print(f"Repacked from frame: {repacked.hex()}")

    except MSPException as e:
        print(f"Error unpacking message: {e}")

    print()


def example_mspv2():
    """Example of MSP v2 usage with the new MSPFrame type"""
    print("=== MSP v2 Example with MSPFrame ===")

    # Create an MSP v2 instance
    msp_v2 = MSPv2()

    # Pack a message (e.g., MSP2_COMMON_SERIAL_CONFIG with ID 0x100B)
    message_id = 0x100B  # Example MSP v2 message ID
    payload = b'\x01\x02\x03\x04'  # Example payload
    flags = b'\x00'  # Example flags

    packed_message = msp_v2.pack(message_id, payload, flags)

    print(f"Packed message: {packed_message.hex()}")
    print(f"Packed message (readable): {packed_message}")

    # Change the header to reply format for unpacking
    reply_message = b'$X>' + packed_message[3:]

    # Unpack the message using the new MSPFrame type
    try:
        frame: MSPFrame = msp_v2.unpack(reply_message)

        print(f"Unpacked as MSPFrame:")
        print(f"  - Header: {frame.header}")
        print(f"  - Size: {frame.size}")
        print(f"  - Flags: {frame.flags.hex()}")
        print(f"  - Message ID: {frame.message_id}")
        print(f"  - Payload: {frame.payload.hex()}")
        print(f"  - Checksum: 0x{frame.checksum:02x}")
        print(f"  - Protocol Version: {frame.protocol_version}")

        # Test the to_bytes method
        repacked = frame.to_bytes()
        print(f"Repacked from frame: {repacked.hex()}")

    except MSPException as e:
        print(f"Error unpacking message: {e}")

    print()


def example_roundtrip():
    """Example showing pack/unpack roundtrip with MSPFrame"""
    print("=== Roundtrip Example with MSPFrame ===")

    # MSP v1 roundtrip
    msp_v1 = MSPv1()
    original_id = 101  # MSP_RAW_IMU
    original_payload = b'\x01\x02\x03\x04\x05'

    print("--- MSP v1 Roundtrip ---")
    packed = msp_v1.pack(original_id, original_payload)
    print(f"Packed: {packed.hex()}")

    # Simulate changing header from starter to reply format for unpacking
    reply_format = b'$M>' + packed[3:]

    # Unpack with new MSPFrame
    frame = msp_v1.unpack(reply_format)

    print(f"Original ID: {original_id}, Unpacked ID: {frame.message_id}")
    print(f"Original payload: {original_payload.hex()}, Unpacked payload: {frame.payload.hex()}")
    print(f"Protocol version: {frame.protocol_version}")
    print(f"Match: {original_id == frame.message_id and original_payload == frame.payload}")

    # MSP v2 roundtrip
    msp_v2 = MSPv2()
    original_id_v2 = 0x2001  # Example MSP v2 ID
    original_payload_v2 = b'\x0A\x0B\x0C'
    original_flags_v2 = b'\x01'

    print("\n--- MSP v2 Roundtrip ---")
    packed_v2 = msp_v2.pack(original_id_v2, original_payload_v2, original_flags_v2)
    print(f"Packed: {packed_v2.hex()}")

    # Simulate changing header from starter to reply format for unpacking
    reply_format_v2 = b'$X>' + packed_v2[3:]

    # Unpack with new MSPFrame
    frame_v2 = msp_v2.unpack(reply_format_v2)

    print(f"Original ID: {original_id_v2}, Unpacked ID: {frame_v2.message_id}")
    print(f"Original payload: {original_payload_v2.hex()}, Unpacked payload: {frame_v2.payload.hex()}")
    print(f"Original flags: {original_flags_v2.hex()}, Unpacked flags: {frame_v2.flags.hex()}")
    print(f"Protocol version: {frame_v2.protocol_version}")
    print(f"Match: {original_id_v2 == frame_v2.message_id and original_payload_v2 == frame_v2.payload and original_flags_v2 == frame_v2.flags}")

    print()


def example_mixed_handling():
    """Example showing how to handle both MSP v1 and v2 with the same MSPFrame type"""
    print("=== Mixed MSP v1/v2 Handling with Unified MSPFrame ===")

    msp_v1 = MSPv1()
    msp_v2 = MSPv2()

    # Pack messages with both versions
    v1_msg = msp_v1.pack(101, b'\x01\x02\x03')  # MSP_STATUS
    v2_msg = msp_v2.pack(0x2001, b'\x04\x05\x06', b'\x00')  # Some MSP v2 message

    # Convert to reply format
    v1_reply = b'$M>' + v1_msg[3:]
    v2_reply = b'$X>' + v2_msg[3:]

    # Process both with the same approach, getting MSPFrame objects
    v1_frame = msp_v1.unpack(v1_reply)
    v2_frame = msp_v2.unpack(v2_reply)

    print("Processing MSP v1 frame:")
    print(f"  - Protocol: v{v1_frame.protocol_version}")
    print(f"  - ID: {v1_frame.message_id}")
    print(f"  - Payload: {v1_frame.payload.hex()}")
    print(f"  - Has flags: {v1_frame.flags != b''}")

    print("\nProcessing MSP v2 frame:")
    print(f"  - Protocol: v{v2_frame.protocol_version}")
    print(f"  - ID: {v2_frame.message_id}")
    print(f"  - Payload: {v2_frame.payload.hex()}")
    print(f"  - Flags: {v2_frame.flags.hex()}")

    # Demonstrate how to handle both frames uniformly
    frames = [v1_frame, v2_frame]
    print("\nProcessing both frames uniformly:")
    for i, frame in enumerate(frames):
        print(f"  Frame {i+1}: v{frame.protocol_version}, ID {frame.message_id}, {frame.size} bytes")

    print()


if __name__ == "__main__":
    example_mspv1()
    example_mspv2()
    example_roundtrip()
    example_mixed_handling()