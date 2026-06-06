from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from uuid import UUID
from typing import Dict, Any, List

class TeamService:
    """Team management business logic with authorization."""
    
    def __init__(self, team_repo: TeamRepository, user_repo: UserRepository):
        self.team_repo = team_repo
        self.user_repo = user_repo
    
    async def create_team(self, user_id: UUID, name: str, description: str = None) -> Dict[str, Any]:
        """Create a new team with current user as admin."""
        return await self.team_repo.create(name, user_id, description)
    
    async def get_team(self, team_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get team if user is a member."""
        if not await self.user_repo.is_team_member(user_id, team_id):
            raise PermissionError("User not a member of this team")
        
        team = await self.team_repo.get_by_id(team_id)
        if not team:
            raise ValueError("Team not found")
        
        return team
    
    async def update_team(self, team_id: UUID, user_id: UUID, name: str = None, description: str = None) -> Dict[str, Any]:
        """Update team if user is admin."""
        if not await self.user_repo.is_team_admin(user_id, team_id):
            raise PermissionError("Only team admins can update team")
        
        team = await self.team_repo.update(team_id, name, description)
        if not team:
            raise ValueError("Team not found")
        
        return team
    
    async def delete_team(self, team_id: UUID, user_id: UUID) -> bool:
        """Delete team if user is admin."""
        if not await self.user_repo.is_team_admin(user_id, team_id):
            raise PermissionError("Only team admins can delete team")
        
        return await self.team_repo.delete(team_id)
    
    async def add_member(self, team_id: UUID, user_id: UUID, requester_id: UUID, role: str = 'member') -> Dict[str, Any]:
        """Add member if requester is admin."""
        if not await self.user_repo.is_team_admin(requester_id, team_id):
            raise PermissionError("Only team admins can add members")
        
        # Check if user exists
        user = await self.user_repo.get_by_id(str(user_id))
        if not user:
            raise ValueError("User not found")
        
        success = await self.team_repo.add_member(team_id, user_id, role)
        if not success:
            raise ValueError("User is already a member of this team")
        
        return {"user_id": user_id, "role": role, "message": "Member added successfully"}
    
    async def remove_member(self, team_id: UUID, user_id: UUID, requester_id: UUID) -> Dict[str, Any]:
        """Remove member if requester is admin and not removing last admin."""
        if not await self.user_repo.is_team_admin(requester_id, team_id):
            raise PermissionError("Only team admins can remove members")
        
        # Can't remove yourself if you're the last admin - repository handles this
        try:
            success = await self.team_repo.remove_member(team_id, user_id)
            if not success:
                raise ValueError("User is not a member of this team")
        except ValueError as e:
            raise ValueError(str(e))
        
        return {"message": "Member removed successfully"}
    
    async def list_teams_for_user(self, user_id: UUID) -> List[Dict[str, Any]]:
        """List all teams a user belongs to."""
        return await self.user_repo.get_teams(user_id)
    
    async def get_members(self, team_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        """List team members if user is member."""
        if not await self.user_repo.is_team_member(user_id, team_id):
            raise PermissionError("User not a member of this team")
        
        return await self.team_repo.get_members(team_id)