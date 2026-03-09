"""
PyMSP - Python library for MSP (MultiWii Serial Protocol) handling

This library provides tools to pack and unpack MSP protocol messages.
"""

from .msp import MSPv1, MSPv2, MSPException

__version__ = "0.1.0"
__author__ = "PyMSP Contributors"
__all__ = ["MSPv1", "MSPv2", "MSPException"]