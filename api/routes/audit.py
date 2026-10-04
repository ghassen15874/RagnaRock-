from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
from api.schemas.common import UnifiedResponse
from core.logger import LoggerFactory
from fastapi import Depends
from api.routes.auth import require_role

router = APIRouter(prefix="/api/v1/audit-logs", tags=["Audit"])

@router.get("/export", response_model=UnifiedResponse, dependencies=[Depends(require_role("Administrator"))])
async def export_audit_logs():
    # Secure random temp file path for the zip
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    
    if LoggerFactory.export_diagnostics(path):
        return FileResponse(
            path=path,
            media_type="application/zip",
            filename="ragnarok_audit_logs.zip"
        )
        
    raise HTTPException(status_code=500, detail="Failed to export audit logs")
