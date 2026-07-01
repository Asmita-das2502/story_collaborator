from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import StoryRoom
from app.schemas import SummaryResponse
from app.memory.cognee_client import get_story_summary, get_unresolved_threads

router = APIRouter(prefix="/api", tags=["summary"])


# ─────────────────────────────────────────────
# STORY SUMMARY
# Queries Cognee's graph for a full narrative
# summary of everything discussed so far
# ─────────────────────────────────────────────

@router.get("/rooms/{room_id}/summary", response_model=SummaryResponse)
async def story_summary(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    summary = await get_story_summary(room_id=room_id)
    return {"summary": summary, "room_id": room_id}


# ─────────────────────────────────────────────
# UNRESOLVED THREADS (stretch goal)
# Uses INSIGHTS search to find loose ends
# Only expose this once core features work
# ─────────────────────────────────────────────

@router.get("/rooms/{room_id}/threads")
async def unresolved_threads(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    threads = await get_unresolved_threads(room_id=room_id)
    return {"threads": threads, "room_id": room_id}