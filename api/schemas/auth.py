from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "Viewer"
    workspaces: List[str] = []

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    workspaces: List[str]
