from app.repositories.sprint_repository import SprintRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from uuid import UUID
from typing import Dict, Any, List, Optional
from datetime import date

class SprintService:
    """Sprint management business logic."""
    
    def __init__(self, sprint_repo: SprintRepository, user_repo: UserRepository, activity_repo: ActivityRepository):
        self.sprint_repo = sprint_repo
        self.user_repo = user_repo
        self.activity_repo = activity_repo
    
    async def _check_team_access(self, user_id: UUID, team_id: UUID):
        """Helper to verify team membership."""
        if not await self.user_repo.is_team_member(user_id, team_id):
            raise PermissionError("User not a member of this team")
    
    async def create_sprint(self, user_id: UUID, team_id: UUID, name: str, 
                           start_date: date, end_date: date, goal: str = None) -> Dict[str, Any]:
        """Create a new sprint."""
        await self._check_team_access(user_id, team_id)
        
        sprint = await self.sprint_repo.create(team_id, user_id, name, start_date, end_date, goal)
        
        await self.activity_repo.log(user_id, team_id, "CREATE_SPRINT", "sprint", sprint['id'],
                                    None, sprint)
        
        return sprint
    
    async def get_sprint(self, user_id: UUID, team_id: UUID, sprint_id: UUID) -> Dict[str, Any]:
        """Get sprint details."""
        await self._check_team_access(user_id, team_id)
        
        sprint = await self.sprint_repo.get_by_id(sprint_id, team_id)
        if not sprint:
            raise ValueError("Sprint not found")
        
        # Add statistics
        stats = await self.sprint_repo.get_sprint_statistics(sprint_id, team_id)
        sprint.update(stats)
        
        return sprint
    
    async def list_sprints(self, user_id: UUID, team_id: UUID, include_inactive: bool = True) -> List[Dict[str, Any]]:
        """List all sprints for a team."""
        await self._check_team_access(user_id, team_id)
        
        sprints = await self.sprint_repo.list_by_team(team_id, include_inactive)
        
        # Add statistics to each sprint
        for sprint in sprints:
            stats = await self.sprint_repo.get_sprint_statistics(sprint['id'], team_id)
            sprint.update(stats)
        
        return sprints
    
    async def update_sprint(self, user_id: UUID, team_id: UUID, sprint_id: UUID, 
                           **kwargs) -> Dict[str, Any]:
        """Update sprint."""
        await self._check_team_access(user_id, team_id)
        
        current = await self.sprint_repo.get_by_id(sprint_id, team_id)
        if not current:
            raise ValueError("Sprint not found")
        
        updated = await self.sprint_repo.update(sprint_id, team_id, **kwargs)
        
        # Log changes
        changes = {k: v for k, v in kwargs.items() if v is not None and current.get(k) != v}
        if changes:
            await self.activity_repo.log(user_id, team_id, "UPDATE_SPRINT", "sprint", sprint_id,
                                        {k: current.get(k) for k in changes.keys()}, changes)
        
        # Add statistics
        stats = await self.sprint_repo.get_sprint_statistics(sprint_id, team_id)
        updated.update(stats)
        
        return updated
    
    async def delete_sprint(self, user_id: UUID, team_id: UUID, sprint_id: UUID) -> bool:
        """Delete sprint (moves items to backlog)."""
        await self._check_team_access(user_id, team_id)
        
        sprint = await self.sprint_repo.get_by_id(sprint_id, team_id)
        if not sprint:
            raise ValueError("Sprint not found")
        
        await self.activity_repo.log(user_id, team_id, "DELETE_SPRINT", "sprint", sprint_id,
                                    sprint, None)
        
        return await self.sprint_repo.delete(sprint_id, team_id)