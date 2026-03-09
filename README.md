# PyMSP

PyMSP is a Python library for handling MSP (MultiWii Serial Protocol) messages. It supports both MSP v1 and MSP v2 protocols used in flight controllers like INAV and Betaflight.

## Features

- Pack MSP v1 and v2 messages
- Unpack MSP v1 and v2 messages
- Support for payloads and flags
- Checksum validation
- Comprehensive error handling

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

## Installation

```bash
pip install pymsp
```

## Usage

### Packing MSP v1 Messages

```python
from pymsp.msp import MSPv1

msp_v1 = MSPv1()
# Pack a message with ID 100 and payload
packed_message = msp_v1.pack(100, b'\x01\x02\x03')
print(packed_message)
```

### Unpacking MSP v1 Messages

```python
from pymsp.msp import MSPv1

msp_v1 = MSPv1()
# Unpack a message
message_id, payload = msp_v1.unpack(b'$M>\x03d\x01\x02\x03\x8c')
print(f"Message ID: {message_id}")
print(f"Payload: {payload}")
```

### Packing MSP v2 Messages

```python
from pymsp.msp import MSPv2

msp_v2 = MSPv2()
# Pack a message with ID 200 and payload
packed_message = msp_v2.pack(200, b'\x01\x02\x03')
print(packed_message)
```

### Unpacking MSP v2 Messages

```python
from pymsp.msp import MSPv2

msp_v2 = MSPv2()
# Unpack a message
message_id, payload, flags = msp_v2.unpack(b'$X>\x03\x00\xc8\x00\x01\x02\x03\x8c')
print(f"Message ID: {message_id}")
print(f"Payload: {payload}")
print(f"Flags: {flags}")
```

## Development & Testing

### TDD Approach
- Implemented following TDD principles
- Started with API specification and test cases
- Developed implementation to meet test requirements
- All tests pass (25/25)
- Comprehensive coverage of functionality and edge cases

### Key Features
- Comprehensive pack/unpack functionality for both protocols
- Strict validation of message format and integrity
- Proper header recognition and generation
- Accurate checksum calculation and verification
- Detailed error handling with MSPException

### Files Structure
- `pymsp/__init__.py` - Package initialization
- `pymsp/msp.py` - Main MSP implementation
- `tests/test_msp.py` - Complete API specification and unit tests
- `tests/test_comprehensive.py` - Edge case and integration tests
- `example_usage.py` - Demonstration script

## API Reference

### MSPv1 Class

Handles MSP v1 protocol messages.

#### Methods

- `pack(message_id, payload=b'')`: Packs a message with the given ID and payload.
- `unpack(raw_message)`: Unpacks a raw MSP message, returning message ID and payload.

### MSPv2 Class

Handles MSP v2 protocol messages.

#### Methods

- `pack(message_id, payload=b'', flags=b'\\x00')`: Packs a message with the given ID, payload, and flags.
- `unpack(raw_message)`: Unpacks a raw MSP message, returning message ID, payload, and flags.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT