"""
HTML parser module -- extracts all SEO-relevant data from raw HTML.

Extends and refines the logic in ``scripts/parse_html.py`` for use as an
importable async-friendly library inside the backend.  Uses BeautifulSoup
with the **lxml** parser for speed.
"""

import json
import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)


def _visible_text(soup: BeautifulSoup) -> str:
    """Return the visible text of a page, stripping scripts/styles/nav/etc."""
    # Work on a copy so we don't mutate the caller's tree
    clone = BeautifulSoup(str(soup), "lxml")
    for tag in clone(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    for comment in clone.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    return clone.get_text(separator=" ", strip=True)


def _count_paragraphs(soup: BeautifulSoup) -> int:
    """Count <p> tags that contain meaningful text (> 20 chars)."""
    return sum(
        1
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 20
    )


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Extract image metadata from all <img> tags."""
    images: list[dict] = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if base_url and src:
            src = urljoin(base_url, src)
        images.append(
            {
                "src": src,
                "alt": img.get("alt"),
                "width": img.get("width"),
                "height": img.get("height"),
            }
        )
    return images


def _extract_links(soup: BeautifulSoup, base_url: str) -> dict:
    """Categorise and count links on the page."""
    internal_count = 0
    external_count = 0
    nofollow_count = 0
    broken_count = 0  # Links with empty/invalid hrefs

    if not base_url:
        return {
            "internal_count": 0,
            "external_count": 0,
            "nofollow_count": 0,
            "broken_count": 0,
        }

    base_domain = urlparse(base_url).netloc

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()

        # Skip fragment-only and javascript: links
        if not href or href.startswith("javascript:") or href.startswith("mailto:"):
            broken_count += 1
            continue

        if href.startswith("#"):
            # Fragment links are not "broken", but also not counted
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if not parsed.scheme or not parsed.netloc:
            broken_count += 1
            continue

        # Check nofollow
        rel = anchor.get("rel", [])
        if isinstance(rel, str):
            rel = rel.split()
        if "nofollow" in rel:
            nofollow_count += 1

        # Internal vs external
        if parsed.netloc == base_domain:
            internal_count += 1
        else:
            external_count += 1

    return {
        "internal_count": internal_count,
        "external_count": external_count,
        "nofollow_count": nofollow_count,
        "broken_count": broken_count,
    }


def _extract_structured_data(soup: BeautifulSoup) -> list[dict]:
    """Extract JSON-LD structured data blocks."""
    schemas: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                schemas.append(data)
            elif isinstance(data, list):
                schemas.extend(d for d in data if isinstance(d, dict))
        except (json.JSONDecodeError, TypeError):
            logger.debug("Malformed JSON-LD block skipped")
    return schemas


def _extract_open_graph(soup: BeautifulSoup) -> dict[str, str]:
    """Extract Open Graph meta properties."""
    og: dict[str, str] = {}
    for meta in soup.find_all("meta", attrs={"property": True}):
        prop = meta.get("property", "").lower()
        if prop.startswith("og:"):
            og[prop] = meta.get("content", "")
    return og


def _extract_twitter_card(soup: BeautifulSoup) -> dict[str, str]:
    """Extract Twitter Card meta tags."""
    tc: dict[str, str] = {}
    for meta in soup.find_all("meta", attrs={"name": True}):
        name = meta.get("name", "").lower()
        if name.startswith("twitter:"):
            tc[name] = meta.get("content", "")
    return tc


def parse_html(html: str, url: str) -> dict:
    """
    Parse HTML and return a structured dict of SEO-relevant data.

    Parameters
    ----------
    html:
        Raw HTML string.
    url:
        The URL the HTML was fetched from (used for resolving relative links
        and classifying internal vs external).

    Returns
    -------
    dict with the following keys:
        title, meta_description, meta_keywords, canonical, robots,
        h1_tags, h2_tags, h3_tags, images, links,
        word_count, paragraph_count, structured_data,
        open_graph, twitter_card,
        has_sitemap_link, has_robots_txt_link,
        language, charset
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        logger.warning("lxml parser failed, falling back to html.parser")
        soup = BeautifulSoup(html, "html.parser")

    result: dict = {}

    # --- Title ---------------------------------------------------------------
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else None

    # --- Meta tags -----------------------------------------------------------
    result["meta_description"] = None
    result["meta_keywords"] = None
    result["robots"] = None

    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        content = meta.get("content", "")

        if name == "description":
            result["meta_description"] = content
        elif name == "keywords":
            result["meta_keywords"] = content
        elif name == "robots":
            result["robots"] = content

    # --- Canonical -----------------------------------------------------------
    canonical_tag = soup.find("link", rel="canonical")
    result["canonical"] = canonical_tag.get("href") if canonical_tag else None

    # --- Headings ------------------------------------------------------------
    result["h1_tags"] = [
        h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)
    ]
    result["h2_tags"] = [
        h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)
    ]
    result["h3_tags"] = [
        h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)
    ]

    # --- Images --------------------------------------------------------------
    result["images"] = _extract_images(soup, url)

    # --- Links ---------------------------------------------------------------
    result["links"] = _extract_links(soup, url)

    # --- Text metrics --------------------------------------------------------
    visible = _visible_text(soup)
    words = re.findall(r"\b\w+\b", visible)
    result["word_count"] = len(words)
    result["paragraph_count"] = _count_paragraphs(soup)

    # --- Structured data (JSON-LD) -------------------------------------------
    result["structured_data"] = _extract_structured_data(soup)

    # --- Social meta ---------------------------------------------------------
    result["open_graph"] = _extract_open_graph(soup)
    result["twitter_card"] = _extract_twitter_card(soup)

    # --- Sitemap / robots.txt links ------------------------------------------
    all_hrefs = [
        (a.get("href") or "").lower() for a in soup.find_all("a", href=True)
    ]
    all_link_hrefs = [
        (link.get("href") or "").lower() for link in soup.find_all("link", href=True)
    ]
    combined_hrefs = all_hrefs + all_link_hrefs

    result["has_sitemap_link"] = any("sitemap" in h for h in combined_hrefs)
    result["has_robots_txt_link"] = any("robots.txt" in h for h in combined_hrefs)

    # --- Language / charset --------------------------------------------------
    html_tag = soup.find("html")
    result["language"] = html_tag.get("lang") if html_tag else None

    charset = None
    # Check <meta charset="...">
    charset_meta = soup.find("meta", charset=True)
    if charset_meta:
        charset = charset_meta.get("charset")
    else:
        # Check <meta http-equiv="Content-Type" content="text/html; charset=...">
        http_equiv = soup.find("meta", attrs={"http-equiv": re.compile("content-type", re.I)})
        if http_equiv:
            content = http_equiv.get("content", "")
            match = re.search(r"charset=([\w-]+)", content, re.I)
            if match:
                charset = match.group(1)
    result["charset"] = charset

    # --- Viewport (useful downstream for mobile scoring) ---------------------
    viewport_meta = soup.find("meta", attrs={"name": "viewport"})
    result["viewport"] = viewport_meta.get("content") if viewport_meta else None

    return result
