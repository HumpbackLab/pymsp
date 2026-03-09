"""
MSP (MultiWii Serial Protocol) implementation for packing and unpacking messages.

Based on the MSP protocol used in INAV and Betaflight flight controllers.
"""

import struct
from enum import IntEnum
from typing import Union, Tuple, Optional


class MSPException(Exception):
    """Base exception for MSP-related errors."""
    pass


class MSPFlag(IntEnum):
    """MSP flag values"""
    MSP_V1 = 0
    MSP_V2 = 1


class MSPv1:
    """MSP v1 protocol implementation"""

    MSP_HEADER_STARTER = b'$M<'
    MSP_HEADER_REPLY = b'$M>'

    def __init__(self):
        pass

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        Calculate checksum for MSP v1 protocol.

        Args:
            data: Data to calculate checksum for

        Returns:
            Checksum value
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum & 0xFF

    def pack(self, message_id: int, payload: bytes = b'') -> bytes:
        """
        Pack MSP v1 message.

        Args:
            message_id: MSP message ID
            payload: Message payload data

        Returns:
            Packed MSP message as bytes
        """
        # Ensure message_id is in valid range
        if not 0 <= message_id <= 255:
            raise MSPException(f"Invalid message ID: {message_id}. Must be between 0-255")

        # Ensure payload size is in valid range for MSP v1 (size field is 1 byte, max 255)
        if len(payload) > 255:
            raise MSPException(f"Payload too large for MSP v1: {len(payload)} bytes. Maximum is 255 bytes.")

        # Create the message without header
        msg_data = struct.pack('<B', len(payload))  # Size
        msg_data += struct.pack('<B', message_id)  # Message ID
        msg_data += payload  # Payload

        # Calculate checksum
        checksum = self.calculate_checksum(msg_data)

        # Create full message with header
        message = self.MSP_HEADER_STARTER + msg_data + struct.pack('<B', checksum)

        return message

    def unpack(self, raw_message: bytes) -> Tuple[int, bytes]:
        """
        Unpack MSP v1 message.

        Args:
            raw_message: Raw MSP message to unpack

        Returns:
            Tuple of (message_id, payload)

        Raises:
            MSPException: If message is malformed
        """
        if len(raw_message) < 6:  # Minimum length: header(3) + size(1) + id(1) + checksum(1)
            raise MSPException("Message too short to be valid MSP v1")

        # Check header
        if not raw_message.startswith(self.MSP_HEADER_REPLY):
            raise MSPException("Invalid MSP v1 header")

        # Extract message components (skip header)
        message_data = raw_message[3:]
        size = message_data[0]
        message_id = message_data[1]
        payload = message_data[2:2+size] if size > 0 else b''
        checksum = message_data[2+size]

        # Verify checksum
        expected_checksum = self.calculate_checksum(message_data[:-1])
        if checksum != expected_checksum:
            raise MSPException(f"Checksum mismatch: expected {expected_checksum:#02x}, got {checksum:#02x}")

        if len(payload) != size:
            raise MSPException(f"Payload size mismatch: expected {size}, got {len(payload)}")

        return message_id, payload


class MSPv2:
    """MSP v2 protocol implementation"""

    MSP_HEADER_STARTER = b'$X<'  # $ (start) X (version) < (direction: to FC)
    MSP_HEADER_REPLY = b'$X>'   # $ (start) X (version) # > (direction: from FC)

    def __init__(self):
        pass

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        Calculate checksum for MSP v2 protocol (simple XOR of all bytes).

        Args:
            data: Data to calculate checksum for

        Returns:
            Checksum value
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum & 0xFF

    def pack(self, message_id: int, payload: bytes = b'', flags: bytes = b'\x00') -> bytes:
        """
        Pack MSP v2 message.

        Args:
            message_id: MSP message ID (16-bit)
            payload: Message payload data
            flags: Additional flags (optional)

        Returns:
            Packed MSP message as bytes
        """
        # Ensure message_id is in valid range
        if not 0 <= message_id <= 0xFFFF:
            raise MSPException(f"Invalid message ID: {message_id}. Must be between 0-65535")

        # Create the message without header
        # Format: size(2 bytes) + flags(1 byte) + message_id(2 bytes) + payload
        size = len(payload)
        msg_data = struct.pack('<H', size)  # Size (little endian)
        msg_data += flags                   # Flags
        msg_data += struct.pack('<H', message_id)  # Message ID (little endian)
        msg_data += payload                 # Payload

        # Calculate checksum
        checksum = self.calculate_checksum(msg_data)

        # Create full message with header
        message = self.MSP_HEADER_STARTER + msg_data + struct.pack('<B', checksum)

        return message

    def unpack(self, raw_message: bytes) -> Tuple[int, bytes, bytes]:
        """
        Unpack MSP v2 message.

        Args:
            raw_message: Raw MSP message to unpack

        Returns:
            Tuple of (message_id, payload, flags)

        Raises:
            MSPException: If message is malformed
        """
        if len(raw_message) < 8:  # Minimum length: header(3) + size(2) + flags(1) + id(2) + checksum(1)
            raise MSPException("Message too short to be valid MSP v2")

        # Check header
        if not raw_message.startswith(self.MSP_HEADER_REPLY):
            raise MSPException("Invalid MSP v2 header")

        # Extract message components (skip header)
        message_data = raw_message[3:]
        checksum_idx = len(message_data) - 1

        # Extract checksum
        checksum = message_data[checksum_idx]

        # The message part for checksum calculation excludes the checksum itself
        msg_part_for_checksum = message_data[:checksum_idx]

        # Verify checksum
        expected_checksum = self.calculate_checksum(msg_part_for_checksum)
        if checksum != expected_checksum:
            raise MSPException(f"Checksum mismatch: expected {expected_checksum:#02x}, got {checksum:#02x}")

        # Now parse the message data
        size = struct.unpack('<H', msg_part_for_checksum[:2])[0]  # Size is first 2 bytes
        flags = msg_part_for_checksum[2:3]                        # Flags is 1 byte
        message_id = struct.unpack('<H', msg_part_for_checksum[3:5])[0]  # Message ID is 2 bytes
        payload = msg_part_for_checksum[5:5+size] if size > 0 else b''  # Payload follows

        if len(payload) != size:
            raise MSPException(f"Payload size mismatch: expected {size}, got {len(payload)}")

        return message_id, payload, flags