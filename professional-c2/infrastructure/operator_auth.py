#!/usr/bin/env python3
"""
Multi-factor authentication for operator access
"""
import asyncio
import time
import hashlib
import hmac
import base64
import secrets
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import jwt
import pyotp
import qrcode
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

@dataclass
class Operator:
    """Operator account with MFA configuration"""
    username: str
    password_hash: str
    role: str = "operator"
    mfa_enabled: bool = False
    totp_secret: Optional[str] = None
    backup_codes: List[str] = None
    last_login: Optional[float] = None
    failed_attempts: int = 0
    locked_until: Optional[float] = None
    session_timeout: int = 3600  # 1 hour
    
    def __post_init__(self):
        if self.backup_codes is None:
            self.backup_codes = []

@dataclass
class AuthSession:
    """Authentication session"""
    session_id: str
    operator: Operator
    created_at: float
    last_activity: float
    ip_address: str
    user_agent: str
    mfa_verified: bool = False

class MultiFactorAuth:
    """
    Multi-factor authentication system for C2 operators
    """
    
    def __init__(self, jwt_secret: str, encryption_key: str):
        self.jwt_secret = jwt_secret
        self.encryption_key = encryption_key
        self.fernet = Fernet(encryption_key)
        
        # Operator storage (in production, use database)
        self.operators: Dict[str, Operator] = {}
        self.sessions: Dict[str, AuthSession] = {}
        
        # Security configuration
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.session_timeout = 3600  # 1 hour
        
        # Initialize with admin operator
        self._initialize_default_operator()
    
    def _initialize_default_operator(self):
        """Initialize default admin operator"""
        admin_password = self._hash_password("admin123")
        admin = Operator(
            username="admin",
            password_hash=admin_password,
            role="admin"
        )
        self.operators["admin"] = admin
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = b"professional_c2_salt"  # In production, use unique salt per user
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            new_hash = self._hash_password(password)
            return hmac.compare_digest(new_hash, password_hash)
        except Exception:
            return False
    
    def _generate_totp_secret(self) -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()
    
    def _get_totp_uri(self, username: str, secret: str, issuer: str = "Professional C2") -> str:
        """Generate TOTP URI for QR code"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username, 
            issuer_name=issuer
        )
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA"""
        codes = []
        for _ in range(count):
            code = f"{secrets.randbelow(1000000):06d}"
            codes.append(self._hash_backup_code(code))
        return codes
    
    def _hash_backup_code(self, code: str) -> str:
        """Hash backup code for storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def _verify_backup_code(self, code: str, stored_hash: str) -> bool:
        """Verify backup code"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        return hmac.compare_digest(code_hash, stored_hash)
    
    async def register_operator(self, username: str, password: str, role: str = "operator") -> bool:
        """Register new operator"""
        if username in self.operators:
            return False
        
        password_hash = self._hash_password(password)
        operator = Operator(
            username=username,
            password_hash=password_hash,
            role=role
        )
        
        self.operators[username] = operator
        return True
    
    async def enable_mfa(self, username: str) -> Dict[str, str]:
        """Enable MFA for operator"""
        if username not in self.operators:
            raise ValueError("Operator not found")
        
        operator = self.operators[username]
        secret = self._generate_totp_secret()
        operator.totp_secret = self.fernet.encrypt(secret.encode()).decode()
        operator.mfa_enabled = True
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes()
        operator.backup_codes = backup_codes
        
        # Generate QR code URI
        totp_uri = self._get_totp_uri(username, secret)
        
        return {
            "secret": secret,  # Only show this once!
            "totp_uri": totp_uri,
            "backup_codes": [f"{i:06d}" for i in range(10)]  # Show plain codes once
        }
    
    async def disable_mfa(self, username: str) -> bool:
        """Disable MFA for operator"""
        if username not in self.operators:
            return False
        
        operator = self.operators[username]
        operator.mfa_enabled = False
        operator.totp_secret = None
        operator.backup_codes = []
        
        return True
    
    async def verify_totp(self, username: str, code: str) -> bool:
        """Verify TOTP code"""
        if username not in self.operators:
            return False
        
        operator = self.operators[username]
        if not operator.mfa_enabled or not operator.totp_secret:
            return False
        
        try:
            encrypted_secret = operator.totp_secret
            secret = self.fernet.decrypt(encrypted_secret.encode()).decode()
            totp = pyotp.TOTP(secret)
            return totp.verify(code)
        except Exception:
            return False
    
    async def verify_backup_code(self, username: str, code: str) -> bool:
        """Verify backup code"""
        if username not in self.operators:
            return False
        
        operator = self.operators[username]
        if not operator.mfa_enabled:
            return False
        
        code_hash = self._hash_backup_code(code)
        for stored_hash in operator.backup_codes:
            if hmac.compare_digest(code_hash, stored_hash):
                # Remove used backup code
                operator.backup_codes.remove(stored_hash)
                return True
        
        return False
    
    async def authenticate(self, username: str, password: str, 
                         mfa_code: Optional[str] = None, 
                         ip_address: str = "", 
                         user_agent: str = "") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Authenticate operator with optional MFA
        
        Returns: (success, session_id, error_message)
        """
        # Check if operator exists
        if username not in self.operators:
            await asyncio.sleep(1)  # Prevent timing attacks
            return False, None, "Invalid credentials"
        
        operator = self.operators[username]
        
        # Check account lockout
        if operator.locked_until and time.time() < operator.locked_until:
            remaining = int(operator.locked_until - time.time())
            return False, None, f"Account locked. Try again in {remaining} seconds"
        
        # Verify password
        if not self._verify_password(password, operator.password_hash):
            operator.failed_attempts += 1
            
            if operator.failed_attempts >= self.max_failed_attempts:
                operator.locked_until = time.time() + self.lockout_duration
                return False, None, "Account locked due to too many failed attempts"
            
            return False, None, "Invalid credentials"
        
        # Reset failed attempts on successful password auth
        operator.failed_attempts = 0
        
        # Check MFA requirement
        if operator.mfa_enabled:
            if not mfa_code:
                return False, None, "MFA code required"
            
            # Verify TOTP or backup code
            if not (await self.verify_totp(username, mfa_code) or 
                   await self.verify_backup_code(username, mfa_code)):
                operator.failed_attempts += 1
                return False, None, "Invalid MFA code"
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        session = AuthSession(
            session_id=session_id,
            operator=operator,
            created_at=time.time(),
            last_activity=time.time(),
            ip_address=ip_address,
            user_agent=user_agent,
            mfa_verified=operator.mfa_enabled
        )
        
        self.sessions[session_id] = session
        operator.last_login = time.time()
        
        # Generate JWT token
        token = self._generate_jwt_token(session)
        
        return True, token, None
    
    def _generate_jwt_token(self, session: AuthSession) -> str:
        """Generate JWT token for session"""
        payload = {
            'session_id': session.session_id,
            'username': session.operator.username,
            'role': session.operator.role,
            'mfa_verified': session.mfa_verified,
            'exp': time.time() + session.operator.session_timeout,
            'iat': time.time()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    async def verify_token(self, token: str) -> Tuple[bool, Optional[AuthSession]]:
        """Verify JWT token and return session"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            session_id = payload.get('session_id')
            
            if session_id not in self.sessions:
                return False, None
            
            session = self.sessions[session_id]
            
            # Check session expiration
            if time.time() - session.last_activity > session.operator.session_timeout:
                await self.logout(session_id)
                return False, None
            
            # Update last activity
            session.last_activity = time.time()
            
            return True, session
            
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
    
    async def logout(self, session_id: str) -> bool:
        """Logout operator session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change operator password"""
        if username not in self.operators:
            return False
        
        operator = self.operators[username]
        
        if not self._verify_password(old_password, operator.password_hash):
            return False
        
        operator.password_hash = self._hash_password(new_password)
        return True
    
    async def get_operator_info(self, username: str) -> Optional[Dict]:
        """Get operator information (without sensitive data)"""
        if username not in self.operators:
            return None
        
        operator = self.operators[username]
        return {
            "username": operator.username,
            "role": operator.role,
            "mfa_enabled": operator.mfa_enabled,
            "last_login": operator.last_login,
            "failed_attempts": operator.failed_attempts,
            "locked": bool(operator.locked_until and time.time() < operator.locked_until)
        }
    
    async def generate_qr_code(self, username: str) -> Optional[bytes]:
        """Generate QR code for MFA setup"""
        if username not in self.operators:
            return None
        
        operator = self.operators[username]
        if not operator.mfa_enabled or not operator.totp_secret:
            return None
        
        try:
            secret = self.fernet.decrypt(operator.totp_secret.encode()).decode()
            totp_uri = self._get_totp_uri(username, secret)
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
            
        except Exception:
            return None
    
    async def send_email_mfa(self, username: str, email: str) -> bool:
        """Send MFA code via email (alternative to TOTP)"""
        if username not in self.operators:
            return False
        
        # Generate one-time code
        code = f"{secrets.randbelow(1000000):06d}"
        
        # Store code with expiration (5 minutes)
        expiration = time.time() + 300
        
        # In production, store in database with expiration
        setattr(self, f"email_code_{username}", {
            "code": code,
            "expires": expiration
        })
        
        # Send email (implement with your SMTP configuration)
        try:
            await self._send_email(
                to_email=email,
                subject="Your MFA Code",
                body=f"Your verification code is: {code}\nThis code will expire in 5 minutes."
            )
            return True
        except Exception:
            return False
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email (implement with your SMTP configuration)"""
        # This is a placeholder implementation
        # In production, use proper SMTP configuration
        try:
            # Example SMTP configuration
            smtp_server = "smtp.example.com"
            smtp_port = 587
            smtp_username = "noreply@example.com"
            smtp_password = "password"
            
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # In production, use async SMTP library
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    async def verify_email_code(self, username: str, code: str) -> bool:
        """Verify email MFA code"""
        if username not in self.operators:
            return False
        
        storage_key = f"email_code_{username}"
        if not hasattr(self, storage_key):
            return False
        
        code_data = getattr(self, storage_key)
        
        # Check expiration
        if time.time() > code_data["expires"]:
            delattr(self, storage_key)
            return False
        
        # Verify code
        if code_data["code"] == code:
            delattr(self, storage_key)
            return True
        
        return False
    
    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > session.operator.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
    
    async def get_active_sessions(self) -> List[Dict]:
        """Get list of active sessions"""
        sessions = []
        for session in self.sessions.values():
            sessions.append({
                "session_id": session.session_id,
                "username": session.operator.username,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "mfa_verified": session.mfa_verified
            })
        return sessions

# Example usage and testing
async def main():
    """Example usage of MFA system"""
    # Initialize MFA system
    mfa = MultiFactorAuth(
        jwt_secret="your-jwt-secret-key",
        encryption_key=Fernet.generate_key()
    )
    
    # Register a new operator
    await mfa.register_operator("alice", "securepassword123")
    
    # Enable MFA for the operator
    mfa_setup = await mfa.enable_mfa("alice")
    print(f"MFA Secret: {mfa_setup['secret']}")
    print(f"TOTP URI: {mfa_setup['totp_uri']}")
    print(f"Backup Codes: {mfa_setup['backup_codes']}")
    
    # Authenticate with MFA (you would get the TOTP code from authenticator app)
    success, token, error = await mfa.authenticate(
        username="alice",
        password="securepassword123",
        mfa_code="123456",  # This would be from authenticator app
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0..."
    )
    
    if success:
        print("Authentication successful!")
        print(f"Token: {token}")
    else:
        print(f"Authentication failed: {error}")

if __name__ == "__main__":
    asyncio.run(main())