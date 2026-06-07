from pydantic import BaseModel, Field, field_validator, model_serializer
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List, ForwardRef

class SprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    goal: Optional[str] = Field(None, max_length=500)
    start_date: date
    end_date: date
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError('end_date must be after start_date')
        return v

class SprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    goal: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class SprintResponse(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    goal: Optional[str]
    start_date: date
    end_date: date
    is_active: bool
    created_by: UUID  
    created_at: datetime
    updated_at: datetime
    total_story_points: Optional[int] = None
    completed_story_points: Optional[int] = None
    item_count: Optional[int] = None
    
    class Config:
        from_attributes = True
# Use string forward reference for the circular dependency
class SprintDetailResponse(SprintResponse):
    items: List["BacklogItemResponse"] = []
    
    class Config:
        from_attributes = True

# Import here at the bottom to resolve circular reference
from app.schemas.backlog import BacklogItemResponse