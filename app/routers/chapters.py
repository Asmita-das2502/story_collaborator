from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import StoryRoom, Chapter
from app.schemas import ChapterDraftRequest, ChapterSaveRequest, ChapterResponse
from app.memory.cognee_client import get_story_context_for_chapter
import os
from groq import AsyncGroq

router = APIRouter(prefix="/api", tags=["chapters"])


groq_client = AsyncGroq(api_key=os.getenv("LLM_API_KEY"))


@router.post("/rooms/{room_id}/draft-chapter")
async def draft_chapter(
    room_id: str,
    payload: ChapterDraftRequest,
    db: AsyncSession = Depends(get_db)
):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    
    print(f"[Chapter Draft] Pulling story context for room {room_id}...")
    context = await get_story_context_for_chapter(
        room_id=room_id,
        chapter_number=payload.chapter_number
    )

    # Step 2: Build a detailed prompt using the graph context
    chapter_title = payload.title or f"Chapter {payload.chapter_number}"

    system_prompt = f"""You are a creative writing assistant helping two authors write their story.
Your job is to draft Chapter {payload.chapter_number}: "{chapter_title}" based on everything 
the authors have discussed so far.

Here is what you know about the story:

CHARACTERS:
{context['characters']}

PLOT THREADS AND DIRECTION:
{context['plot_threads']}

TONE, GENRE AND SETTING:
{context['tone_setting']}

Write in a style consistent with what the authors have discussed.
The chapter should feel natural, engaging, and true to the story world they've built.
Write approximately 400-600 words for this draft."""

    user_prompt = (
        f"Please write Chapter {payload.chapter_number}: \"{chapter_title}\". "
        f"Make it compelling and consistent with everything we've discussed about our story."
    )

  
    print(f"[Chapter Draft] Generating chapter with Groq...")
    response = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1000,
        temperature=0.8  # Slightly creative for storytelling
    )

    draft_content = response.choices[0].message.content

    chapter = Chapter(
        room_id=room_id,
        chapter_number=payload.chapter_number,
        title=payload.title,
        content=draft_content,
        is_draft=True  # Marked as draft until authors review and finalize
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)

    return {
        "chapter": ChapterResponse.model_validate(chapter),
        "context_used": context 
    }


@router.put("/rooms/{room_id}/chapters/{chapter_id}", response_model=ChapterResponse)
async def save_chapter(
    room_id: str,
    chapter_id: str,
    payload: ChapterSaveRequest,
    db: AsyncSession = Depends(get_db)
):
    chapter = await db.get(Chapter, chapter_id)
    if not chapter or chapter.room_id != room_id:
        raise HTTPException(status_code=404, detail="Chapter not found")

    chapter.content = payload.content
    chapter.is_draft = payload.is_draft
    if payload.title:
        chapter.title = payload.title

    await db.flush()
    await db.refresh(chapter)
    return chapter

@router.get("/rooms/{room_id}/chapters", response_model=list[ChapterResponse])
async def get_chapters(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await db.get(StoryRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Story room not found")

    result = await db.execute(
        select(Chapter)
        .where(Chapter.room_id == room_id)
        .order_by(Chapter.chapter_number)
    )
    return result.scalars().all()