from asyncpg import Connection
from uuid import UUID
from typing import Optional, Dict, Any, List
from app.core.security import get_password_hash

class UserRepository:
    """Handles user data access."""
    
    def __init__(self, conn: Connection):
        self.conn = conn
    
    async def create(self, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user with hashed password."""
        password_hash = get_password_hash(password)
        
        row = await self.conn.fetchrow(
            """
            INSERT INTO users (email, password_hash, full_name)
            VALUES ($1, $2, $3)
            RETURNING id, email, full_name, is_active, created_at
            """,
            email, password_hash, full_name
        )
        
        return dict(row) if row else None
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (for authentication)."""
        row = await self.conn.fetchrow(
            "SELECT id, email, password_hash, full_name, is_active, created_at FROM users WHERE email = $1",
            email
        )
        return dict(row) if row else None
    
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        row = await self.conn.fetchrow(
            "SELECT id, email, full_name, is_active, created_at FROM users WHERE id = $1",
            UUID(user_id) if isinstance(user_id, str) else user_id
        )
        return dict(row) if row else None
    
    async def get_teams(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all teams a user belongs to."""
        rows = await self.conn.fetch(
            """
            SELECT t.*, tm.role 
            FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            WHERE tm.user_id = $1
            ORDER BY t.created_at DESC
            """,
            user_id
        )
        return [dict(row) for row in rows]
    
    async def is_team_member(self, user_id: UUID, team_id: UUID) -> bool:
        """Check if user is a member of a team."""
        row = await self.conn.fetchval(
            "SELECT 1 FROM team_members WHERE user_id = $1 AND team_id = $2",
            user_id, team_id
        )
        return row is not None
    
    async def is_team_admin(self, user_id: UUID, team_id: UUID) -> bool:
        """Check if user is an admin of a team."""
        row = await self.conn.fetchval(
            "SELECT 1 FROM team_members WHERE user_id = $1 AND team_id = $2 AND role = 'admin'",
            user_id, team_id
        )
        return row is not None