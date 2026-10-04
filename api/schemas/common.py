from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any, List

T = TypeVar('T')

class UnifiedResponse(BaseModel, Generic[T]):
    status: str
    message: Optional[str] = None
    data: Optional[T] = None

class Workspace(BaseModel):
    name: str

class Host(BaseModel):
    id: int
    workspace: str
    ip: str
    mac: Optional[str] = None
    os: Optional[str] = None
    status: str

class Service(BaseModel):
    id: int
    host_id: int
    port: int
    protocol: str
    name: Optional[str] = None
    state: str
