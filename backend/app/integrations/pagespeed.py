"""
Google PageSpeed Insights API client.
Docs: https://developers.google.com/speed/docs/insights/v5/get-started
"""

import httpx

PAGESPEED_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEFAULT_TIMEOUT = 30.0


async def analyze(
    url: str,
    api_key: str | None = None,
    strategy: str = "mobile",
) -> dict:
    """
    Analyse a URL with PageSpeed Insights.

    Args:
        url: The page URL to audit.
        api_key: Optional Google API key (increases quota).
        strategy: "mobile" or "desktop" (default "mobile").

    Returns:
        dict containing performance_score, Core Web Vitals
        (lcp, inp, cls, fcp, ttfb), and the raw categories and audits
        from Lighthouse.  Returns error key on failure.
    """
    params: dict = {
        "url": url,
        "strategy": strategy,
        "category": "performance",
    }
    if api_key:
        params["key"] = api_key

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(PAGESPEED_URL, params=params)
            response.raise_for_status()
            data = response.json()

        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})

        # Performance score (0-100)
        perf_category = categories.get("performance", {})
        performance_score = perf_category.get("score")
        if performance_score is not None:
            performance_score = round(performance_score * 100)

        # Core Web Vitals & metrics
        lcp = _extract_metric(audits, "largest-contentful-paint")
        inp = _extract_metric(audits, "interaction-to-next-paint")
        cls = _extract_metric(audits, "cumulative-layout-shift")
        fcp = _extract_metric(audits, "first-contentful-paint")
        ttfb = _extract_metric(audits, "server-response-time")

        return {
            "performance_score": performance_score,
            "lcp": lcp,
            "inp": inp,
            "cls": cls,
            "fcp": fcp,
            "ttfb": ttfb,
            "categories": categories,
            "audits": audits,
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


def _extract_metric(audits: dict, audit_id: str) -> dict | None:
    """
    Pull display value, numeric value, and score from a Lighthouse audit.
    """
    audit = audits.get(audit_id)
    if audit is None:
        return None
    return {
        "display_value": audit.get("displayValue"),
        "numeric_value": audit.get("numericValue"),
        "score": audit.get("score"),
    }
