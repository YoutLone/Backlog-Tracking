from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Connection
from uuid import UUID
from typing import List
from app.db.database import get_db_connection
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.services.team_service import TeamService
from app.api.dependencies import get_current_active_user
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, AddTeamMember, TeamMemberResponse

router = APIRouter()

def get_team_service(conn: Connection = Depends(get_db_connection)) -> TeamService:
    """Dependency injection for team service."""
    team_repo = TeamRepository(conn)
    user_repo = UserRepository(conn)
    return TeamService(team_repo, user_repo)

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """Create a new team (creator becomes admin)."""
    try:
        team = await team_service.create_team(
            user_id=current_user['id'],
            name=team_data.name,
            description=team_data.description
        )
        return team
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[TeamResponse])
async def list_my_teams(
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """List all teams the current user belongs to."""
    teams = await team_service.list_teams_for_user(current_user['id'])
    return teams

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """Get team details (requires membership)."""
    try:
        team = await team_service.get_team(team_id, current_user['id'])
        return team
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """Update team (admin only)."""
    try:
        team = await team_service.update_team(
            team_id=team_id,
            user_id=current_user['id'],
            name=team_data.name,
            description=team_data.description
        )
        return team
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """Delete team (admin only)."""
    try:
        await team_service.delete_team(team_id, current_user['id'])
        return None
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{team_id}/members", response_model=dict)
async def add_team_member(
    team_id: UUID,
    member_data: AddTeamMember,
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """Add a member to the team (admin only)."""
    try:
        result = await team_service.add_member(
            team_id=team_id,
            user_id=member_data.user_id,
            requester_id=current_user['id'],
            role=member_data.role.value
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """Remove a member from the team (admin only)."""
    try:
        await team_service.remove_member(
            team_id=team_id,
            user_id=user_id,
            requester_id=current_user['id']
        )
        return None
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    team_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    team_service: TeamService = Depends(get_team_service)
):
    """List all members of a team (requires membership)."""
    try:
        members = await team_service.get_members(team_id, current_user['id'])
        return members
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))