"""
Example usage of the PyMSP library.

This script demonstrates how to use the PyMSP library to pack and unpack
MSP v1 and MSP v2 protocol messages.
"""

from pymsp.msp import MSPv1, MSPv2, MSPException


def example_mspv1():
    """Example of MSP v1 usage"""
    print("=== MSP v1 Example ===")

    # Create an MSP v1 instance
    msp_v1 = MSPv1()

    # Pack a message (e.g., MSP_STATUS with ID 100)
    message_id = 100
    payload = b'\x01\x02\x03'  # Example payload
    packed_message = msp_v1.pack(message_id, payload)

    print(f"Packed message: {packed_message.hex()}")
    print(f"Packed message (readable): {packed_message}")

    # Unpack the message
    try:
        unpacked_id, unpacked_payload = msp_v1.unpack(packed_message.replace(b'<', b'>'))  # Replace '<' with '>' for reply
        print(f"Unpacked message ID: {unpacked_id}")
        print(f"Unpacked payload: {unpacked_payload.hex()}")
    except MSPException as e:
        print(f"Error unpacking message: {e}")

    print()


def example_mspv2():
    """Example of MSP v2 usage"""
    print("=== MSP v2 Example ===")

    # Create an MSP v2 instance
    msp_v2 = MSPv2()

    # Pack a message (e.g., MSP2_COMMON_SERIAL_CONFIG with ID 0x100B)
    message_id = 0x100B  # Example MSP v2 message ID
    payload = b'\x01\x02\x03\x04'  # Example payload
    flags = b'\x00'  # Example flags

    packed_message = msp_v2.pack(message_id, payload, flags)

    print(f"Packed message: {packed_message.hex()}")
    print(f"Packed message (readable): {packed_message}")

    # Unpack the message
    try:
        # Need to replace header for reply format
        reply_message = b'$X>' + packed_message[3:]  # Replace '<' with '>'
        unpacked_id, unpacked_payload, unpacked_flags = msp_v2.unpack(reply_message)
        print(f"Unpacked message ID: {unpacked_id}")
        print(f"Unpacked payload: {unpacked_payload.hex()}")
        print(f"Unpacked flags: {unpacked_flags.hex()}")
    except MSPException as e:
        print(f"Error unpacking message: {e}")

    print()


def example_roundtrip():
    """Example showing pack/unpack roundtrip"""
    print("=== Roundtrip Example ===")

    # MSP v1 roundtrip
    msp_v1 = MSPv1()
    original_id = 101  # MSP_RAW_IMU
    original_payload = b'\x01\x02\x03\x04\x05'

    print("--- MSP v1 Roundtrip ---")
    packed = msp_v1.pack(original_id, original_payload)
    print(f"Packed: {packed.hex()}")

    # Simulate changing header from starter to reply format for unpacking
    reply_format = b'$M>' + packed[3:]
    unpacked_id, unpacked_payload = msp_v1.unpack(reply_format)

    print(f"Original ID: {original_id}, Unpacked ID: {unpacked_id}")
    print(f"Original payload: {original_payload.hex()}, Unpacked payload: {unpacked_payload.hex()}")
    print(f"Match: {original_id == unpacked_id and original_payload == unpacked_payload}")

    # MSP v2 roundtrip
    msp_v2 = MSPv2()
    original_id = 0x2001  # Example MSP v2 ID
    original_payload = b'\x0A\x0B\x0C'
    original_flags = b'\x01'

    print("\n--- MSP v2 Roundtrip ---")
    packed = msp_v2.pack(original_id, original_payload, original_flags)
    print(f"Packed: {packed.hex()}")

    # Simulate changing header from starter to reply format for unpacking
    reply_format = b'$X>' + packed[3:]
    unpacked_id, unpacked_payload, unpacked_flags = msp_v2.unpack(reply_format)

    print(f"Original ID: {original_id}, Unpacked ID: {unpacked_id}")
    print(f"Original payload: {original_payload.hex()}, Unpacked payload: {unpacked_payload.hex()}")
    print(f"Original flags: {original_flags.hex()}, Unpacked flags: {unpacked_flags.hex()}")
    print(f"Match: {original_id == unpacked_id and original_payload == unpacked_payload and original_flags == unpacked_flags}")


if __name__ == "__main__":
    example_mspv1()
    example_mspv2()
    example_roundtrip()