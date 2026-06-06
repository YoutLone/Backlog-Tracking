from fastapi import APIRouter, Depends, HTTPException, status, Query
from asyncpg import Connection
from uuid import UUID
from typing import Optional, List, Dict, Any
from app.db.database import get_db_connection
from app.repositories.backlog_repository import BacklogRepository
from app.repositories.sprint_repository import SprintRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.services.backlog_service import BacklogService
from app.api.dependencies import get_current_active_user
from app.schemas.backlog import (
    BacklogItemCreate, BacklogItemUpdate, BacklogItemStatusUpdate,
    BacklogItemReorder, BacklogItemResponse, BacklogListFilters
)

router = APIRouter()

def get_backlog_service(conn: Connection = Depends(get_db_connection)) -> BacklogService:
    """Dependency injection for backlog service."""
    backlog_repo = BacklogRepository(conn)
    user_repo = UserRepository(conn)
    sprint_repo = SprintRepository(conn)
    activity_repo = ActivityRepository(conn)
    return BacklogService(backlog_repo, user_repo, sprint_repo, activity_repo)

@router.post("/teams/{team_id}/items", response_model=BacklogItemResponse, status_code=status.HTTP_201_CREATED)
async def create_backlog_item(
    team_id: UUID,
    item_data: BacklogItemCreate,
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Create a new backlog item."""
    try:
        item = await backlog_service.create_item(
            user_id=current_user['id'],
            team_id=team_id,
            title=item_data.title,
            description=item_data.description,
            item_type=item_data.type.value,
            story_points=item_data.story_points,
            assigned_to=item_data.assigned_to
        )
        return item
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/teams/{team_id}/items", response_model=Dict[str, Any])
async def list_backlog_items(
    team_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by type"),
    sprint_id: Optional[UUID] = Query(None, description="Filter by sprint"),
    assigned_to: Optional[UUID] = Query(None, description="Filter by assignee"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """List backlog items with pagination and filtering."""
    filters = {
        'status': status,
        'type': type,
        'sprint_id': sprint_id,
        'assigned_to': assigned_to
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    try:
        items, total = await backlog_service.list_items(
            user_id=current_user['id'],
            team_id=team_id,
            filters=filters,
            limit=limit,
            offset=offset
        )
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "next_offset": offset + limit if offset + limit < total else None
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/teams/{team_id}/items/{item_id}", response_model=BacklogItemResponse)
async def get_backlog_item(
    team_id: UUID,
    item_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Get a specific backlog item."""
    try:
        item = await backlog_service.get_item(
            user_id=current_user['id'],
            team_id=team_id,
            item_id=item_id
        )
        return item
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/teams/{team_id}/items/{item_id}", response_model=BacklogItemResponse)
async def update_backlog_item(
    team_id: UUID,
    item_id: UUID,
    item_data: BacklogItemUpdate,
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Update a backlog item."""
    try:
        # Build update dict with only provided fields
        updates = item_data.model_dump(exclude_unset=True)
        item = await backlog_service.update_item(
            user_id=current_user['id'],
            team_id=team_id,
            item_id=item_id,
            **updates
        )
        return item
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/teams/{team_id}/items/{item_id}/status", response_model=BacklogItemResponse)
async def update_item_status(
    team_id: UUID,
    item_id: UUID,
    status_data: BacklogItemStatusUpdate,
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Update item status with workflow validation."""
    try:
        item = await backlog_service.update_status(
            user_id=current_user['id'],
            team_id=team_id,
            item_id=item_id,
            new_status=status_data.status.value
        )
        return item
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/teams/{team_id}/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_backlog_items(
    team_id: UUID,
    reorder_data: List[BacklogItemReorder],
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Reorder backlog items (bulk update priority ranks)."""
    try:
        reorder_list = [(item.item_id, item.new_rank) for item in reorder_data]
        await backlog_service.reorder_items(
            user_id=current_user['id'],
            team_id=team_id,
            reorder_list=reorder_list
        )
        return None
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/teams/{team_id}/items/{item_id}/sprint", response_model=BacklogItemResponse)
async def move_item_to_sprint(
    team_id: UUID,
    item_id: UUID,
    sprint_id: Optional[UUID] = Query(None, description="Sprint ID to assign (null to remove from sprint)"),
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Move backlog item to a sprint or remove from sprint."""
    try:
        item = await backlog_service.move_to_sprint(
            user_id=current_user['id'],
            team_id=team_id,
            item_id=item_id,
            sprint_id=sprint_id
        )
        return item
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/teams/{team_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backlog_item(
    team_id: UUID,
    item_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    backlog_service: BacklogService = Depends(get_backlog_service)
):
    """Delete a backlog item."""
    try:
        await backlog_service.delete_item(
            user_id=current_user['id'],
            team_id=team_id,
            item_id=item_id
        )
        return None
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))