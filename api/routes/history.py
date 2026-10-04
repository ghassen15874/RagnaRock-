from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
from api.schemas.common import UnifiedResponse
from api.services.framework_service import FrameworkService
from api.routes.auth import get_current_user
from api.services.auth_service import auth_service
from core.history import HistoryAnalyzer

router = APIRouter(prefix="/api/v1/history", tags=["Historical Analysis"])

def get_analyzer():
    db = FrameworkService.get_db()
    return HistoryAnalyzer(db)

@router.post("/snapshot", response_model=UnifiedResponse)
async def create_snapshot(
    workspace: str = Query(..., description="Workspace name"),
    source: str = Query("API Snapshot", description="Source of the scan data"),
    user: dict = Depends(get_current_user),
    analyzer: HistoryAnalyzer = Depends(get_analyzer)
):
    """Takes a snapshot of the current workspace state to be stored in history."""
    if not auth_service.check_permission(user, "Analyst", workspace):
        raise HTTPException(status_code=403, detail="Analyst role or higher required")
        
    try:
        scan_id = analyzer.save_snapshot(workspace, source)
        return UnifiedResponse(status="success", data={"scan_id": scan_id})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scans", response_model=UnifiedResponse[List[Dict[str, Any]]])
async def list_scans(
    workspace: str = Query(..., description="Workspace name"),
    user: dict = Depends(get_current_user),
    analyzer: HistoryAnalyzer = Depends(get_analyzer)
):
    """Retrieves the history of scans for a given workspace."""
    if not auth_service.check_permission(user, "Viewer", workspace):
        raise HTTPException(status_code=403, detail="Permission denied for this workspace")
        
    history = analyzer.get_scan_history(workspace)
    return UnifiedResponse(status="success", data=history)

@router.get("/compare", response_model=UnifiedResponse[Dict[str, Any]])
async def compare_scans(
    workspace: str = Query(..., description="Workspace name"),
    old_scan_id: str = Query(..., description="The older scan ID to use as base"),
    new_scan_id: str = Query(..., description="The newer scan ID to compare against"),
    user: dict = Depends(get_current_user),
    analyzer: HistoryAnalyzer = Depends(get_analyzer)
):
    """Compares two historical scans and returns the differences (new, removed, state changes)."""
    if not auth_service.check_permission(user, "Viewer", workspace):
        raise HTTPException(status_code=403, detail="Permission denied for this workspace")
        
    try:
        report = analyzer.compare_scans(workspace, old_scan_id, new_scan_id)
        return UnifiedResponse(status="success", data=report)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
