from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.routes import workspaces, hosts, services, reports, audit, health, auth, history
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup basic logging for API
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RagnaRokAPI")

app = FastAPI(
    title="RagnaRok API",
    description="Secure REST API for RagnaRok Data & Reports Management",
    version="1.0.0"
)

# Global exception handler for Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Validation Error", "details": exc.errors()}
    )

# Global generic exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"}
    )

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the dashboard origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(workspaces.router)
app.include_router(hosts.router)
app.include_router(services.router)
app.include_router(reports.router)
app.include_router(audit.router)
app.include_router(history.router)

if __name__ == "__main__":
    print("="*50)
    print("Starting RagnaRok API Server")
    print(f"API TOKEN: {API_TOKEN}")
    print("Please keep this token secure.")
    print("="*50)
    
    import uvicorn
    uvicorn.run("api.app:app", host="127.0.0.1", port=5000, reload=False)
