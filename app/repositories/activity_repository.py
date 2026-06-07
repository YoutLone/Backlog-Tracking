from asyncpg import Connection
from uuid import UUID
from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

class ActivityRepository:
    """Handles activity logging for audit trail."""
    
    def __init__(self, conn: Connection):
        self.conn = conn
    
    async def log(self, user_id: UUID, team_id: UUID, action: str, 
                  entity_type: str, entity_id: UUID, 
                  old_values: Optional[Dict] = None, 
                  new_values: Optional[Dict] = None) -> None:
        """Log an activity."""
        try:
            # default=str handles UUID and datetime values.
            old_json = json.dumps(old_values, default=str) if old_values else None
            new_json = json.dumps(new_values, default=str) if new_values else None
            
            await self.conn.execute(
                """
                INSERT INTO activity_log (user_id, team_id, action, entity_type, entity_id, old_values, new_values)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user_id, team_id, action, entity_type, entity_id, old_json, new_json
            )
        except Exception as e:
            # Audit failures should not block the main action.
            logger.error(f"Failed to log activity: {e}. Action: {action}, Entity: {entity_type}/{entity_id}")
    
    async def get_for_entity(self, entity_type: str, entity_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activity log for a specific entity."""
        try:
            rows = await self.conn.fetch(
                """
                SELECT al.*, u.email as user_email
                FROM activity_log al
                JOIN users u ON al.user_id = u.id
                WHERE al.entity_type = $1 AND al.entity_id = $2
                ORDER BY al.created_at DESC
                LIMIT $3
                """,
                entity_type, entity_id, limit
            )
            
            # Return JSONB values as normal dicts when possible.
            result = []
            for row in rows:
                row_dict = dict(row)
                if row_dict.get('old_values') and isinstance(row_dict['old_values'], str):
                    try:
                        row_dict['old_values'] = json.loads(row_dict['old_values'])
                    except json.JSONDecodeError:
                        pass
                if row_dict.get('new_values') and isinstance(row_dict['new_values'], str):
                    try:
                        row_dict['new_values'] = json.loads(row_dict['new_values'])
                    except json.JSONDecodeError:
                        pass
                result.append(row_dict)
            
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve activity log: {e}")
            return []
