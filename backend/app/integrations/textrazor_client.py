"""
TextRazor API client for entity and topic extraction.
Docs: https://www.textrazor.com/docs/rest
"""

import httpx

TEXTRAZOR_URL = "https://api.textrazor.com"
DEFAULT_TIMEOUT = 30.0


async def extract_entities(
    api_key: str,
    text: str,
) -> list[dict]:
    """
    Extract named entities and topics from text using TextRazor.

    Args:
        api_key: TextRazor API key.
        text: The text content to analyse.

    Returns:
        A list of entity dicts, each containing entity_id, type,
        relevance_score, confidence_score, and matched_text.
        Returns a single-element list with an error key on failure.
    """
    headers = {
        "X-TextRazor-Key": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "text": text,
        "extractors": "entities,topics",
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                TEXTRAZOR_URL,
                headers=headers,
                data=payload,
            )
            response.raise_for_status()
            data = response.json()

        raw_response = data.get("response", {})
        raw_entities = raw_response.get("entities", [])
        raw_topics = raw_response.get("topics", [])

        entities: list[dict] = []
        for ent in raw_entities:
            entities.append({
                "entity_id": ent.get("entityId"),
                "type": ent.get("type", []),
                "relevance_score": ent.get("relevanceScore"),
                "confidence_score": ent.get("confidenceScore"),
                "matched_text": ent.get("matchedText"),
                "wiki_link": ent.get("wikiLink"),
            })

        topics: list[dict] = []
        for topic in raw_topics:
            topics.append({
                "label": topic.get("label"),
                "score": topic.get("score"),
            })

        if entities:
            return entities
        return [{"info": "No entities found", "topics": topics}]

    except httpx.HTTPStatusError as exc:
        return [{"error": f"HTTP {exc.response.status_code}: {exc.response.text}"}]
    except httpx.RequestError as exc:
        return [{"error": f"Request failed: {str(exc)}"}]
    except Exception as exc:
        return [{"error": f"Unexpected error: {str(exc)}"}]
