from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context using Argon2
# Argon2 has no 72-byte limitation and is more secure than bcrypt
# It's the winner of the Password Hashing Competition
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=2,      # Number of iterations (higher = slower but more secure)
    argon2__memory_cost=1024,  # Memory in KB (default 1024)
    argon2__parallelism=2,     # Number of parallel threads
    argon2__hash_len=32,       # Length of the hash in bytes
    argon2__salt_len=16        # Length of the salt in bytes
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash password with Argon2."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with user claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key.get_secret_value(), 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key.get_secret_value(), 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")