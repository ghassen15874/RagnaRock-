#!/usr/bin/env python3
"""
Unified Payload Generator
"""

class PayloadGenerator:
    def __init__(self, framework):
        self.framework = framework
    
    def generate(self, payload_type, lhost=None, lport=None, options=None):
        """Generate payload with encoding and formatting"""
        if options is None:
            options = {}
        
        # Parse payload type (windows/reverse_tcp)
        if '/' in payload_type:
            category, method = payload_type.split('/', 1)
        else:
            category, method = 'windows', payload_type
        
        # Get payload module
        if category not in self.framework.payloads:
            raise ValueError(f"Unknown payload category: {category}")
        
        payload_module = self.framework.payloads[category]
        if not payload_module or not hasattr(payload_module, method):
            raise ValueError(f"Unknown payload method: {method}")
        
        # Generate base payload
        payload_method = getattr(payload_module, method)
        payload = payload_method(lhost, lport, options)
        
        # Apply encoding
        if 'encoder' in options:
            payload = self.encode_payload(payload, options['encoder'])
        
        # Apply formatting
        if 'format' in options:
            payload = self.format_payload(payload, options['format'])
        
        return payload
    
    def encode_payload(self, payload, encoder_chain):
        """Apply encoding chain"""
        encoders = encoder_chain.split(',')
        
        for encoder_name in encoders:
            if encoder_name in self.framework.encoders:
                encoder = self.framework.encoders[encoder_name]
                payload = encoder.encode(payload)
        
        return payload
    
    def format_payload(self, payload, format_type):
        """Format payload output"""
        if format_type in self.framework.formatters:
            formatter = self.framework.formatters[format_type]
            return formatter.format(payload)
        
        return payload