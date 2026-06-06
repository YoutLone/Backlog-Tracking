import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.services.auth_service import AuthService
from unittest.mock import AsyncMock, Mock

def test_password_hashing():
    """Test password hashing and verification."""
    password = "Test1234!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_jwt_token():
    """Test JWT token creation and decoding."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(data={"sub": user_id})
    
    assert token is not None
    assert isinstance(token, str)
    
    payload = decode_token(token)
    assert payload['sub'] == user_id

@pytest.mark.asyncio
async def test_register_user():
    """Test user registration."""
    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = None
    mock_repo.create.return_value = {
        'id': 'test-id',
        'email': 'test@example.com',
        'full_name': 'Test User'
    }
    
    auth_service = AuthService(mock_repo)
    user = await auth_service.register_user(
        email="test@example.com",
        password="Test1234!",
        full_name="Test User"
    )
    
    assert user is not None
    assert user['email'] == "test@example.com"

@pytest.mark.asyncio
async def test_register_duplicate_user():
    """Test registration with existing email."""
    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = {'email': 'existing@example.com'}
    
    auth_service = AuthService(mock_repo)
    
    with pytest.raises(ValueError, match="already exists"):
        await auth_service.register_user(
            email="existing@example.com",
            password="Test1234!"
        )