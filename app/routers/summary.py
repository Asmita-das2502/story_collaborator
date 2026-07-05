from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import StoryRoom
from app.schemas import SummaryResponse
from app.memory.cognee_client import (
    get_story_summary,
    get_unresolved_threads,
    get_story_suggestions,
    forget_story_memory
)

router = APIRouter(prefix="/api", tags=["summary"])


@router.get("/rooms/{room_id}/summary", response_model=SummaryResponse)
async def story_summary(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")
    summary = await get_story_summary(room_id=room_id)
    return {"summary": summary, "room_id": room_id}


@router.get("/rooms/{room_id}/threads")
async def unresolved_threads(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")
    threads = await get_unresolved_threads(room_id=room_id)
    return {"threads": threads, "room_id": room_id}


@router.get("/rooms/{room_id}/suggestions")
async def story_suggestions(
    room_id: str,
    suggestion_type: str = Query(default="plot"),
    db: AsyncSession = Depends(get_db)
):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    if suggestion_type not in ["plot", "character", "twist", "ending"]:
        raise HTTPException(
            status_code=400,
            detail="suggestion_type must be one of: plot, character, twist, ending"
        )

    suggestions = await get_story_suggestions(
        room_id=room_id,
        suggestion_type=suggestion_type
    )
    return {"suggestions": suggestions, "suggestion_type": suggestion_type, "room_id": room_id}


@router.delete("/rooms/{room_id}/memory")
async def clear_memory(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    success = await forget_story_memory(room_id=room_id)
    if success:
        return {"message": "Story memory cleared successfully. Your messages are preserved but the knowledge graph has been reset.", "room_id": room_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear memory")