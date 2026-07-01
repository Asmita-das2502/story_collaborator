from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
# User schemas
# ─────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# StoryRoom schemas
# ─────────────────────────────────────────────
class StoryRoomCreate(BaseModel):
    name: str

class StoryRoomResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Message schemas
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# Chapter schemas
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# Summary schema
# ─────────────────────────────────────────────
class SummaryResponse(BaseModel):
    summary: str
    room_id: str