"""
app/memory/cognee_client.py

All Cognee memory operations for Story Collaborator.
Uses the full Cognee lifecycle API:
- cognee.remember() — ingest messages into the knowledge graph (V2 API)
- cognee.recall()   — simple freeform retrieval (V2 API)
- cognee.search()   — advanced retrieval with specific SearchType control
- cognee.improve()  — reinforce graph when a chapter is finalized
- cognee.forget()   — surgically clear a story room's graph
"""

import cognee
from cognee.api.v1.search.search import SearchType
import os
from dotenv import load_dotenv

load_dotenv()


def _dataset_name(room_id: str) -> str:
    return f"story_room_{room_id}"



def _extract_text(results) -> str:
    if not results:
        return ""
    parts = []
    for r in results:
        if isinstance(r, dict):
            search_result = r.get("search_result", [])
            if isinstance(search_result, list):
                parts.extend(search_result)
            elif search_result:
                parts.append(str(search_result))
            else:
                parts.append(r.get("text", str(r)))
        else:
            parts.append(str(r))
    return "\n\n".join(p for p in parts if p)



async def remember_message(room_id: str, sender_name: str, content: str) -> bool:
    """
    Ingests a chat message into Cognee's knowledge graph.
    Uses cognee.remember() — the V2 API that combines add + cognify in one call.
    Format: "Sender said: content" — gives Cognee enough context to extract
    who said what as named entities in the graph.
    """
    try:
        formatted_text = f'{sender_name} said: "{content}"'
        dataset = _dataset_name(room_id)

        # V2 API: remember = add + cognify in one call
        await cognee.remember(formatted_text, dataset_name=dataset)
        return True

    except Exception as e:
        print(f"[Cognee] remember() failed: {e}")
        return False



async def recall_story_context(room_id: str, query: str) -> str:
    """
    General-purpose recall from the story's knowledge graph.
    Uses cognee.recall() — the V2 API for simple retrieval.
    Best for freeform questions like "what do we know about Kira?"
    """
    try:
        dataset = _dataset_name(room_id)

        # V2 API: recall = search with smart defaults
        results = await cognee.recall(query, dataset_name=dataset)

        return _extract_text(results) or "I couldn't find relevant information about that in your story memory."

    except Exception as e:
        print(f"[Cognee] recall() failed: {e}")
        # Fallback to search() if recall() fails
        try:
            results = await cognee.search(
                query,
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=[dataset]
            )
            return _extract_text(results) or "I couldn't find relevant information."
        except Exception as e2:
            return f"Memory recall failed: {str(e2)}"


async def improve_from_chapter(room_id: str, chapter_content: str) -> bool:
    """
    Feeds finalized chapter content back into the graph via cognee.improve().
    This reinforces successful story decisions so future recalls and
    suggestions are shaped by what the authors actually approved — not
    just raw discussion messages.
    Called automatically when is_draft is set to False.
    """
    try:
        dataset = _dataset_name(room_id)

        # Use first 800 chars — enough context without overwhelming the graph
        content_preview = chapter_content[:800]
        await cognee.improve(
            f"Finalized and approved chapter content: {content_preview}",
            dataset_name=dataset
        )
        return True

    except Exception as e:
        print(f"[Cognee] improve() failed: {e}")
        return False



async def forget_story_memory(room_id: str) -> bool:
    """
    Surgically clears the knowledge graph for a specific story room.
    Uses cognee.forget() — removes only this room's dataset.
    Raw messages in Postgres are preserved — only the Cognee graph is cleared.
    Useful when authors completely change story direction and want
    the agent to forget old context.
    """
    try:
        dataset = _dataset_name(room_id)
        await cognee.forget(dataset_name=dataset)
        return True

    except Exception as e:
        print(f"[Cognee] forget() failed: {e}")
        return False



