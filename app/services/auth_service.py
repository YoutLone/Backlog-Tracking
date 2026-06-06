from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.schemas.user import Token
from uuid import UUID
from typing import Dict, Any

class AuthService:
    """Authentication business logic."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def register_user(self, email: str, password: str, full_name: str = None) -> Dict[str, Any]:
        """Register a new user."""
        # Check if user exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("User with this email already exists")
        
        # Create user
        user = await self.user_repo.create(email, password, full_name)
        return user
    
    async def login(self, email: str, password: str) -> Token:
        """Authenticate user and return JWT token."""
        # Get user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            raise ValueError("Invalid email or password")
        
        # Check if active
        if not user.get('is_active', True):
            raise ValueError("Account is deactivated")
        
        # Create token
        token = create_access_token(data={"sub": str(user['id'])})
        return Token(access_token=token)