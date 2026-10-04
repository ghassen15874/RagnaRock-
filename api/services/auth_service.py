import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets
import os
from typing import Optional, List
from core.auth_db import AuthDatabase

# Use argon2 or bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key for JWT. In production, this should be an environment variable.
JWT_SECRET = os.environ.get("RAGNAROK_JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class AuthService:
    def __init__(self, db_path="auth.db"):
        self.db = AuthDatabase(db_path)
        # Create a default admin if no users exist
        self._ensure_admin_exists()

    def _ensure_admin_exists(self):
        # We can check if 'admin' exists, if not, create it with a default password 'admin'
        # In a real scenario, the installer would prompt for this.
        user = self.db.get_user("admin")
        if not user:
            self.create_user("admin", "admin123", "Administrator", ["*"])

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def create_user(self, username, password, role="Viewer", workspaces: List[str] = None):
        hashed = self.get_password_hash(password)
        return self.db.add_user(username, hashed, role, workspaces or [])

    def authenticate_user(self, ip: str, username: str, password: str):
        attempts, last_attempt = self.db.get_login_attempts(ip, username)
        
        # Simple rate limiting: 5 attempts per 15 minutes
        if attempts >= 5 and last_attempt:
            if datetime.now() - last_attempt < timedelta(minutes=15):
                return None, "Rate limit exceeded. Try again later."
                
        user = self.db.get_user(username)
        if not user or not self.verify_password(password, user['password_hash']):
            self.db.record_login_attempt(ip, username, success=False)
            return None, "Invalid username or password"
            
        self.db.record_login_attempt(ip, username, success=True)
        return user, "Success"

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire, "jti": secrets.token_hex(16)})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    def revoke_token(self, jti: str):
        self.db.revoke_token(jti)

    def is_token_revoked(self, jti: str):
        return self.db.is_token_revoked(jti)

    def get_user_from_token(self, token: str):
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            if not jti or self.is_token_revoked(jti):
                return None
            username: str = payload.get("sub")
            if username is None:
                return None
            return self.db.get_user(username)
        except jwt.PyJWTError:
            return None

    def check_permission(self, user, required_role: str, workspace: str = None):
        """
        Check if user has required role and access to workspace.
        Roles hierarchy: Administrator > Analyst > Viewer
        """
        if not user:
            return False
            
        role_levels = {"Viewer": 1, "Analyst": 2, "Administrator": 3}
        user_level = role_levels.get(user['role'], 0)
        req_level = role_levels.get(required_role, 1)
        
        if user_level < req_level:
            return False
            
        # Check workspace access
        if workspace:
            allowed_workspaces = user['workspaces']
            if "*" not in allowed_workspaces and workspace not in allowed_workspaces:
                return False
                
        return True

# Singleton instance
auth_service = AuthService()
