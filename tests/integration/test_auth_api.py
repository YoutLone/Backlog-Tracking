import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration endpoint."""
    unique_email = f"newuser_{uuid4()}@example.com"
    response = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Test1234!",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data['email'] == unique_email
    assert data['full_name'] == "New User"
    assert 'id' in data
    assert data['is_active'] == True

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email."""
    unique_email = f"duplicate_{uuid4()}@example.com"
    
    # First registration
    response1 = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Test1234!",
            "full_name": "User 1"
        }
    )
    assert response1.status_code == 201
    
    # Second registration with same email
    response2 = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Test1234!",
            "full_name": "User 2"
        }
    )
    
    assert response2.status_code == 400
    assert "already exists" in response2.json()['detail']

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login."""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": test_user['email'],
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password."""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": test_user['email'],
            "password": "WrongPassword123!"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid" in response.json()['detail']