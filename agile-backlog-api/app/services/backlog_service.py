from app.repositories.backlog_repository import BacklogRepository
from app.repositories.sprint_repository import SprintRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from uuid import UUID
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class BacklogService:
    """Backlog management with ranking and workflow rules."""
    
    # Workflow transition rules
    ALLOWED_TRANSITIONS = {
        'backlog': ['todo'],  # Can also delete from backlog
        'todo': ['in_progress', 'backlog'],
        'in_progress': ['review', 'todo'],
        'review': ['done', 'in_progress'],
        'done': ['backlog']  # Allow reopening
    }
    
    def __init__(self, backlog_repo: BacklogRepository, user_repo: UserRepository, 
                 sprint_repo: SprintRepository, activity_repo: ActivityRepository):
        self.backlog_repo = backlog_repo
        self.user_repo = user_repo
        self.sprint_repo = sprint_repo
        self.activity_repo = activity_repo
    
    async def _check_team_access(self, user_id: UUID, team_id: UUID):
        """Helper to verify team membership."""
        if not await self.user_repo.is_team_member(user_id, team_id):
            raise PermissionError("User not a member of this team")
    
    async def _log_activity(self, user_id: UUID, team_id: UUID, action: str, 
                           entity_type: str, entity_id: UUID, 
                           old_values: Dict = None, new_values: Dict = None):
        """Helper to log activities."""
        await self.activity_repo.log(user_id, team_id, action, entity_type, entity_id, old_values, new_values)
    
    async def create_item(self, user_id: UUID, team_id: UUID, title: str, item_type: str,
                         description: str = None, story_points: int = None, 
                         assigned_to: UUID = None, sprint_id: UUID = None) -> Dict[str, Any]:
        """Create a new backlog item."""
        await self._check_team_access(user_id, team_id)
        
        # Validate sprint if provided
        if sprint_id:
            sprint = await self.sprint_repo.get_by_id(sprint_id, team_id)
            if not sprint:
                raise ValueError("Sprint not found or doesn't belong to this team")
        
        # Validate assigned_to if provided
        if assigned_to:
            if not await self.user_repo.is_team_member(assigned_to, team_id):
                raise ValueError("Assigned user is not a member of this team")
        
        item = await self.backlog_repo.create(
            team_id, user_id, title, item_type, description, 
            story_points, assigned_to, sprint_id
        )
        
        # Log activity
        await self._log_activity(user_id, team_id, "CREATE", "backlog_item", item['id'], 
                                None, item)
        
        return item
    
    async def get_item(self, user_id: UUID, team_id: UUID, item_id: UUID) -> Dict[str, Any]:
        """Get a single backlog item."""
        await self._check_team_access(user_id, team_id)
        
        item = await self.backlog_repo.get_by_id(item_id, team_id)
        if not item:
            raise ValueError("Backlog item not found")
        
        return item
    
    async def list_items(self, user_id: UUID, team_id: UUID, filters: Dict[str, Any],
                        limit: int = 20, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """List backlog items with filters."""
        await self._check_team_access(user_id, team_id)
        
        return await self.backlog_repo.list_by_team(team_id, filters, limit, offset)
    
    async def update_item(self, user_id: UUID, team_id: UUID, item_id: UUID, 
                         **kwargs) -> Dict[str, Any]:
        """Update item fields."""
        await self._check_team_access(user_id, team_id)
        
        # Get current state for audit
        current = await self.backlog_repo.get_by_id(item_id, team_id)
        if not current:
            raise ValueError("Backlog item not found")
        
        # Validate sprint if updating
        if kwargs.get('sprint_id'):
            sprint = await self.sprint_repo.get_by_id(kwargs['sprint_id'], team_id)
            if not sprint:
                raise ValueError("Sprint not found or doesn't belong to this team")
        
        # Validate assigned_to if updating
        if kwargs.get('assigned_to'):
            if not await self.user_repo.is_team_member(kwargs['assigned_to'], team_id):
                raise ValueError("Assigned user is not a member of this team")
        
        updated = await self.backlog_repo.update(item_id, team_id, **kwargs)
        
        # Log changes
        changes = {k: v for k, v in kwargs.items() if v is not None and current.get(k) != v}
        if changes:
            await self._log_activity(user_id, team_id, "UPDATE", "backlog_item", item_id,
                                    {k: current.get(k) for k in changes.keys()}, changes)
        
        return updated
    
    async def update_status(self, user_id: UUID, team_id: UUID, item_id: UUID, new_status: str) -> Dict[str, Any]:
        """Change item status with workflow validation."""
        await self._check_team_access(user_id, team_id)
        
        # Get current item
        item = await self.backlog_repo.get_by_id(item_id, team_id)
        if not item:
            raise ValueError("Backlog item not found")
        
        old_status = item['status']
        
        # Validate transition
        if new_status not in self.ALLOWED_TRANSITIONS.get(old_status, []):
            allowed = ', '.join(self.ALLOWED_TRANSITIONS.get(old_status, []))
            raise ValueError(f"Invalid status transition from '{old_status}' to '{new_status}'. "
                           f"Allowed: {allowed if allowed else 'none (item cannot be changed)'}")
        
        # Additional validation: can't mark as done if not assigned
        if new_status == 'done' and not item.get('assigned_to'):
            # We'll allow but warn in logs - in strict mode, reject
            pass
        
        updated = await self.backlog_repo.update_status(item_id, team_id, new_status)
        
        # Log status change
        await self._log_activity(user_id, team_id, "STATUS_CHANGE", "backlog_item", item_id,
                                {'status': old_status}, {'status': new_status})
        
        return updated
    
    async def reorder_items(self, user_id: UUID, team_id: UUID, reorder_list: List[Tuple[UUID, int]]) -> bool:
        """Bulk reorder items by setting new priority ranks.
        
        Args:
            reorder_list: List of (item_id, new_rank) tuples
        """
        await self._check_team_access(user_id, team_id)
        
        # Verify all items belong to team
        for item_id, _ in reorder_list:
            item = await self.backlog_repo.get_by_id(item_id, team_id)
            if not item:
                raise ValueError(f"Item {item_id} not found in this team")
        
        # Perform reorder
        success = await self.backlog_repo.reorder_items(team_id, reorder_list)
        
        # Log reorder action
        await self._log_activity(user_id, team_id, "REORDER", "backlog", team_id,
                                None, {'reordered_items': len(reorder_list)})
        
        return success
    
    async def move_to_sprint(self, user_id: UUID, team_id: UUID, item_id: UUID, sprint_id: Optional[UUID]) -> Dict[str, Any]:
        """Move item to a sprint or remove from sprint."""
        await self._check_team_access(user_id, team_id)
        
        # Get current item
        item = await self.backlog_repo.get_by_id(item_id, team_id)
        if not item:
            raise ValueError("Backlog item not found")
        
        # Validate sprint if provided
        if sprint_id:
            sprint = await self.sprint_repo.get_by_id(sprint_id, team_id)
            if not sprint:
                raise ValueError("Sprint not found or doesn't belong to this team")
        
        updated = await self.backlog_repo.update(item_id, team_id, sprint_id=sprint_id)
        
        await self._log_activity(user_id, team_id, "SPRINT_MOVE", "backlog_item", item_id,
                                {'sprint_id': item.get('sprint_id')}, {'sprint_id': sprint_id})
        
        return updated
    
    async def delete_item(self, user_id: UUID, team_id: UUID, item_id: UUID) -> bool:
        """Delete an item."""
        await self._check_team_access(user_id, team_id)
        
        # Get item for audit before deletion
        item = await self.backlog_repo.get_by_id(item_id, team_id)
        if not item:
            raise ValueError("Backlog item not found")
        
        await self._log_activity(user_id, team_id, "DELETE", "backlog_item", item_id,
                                item, None)
        
        return await self.backlog_repo.delete(item_id, team_id)
    
    async def get_sprint_items(self, user_id: UUID, team_id: UUID, sprint_id: UUID) -> List[Dict[str, Any]]:
        """Get all items in a sprint with statistics."""
        await self._check_team_access(user_id, team_id)
        
        # Verify sprint belongs to team
        sprint = await self.sprint_repo.get_by_id(sprint_id, team_id)
        if not sprint:
            raise ValueError("Sprint not found or doesn't belong to this team")
        
        return await self.backlog_repo.get_team_items_in_sprint(team_id, sprint_id)