from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, StoryRoom, Message
from app.schemas import (
    UserCreate, UserResponse,
    StoryRoomCreate, StoryRoomResponse,
    MessageCreate, MessageResponse
)
from app.memory.cognee_client import remember_message, recall_story_context

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/users", response_model=UserResponse)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.name == payload.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this name already exists")
    user = User(name=payload.name)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.get("/users", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()


@router.post("/rooms", response_model=StoryRoomResponse)
async def create_room(payload: StoryRoomCreate, db: AsyncSession = Depends(get_db)):
    room = StoryRoom(name=payload.name)
    db.add(room)
    await db.flush()
    await db.refresh(room)
    return room


@router.get("/rooms", response_model=list[StoryRoomResponse])
async def get_rooms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StoryRoom).order_by(StoryRoom.created_at))
    return result.scalars().all()


@router.post("/messages", response_model=MessageResponse)
async def send_message(payload: MessageCreate, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, payload.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    sender = await db.get(User, payload.sender_id)
    if not sender:
        raise HTTPException(status_code=404, detail="User not found")

    
    message = Message(
        room_id=payload.room_id,
        sender_id=payload.sender_id,
        content=payload.content
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)


    ingested = await remember_message(
        room_id=payload.room_id,
        sender_name=sender.name,
        content=payload.content
    )

    if ingested:
        message.fed_to_cognee = True
        await db.flush()

    return message


@router.get("/rooms/{room_id}/messages", response_model=list[MessageResponse])
async def get_messages(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    result = await db.execute(
        select(Message)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()


@router.post("/rooms/{room_id}/recall")
async def recall(room_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    query = body.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    answer = await recall_story_context(room_id=room_id, query=query)
    return {"query": query, "answer": answer, "room_id": room_id}