#!/usr/bin/env python3
"""
Helper Functions
"""

import random
import string

def generate_random_string(length=10):
    """Generate random string"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def validate_ip(ip):
    """Validate IP address"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True