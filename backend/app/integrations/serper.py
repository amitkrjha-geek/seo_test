"""
Serper.dev API client for Google SERP and News search.
Docs: https://serper.dev/
"""

import httpx

SERPER_BASE_URL = "https://google.serper.dev"
DEFAULT_TIMEOUT = 30.0


async def search_serp(
    api_key: str,
    query: str,
    num: int = 10,
    country: str = "us",
) -> dict:
    """
    Search Google SERP via Serper.dev.

    Args:
        api_key: Serper.dev API key.
        query: Search query string.
        num: Number of results to return (default 10).
        country: Country code for localised results (default "us").

    Returns:
        dict with keys organic, people_also_ask, related_searches,
        knowledge_graph (when available), or error on failure.
    """
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "num": num,
        "gl": country,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{SERPER_BASE_URL}/search",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "organic": data.get("organic", []),
                "people_also_ask": data.get("peopleAlsoAsk", []),
                "related_searches": data.get("relatedSearches", []),
                "knowledge_graph": data.get("knowledgeGraph"),
                "search_parameters": data.get("searchParameters", {}),
            }

    except httpx.HTTPStatusError as exc:
        return {
            "error": f"HTTP {exc.response.status_code}: {exc.response.text}",
        }
    except httpx.RequestError as exc:
        return {
            "error": f"Request failed: {str(exc)}",
        }
    except Exception as exc:
        return {
            "error": f"Unexpected error: {str(exc)}",
        }


async def search_news(
    api_key: str,
    query: str,
) -> dict:
    """
    Search Google News via Serper.dev.

    Args:
        api_key: Serper.dev API key.
        query: News search query string.

    Returns:
        dict with key news containing a list of news articles,
        or error on failure.
    """
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{SERPER_BASE_URL}/news",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "news": data.get("news", []),
                "search_parameters": data.get("searchParameters", {}),
            }

    except httpx.HTTPStatusError as exc:
        return {
            "error": f"HTTP {exc.response.status_code}: {exc.response.text}",
        }
    except httpx.RequestError as exc:
        return {
            "error": f"Request failed: {str(exc)}",
        }
    except Exception as exc:
        return {
            "error": f"Unexpected error: {str(exc)}",
        }
