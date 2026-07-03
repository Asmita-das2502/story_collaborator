import cognee
from cognee.api.v1.search.search import SearchType
from dotenv import load_dotenv

load_dotenv()


def _dataset_name(room_id: str) -> str:
    return f"story_room_{room_id}"


def _extract_text(results) -> str:
    """
    Extracts readable text from Cognee search results.
    Results look like:
    [{'dataset_id': ..., 'dataset_name': ..., 'search_result': ["text here"]}]
    """
    if not results:
        return ""
    parts = []
    for r in results:
        if isinstance(r, dict):
            # New format: search_result is a list of strings
            search_result = r.get("search_result", [])
            if isinstance(search_result, list):
                parts.extend(search_result)
            elif search_result:
                parts.append(str(search_result))
            else:
                # Fallback: try text field or stringify
                parts.append(r.get("text", str(r)))
        else:
            parts.append(str(r))
    return "\n\n".join(p for p in parts if p)


async def remember_message(room_id: str, sender_name: str, content: str) -> bool:
    try:
        formatted_text = f'{sender_name} said: "{content}"'
        dataset = _dataset_name(room_id)
        await cognee.add(formatted_text, dataset_name=dataset)
        await cognee.cognify(datasets=[dataset])
        return True
    except Exception as e:
        print(f"[Cognee] Failed to ingest message: {e}")
        return False


async def get_story_summary(room_id: str) -> str:
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
        text = _extract_text(results)
        return text or "No story content has been added to memory yet. Start discussing your story and the summary will appear here."
    except Exception as e:
        print(f"[Cognee] Summary retrieval failed: {e}")
        return f"Could not retrieve summary at this time. Error: {str(e)}"


async def get_story_context_for_chapter(room_id: str, chapter_number: int) -> dict:
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


async def recall_story_context(room_id: str, query: str) -> str:
    try:
        dataset = _dataset_name(room_id)
        results = await cognee.search(
            query,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[dataset]
        )
        return _extract_text(results) or "I couldn't find relevant information about that in your story memory."
    except Exception as e:
        print(f"[Cognee] Recall failed: {e}")
        return f"Memory recall failed: {str(e)}"


async def get_unresolved_threads(room_id: str) -> str:
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


async def get_story_suggestions(room_id: str, suggestion_type: str = "plot") -> str:
    """
    Suggests story directions based on what's already in the graph.
    suggestion_type can be: "plot", "character", "twist", "ending"
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
                "Based on the story's themes, characters and conflicts so far, "
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