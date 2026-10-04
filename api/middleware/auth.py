from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import secrets
import os

# Generate a master token for the API session or load from environment
API_TOKEN = os.environ.get("RAGNAROK_API_TOKEN", secrets.token_hex(32))

async def auth_middleware(request: Request, call_next):
    # Skip auth for openapi docs if desired, but for security we might want to block everything
    # Let's allow only the root or specific docs if needed, but normally block all
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json"):
        return await call_next(request)
        
    token = request.headers.get("X-Api-Token")
    if not token or token != API_TOKEN:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "Unauthorized: Invalid or missing X-Api-Token"}
        )
        
    response = await call_next(request)
    return response
