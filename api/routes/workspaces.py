from fastapi import APIRouter, HTTPException, Depends
from typing import List
from api.schemas.common import UnifiedResponse, Workspace
from api.services.framework_service import FrameworkService

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspaces"])

@router.get("", response_model=UnifiedResponse[List[str]])
async def list_workspaces():
    db = FrameworkService.get_db()
    workspaces = db.get_workspaces()
    return UnifiedResponse(status="success", data=workspaces)

@router.post("", response_model=UnifiedResponse[Workspace])
async def create_workspace(workspace: Workspace):
    db = FrameworkService.get_db()
    if db.add_workspace(workspace.name):
        return UnifiedResponse(status="success", data=workspace, message="Workspace created")
    raise HTTPException(status_code=400, detail="Could not create workspace (it may already exist)")

@router.delete("/{name}", response_model=UnifiedResponse)
async def delete_workspace(name: str):
    db = FrameworkService.get_db()
    if name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default workspace")
    if db.delete_workspace(name):
        return UnifiedResponse(status="success", message=f"Workspace {name} deleted")
    raise HTTPException(status_code=404, detail="Workspace not found or could not be deleted")
