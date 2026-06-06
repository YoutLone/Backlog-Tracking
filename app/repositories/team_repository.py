from asyncpg import Connection
from uuid import UUID
from typing import Optional, Dict, Any, List

class TeamRepository:
    """Handles team data access with membership validation."""
    
    def __init__(self, conn: Connection):
        self.conn = conn
    
    async def create(self, name: str, created_by: UUID, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new team and add creator as admin."""
        async with self.conn.transaction():
            # Create team
            row = await self.conn.fetchrow(
                """
                INSERT INTO teams (name, description, created_by)
                VALUES ($1, $2, $3)
                RETURNING id, name, description, created_by, created_at, updated_at
                """,
                name, description, created_by
            )
            
            # Add creator as admin
            await self.conn.execute(
                "INSERT INTO team_members (team_id, user_id, role) VALUES ($1, $2, 'admin')",
                row['id'], created_by
            )
            
            return dict(row)
    
    async def get_by_id(self, team_id: UUID) -> Optional[Dict[str, Any]]:
        """Get team by ID."""
        row = await self.conn.fetchrow(
            "SELECT id, name, description, created_by, created_at, updated_at FROM teams WHERE id = $1",
            team_id
        )
        return dict(row) if row else None
    
    async def update(self, team_id: UUID, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Update team details."""
        # Build dynamic update query
        updates = []
        params = []
        param_counter = 1
        
        if name is not None:
            updates.append(f"name = ${param_counter}")
            params.append(name)
            param_counter += 1
        if description is not None:
            updates.append(f"description = ${param_counter}")
            params.append(description)
            param_counter += 1
        
        if not updates:
            return await self.get_by_id(team_id)
        
        params.append(team_id)
        query = f"""
            UPDATE teams 
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_counter}
            RETURNING id, name, description, created_by, created_at, updated_at
        """
        
        row = await self.conn.fetchrow(query, *params)
        return dict(row) if row else None
    
    async def delete(self, team_id: UUID) -> bool:
        """Delete team (cascades to members, backlog, sprints)."""
        result = await self.conn.execute("DELETE FROM teams WHERE id = $1", team_id)
        return result == "DELETE 1"
    
    async def add_member(self, team_id: UUID, user_id: UUID, role: str = 'member') -> bool:
        """Add user to team."""
        try:
            await self.conn.execute(
                "INSERT INTO team_members (team_id, user_id, role) VALUES ($1, $2, $3)",
                team_id, user_id, role
            )
            return True
        except Exception:
            return False  # Duplicate or other error
    
    async def remove_member(self, team_id: UUID, user_id: UUID) -> bool:
        """Remove user from team (cannot remove last admin)."""
        # Check if this is the last admin
        admin_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM team_members WHERE team_id = $1 AND role = 'admin'",
            team_id
        )
        
        user_role = await self.conn.fetchval(
            "SELECT role FROM team_members WHERE team_id = $1 AND user_id = $2",
            team_id, user_id
        )
        
        if user_role == 'admin' and admin_count <= 1:
            raise ValueError("Cannot remove the last admin of the team")
        
        result = await self.conn.execute(
            "DELETE FROM team_members WHERE team_id = $1 AND user_id = $2",
            team_id, user_id
        )
        return result == "DELETE 1"
    
    async def get_members(self, team_id: UUID) -> List[Dict[str, Any]]:
        """Get all members of a team with their details."""
        rows = await self.conn.fetch(
            """
            SELECT tm.user_id, tm.role, tm.joined_at, u.email, u.full_name
            FROM team_members tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.team_id = $1
            ORDER BY tm.role DESC, u.email
            """,
            team_id
        )
        return [dict(row) for row in rows]
    
    async def get_user_teams(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all teams a user belongs to."""
        rows = await self.conn.fetch(
            """
            SELECT t.id, t.name, t.description, tm.role
            FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            WHERE tm.user_id = $1
            ORDER BY t.name
            """,
            user_id
        )
        return [dict(row) for row in rows]