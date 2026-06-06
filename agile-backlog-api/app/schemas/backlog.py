from pydantic import BaseModel, Field, field_validator, model_serializer
from uuid import UUID
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING, ForwardRef
from enum import Enum

class BacklogItemType(str, Enum):
    STORY = "story"
    BUG = "bug"
    TASK = "task"

class BacklogItemStatus(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class BacklogItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    type: BacklogItemType = BacklogItemType.TASK
    story_points: Optional[int] = Field(None, ge=0, le=100)
    assigned_to: Optional[UUID] = None

class BacklogItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    type: Optional[BacklogItemType] = None
    story_points: Optional[int] = Field(None, ge=0, le=100)
    assigned_to: Optional[UUID] = None

class BacklogItemStatusUpdate(BaseModel):
    status: BacklogItemStatus
    
    @field_validator('status')
    @classmethod
    def validate_transition(cls, v: BacklogItemStatus) -> BacklogItemStatus:
        return v

class BacklogItemReorder(BaseModel):
    """Request to reorder items."""
    item_id: UUID
    new_rank: int  # Position where to place this item (1-based index)
    
class BacklogItemResponse(BaseModel):
    id: UUID
    team_id: UUID
    sprint_id: Optional[UUID]
    title: str
    description: Optional[str]
    type: BacklogItemType
    status: BacklogItemStatus
    priority_rank: int
    story_points: Optional[int]
    created_by: UUID
    assigned_to: Optional[UUID]
    creator_email: Optional[str] = None
    assignee_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class BacklogListFilters(BaseModel):
    """Query parameters for listing backlog items."""
    status: Optional[BacklogItemStatus] = None
    type: Optional[BacklogItemType] = None
    sprint_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)