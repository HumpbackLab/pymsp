# PyMSP

PyMSP is a Python library for handling MSP (MultiWii Serial Protocol) messages. It supports both MSP v1 and MSP v2 protocols used in flight controllers like INAV and Betaflight. The library features a unified MSPFrame type for handling both MSP v1 and v2 messages, plus streaming MSP data processing with MSPStreamProcessor.

## Features

- Pack MSP v1 and v2 messages
- Unpack MSP v1 and v2 messages with the unified MSPFrame type
- Support for payloads and flags
- Checksum validation
- Comprehensive error handling
- Unified MSPFrame class for consistent handling of both MSP versions
- MSPStreamProcessor for handling streaming MSP data with partial frame support
- Garbage data recovery and synchronization
- Support for both MSP v1 and v2 protocols in streaming mode

## Implementation Details

### MSP v1 Support
- Header format: `$M<` (to FC) and `$M>` (from FC)
- Size field: 1 byte (max 255 bytes payload)
- Message ID: 1 byte (0-255)
- Checksum: XOR of all data bytes
- Proper error handling for oversized payloads

### MSP v2 Support
- Header format: `$X<` (to FC) and `$X>` (from FC)
- Size field: 2 bytes (little endian, max 65535 bytes payload)
- Message ID: 2 bytes (little endian, 0-65535)
- Flags: 1 byte
- Checksum: XOR of all data bytes

### Unified MSPFrame Type
- New `MSPFrame` dataclass that represents both MSP v1 and v2 messages
- Provides uniform interface for handling different MSP versions
- Includes all frame components: header, size, flags, message_id, payload, checksum, and protocol_version

### MSPStreamProcessor
- Handles streaming MSP data with partial frame delivery support
- Recovers from garbage data in the stream
- Processes both MSP v1 and v2 frames in the same stream
- Implements the `push_bytes` method that accepts new data and yields complete frames as they become available

## Installation

```bash
pip install pymsp
```

## Usage

### Packing MSP v1 Messages

```python
from pymsp.msp import MSPv1

msp_v1 = MSPv1()
# Pack a message with ID 101 and payload
packed_message = msp_v1.pack(101, b'\x01\x02\x03\x04')
print(packed_message)
```

### Unpacking MSP v1 Messages with MSPFrame

```python
from pymsp.msp import MSPv1, MSPFrame

msp_v1 = MSPv1()
# Unpack a message - now returns an MSPFrame object
frame: MSPFrame = msp_v1.unpack(b'$M>\x03\x65\x01\x02\x03\x8c')
print(f"Message ID: {frame.message_id}")
print(f"Payload: {frame.payload}")
print(f"Protocol: v{frame.protocol_version}")
print(f"Size: {frame.size}")
print(f"Header: {frame.header}")
```

### Packing MSP v2 Messages

```python
from pymsp.msp import MSPv2

msp_v2 = MSPv2()
# Pack a message with ID 200 and payload
packed_message = msp_v2.pack(200, b'\x01\x02\x03\x04')
print(packed_message)
```

### Unpacking MSP v2 Messages with MSPFrame

```python
from pymsp.msp import MSPv2, MSPFrame

msp_v2 = MSPv2()
# Unpack a message - now returns an MSPFrame object
frame: MSPFrame = msp_v2.unpack(b'$X>\x03\x00\xc8\x00\x01\x02\x03\x8c')
print(f"Message ID: {frame.message_id}")
print(f"Payload: {frame.payload}")
print(f"Flags: {frame.flags}")
print(f"Protocol: v{frame.protocol_version}")
print(f"Size: {frame.size}")
```

### Using the to_bytes Method

Both MSP v1 and v2 frames can be converted back to bytes:

```python
from pymsp.msp import MSPv1

msp_v1 = MSPv1()
# Pack and unpack a message
packed_message = msp_v1.pack(101, b'\x01\x02\x03\x04')
frame = msp_v1.unpack(b'$M>' + packed_message[3:])

# Convert frame back to bytes
bytes_again = frame.to_bytes()
print(bytes_again)
```

### Streaming MSP Data Processing

The MSPStreamProcessor handles streaming MSP data, including:
- Partial frame delivery (frames split across multiple reads)
- Multiple frames in a single data chunk
- Garbage data recovery
- Both MSP v1 and v2 protocol support

```python
from pymsp.msp import MSPStreamProcessor, MSPFrame

# Create a stream processor
processor = MSPStreamProcessor()

# Process incoming data in chunks
data_chunk1 = b"GARBAGE$data"  # May include non-MSP data
data_chunk2 = b"$M>\x04\x65\x01\x02\x03\x04\x65"  # Complete MSP v1 frame
data_chunk3 = b"$X>\x04\x00\x01\x00\x0B\x01\x02\x03\x04\x1B"  # Complete MSP v2 frame

# Process each chunk and collect frames
all_frames = []
for chunk in [data_chunk1, data_chunk2, data_chunk3]:
    frames = list(processor.push_bytes(chunk))
    all_frames.extend(frames)

# Process the collected frames
for frame in all_frames:
    print(f"MSP {frame.protocol_version} Frame - ID: {frame.message_id}, Payload: {frame.payload.hex()}")
```

## Development & Testing

### TDD Approach
- Implemented following TDD principles
- Started with API specification and test cases
- Developed implementation to meet test requirements
- All tests pass (34/34 including streaming processor tests)
- Comprehensive coverage of functionality and edge cases

### Key Features
- Comprehensive pack/unpack functionality for both protocols
- Strict validation of message format and integrity
- Proper header recognition and generation
- Accurate checksum calculation and verification
- Detailed error handling with MSPException
- Unified MSPFrame for consistent handling of both MSP versions
- MSPStreamProcessor for streaming data handling with partial frame support
- Garbage data recovery and synchronization capability

### Files Structure
- `pymsp/__init__.py` - Package initialization
- `pymsp/msp.py` - Main MSP implementation with MSPFrame and MSPStreamProcessor
- `tests/test_msp.py` - Complete API specification and unit tests
- `tests/test_comprehensive.py` - Edge case and integration tests
- `example_usage.py` - Demonstration script with MSPFrame usage

## API Reference

### MSPv1 Class

Handles MSP v1 protocol messages.

#### Methods

- `pack(message_id, payload=b'')`: Packs a message with the given ID and payload.
- `unpack(raw_message)`: Unpacks a raw MSP message, returning an MSPFrame object.

### MSPv2 Class

Handles MSP v2 protocol messages.

#### Methods

- `pack(message_id, payload=b'', flags=b'\\x00')`: Packs a message with the given ID, payload, and flags.
- `unpack(raw_message)`: Unpacks a raw MSP message, returning an MSPFrame object.

### MSPFrame Class

Unified class representing both MSP v1 and v2 messages.

#### Attributes

- `header`: Message header bytes
- `size`: Size of the payload
- `flags`: Flags (for MSP v2), empty for MSP v1
- `message_id`: Message identifier
- `payload`: Message payload bytes
- `checksum`: Checksum value
- `protocol_version`: 1 for MSP v1, 2 for MSP v2

#### Methods

- `to_bytes()`: Converts the frame back to raw bytes format

### MSPStreamProcessor Class

Handles streaming MSP data with support for partial frames.

#### Methods

- `__init__()`: Creates a new stream processor with internal buffer
- `push_bytes(new_bytes)`: Processes new bytes and yields complete MSPFrame objects as they become available

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT