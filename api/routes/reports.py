from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os
import tempfile
from typing import List
from api.schemas.common import UnifiedResponse
from api.services.framework_service import FrameworkService
from core.reporter import Reporter
from fastapi import Depends
from api.routes.auth import get_current_user
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

@router.get("/available", response_model=UnifiedResponse[List[str]])
async def list_available_formats(user: dict = Depends(get_current_user)):
    # Returns the available formats for export
    return UnifiedResponse(status="success", data=["markdown", "html", "json"])

@router.get("/generate", response_model=UnifiedResponse)
async def generate_report(
    workspace: str = Query("default", description="Workspace name"),
    format: str = Query("markdown", description="Format: 'html', 'markdown', or 'json'"),
    user: dict = Depends(get_current_user)
):
    if not auth_service.check_permission(user, "Analyst", workspace):
        raise HTTPException(status_code=403, detail="Analyst role or higher required for this workspace")
        
    db = FrameworkService.get_db()
    if workspace not in db.get_workspaces():
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    reporter = Reporter(db)
    
    # Secure random temp file path for the report
    fd, path = tempfile.mkstemp(suffix=f".{format}")
    os.close(fd)
    
    fmt = format.lower()
    if fmt == "html":
        success = reporter.generate_html(workspace, path)
        media_type = "text/html"
    elif fmt == "json":
        success = reporter.generate_json(workspace, path)
        media_type = "application/json"
    else:
        success = reporter.generate_markdown(workspace, path)
        media_type = "text/markdown"
        fmt = "markdown" # Normalize
        
    if not success:
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(status_code=500, detail="Failed to generate report")
        
    # Using FileResponse will return the file directly
    return FileResponse(
        path=path, 
        media_type=media_type,
        filename=f"ragnarok_report_{workspace}.{fmt}"
    )
