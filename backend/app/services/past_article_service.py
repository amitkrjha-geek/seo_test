import re
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from sqlmodel import Session, select

import httpx

from ..models.past_article import PastArticle


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

class _TitleExtractor(HTMLParser):
    """Extract <title> text from HTML."""

    def __init__(self):
        super().__init__()
        self._in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


class _BodyTextExtractor(HTMLParser):
    """Extract visible text from <body>, skipping script/style tags."""

    SKIP_TAGS = {"script", "style", "noscript", "svg", "head"}

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self.parts.append(text)

    def get_text(self) -> str:
        return " ".join(self.parts)


def _extract_title(html: str) -> str:
    parser = _TitleExtractor()
    parser.feed(html)
    return parser.title.strip() or "Untitled"


def _extract_body_text(html: str) -> str:
    parser = _BodyTextExtractor()
    parser.feed(html)
    return parser.get_text()


# ---------------------------------------------------------------------------
# SEO scoring
# ---------------------------------------------------------------------------

def _basic_seo_score(html: str, body_text: str, title: str) -> float:
    """Compute a rough 0-100 SEO score from HTML content."""
    score = 0.0
    html_lower = html.lower()

    # Title present (15 pts)
    if title and title != "Untitled":
        score += 10
        if 30 <= len(title) <= 70:
            score += 5

    # Meta description present (10 pts)
    if 'name="description"' in html_lower or "name='description'" in html_lower:
        score += 10

    # Has H1 (10 pts)
    if "<h1" in html_lower:
        score += 10

    # Has H2s (10 pts)
    h2_count = html_lower.count("<h2")
    if h2_count >= 3:
        score += 10
    elif h2_count >= 1:
        score += 5

    # Word count (20 pts)
    word_count = len(body_text.split())
    if word_count >= 1500:
        score += 20
    elif word_count >= 1000:
        score += 15
    elif word_count >= 500:
        score += 10
    elif word_count >= 300:
        score += 5

    # Has images with alt (10 pts)
    if re.search(r'<img[^>]+alt="[^"]+', html_lower):
        score += 10
    elif "<img" in html_lower:
        score += 3

    # Has internal links (10 pts)
    if '<a href="/' in html_lower or "<a href='/" in html_lower:
        score += 10
    elif "<a " in html_lower:
        score += 5

    # Has canonical tag (5 pts)
    if 'rel="canonical"' in html_lower or "rel='canonical'" in html_lower:
        score += 5

    # Has structured data (5 pts)
    if "application/ld+json" in html_lower:
        score += 5

    return min(score, 100.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def import_article(db: Session, project_id: str, url: str) -> dict:
    """Fetch a URL, extract content, calculate SEO score, and store as PastArticle."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(url, headers={
            "User-Agent": "SEOBot/1.0 (content-audit)"
        })
        resp.raise_for_status()
        html = resp.text

    title = _extract_title(html)
    body_text = _extract_body_text(html)
    word_count = len(body_text.split())
    seo_score = _basic_seo_score(html, body_text, title)

    article = PastArticle(
        project_id=project_id,
        url=url,
        title=title,
        body=body_text[:50_000],  # cap stored body size
        word_count=word_count,
        seo_score=round(seo_score, 1),
        needs_refresh=seo_score < 50,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return _article_to_dict(article)


def list_articles(db: Session, project_id: str) -> list[dict]:
    articles = db.exec(
        select(PastArticle)
        .where(PastArticle.project_id == project_id)
        .order_by(PastArticle.created_at.desc())
    ).all()
    return [_article_to_dict(a) for a in articles]


def get_article(db: Session, article_id: str) -> dict | None:
    article = db.get(PastArticle, article_id)
    if not article:
        return None
    return _article_to_dict(article)


def delete_article(db: Session, article_id: str) -> bool:
    article = db.get(PastArticle, article_id)
    if not article:
        return False
    db.delete(article)
    db.commit()
    return True


def check_refresh(db: Session, article_id: str) -> dict | None:
    """Check if an article needs refresh based on age and score."""
    article = db.get(PastArticle, article_id)
    if not article:
        return None

    needs_refresh = False
    reasons: list[str] = []

    # Low SEO score
    if article.seo_score is not None and article.seo_score < 50:
        needs_refresh = True
        reasons.append(f"Low SEO score ({article.seo_score}/100)")

    # Article is old (>180 days since crawl)
    age_days = (datetime.now(timezone.utc) - article.crawled_at).days
    if age_days > 180:
        needs_refresh = True
        reasons.append(f"Article crawled {age_days} days ago")

    # Low word count
    if article.word_count < 500:
        needs_refresh = True
        reasons.append(f"Low word count ({article.word_count} words)")

    article.needs_refresh = needs_refresh
    article.refresh_suggestions = json.dumps(reasons)
    db.add(article)
    db.commit()
    db.refresh(article)

    return _article_to_dict(article)


def _article_to_dict(a: PastArticle) -> dict:
    refresh_suggestions = []
    try:
        refresh_suggestions = json.loads(a.refresh_suggestions) if a.refresh_suggestions else []
    except (json.JSONDecodeError, TypeError):
        refresh_suggestions = []
    return {
        "id": a.id,
        "project_id": a.project_id,
        "url": a.url,
        "title": a.title,
        "word_count": a.word_count,
        "publish_date": a.publish_date.isoformat() if a.publish_date else None,
        "seo_score": a.seo_score,
        "needs_refresh": a.needs_refresh,
        "refresh_suggestions": refresh_suggestions,
        "crawled_at": a.crawled_at.isoformat(),
        "created_at": a.created_at.isoformat(),
    }
