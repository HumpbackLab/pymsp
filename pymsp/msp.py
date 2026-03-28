"""
MSP (MultiWii Serial Protocol) implementation for packing and unpacking messages.

Based on the MSP protocol used in INAV and Betaflight flight controllers.
"""

from dataclasses import dataclass
from enum import IntEnum
import struct
from typing import Iterator, Optional


@dataclass
class MSPFrame:
    """Generic MSP frame structure containing all components of a message"""
    header: bytes
    size: int
    flags: bytes  # Will be b'' for MSP v1
    message_id: int
    payload: bytes
    checksum: int
    protocol_version: int  # 1 for MSPv1, 2 for MSPv2

    def to_bytes(self) -> bytes:
        """Convert the frame back to bytes format"""
        if self.protocol_version == 1:
            # MSP v1 format: header + size + message_id + payload + checksum
            msg_data = struct.pack('<B', self.size)
            msg_data += struct.pack('<B', self.message_id)
            msg_data += self.payload
            return self.header + msg_data + struct.pack('<B', self.checksum)
        else:  # MSP v2
            # MSP v2 format: header + flags + message_id + size + payload + checksum
            msg_data = self.flags
            msg_data += struct.pack('<H', self.message_id)
            msg_data += struct.pack('<H', self.size)
            msg_data += self.payload
            return self.header + msg_data + struct.pack('<B', self.checksum)


class MSPStreamProcessor:
    """
    Stream processor for MSP messages that can handle partial packets
    and return complete frames as they become available.
    """

    def __init__(self):
        self.buffer = b""
        self.msp_v1 = MSPv1()
        self.msp_v2 = MSPv2()

    def push_bytes(self, new_bytes: bytes) -> Iterator[Optional[MSPFrame]]:
        """
        Push new bytes into the stream and return an iterator for any complete frames.

        Args:
            new_bytes: Bytes to add to the stream

        Yields:
            MSPFrame for each complete frame found, or None if buffer doesn't contain complete frame
        """
        self.buffer += new_bytes

        while True:
            frame = self._try_extract_frame()
            if frame is not None:
                yield frame
            else:
                # No more complete frames in buffer
                break

    def _try_extract_frame(self) -> Optional[MSPFrame]:
        """
        Try to extract a complete frame from the current buffer.

        Returns:
            MSPFrame if a complete frame is found, None otherwise
        """
        header_pos = self._find_first_header()
        if header_pos == -1:
            if len(self.buffer) > 2:
                self.buffer = self.buffer[-2:]
            return None

        if header_pos > 0:
            self.buffer = self.buffer[header_pos:]

        if len(self.buffer) < 6:
            return None

        if self.buffer.startswith((b'$M<', b'$M>')):
            size = self.buffer[3]
            required_length = 3 + 1 + 1 + size + 1
            parser = self.msp_v1
        elif self.buffer.startswith((b'$X<', b'$X>')):
            if len(self.buffer) < 9:
                return None
            size = struct.unpack('<H', self.buffer[6:8])[0]
            required_length = 3 + 1 + 2 + 2 + size + 1
            parser = self.msp_v2
        else:
            self.buffer = self.buffer[1:]
            return None

        if len(self.buffer) < required_length:
            return None

        potential_frame = self.buffer[:required_length]
        try:
            frame = parser.unpack(potential_frame)
            self.buffer = self.buffer[required_length:]
            return frame
        except MSPException:
            self.buffer = self.buffer[1:]
            return None

    def _find_first_header(self) -> int:
        positions = []
        for header in (b'$M<', b'$M>', b'$X<', b'$X>'):
            pos = self.buffer.find(header)
            if pos != -1:
                positions.append(pos)
        if not positions:
            return -1
        return min(positions)


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

    def unpack(self, raw_message: bytes) -> MSPFrame:
        """
        Unpack MSP v1 message.

        Args:
            raw_message: Raw MSP message to unpack

        Returns:
            MSPFrame object containing all components of the message

        Raises:
            MSPException: If message is malformed
        """
        if len(raw_message) < 6:  # Minimum length: header(3) + size(1) + id(1) + checksum(1)
            raise MSPException("Message too short to be valid MSP v1")

        # Check header
        if not raw_message.startswith((self.MSP_HEADER_REPLY, self.MSP_HEADER_STARTER)):
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

        # Return the complete frame
        return MSPFrame(
            header=raw_message[:3],
            size=size,
            flags=b'',  # No flags in MSP v1
            message_id=message_id,
            payload=payload,
            checksum=checksum,
            protocol_version=1
        )


class MSPv2:
    """MSP v2 protocol implementation"""

    MSP_HEADER_STARTER = b'$X<'  # $ (start) X (version) < (direction: to FC)
    MSP_HEADER_REPLY = b'$X>'   # $ (start) X (version) # > (direction: from FC)

    def __init__(self):
        pass

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        Calculate checksum for MSP v2 protocol (CRC8-DVB-S2).

        Args:
            data: Data to calculate checksum for

        Returns:
            Checksum value
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
            for _ in range(8):
                if checksum & 0x80:
                    checksum = ((checksum << 1) ^ 0xD5) & 0xFF
                else:
                    checksum = (checksum << 1) & 0xFF
        return checksum

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

        if len(flags) != 1:
            raise MSPException(f"Invalid flags length: {len(flags)}. Must be exactly 1 byte.")

        # Create the message without header
        # Format: flags(1 byte) + message_id(2 bytes) + size(2 bytes) + payload
        size = len(payload)
        msg_data = flags
        msg_data += struct.pack('<H', message_id)   # Message ID (little endian)
        msg_data += struct.pack('<H', size)         # Size (little endian)
        msg_data += payload                         # Payload

        # Calculate checksum
        checksum = self.calculate_checksum(msg_data)

        # Create full message with header
        message = self.MSP_HEADER_STARTER + msg_data + struct.pack('<B', checksum)

        return message

    def unpack(self, raw_message: bytes) -> MSPFrame:
        """
        Unpack MSP v2 message.

        Args:
            raw_message: Raw MSP message to unpack

        Returns:
            MSPFrame object containing all components of the message

        Raises:
            MSPException: If message is malformed
        """
        if not raw_message.startswith((self.MSP_HEADER_REPLY, self.MSP_HEADER_STARTER)):
            raise MSPException("Invalid MSP v2 header")

        if len(raw_message) < 9:  # Minimum length: header(3) + flags(1) + id(2) + size(2) + checksum(1)
            raise MSPException("Message too short to be valid MSP v2")

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

        # Format: flags(1 byte) + message_id(2 bytes) + size(2 bytes) + payload
        flags = msg_part_for_checksum[:1]
        message_id = struct.unpack('<H', msg_part_for_checksum[1:3])[0]
        size = struct.unpack('<H', msg_part_for_checksum[3:5])[0]
        payload = msg_part_for_checksum[5:5 + size] if size > 0 else b''

        if len(payload) != size:
            raise MSPException(f"Payload size mismatch: expected {size}, got {len(payload)}")

        # Return the complete frame
        return MSPFrame(
            header=raw_message[:3],
            size=size,
            flags=flags,
            message_id=message_id,
            payload=payload,
            checksum=checksum,
            protocol_version=2
        )
