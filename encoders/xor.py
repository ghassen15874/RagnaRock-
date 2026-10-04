#!/usr/bin/env python3
"""
XOR Encoder
"""

import random

class XOREncoder:
    def encode(self, payload, key=None):
        """XOR encode payload"""
        if key is None:
            key = random.randint(1, 255)
        
        if isinstance(payload, str):
            payload = payload.encode()
        
        encoded = bytes([b ^ key for b in payload])
        return f"# XOR Key: {key}\n" + ''.join([f'\\x{byte:02x}' for byte in encoded])