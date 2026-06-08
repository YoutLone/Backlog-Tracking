from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Connection
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_active_user
from app.db.database import get_db_connection
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse

router = APIRouter()

def get_auth_service(conn: Connection = Depends(get_db_connection)) -> AuthService:
    """Dependency injection for auth service."""
    user_repo = UserRepository(conn)
    return AuthService(user_repo)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, 
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        user = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin, 
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login and receive JWT token."""
    try:
        token = await auth_service.login(email=login_data.email, password=login_data.password)
        return token
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    conn: Connection = Depends(get_db_connection)
):
    """
    Get the currently authenticated user's information.
    Returns user details including id, email, full_name, etc.
    """
    user_repo = UserRepository(conn)
    user = await user_repo.get_by_id(current_user['id'])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user