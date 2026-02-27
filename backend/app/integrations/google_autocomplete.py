"""
Google Autocomplete (Suggest) client.
Free endpoint - no API key required.
"""

import httpx

SUGGEST_URL = "http://suggestqueries.google.com/complete/search"
DEFAULT_TIMEOUT = 30.0


async def get_suggestions(
    query: str,
    language: str = "en",
) -> list[str]:
    """
    Fetch Google Autocomplete suggestions for a given query.

    Args:
        query: The partial or full search query.
        language: Language code for suggestions (default "en").

    Returns:
        A list of suggestion strings.  Returns an empty list on any error.
    """
    params = {
        "client": "firefox",
        "q": query,
        "hl": language,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(SUGGEST_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Response format: ["query", ["suggestion1", "suggestion2", ...]]
            if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
                return [str(s) for s in data[1]]

            return []

    except httpx.HTTPStatusError:
        return []
    except httpx.RequestError:
        return []
    except Exception:
        return []
