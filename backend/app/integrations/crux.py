"""
Chrome UX Report (CrUX) API client.
Docs: https://developer.chrome.com/docs/crux/api
"""

import httpx

CRUX_URL = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"
DEFAULT_TIMEOUT = 30.0


async def get_crux_data(
    url: str,
    api_key: str | None = None,
) -> dict:
    """
    Query the Chrome UX Report for real-user field metrics.

    Args:
        url: The page URL (or origin) to look up.
        api_key: Optional Google API key (required for production usage).

    Returns:
        dict with lcp, inp, cls - each containing a p75 value and
        histogram data.  Returns error key on failure.
    """
    params: dict = {}
    if api_key:
        params["key"] = api_key

    payload = {
        "url": url,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                CRUX_URL,
                params=params,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        record = data.get("record", {})
        metrics = record.get("metrics", {})

        lcp = _extract_field_metric(metrics, "largest_contentful_paint")
        inp = _extract_field_metric(metrics, "interaction_to_next_paint")
        cls = _extract_field_metric(metrics, "cumulative_layout_shift")

        return {
            "lcp": lcp,
            "inp": inp,
            "cls": cls,
            "key": record.get("key", {}),
            "collection_period": record.get("collectionPeriod", {}),
        }

    except httpx.HTTPStatusError as exc:
        # 404 means CrUX has no data for this URL
        if exc.response.status_code == 404:
            return {
                "error": "No CrUX data available for this URL.",
                "lcp": None,
                "inp": None,
                "cls": None,
            }
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


def _extract_field_metric(metrics: dict, metric_key: str) -> dict | None:
    """
    Extract p75 value and histogram from a CrUX metric entry.
    """
    metric = metrics.get(metric_key)
    if metric is None:
        return None

    percentiles = metric.get("percentiles", {})
    histogram = metric.get("histogram", [])

    return {
        "p75": percentiles.get("p75"),
        "histogram": histogram,
    }
