from fastapi import APIRouter, Depends, HTTPException, status, Query
from asyncpg import Connection
from uuid import UUID
from typing import List, Optional
from datetime import date
from app.db.database import get_db_connection
from app.repositories.sprint_repository import SprintRepository
from app.repositories.backlog_repository import BacklogRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.services.sprint_service import SprintService
from app.services.backlog_service import BacklogService
from app.api.dependencies import get_current_active_user
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintResponse, SprintDetailResponse
from app.schemas.backlog import BacklogItemResponse

router = APIRouter()

def get_sprint_service(conn: Connection = Depends(get_db_connection)) -> SprintService:
    """Dependency injection for sprint service."""
    sprint_repo = SprintRepository(conn)
    user_repo = UserRepository(conn)
    activity_repo = ActivityRepository(conn)
    return SprintService(sprint_repo, user_repo, activity_repo)

def get_backlog_service(conn: Connection = Depends(get_db_connection)) -> BacklogService:
    """Dependency injection for backlog service."""
    backlog_repo = BacklogRepository(conn)
    user_repo = UserRepository(conn)
    sprint_repo = SprintRepository(conn)
    activity_repo = ActivityRepository(conn)
    return BacklogService(backlog_repo, user_repo, sprint_repo, activity_repo)

@router.post("/teams/{team_id}/sprints", response_model=SprintResponse, status_code=status.HTTP_201_CREATED)
async def create_sprint(
    team_id: UUID,
    sprint_data: SprintCreate,
    current_user: dict = Depends(get_current_active_user),
    sprint_service: SprintService = Depends(get_sprint_service)
):
    """Create a new sprint for a team."""
    try:
        sprint = await sprint_service.create_sprint(
            user_id=current_user['id'],
            team_id=team_id,
            name=sprint_data.name,
            start_date=sprint_data.start_date,
            end_date=sprint_data.end_date,
            goal=sprint_data.goal
        )
        return sprint
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/teams/{team_id}/sprints", response_model=List[SprintResponse])
async def list_sprints(
    team_id: UUID,
    include_inactive: bool = Query(True, description="Include inactive sprints"),
    current_user: dict = Depends(get_current_active_user),
    sprint_service: SprintService = Depends(get_sprint_service)
):
    """List all sprints for a team."""
    try:
        sprints = await sprint_service.list_sprints(
            user_id=current_user['id'],
            team_id=team_id,
            include_inactive=include_inactive
        )
        return sprints
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/teams/{team_id}/sprints/{sprint_id}", response_model=SprintDetailResponse)
async def get_sprint(
    team_id: UUID,
    sprint_id: UUID,
    include_items: bool = Query(True, description="Include backlog items in sprint"),
    current_user: dict = Depends(get_current_active_user),
    sprint_service: SprintService = Depends(get_sprint_service),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Get sprint details with optional items."""
    try:
        sprint = await sprint_service.get_sprint(
            user_id=current_user['id'],
            team_id=team_id,
            sprint_id=sprint_id
        )
        
        if include_items:
            items = await backlog_service.get_sprint_items(
                user_id=current_user['id'],
                team_id=team_id,
                sprint_id=sprint_id
            )
            sprint['items'] = items
        
        return sprint
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/teams/{team_id}/sprints/{sprint_id}", response_model=SprintResponse)
async def update_sprint(
    team_id: UUID,
    sprint_id: UUID,
    sprint_data: SprintUpdate,
    current_user: dict = Depends(get_current_active_user),
    sprint_service: SprintService = Depends(get_sprint_service)
):
    """Update a sprint."""
    try:
        updates = sprint_data.model_dump(exclude_unset=True)
        sprint = await sprint_service.update_sprint(
            user_id=current_user['id'],
            team_id=team_id,
            sprint_id=sprint_id,
            **updates
        )
        return sprint
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/teams/{team_id}/sprints/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sprint(
    team_id: UUID,
    sprint_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    sprint_service: SprintService = Depends(get_sprint_service)
):
    """Delete a sprint (moves items to backlog)."""
    try:
        await sprint_service.delete_sprint(
            user_id=current_user['id'],
            team_id=team_id,
            sprint_id=sprint_id
        )
        return None
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))