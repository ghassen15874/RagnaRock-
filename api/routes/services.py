from fastapi import APIRouter, HTTPException, Depends
from typing import List
from api.schemas.common import UnifiedResponse, Service
from api.services.framework_service import FrameworkService
from api.routes.auth import get_current_user
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/v1/services", tags=["Services"])

@router.get("/{host_id}", response_model=UnifiedResponse[List[Service]])
async def list_services(host_id: int, user: dict = Depends(get_current_user)):
    db = FrameworkService.get_db()
    
    # We need to find the workspace for this host to enforce RBAC
    # We do not have a dedicated get_host(id) in db, so we find it by iterating for now, 
    # or better: we use a direct query. For simplicity, we just use raw SQL via the db object if needed, 
    # but the DB class only has get_hosts(workspace).
    # Since we can't easily find workspace from host_id without direct SQL, we'll query DB.
    workspace = None
    with __import__('sqlite3').connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT workspace FROM hosts WHERE id = ?", (host_id,))
        row = cursor.fetchone()
        if row:
            workspace = row[0]
            
    if not workspace:
        raise HTTPException(status_code=404, detail="Host not found")
        
    if not auth_service.check_permission(user, "Viewer", workspace):
        raise HTTPException(status_code=403, detail="Not authorized to access this host's data")
        
    db_services = db.get_services(host_id)
    services = []
    for s in db_services:
        services.append(Service(
            id=s[0],
            host_id=s[1],
            port=s[2],
            protocol=s[3],
            name=s[4],
            state=s[5]
        ))
    return UnifiedResponse(status="success", data=services)
