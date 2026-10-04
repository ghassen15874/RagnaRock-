from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import List, Optional
from api.schemas.common import UnifiedResponse, PaginatedResponse, PaginatedData, Service
from api.routes.auth import get_current_user
from api.services.auth_service import auth_service
from api.services.data_service import DataService

router = APIRouter(prefix="/api/v1/services", tags=["Services"])

@router.get("/host/{host_id}", response_model=PaginatedResponse[Service])
async def list_services(
    host_id: int = Path(..., description="The ID of the host"),
    workspace: str = Query("default", description="Workspace name for data isolation"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("port", pattern="^(id|port|protocol|service_name|state)$"),
    sort_desc: bool = Query(False),
    protocol: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    if not auth_service.check_permission(user, "Viewer", workspace):
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    services_dicts, total = DataService.get_services(
        host_id, workspace, limit, offset, sort_by, sort_desc, protocol
    )
    
    if not services_dicts and total == 0:
        # Check if host exists at all
        if not DataService.get_host_by_id(host_id, workspace):
            raise HTTPException(status_code=404, detail="Host not found in the specified workspace")

    services = []
    for s in services_dicts:
        services.append(Service(
            id=s["id"],
            host_id=s["host_id"],
            port=s["port"],
            protocol=s["protocol"],
            name=s["service_name"],
            state=s["state"]
        ))
        
    data = PaginatedData(items=services, total=total, limit=limit, offset=offset)
    return PaginatedResponse(status="success", data=data)

@router.get("/{service_id}", response_model=UnifiedResponse[Service])
async def get_service(
    service_id: int = Path(..., description="The ID of the service"),
    workspace: str = Query("default", description="Workspace name"),
    user: dict = Depends(get_current_user)
):
    if not auth_service.check_permission(user, "Viewer", workspace):
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    service_dict = DataService.get_service_by_id(service_id, workspace)
    if not service_dict:
        raise HTTPException(status_code=404, detail="Service not found in the specified workspace")
        
    service = Service(
        id=service_dict["id"],
        host_id=service_dict["host_id"],
        port=service_dict["port"],
        protocol=service_dict["protocol"],
        name=service_dict["service_name"],
        state=service_dict["state"]
    )
    return UnifiedResponse(status="success", data=service)