async def get_story_summary(room_id: str) -> str:
    """
    Returns a comprehensive narrative summary pulled from the knowledge graph.
    Uses cognee.search() with GRAPH_COMPLETION for full graph traversal —
    connects characters, plot points, conflicts and themes into one summary.
    """
    try:
        dataset = _dataset_name(room_id)

        results = await cognee.search(
            "Give me a comprehensive summary of this story so far. "
            "Include the main characters and their roles, "
            "the key plot points discussed, "
            "any conflicts or tensions, "
            "and the overall themes or tone.",
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[dataset]
        )

        return _extract_text(results) or "No story content has been added to memory yet. Start discussing your story and the summary will appear here."

    except Exception as e:
        print(f"[Cognee] Summary retrieval failed: {e}")
        return f"Could not retrieve summary at this time. Error: {str(e)}"



async def get_story_context_for_chapter(room_id: str, chapter_number: int) -> dict:
    """
    Pulls structured story context for chapter drafting.
    Runs three separate GRAPH_COMPLETION queries — characters, plot, tone —
    so the LLM gets focused, structured context rather than a raw dump.
    """
    dataset = _dataset_name(room_id)

    async def _query(question: str) -> str:
        try:
            results = await cognee.search(
                question,
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=[dataset]
            )
            return _extract_text(results) or "Not enough information in memory yet."
        except Exception as e:
            return f"Could not retrieve: {str(e)}"

    characters = await _query(
        "Who are the main characters in this story? "
        "Describe each one briefly including their role and personality."
    )
    plot_threads = await _query(
        f"What are the most important plot threads and events discussed so far? "
        f"What should happen in chapter {chapter_number} based on the story's direction?"
    )
    tone_setting = await _query(
        "What is the tone, genre, and setting of this story? "
        "Describe the world or atmosphere the authors have discussed."
    )

    return {
        "characters": characters,
        "plot_threads": plot_threads,
        "tone_setting": tone_setting,
    }


async def get_story_suggestions(room_id: str, suggestion_type: str = "plot") -> str:
    """
    Suggests story directions based on the knowledge graph.
    Uses GRAPH_COMPLETION to generate ideas organic to this specific story.
    """
    try:
        dataset = _dataset_name(room_id)

        prompts = {
            "plot": (
                "Based on the story so far, suggest 3 compelling plot directions "
                "the authors could take next. Consider the existing characters, "
                "conflicts, and themes. Make each suggestion specific and exciting."
            ),
            "character": (
                "Based on the characters discussed so far, suggest 2-3 ways "
                "to deepen their arcs or introduce a new character that would "
                "add interesting conflict or dynamic to the story."
            ),
            "twist": (
                "Based on the story so far, suggest 2-3 unexpected plot twists "
                "that would feel surprising but inevitable in hindsight. "
                "Each twist should connect to something already established."
            ),
            "ending": (
                "Based on the story themes, characters and conflicts so far, "
                "suggest 2-3 possible endings — one hopeful, one tragic, "
                "and one ambiguous. Each should feel earned by the story."
            )
        }

        query = prompts.get(suggestion_type, prompts["plot"])

        results = await cognee.search(
            query,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[dataset]
        )

        return _extract_text(results) or "Add more story details first so I can make meaningful suggestions!"

    except Exception as e:
        print(f"[Cognee] Story suggestions failed: {e}")
        return f"Could not generate suggestions: {str(e)}"


async def get_unresolved_threads(room_id: str) -> str:
    """
    Finds unresolved plot threads and character arcs.
    Uses GRAPH_SUMMARY_COMPLETION which summarizes patterns across the
    entire graph — ideal for detecting what's been mentioned but never resolved.
    """
    try:
        dataset = _dataset_name(room_id)

        results = await cognee.search(
            "What plot threads, character arcs, or story questions "
            "have been raised in our discussions but not yet resolved or answered? "
            "List any loose ends or unanswered questions in the story.",
            query_type=SearchType.GRAPH_SUMMARY_COMPLETION,
            datasets=[dataset]
        )

        return _extract_text(results) or "No unresolved threads detected yet — keep adding to your story!"

    except Exception as e:
        print(f"[Cognee] Unresolved thread detection failed: {e}")
        return f"Could not analyse story threads: {str(e)}"