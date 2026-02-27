"""
SEO Health Score calculator.

Takes the parsed HTML data (from parser.parse_html) and optional
PageSpeed Insights data, then produces a 0-100 score together with a
detailed list of issues / recommendations.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

WEIGHTS: dict[str, float] = {
    "title": 0.1,
    "meta_description": 0.08,
    "headings": 0.1,
    "content": 0.15,
    "images": 0.08,
    "links": 0.08,
    "technical": 0.15,
    "performance": 0.15,
    "mobile": 0.06,
    "social": 0.05,
}

SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"
SEVERITY_PASS = "pass"


def _issue(category: str, severity: str, title: str, description: str, recommendation: str) -> dict:
    """Build a standardised issue dict."""
    return {
        "category": category,
        "severity": severity,
        "title": title,
        "description": description,
        "recommendation": recommendation,
    }


def _score_title(data: dict) -> tuple[float, list[dict]]:
    """Score the <title> tag (0-1 fraction)."""
    issues: list[dict] = []
    score = 0.0
    title = data.get("title")

    if not title:
        issues.append(_issue("title", SEVERITY_CRITICAL, "Missing title tag",
            "The page has no <title> element.",
            "Add a unique, descriptive <title> tag between 50 and 60 characters."))
        return 0.0, issues

    score += 0.4
    length = len(title)

    if 50 <= length <= 60:
        score += 0.4
        issues.append(_issue("title", SEVERITY_PASS, "Title length is optimal",
            f"Title is {length} characters (50-60 recommended).", ""))
    elif 30 <= length < 50:
        score += 0.2
        issues.append(_issue("title", SEVERITY_WARNING, "Title is slightly short",
            f"Title is {length} characters; 50-60 is optimal.",
            "Consider expanding the title to 50-60 characters for better SERP display."))
    elif 60 < length <= 70:
        score += 0.2
        issues.append(_issue("title", SEVERITY_WARNING, "Title is slightly long",
            f"Title is {length} characters; it may be truncated in SERPs.",
            "Trim the title to 60 characters or fewer."))
    elif length > 70:
        issues.append(_issue("title", SEVERITY_CRITICAL, "Title is too long",
            f"Title is {length} characters; search engines will truncate it.",
            "Shorten the title to 60 characters or fewer."))
    else:
        issues.append(_issue("title", SEVERITY_WARNING, "Title is very short",
            f"Title is only {length} characters.",
            "A good title should be 50-60 characters to maximise SERP visibility."))

    if length > 10:
        score += 0.2

    return min(score, 1.0), issues


def _score_meta_description(data: dict) -> tuple[float, list[dict]]:
    """Score the meta description (0-1 fraction)."""
    issues: list[dict] = []
    desc = data.get("meta_description")
    if not desc:
        issues.append(_issue("meta_description", SEVERITY_CRITICAL, "Missing meta description",
            "No meta description tag was found.",
            "Add a <meta name=\"description\"> tag with 150-160 characters."))
        return 0.0, issues
    score = 0.4
    length = len(desc)
    if 150 <= length <= 160:
        score += 0.6
        issues.append(_issue("meta_description", SEVERITY_PASS, "Meta description length is optimal",
            f"Meta description is {length} characters.", ""))
    elif 120 <= length < 150:
        score += 0.4
        issues.append(_issue("meta_description", SEVERITY_WARNING, "Meta description is slightly short",
            f"Meta description is {length} characters; 150-160 is ideal.",
            "Expand the meta description to better use the available SERP space."))
    elif 160 < length <= 200:
        score += 0.3
        issues.append(_issue("meta_description", SEVERITY_WARNING, "Meta description is slightly long",
            f"Meta description is {length} characters; it may be truncated.",
            "Trim to 160 characters or fewer."))
    elif length > 200:
        score += 0.1
        issues.append(_issue("meta_description", SEVERITY_CRITICAL, "Meta description is too long",
            f"Meta description is {length} characters and will likely be truncated.",
            "Shorten to 160 characters for full SERP display."))
    else:
        score += 0.1
        issues.append(_issue("meta_description", SEVERITY_WARNING, "Meta description is very short",
            f"Meta description is only {length} characters.",
            "Aim for 150-160 characters to fully leverage search snippet space."))
    return min(score, 1.0), issues


def _score_headings(data: dict) -> tuple[float, list[dict]]:
    """Score heading structure (0-1 fraction)."""
    issues: list[dict] = []
    score = 0.0
    h1_tags = data.get("h1_tags", [])
    h2_tags = data.get("h2_tags", [])
    h3_tags = data.get("h3_tags", [])
    if len(h1_tags) == 1:
        score += 0.5
        issues.append(_issue("headings", SEVERITY_PASS, "Single H1 tag present",
            f'H1: "{h1_tags[0][:80]}"', ""))
    elif len(h1_tags) == 0:
        issues.append(_issue("headings", SEVERITY_CRITICAL, "No H1 tag found",
            "The page is missing an H1 heading.",
            "Add exactly one H1 tag that describes the main topic."))
    else:
        score += 0.2
        issues.append(_issue("headings", SEVERITY_WARNING, "Multiple H1 tags found",
            f"Found {len(h1_tags)} H1 tags; best practice is exactly one.",
            "Consolidate to a single H1 and use H2/H3 for subsections."))
    if h2_tags:
        score += 0.3
        issues.append(_issue("headings", SEVERITY_PASS, "H2 tags present",
            f"Found {len(h2_tags)} H2 tag(s).", ""))
    else:
        issues.append(_issue("headings", SEVERITY_WARNING, "No H2 tags found",
            "No H2 headings were detected on the page.",
            "Use H2 tags to break content into logical sections."))
    if h3_tags:
        score += 0.2
        issues.append(_issue("headings", SEVERITY_PASS, "H3 tags present",
            f"Found {len(h3_tags)} H3 tag(s).", ""))
    return min(score, 1.0), issues


def _score_content(data: dict) -> tuple[float, list[dict]]:
    """Score content quality signals (0-1 fraction)."""
    issues: list[dict] = []
    score = 0.0
    word_count = data.get("word_count", 0)
    paragraph_count = data.get("paragraph_count", 0)
    if word_count >= 1000:
        score += 0.5
        issues.append(_issue("content", SEVERITY_PASS, "Strong word count",
            f"Page has {word_count} words.", ""))
    elif word_count >= 600:
        score += 0.4
        issues.append(_issue("content", SEVERITY_PASS, "Good word count",
            f"Page has {word_count} words.", ""))
    elif word_count >= 300:
        score += 0.25
        issues.append(_issue("content", SEVERITY_WARNING, "Moderate word count",
            f"Page has {word_count} words; consider adding more content.",
            "Aim for at least 600 words for competitive keyword ranking."))
    else:
        issues.append(_issue("content", SEVERITY_CRITICAL, "Thin content",
            f"Page has only {word_count} words.",
            "Pages with fewer than 300 words are considered thin content. Add substantive, valuable content."))
    if paragraph_count >= 5:
        score += 0.3
        issues.append(_issue("content", SEVERITY_PASS, "Good paragraph structure",
            f"Found {paragraph_count} meaningful paragraphs.", ""))
    elif paragraph_count >= 2:
        score += 0.15
        issues.append(_issue("content", SEVERITY_WARNING, "Limited paragraph structure",
            f"Only {paragraph_count} substantial paragraphs found.",
            "Break content into more paragraphs for readability."))
    else:
        issues.append(_issue("content", SEVERITY_WARNING, "Poor paragraph structure",
            "Very few or no meaningful paragraphs detected.",
            "Structure content with clear paragraphs for better readability and SEO."))
    if word_count >= 300 and paragraph_count >= 3:
        score += 0.2
    return min(score, 1.0), issues


def _score_images(data: dict) -> tuple[float, list[dict]]:
    """Score image optimisation (0-1 fraction)."""
    issues: list[dict] = []
    images = data.get("images", [])
    if not images:
        issues.append(_issue("images", SEVERITY_INFO, "No images found",
            "The page contains no images.",
            "Consider adding relevant images to improve engagement."))
        return 0.5, issues
    score = 0.3
    missing_alt = [img for img in images if not img.get("alt")]
    if not missing_alt:
        score += 0.5
        issues.append(_issue("images", SEVERITY_PASS, "All images have alt text",
            f"All {len(images)} images have alt attributes.", ""))
    else:
        ratio = (len(images) - len(missing_alt)) / len(images)
        score += 0.5 * ratio
        sev = SEVERITY_WARNING if len(missing_alt) < len(images) else SEVERITY_CRITICAL
        issues.append(_issue("images", sev, "Images missing alt text",
            f"{len(missing_alt)} of {len(images)} images lack alt text.",
            "Add descriptive alt text to every image for accessibility and SEO."))
    missing_dims = [img for img in images if not img.get("width") or not img.get("height")]
    if not missing_dims:
        score += 0.2
        issues.append(_issue("images", SEVERITY_PASS, "All images specify dimensions",
            "Width and height attributes are set.", ""))
    else:
        issues.append(_issue("images", SEVERITY_INFO, "Images missing dimension attributes",
            f"{len(missing_dims)} images lack explicit width/height.",
            "Set width and height attributes to prevent cumulative layout shift (CLS)."))
    return min(score, 1.0), issues


def _score_links(data: dict) -> tuple[float, list[dict]]:
    """Score link profile (0-1 fraction)."""
    issues: list[dict] = []
    links = data.get("links", {})
    internal = links.get("internal_count", 0)
    external = links.get("external_count", 0)
    broken = links.get("broken_count", 0)
    score = 0.0
    if internal >= 3:
        score += 0.4
        issues.append(_issue("links", SEVERITY_PASS, "Good internal linking",
            f"Found {internal} internal links.", ""))
    elif internal >= 1:
        score += 0.2
        issues.append(_issue("links", SEVERITY_WARNING, "Few internal links",
            f"Only {internal} internal link(s) found.",
            "Add more internal links to help search engines discover related content."))
    else:
        issues.append(_issue("links", SEVERITY_CRITICAL, "No internal links",
            "The page has no internal links.",
            "Add internal links to improve crawlability and distribute page authority."))
    if external >= 1:
        score += 0.3
        issues.append(_issue("links", SEVERITY_PASS, "Has external links",
            f"Found {external} external link(s).", ""))
    else:
        issues.append(_issue("links", SEVERITY_INFO, "No external links",
            "No outbound external links found.",
            "Linking to authoritative external sources can improve topical relevance."))
    if broken == 0:
        score += 0.3
        issues.append(_issue("links", SEVERITY_PASS, "No broken links detected",
            "All link hrefs appear valid.", ""))
    else:
        issues.append(_issue("links", SEVERITY_WARNING, "Potentially broken links",
            f"{broken} link(s) have empty or invalid href attributes.",
            "Review and fix broken links to improve user experience and crawlability."))
    return min(score, 1.0), issues


def _score_technical(data: dict) -> tuple[float, list[dict]]:
    """Score technical SEO signals (0-1 fraction)."""
    issues: list[dict] = []
    score = 0.0
    if data.get("canonical"):
        score += 0.2
        issues.append(_issue("technical", SEVERITY_PASS, "Canonical tag present",
            f"Canonical URL: {data['canonical']}", ""))
    else:
        issues.append(_issue("technical", SEVERITY_WARNING, "Missing canonical tag",
            "No canonical URL is specified.",
            "Add a <link rel='canonical'> to avoid duplicate content issues."))
    robots = data.get("robots")
    if robots:
        score += 0.1
        if "noindex" in robots.lower():
            score -= 0.1
            issues.append(_issue("technical", SEVERITY_CRITICAL, "Page is set to noindex",
                f'Robots meta: "{robots}"',
                "Remove noindex if you want this page to appear in search results."))
        else:
            issues.append(_issue("technical", SEVERITY_PASS, "Robots meta tag present",
                f'Robots: "{robots}"', ""))
    else:
        issues.append(_issue("technical", SEVERITY_INFO, "No robots meta tag",
            "Defaults to index/follow (which is fine for most pages).", ""))
        score += 0.1
    schemas = data.get("structured_data", [])
    if schemas:
        score += 0.25
        types = [s.get("@type", "Unknown") for s in schemas]
        issues.append(_issue("technical", SEVERITY_PASS, "Structured data found",
            "JSON-LD types: " + ", ".join(types), ""))
    else:
        issues.append(_issue("technical", SEVERITY_WARNING, "No structured data",
            "No JSON-LD schema markup was found.",
            "Add structured data (e.g. Organization, Article, FAQ) to enhance rich results."))
    if data.get("charset"):
        score += 0.15
        issues.append(_issue("technical", SEVERITY_PASS, "Charset declared",
            f"Charset: {data['charset']}", ""))
    else:
        issues.append(_issue("technical", SEVERITY_WARNING, "No charset declaration",
            "No character encoding was specified in the HTML.",
            "Add <meta charset='UTF-8'> for proper character rendering."))
    if data.get("language"):
        score += 0.15
        issues.append(_issue("technical", SEVERITY_PASS, "Language attribute set",
            f"Language: {data['language']}", ""))
    else:
        issues.append(_issue("technical", SEVERITY_WARNING, "Missing language attribute",
            "The <html> tag has no lang attribute.",
            "Add lang='en' (or the appropriate language) to the <html> element."))
    if data.get("has_sitemap_link"):
        score += 0.075
        issues.append(_issue("technical", SEVERITY_PASS, "Sitemap link found",
            "A link to the sitemap was detected.", ""))
    if data.get("has_robots_txt_link"):
        score += 0.075
        issues.append(_issue("technical", SEVERITY_PASS, "Robots.txt link found",
            "A link to robots.txt was detected.", ""))
    return min(score, 1.0), issues


def _extract_perf_score(pagespeed_data: dict) -> float | None:
    """Try several common structures for the PSI response to find the performance score (0-1)."""
    try:
        return pagespeed_data["lighthouseResult"]["categories"]["performance"]["score"]
    except (KeyError, TypeError):
        pass
    for key in ("performance_score", "score", "performance"):
        val = pagespeed_data.get(key)
        if isinstance(val, (int, float)):
            return float(val) if val <= 1.0 else float(val) / 100.0
    return None


def _score_performance(pagespeed_data: dict | None) -> tuple[float, list[dict]]:
    """Score performance using PageSpeed Insights data (0-1 fraction)."""
    issues: list[dict] = []
    if not pagespeed_data:
        issues.append(_issue("performance", SEVERITY_INFO, "No PageSpeed data available",
            "Performance analysis was skipped because PageSpeed data is not provided.",
            "Run a PageSpeed Insights analysis for detailed performance metrics."))
        return 0.5, issues
    score = 0.0
    try:
        perf_score = _extract_perf_score(pagespeed_data)
        if perf_score is not None:
            score = perf_score
            label = "excellent" if perf_score >= 0.9 else ("good" if perf_score >= 0.5 else "needs improvement")
            sev = SEVERITY_PASS if perf_score >= 0.9 else (SEVERITY_WARNING if perf_score >= 0.5 else SEVERITY_CRITICAL)
            issues.append(_issue("performance", sev,
                f"PageSpeed score: {int(perf_score * 100)}",
                f"Lighthouse performance score is {label}.",
                "" if perf_score >= 0.9 else "Optimise images, reduce JavaScript, and leverage caching."))
        else:
            score = 0.5
            issues.append(_issue("performance", SEVERITY_INFO, "Could not parse PageSpeed score",
                "The performance score was not found in the provided data.", ""))
    except Exception as exc:
        logger.warning("Error parsing PageSpeed data: %s", exc)
        score = 0.5
        issues.append(_issue("performance", SEVERITY_INFO, "Error parsing PageSpeed data", str(exc), ""))
    return min(score, 1.0), issues


def _score_mobile(data: dict) -> tuple[float, list[dict]]:
    """Score mobile-friendliness indicators (0-1 fraction)."""
    issues: list[dict] = []
    score = 0.0
    viewport = data.get("viewport")
    if viewport:
        score += 0.6
        issues.append(_issue("mobile", SEVERITY_PASS, "Viewport meta tag present",
            f"Viewport: {viewport}", ""))
        if "width=device-width" in viewport.lower().replace(" ", ""):
            score += 0.2
        else:
            issues.append(_issue("mobile", SEVERITY_WARNING, "Viewport may not be responsive",
                "The viewport meta tag does not include width=device-width.",
                "Use <meta name='viewport' content='width=device-width, initial-scale=1'>."))
    else:
        issues.append(_issue("mobile", SEVERITY_CRITICAL, "Missing viewport meta tag",
            "No viewport meta tag found -- page is not mobile-friendly.",
            "Add <meta name='viewport' content='width=device-width, initial-scale=1'>."))
    images = data.get("images", [])
    has_responsive = any(img.get("width") or img.get("height") for img in images) if images else False
    if has_responsive:
        score += 0.2
        issues.append(_issue("mobile", SEVERITY_PASS, "Images have dimension attributes",
            "At least some images specify width/height for layout stability.", ""))
    return min(score, 1.0), issues


def _score_social(data: dict) -> tuple[float, list[dict]]:
    """Score social media meta tags (0-1 fraction)."""
    issues: list[dict] = []
    score = 0.0
    og = data.get("open_graph", {})
    tc = data.get("twitter_card", {})
    if og:
        essential_og = {"og:title", "og:description", "og:image", "og:url"}
        present = essential_og & set(og.keys())
        ratio = len(present) / len(essential_og)
        score += 0.6 * ratio
        if ratio >= 1.0:
            issues.append(_issue("social", SEVERITY_PASS, "Full Open Graph tags",
                "All essential OG tags (title, description, image, url) are present.", ""))
        else:
            missing = essential_og - present
            issues.append(_issue("social", SEVERITY_WARNING, "Incomplete Open Graph tags",
                "Missing OG tags: " + ", ".join(sorted(missing)) + ".",
                "Add the missing OG tags for optimal social sharing previews."))
    else:
        issues.append(_issue("social", SEVERITY_WARNING, "No Open Graph tags",
            "No OG meta tags found.",
            "Add Open Graph tags (og:title, og:description, og:image, og:url) for social sharing."))
    if tc:
        score += 0.4
        issues.append(_issue("social", SEVERITY_PASS, "Twitter Card tags present",
            f"Found {len(tc)} Twitter Card tag(s).", ""))
    else:
        issues.append(_issue("social", SEVERITY_INFO, "No Twitter Card tags",
            "No twitter: meta tags found.",
            "Add Twitter Card tags for better display when shared on Twitter/X."))
    return min(score, 1.0), issues


def calculate_health_score(
    parsed_data: dict,
    pagespeed_data: dict | None = None,
) -> tuple[int, list[dict]]:
    """Calculate an overall SEO health score from parsed page data.
    Returns a tuple of (score 0-100, list of issue dicts)."""
    all_issues: list[dict] = []
    weighted_score = 0.0
    scorers: dict[str, Any] = {
        "title": lambda: _score_title(parsed_data),
        "meta_description": lambda: _score_meta_description(parsed_data),
        "headings": lambda: _score_headings(parsed_data),
        "content": lambda: _score_content(parsed_data),
        "images": lambda: _score_images(parsed_data),
        "links": lambda: _score_links(parsed_data),
        "technical": lambda: _score_technical(parsed_data),
        "performance": lambda: _score_performance(pagespeed_data),
        "mobile": lambda: _score_mobile(parsed_data),
        "social": lambda: _score_social(parsed_data),
    }
    for category, scorer in scorers.items():
        try:
            cat_score, cat_issues = scorer()
        except Exception as exc:
            logger.error("Error scoring %%s: %%s", category, exc)
            cat_score = 0.0
            cat_issues = [_issue(category, SEVERITY_INFO,
                f"Error analysing {category}", str(exc), "")]
        weighted_score += cat_score * WEIGHTS[category]
        all_issues.extend(cat_issues)
    final_score = max(0, min(100, round(weighted_score * 100)))
    severity_order = {SEVERITY_CRITICAL: 0, SEVERITY_WARNING: 1, SEVERITY_INFO: 2, SEVERITY_PASS: 3}
    all_issues.sort(key=lambda i: severity_order.get(i["severity"], 99))
    return final_score, all_issues
