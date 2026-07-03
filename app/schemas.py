from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}

class StoryRoomCreate(BaseModel):
    name: str

class StoryRoomResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}

class MessageCreate(BaseModel):
    room_id: str
    sender_id: str
    content: str

class MessageResponse(BaseModel):
    id: str
    room_id: str
    sender_id: str
    content: str
    fed_to_cognee: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class ChapterDraftRequest(BaseModel):
    room_id: str
    chapter_number: int
    title: Optional[str] = None

class ChapterSaveRequest(BaseModel):
    title: Optional[str] = None
    content: str
    is_draft: bool = False  # False = reviewed and finalized

class ChapterResponse(BaseModel):
    id: str
    room_id: str
    chapter_number: int
    title: Optional[str]
    content: str
    is_draft: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class SummaryResponse(BaseModel):
    summary: str
    room_id: str