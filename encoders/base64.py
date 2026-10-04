#!/usr/bin/env python3
"""
Base64 Encoder
"""

import base64

class Base64Encoder:
    def encode(self, payload):
        """Base64 encode payload"""
        if isinstance(payload, str):
            payload = payload.encode()
        return base64.b64encode(payload).decode()