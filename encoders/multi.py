#!/usr/bin/env python3
"""
Multi-Encoder
"""

from encoders.xor import XOREncoder
from encoders.base64 import Base64Encoder

class MultiEncoder:
    def encode(self, payload):
        """Apply multiple encoding layers"""
        encoders = [XOREncoder(), Base64Encoder()]
        
        for encoder in encoders:
            payload = encoder.encode(payload)
        
        return payload