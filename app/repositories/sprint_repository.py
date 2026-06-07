from asyncpg import Connection
from uuid import UUID
from typing import Optional, Dict, Any, List
from datetime import date

class SprintRepository:
    """Handles sprint data access."""
    
    def __init__(self, conn: Connection):
        self.conn = conn
    
    async def create(self, team_id: UUID, created_by: UUID, name: str, start_date: date, 
                     end_date: date, goal: Optional[str] = None) -> Dict[str, Any]:
        """Create a new sprint."""
        row = await self.conn.fetchrow(
            """
            INSERT INTO sprints (team_id, created_by, name, goal, start_date, end_date)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, team_id, name, goal, start_date, end_date, is_active, 
                      created_by, created_at, updated_at
            """,
            team_id, created_by, name, goal, start_date, end_date
        )
        return dict(row)
    
    async def get_by_id(self, sprint_id: UUID, team_id: UUID) -> Optional[Dict[str, Any]]:
        """Get sprint by ID with team check."""
        row = await self.conn.fetchrow(
            """
            SELECT id, team_id, name, goal, start_date, end_date, is_active, 
                   created_by, created_at, updated_at 
            FROM sprints 
            WHERE id = $1 AND team_id = $2
            """,
            sprint_id, team_id
        )
        return dict(row) if row else None
    
    async def list_by_team(self, team_id: UUID, include_inactive: bool = True) -> List[Dict[str, Any]]:
        """List all sprints for a team."""
        query = """
            SELECT id, team_id, name, goal, start_date, end_date, is_active, 
                   created_by, created_at, updated_at 
            FROM sprints 
            WHERE team_id = $1
        """
        if not include_inactive:
            query += " AND is_active = true"
        query += " ORDER BY start_date DESC"
        
        rows = await self.conn.fetch(query, team_id)
        return [dict(row) for row in rows]
    
    async def update(self, sprint_id: UUID, team_id: UUID, **kwargs) -> Optional[Dict[str, Any]]:
        """Update sprint fields."""
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return await self.get_by_id(sprint_id, team_id)
        
        set_parts = []
        params = []
        param_counter = 1
        
        allowed_fields = ['name', 'goal', 'start_date', 'end_date', 'is_active']
        for field in allowed_fields:
            if field in updates:
                set_parts.append(f"{field} = ${param_counter}")
                params.append(updates[field])
                param_counter += 1
        
        if not set_parts:
            return await self.get_by_id(sprint_id, team_id)
        
        params.extend([sprint_id, team_id])
        query = f"""
            UPDATE sprints 
            SET {', '.join(set_parts)}, updated_at = NOW()
            WHERE id = ${param_counter} AND team_id = ${param_counter + 1}
            RETURNING id, team_id, name, goal, start_date, end_date, is_active, 
                      created_by, created_at, updated_at
        """
        
        row = await self.conn.fetchrow(query, *params)
        return dict(row) if row else None
    
    async def delete(self, sprint_id: UUID, team_id: UUID) -> bool:
        """Delete sprint (sets backlog_items.sprint_id to NULL)."""
        result = await self.conn.execute(
            "DELETE FROM sprints WHERE id = $1 AND team_id = $2",
            sprint_id, team_id
        )
        return result == "DELETE 1"
    
    async def get_sprint_statistics(self, sprint_id: UUID, team_id: UUID) -> Dict[str, Any]:
        """Get story points summary for a sprint."""
        row = await self.conn.fetchrow(
            """
            SELECT 
                COUNT(*) as item_count,
                COALESCE(SUM(story_points), 0) as total_story_points,
                COALESCE(SUM(CASE WHEN status = 'done' THEN story_points ELSE 0 END), 0) as completed_story_points
            FROM backlog_items
            WHERE sprint_id = $1 AND team_id = $2
            """,
            sprint_id, team_id
        )
        return dict(row) if row else {'item_count': 0, 'total_story_points': 0, 'completed_story_points': 0}