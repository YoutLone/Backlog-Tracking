from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TeamRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class TeamResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class AddTeamMember(BaseModel):
    user_id: UUID
    role: TeamRole = TeamRole.MEMBER

class TeamMemberResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: Optional[str]
    role: str
    joined_at: datetime