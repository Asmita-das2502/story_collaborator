"""
app/memory/cognee_client.py

All Cognee memory operations for Story Collaborator live here.
This is the "memory brain" of the app — every other file that needs
to remember or recall story context imports from here.

Why centralise here?
- One place to configure session_id / dataset scoping
- Easy to swap local Cognee for Cognee Cloud later (just change config)
- Clear separation: routers handle HTTP, this file handles memory
"""

import cognee
from cognee.api.v1.search.search import SearchType
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────
# DATASET NAMING CONVENTION
#
# We scope all memory per story room using Cognee's dataset_name param.
# This means two story rooms never bleed into each other's graph.
#
# dataset name: "story_room_{room_id}"
# ─────────────────────────────────────────────────────────────────────

def _dataset_name(room_id: str) -> str:
    """Returns the Cognee dataset name scoped to a specific story room."""
    return f"story_room_{room_id}"


# ─────────────────────────────────────────────────────────────────────
# INGEST A MESSAGE INTO THE KNOWLEDGE GRAPH
#
# Called every time a user sends a message.
# We format it as "Character/User said: message content" so the graph
# extracts who said what, not just raw text.
# ─────────────────────────────────────────────────────────────────────

async def remember_message(room_id: str, sender_name: str, content: str) -> bool:
    """
    Ingests a single chat message into Cognee's knowledge graph
    for the given story room.

    Returns True on success, False on failure (so the app doesn't crash
    if Cognee has a hiccup — the message is still saved in Postgres).
    """
    try:
        # Format: gives Cognee enough context to extract meaningful entities
        # e.g. "Asmita said: Kira is a warrior who lost her memory..."
        # → Cognee extracts: entity "Kira", relationship "is a warrior", attribute "lost memory"
        formatted_text = f'{sender_name} said: "{content}"'

        dataset = _dataset_name(room_id)

        # V1 API: add → cognify
        # We use V1 here (not remember()) because we want explicit dataset scoping
        # per story room, which is cleaner with V1's dataset_name param
        await cognee.add(formatted_text, dataset_name=dataset)
        await cognee.cognify(datasets=[dataset])

        return True

    except Exception as e:
        print(f"[Cognee] Failed to ingest message: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────
# GET A STORY SUMMARY
#
# Queries the graph for a structured summary of the story so far —
# characters, plot points, conflicts, themes.
# Uses GRAPH_COMPLETION: natural language Q&A using full graph context.
# ─────────────────────────────────────────────────────────────────────

async def get_story_summary(room_id: str) -> str:
    """
    Returns a narrative summary of the story so far, pulled from
    the knowledge graph built from all past messages in this room.
    """
    try:
        dataset = _dataset_name(room_id)

        results = await cognee.search(
            SearchType.GRAPH_COMPLETION,
            query_text=(
                "Give me a comprehensive summary of this story so far. "
                "Include: the main characters and their roles, "
                "the key plot points discussed, "
                "any conflicts or tensions, "
                "and the overall themes or tone."
            ),
            datasets=[dataset]
        )

        if not results:
            return "No story content has been added to memory yet. Start discussing your story and the summary will appear here."

        # results is a list — join them into a readable block
        if isinstance(results, list):
            return "\n\n".join(
                r.get("text", str(r)) if isinstance(r, dict) else str(r)
                for r in results
            )

        return str(results)

    except Exception as e:
        print(f"[Cognee] Summary retrieval failed: {e}")
        return f"Could not retrieve summary at this time. Error: {str(e)}"


# ─────────────────────────────────────────────────────────────────────
# GET STORY CONTEXT FOR CHAPTER DRAFTING
#
# Before drafting a chapter, we pull targeted context from the graph:
# - Who are the active characters?
# - What's the most recent plot thread?
# - What's the tone/setting?
# This context gets passed to Groq as a system prompt for generation.
# ─────────────────────────────────────────────────────────────────────

async def get_story_context_for_chapter(room_id: str, chapter_number: int) -> dict:
    """
    Returns structured story context to use when drafting a chapter.
    Queries the graph with targeted questions to extract:
    - characters
    - recent plot threads
    - setting/tone

    Returns a dict with keys: characters, plot_threads, tone_setting
    """
    dataset = _dataset_name(room_id)

    async def _query(question: str) -> str:
        try:
            results = await cognee.search(
                SearchType.GRAPH_COMPLETION,
                query_text=question,
                datasets=[dataset]
            )
            if not results:
                return "Not enough information in memory yet."
            if isinstance(results, list):
                return "\n".join(
                    r.get("text", str(r)) if isinstance(r, dict) else str(r)
                    for r in results
                )
            return str(results)
        except Exception as e:
            return f"Could not retrieve: {str(e)}"

    # Three targeted graph queries — each pulls a different aspect
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


# ─────────────────────────────────────────────────────────────────────
# RECALL — GENERAL PURPOSE QUERY
#
# For any freeform question about the story memory.
# Uses GRAPH_COMPLETION by default.
# ─────────────────────────────────────────────────────────────────────

async def recall_story_context(room_id: str, query: str) -> str:
    """
    General-purpose recall from the story's knowledge graph.
    Use this for freeform questions like:
    - "What do we know about Kira's backstory?"
    - "Have we decided on the magic system yet?"
    - "What happened in the last scene we discussed?"
    """
    try:
        dataset = _dataset_name(room_id)

        results = await cognee.search(
            SearchType.GRAPH_COMPLETION,
            query_text=query,
            datasets=[dataset]
        )

        if not results:
            return "I couldn't find relevant information about that in your story memory."

        if isinstance(results, list):
            return "\n\n".join(
                r.get("text", str(r)) if isinstance(r, dict) else str(r)
                for r in results
            )

        return str(results)

    except Exception as e:
        print(f"[Cognee] Recall failed: {e}")
        return f"Memory recall failed: {str(e)}"


# ─────────────────────────────────────────────────────────────────────
# STRETCH GOAL: UNRESOLVED THREAD DETECTOR
#
# Uses INSIGHTS search type to find plot threads or character arcs
# that were mentioned but never resolved — the "suggestions" feature.
# Only wire this in once the core Memory + Summary + Draft is working.
# ─────────────────────────────────────────────────────────────────────

async def get_unresolved_threads(room_id: str) -> str:
    """
    Stretch-goal feature: finds unresolved plot threads and
    character arcs from the story graph.

    Uses INSIGHTS search type which combines graph traversal
    with pattern recognition — ideal for "what's missing" queries.
    """
    try:
        dataset = _dataset_name(room_id)

        results = await cognee.search(
            SearchType.INSIGHTS,
            query_text=(
                "What plot threads, character arcs, or story questions "
                "have been raised in our discussions but not yet resolved or answered? "
                "List any loose ends or unanswered questions in the story."
            ),
            datasets=[dataset]
        )

        if not results:
            return "No unresolved threads detected yet — keep adding to your story!"

        if isinstance(results, list):
            return "\n\n".join(
                r.get("text", str(r)) if isinstance(r, dict) else str(r)
                for r in results
            )

        return str(results)

    except Exception as e:
        print(f"[Cognee] Unresolved thread detection failed: {e}")
        return f"Could not analyse story threads: {str(e)}"