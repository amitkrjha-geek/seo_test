"""
Google Trends client via the pytrends library.
Note: pytrends is synchronous - these functions are intentionally sync.
Wrap them with asyncio.to_thread() when calling from async code.

Install: pip install pytrends
"""

from pytrends.request import TrendReq


def get_interest_over_time(
    keywords: list[str],
    timeframe: str = "today 12-m",
) -> dict:
    """
    Fetch Google Trends interest-over-time data for up to 5 keywords.

    Args:
        keywords: List of keywords (max 5 per Google Trends limit).
        timeframe: Trends timeframe string (default "today 12-m").

    Returns:
        dict with dates (list of ISO date strings) and one key per
        keyword containing a list of interest values.
        Returns error key on failure.
    """
    try:
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 30))
        pytrends.build_payload(keywords[:5], timeframe=timeframe)

        df = pytrends.interest_over_time()
        if df.empty:
            return {
                "error": "No interest-over-time data returned.",
                "dates": [],
                "keywords": keywords,
            }

        # Drop the isPartial column if present
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])

        result: dict = {
            "dates": [d.isoformat() for d in df.index],
        }
        for col in df.columns:
            result[col] = df[col].tolist()

        return result

    except Exception as exc:
        return {"error": f"pytrends error: {str(exc)}"}


def get_related_queries(
    keyword: str,
) -> dict:
    """
    Fetch related queries (top and rising) for a single keyword.

    Args:
        keyword: The keyword to look up.

    Returns:
        dict with top and rising keys, each containing a list of
        dicts with query and value keys.
        Returns error key on failure.
    """
    try:
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 30))
        pytrends.build_payload([keyword], timeframe="today 12-m")

        related = pytrends.related_queries()
        kw_data = related.get(keyword, {})

        top_df = kw_data.get("top")
        rising_df = kw_data.get("rising")

        top: list[dict] = []
        if top_df is not None and not top_df.empty:
            top = top_df.rename(
                columns={"query": "query", "value": "value"}
            ).to_dict(orient="records")

        rising: list[dict] = []
        if rising_df is not None and not rising_df.empty:
            rising = rising_df.rename(
                columns={"query": "query", "value": "value"}
            ).to_dict(orient="records")

        return {
            "keyword": keyword,
            "top": top,
            "rising": rising,
        }

    except Exception as exc:
        return {"error": f"pytrends error: {str(exc)}"}
