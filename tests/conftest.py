import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient, ASGITransport
from asyncpg import Connection, create_pool
from uuid import uuid4

from app.main import app
from app.core.config import settings
from app.db.database import Database, get_db_connection
from app.repositories.user_repository import UserRepository
from app.repositories.team_repository import TeamRepository
from app.services.auth_service import AuthService
from app.services.team_service import TeamService

# Test database URL (create a separate test database in Supabase)
# For local testing, you can use a local Postgres instance
TEST_DATABASE_URL = settings.database_url.get_secret_value() + "_test"  # Or use a separate test DB

@pytest.fixture
async def db_connection() -> AsyncGenerator[Connection, None]:
    """Provide a database connection for testing."""
    # Create a connection pool for testing
    pool = await create_pool(
        settings.database_url.get_secret_value(),
        min_size=1,
        max_size=2,
        statement_cache_size=0
    )
    
    async with pool.acquire() as conn:
        # Start a transaction that will be rolled back after test
        async with conn.transaction():
            yield conn
    
    await pool.close()

@pytest.fixture
async def client(db_connection: Connection) -> AsyncGenerator[AsyncClient, None]:
    """Provide a test client with database connection override."""
    
    async def override_get_db():
        yield db_connection
    
    app.dependency_overrides[get_db_connection] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_connection: Connection) -> Dict[str, Any]:
    """Create a test user."""
    user_repo = UserRepository(db_connection)
    auth_service = AuthService(user_repo)
    
    email = f"test_{uuid4()}@example.com"
    user = await auth_service.register_user(
        email=email,
        password="Test1234!",
        full_name="Test User"
    )
    
    return user

@pytest.fixture
async def test_user_token(client: AsyncClient, test_user: Dict[str, Any]) -> str:
    """Get JWT token for test user."""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": test_user['email'],
            "password": "Test1234!"
        }
    )
    return response.json()['access_token']

@pytest.fixture
async def test_team(db_connection: Connection, test_user: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test team."""
    team_repo = TeamRepository(db_connection)
    team = await team_repo.create(
        name=f"Test Team {uuid4()}",
        created_by=test_user['id'],
        description="Test team for integration tests"
    )
    return team

@pytest.fixture(autouse=True)
async def clean_database(db_connection: Connection):
    """Clean database before each test."""
    # Delete test data from previous runs
    await db_connection.execute("DELETE FROM activity_log")
    await db_connection.execute("DELETE FROM backlog_items")
    await db_connection.execute("DELETE FROM team_members")
    await db_connection.execute("DELETE FROM sprints")
    await db_connection.execute("DELETE FROM teams")
    await db_connection.execute("DELETE FROM users")
    yield