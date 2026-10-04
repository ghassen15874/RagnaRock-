#!/usr/bin/env python3
"""
AES Encoder Module
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class AESEncoder:
    def __init__(self):
        self.name = "AES Encoder"
    
    def encode(self, payload, password=None):
        """AES encrypt payload"""
        if password is None:
            password = os.urandom(32)
        
        if isinstance(payload, str):
            payload = payload.encode()
        
        # Generate key from password
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Encrypt payload
        fernet = Fernet(key)
        encrypted = fernet.encrypt(payload)

        # Return encoded payload with salt only — NEVER include the key (fixes S2).
        # The key must be stored separately by the caller.
        result = {
            'ciphertext': base64.b64encode(encrypted).decode(),
            'salt': base64.b64encode(salt).decode(),
        }

        return f"# AES Encrypted Payload\n{result}"
    
    def decode_stub(self):
        """Generate AES decode stub"""
        return """
# AES Decode Stub
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def aes_decrypt(encrypted_data, password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data)
"""