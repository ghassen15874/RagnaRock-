from fastapi import APIRouter, HTTPException, Query
from typing import List
from api.schemas.common import UnifiedResponse, Host
from api.services.framework_service import FrameworkService

router = APIRouter(prefix="/api/v1/hosts", tags=["Hosts"])

@router.get("", response_model=UnifiedResponse[List[Host]])
async def list_hosts(workspace: str = Query("default", description="Workspace name for data isolation")):
    db = FrameworkService.get_db()
    
    # Ensure workspace exists before querying
    workspaces = db.get_workspaces()
    if workspace not in workspaces:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    db_hosts = db.get_hosts(workspace)
    hosts = []
    for h in db_hosts:
        hosts.append(Host(
            id=h[0],
            workspace=h[1],
            ip=h[2],
            mac=h[3],
            os=h[4],
            status=h[5]
        ))
    return UnifiedResponse(status="success", data=hosts)
