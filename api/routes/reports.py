from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os
import tempfile
from api.schemas.common import UnifiedResponse
from api.services.framework_service import FrameworkService
from core.reporter import Reporter
from fastapi import Depends
from api.routes.auth import get_current_user
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

@router.get("/generate", response_model=UnifiedResponse)
async def generate_report(
    workspace: str = Query("default", description="Workspace name"),
    format: str = Query("markdown", description="Format: 'html' or 'markdown'"),
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
    
    if format.lower() == "html":
        success = reporter.generate_html(workspace, path)
    else:
        success = reporter.generate_markdown(workspace, path)
        
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate report")
        
    # Using FileResponse will return the file directly
    return FileResponse(
        path=path, 
        media_type="text/html" if format == "html" else "text/markdown",
        filename=f"ragnarok_report_{workspace}.{format}"
    )
