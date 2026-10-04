#!/usr/bin/env python3
"""
Base Encoder Class
"""

class BaseEncoder:
    def __init__(self):
        self.name = "Base Encoder"
    
    def encode(self, payload):
        """Encode payload - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement encode method")
    
    def decode_stub(self):
        """Generate decode stub - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement decode_stub method")