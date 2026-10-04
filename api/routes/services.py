from fastapi import APIRouter, HTTPException
from typing import List
from api.schemas.common import UnifiedResponse, Service
from api.services.framework_service import FrameworkService

router = APIRouter(prefix="/api/v1/services", tags=["Services"])

@router.get("/{host_id}", response_model=UnifiedResponse[List[Service]])
async def list_services(host_id: int):
    db = FrameworkService.get_db()
    
    # Simple check if host exists could be done here, but get_services returns empty list if not
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
