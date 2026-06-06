from asyncpg import Connection
from uuid import UUID
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

class BacklogRepository:
    """Handles backlog item data access with team isolation."""
    
    def __init__(self, conn: Connection):
        self.conn = conn
    
    async def get_next_rank(self, team_id: UUID) -> int:
        """Get the next priority rank for a team (lowest rank + 1000)."""
        max_rank = await self.conn.fetchval(
            "SELECT COALESCE(MAX(priority_rank), 0) FROM backlog_items WHERE team_id = $1",
            team_id
        )
        return max_rank + 1000
    
    async def create(self, team_id: UUID, created_by: UUID, title: str, 
                    item_type: str, description: Optional[str] = None,
                    story_points: Optional[int] = None, assigned_to: Optional[UUID] = None,
                    sprint_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Create a new backlog item with auto-ranking."""
        rank = await self.get_next_rank(team_id)
        
        row = await self.conn.fetchrow(
            """
            INSERT INTO backlog_items 
            (team_id, created_by, title, description, type, story_points, assigned_to, sprint_id, priority_rank)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, team_id, title, description, type, status, priority_rank, 
                    story_points, created_by, assigned_to, sprint_id, created_at, updated_at, completed_at
            """,
            team_id, created_by, title, description, item_type, story_points, assigned_to, sprint_id, rank
        )
        return dict(row)
    
    async def get_by_id(self, item_id: UUID, team_id: UUID) -> Optional[Dict[str, Any]]:
        """Get item by ID, ensuring it belongs to team."""
        row = await self.conn.fetchrow(
            """
            SELECT bi.*, 
                u1.email as creator_email,
                u2.email as assignee_email
            FROM backlog_items bi
            LEFT JOIN users u1 ON bi.created_by = u1.id
            LEFT JOIN users u2 ON bi.assigned_to = u2.id
            WHERE bi.id = $1 AND bi.team_id = $2
            """,
            item_id, team_id
        )
        return dict(row) if row else None
    
    async def list_by_team(self, team_id: UUID, filters: Dict[str, Any], 
                        limit: int = 20, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """List backlog items with filters, ordered by priority_rank."""
        # Build WHERE clause
        where_parts = ["team_id = $1"]
        params = [team_id]
        param_counter = 2
        
        if filters.get('status'):
            where_parts.append(f"status = ${param_counter}")
            params.append(filters['status'])
            param_counter += 1
        
        if filters.get('type'):
            where_parts.append(f"type = ${param_counter}")
            params.append(filters['type'])
            param_counter += 1
        
        if filters.get('sprint_id'):
            where_parts.append(f"sprint_id = ${param_counter}")
            params.append(filters['sprint_id'])
            param_counter += 1
        
        if filters.get('assigned_to'):
            where_parts.append(f"assigned_to = ${param_counter}")
            params.append(filters['assigned_to'])
            param_counter += 1
        
        where_clause = " AND ".join(where_parts)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM backlog_items WHERE {where_clause}"
        total = await self.conn.fetchval(count_query, *params)
        
        # Get paginated results
        query = f"""
            SELECT bi.*, 
                u1.email as creator_email,
                u2.email as assignee_email
            FROM backlog_items bi
            LEFT JOIN users u1 ON bi.created_by = u1.id
            LEFT JOIN users u2 ON bi.assigned_to = u2.id
            WHERE {where_clause}
            ORDER BY bi.priority_rank ASC
            LIMIT ${param_counter} OFFSET ${param_counter + 1}
        """
        params.extend([limit, offset])
        
        rows = await self.conn.fetch(query, *params)
        return [dict(row) for row in rows], total
    
    async def update(self, item_id: UUID, team_id: UUID, **kwargs) -> Optional[Dict[str, Any]]:
        """Update item fields."""
        # Filter out None values
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return await self.get_by_id(item_id, team_id)
        
        # Build dynamic update query
        set_parts = []
        params = []
        param_counter = 1
        
        allowed_fields = ['title', 'description', 'type', 'story_points', 'assigned_to', 'sprint_id']
        for field in allowed_fields:
            if field in updates:
                set_parts.append(f"{field} = ${param_counter}")
                params.append(updates[field])
                param_counter += 1
        
        if not set_parts:
            return await self.get_by_id(item_id, team_id)
        
        params.extend([item_id, team_id])
        query = f"""
            UPDATE backlog_items 
            SET {', '.join(set_parts)}, updated_at = NOW()
            WHERE id = ${param_counter} AND team_id = ${param_counter + 1}
            RETURNING id, team_id, title, description, type, status, priority_rank, 
                    story_points, created_by, assigned_to, sprint_id, created_at, updated_at, completed_at
        """
        
        row = await self.conn.fetchrow(query, *params)
        return dict(row) if row else None
    
    async def update_status(self, item_id: UUID, team_id: UUID, new_status: str) -> Optional[Dict[str, Any]]:
        """Update status and set completed_at if done."""
        completed_at = datetime.utcnow() if new_status == 'done' else None
        
        row = await self.conn.fetchrow(
            """
            UPDATE backlog_items 
            SET status = $1, completed_at = $2, updated_at = NOW()
            WHERE id = $3 AND team_id = $4
            RETURNING id, team_id, title, description, type, status, priority_rank, 
                    story_points, created_by, assigned_to, sprint_id, created_at, updated_at, completed_at
            """,
            new_status, completed_at, item_id, team_id
        )
        return dict(row) if row else None
    
    async def reorder_items(self, team_id: UUID, reorders: List[Tuple[UUID, int]]) -> bool:
        """Bulk update priority ranks (optimistic locking style)."""
        async with self.conn.transaction():
            for item_id, new_rank in reorders:
                await self.conn.execute(
                    "UPDATE backlog_items SET priority_rank = $1, updated_at = NOW() WHERE id = $2 AND team_id = $3",
                    new_rank, item_id, team_id
                )
        return True
    
    async def delete(self, item_id: UUID, team_id: UUID) -> bool:
        """Delete item."""
        result = await self.conn.execute(
            "DELETE FROM backlog_items WHERE id = $1 AND team_id = $2",
            item_id, team_id
        )
        return result == "DELETE 1"
    
    async def get_team_items_in_sprint(self, team_id: UUID, sprint_id: UUID) -> List[Dict[str, Any]]:
        """Get all items for a sprint."""
        rows = await self.conn.fetch(
            """
            SELECT bi.*, u.email as assignee_email
            FROM backlog_items bi
            LEFT JOIN users u ON bi.assigned_to = u.id
            WHERE bi.team_id = $1 AND bi.sprint_id = $2
            ORDER BY bi.priority_rank ASC
            """,
            team_id, sprint_id
        )
        return [dict(row) for row in rows]