from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import List, Optional
from api.schemas.common import UnifiedResponse, PaginatedResponse, PaginatedData, Host
from api.routes.auth import get_current_user
from api.services.auth_service import auth_service
from api.services.data_service import DataService

router = APIRouter(prefix="/api/v1/hosts", tags=["Hosts"])

@router.get("", response_model=PaginatedResponse[Host])
async def list_hosts(
    workspace: str = Query("default", description="Workspace name for data isolation"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("id", pattern="^(id|ip_address|os_name|status|created_at)$"),
    sort_desc: bool = Query(False),
    status: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    if not auth_service.check_permission(user, "Viewer", workspace):
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    hosts_dicts, total = DataService.get_hosts(workspace, limit, offset, sort_by, sort_desc, status)
    
    hosts = []
    for h in hosts_dicts:
        hosts.append(Host(
            id=h["id"],
            workspace=h["workspace"],
            ip=h["ip_address"],
            mac=h["mac_address"],
            os=h["os_name"],
            status=h["status"]
        ))
        
    data = PaginatedData(items=hosts, total=total, limit=limit, offset=offset)
    return PaginatedResponse(status="success", data=data)

@router.get("/{host_id}", response_model=UnifiedResponse[Host])
async def get_host(
    host_id: int = Path(..., description="The ID of the host"),
    workspace: str = Query("default", description="Workspace name"),
    user: dict = Depends(get_current_user)
):
    if not auth_service.check_permission(user, "Viewer", workspace):
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    host_dict = DataService.get_host_by_id(host_id, workspace)
    if not host_dict:
        raise HTTPException(status_code=404, detail="Host not found in the specified workspace")
        
    host = Host(
        id=host_dict["id"],
        workspace=host_dict["workspace"],
        ip=host_dict["ip_address"],
        mac=host_dict["mac_address"],
        os=host_dict["os_name"],
        status=host_dict["status"]
    )
    return UnifiedResponse(status="success", data=host)
