from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta
from api.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse
from api.schemas.common import UnifiedResponse
from api.services.auth_service import auth_service, ACCESS_TOKEN_EXPIRE_MINUTES
from core.logger import LoggerFactory

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

logger = LoggerFactory.get_logger("system")

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_role(role: str):
    def role_checker(user: dict = Depends(get_current_user)):
        if not auth_service.check_permission(user, role):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user
    return role_checker

@router.post("/login", response_model=UnifiedResponse[TokenResponse])
async def login(request: Request, login_data: LoginRequest):
    ip = request.client.host
    user, msg = auth_service.authenticate_user(ip, login_data.username, login_data.password)
    
    if not user:
        logger.warning(f"Failed login attempt from {ip} for user {login_data.username}: {msg}")
        raise HTTPException(status_code=401, detail=msg)
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user {user['username']} from {ip}")
    
    return UnifiedResponse(
        status="success", 
        data=TokenResponse(access_token=access_token)
    )

@router.post("/logout", response_model=UnifiedResponse)
async def logout(token: str = Depends(oauth2_scheme)):
    # Decode token just to get JTI to revoke it
    import jwt
    from api.services.auth_service import JWT_SECRET, JWT_ALGORITHM
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        jti = payload.get("jti")
        if jti:
            auth_service.revoke_token(jti)
    except jwt.PyJWTError:
        pass # Ignore invalid tokens on logout
        
    return UnifiedResponse(status="success", message="Successfully logged out")

@router.post("/users", response_model=UnifiedResponse[UserResponse], dependencies=[Depends(require_role("Administrator"))])
async def create_user(user: UserCreate):
    if auth_service.create_user(user.username, user.password, user.role, user.workspaces):
        # We don't return the password
        user_info = auth_service.db.get_user(user.username)
        return UnifiedResponse(
            status="success",
            data=UserResponse(**user_info),
            message="User created successfully"
        )
    raise HTTPException(status_code=400, detail="Username already registered")
