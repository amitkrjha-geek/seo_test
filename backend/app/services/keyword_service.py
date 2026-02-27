from sqlmodel import Session, select
from ..models.keyword import KeywordResearch, Keyword, KeywordStatus, KeywordSource
from ..integrations.google_autocomplete import get_suggestions
from ..integrations.serper import search_serp
from ..integrations.pytrends_client import get_related_queries
from ..core.nlp_analyzer import analyze_text
import json
import traceback


async def run_keyword_research(
    db: Session,
    research_id: str,
    seed_keyword: str,
    serper_api_key: str | None = None,
    on_progress: callable = None,
) -> KeywordResearch:
    """Run keyword research from multiple sources."""
    research = db.get(KeywordResearch, research_id)
    if not research:
        raise ValueError(f"Research {research_id} not found")

    research.status = KeywordStatus.RUNNING
    db.add(research)
    db.commit()

    try:
        all_keywords: list[dict] = []

        # Source 1: Google Autocomplete (free, no key)
        if on_progress:
            await on_progress({"step": "autocomplete", "message": "Fetching Google Autocomplete suggestions..."})
        try:
            suggestions = await get_suggestions(seed_keyword)
            for s in suggestions:
                all_keywords.append({"keyword": s, "source": KeywordSource.AUTOCOMPLETE})
            # Also get variations with prefixes
            for prefix in ["how to", "what is", "best", "why"]:
                extra = await get_suggestions(f"{prefix} {seed_keyword}")
                for s in extra:
                    all_keywords.append({"keyword": s, "source": KeywordSource.AUTOCOMPLETE})
        except Exception:
            pass

        # Source 2: Serper SERP data (related searches, people also ask)
        if serper_api_key:
            if on_progress:
                await on_progress({"step": "serper", "message": "Fetching SERP data..."})
            try:
                serp_data = await search_serp(serper_api_key, seed_keyword, num=10)
                # Extract "People Also Ask"
                for paa in serp_data.get("peopleAlsoAsk", []):
                    all_keywords.append({
                        "keyword": paa.get("question", ""),
                        "source": KeywordSource.SERPER,
                        "intent": "informational",
                    })
                # Extract related searches
                for rs in serp_data.get("relatedSearches", []):
                    all_keywords.append({
                        "keyword": rs.get("query", ""),
                        "source": KeywordSource.SERPER,
                    })
            except Exception:
                pass

        # Source 3: Google Trends related queries
        if on_progress:
            await on_progress({"step": "trends", "message": "Fetching Google Trends data..."})
        try:
            related = get_related_queries(seed_keyword)
            for q_type in ["top", "rising"]:
                for item in related.get(q_type, []):
                    all_keywords.append({
                        "keyword": item.get("query", ""),
                        "source": KeywordSource.PYTRENDS,
                    })
        except Exception:
            pass

        # Deduplicate
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            normalized = kw["keyword"].lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                kw["keyword"] = normalized
                unique_keywords.append(kw)

        # Simple clustering by common terms
        if on_progress:
            await on_progress({"step": "cluster", "message": f"Clustering {len(unique_keywords)} keywords..."})

        clusters = _cluster_keywords(unique_keywords, seed_keyword)

        # Save to database
        for kw_data in clusters:
            keyword = Keyword(
                research_id=research.id,
                keyword=kw_data["keyword"],
                source=kw_data.get("source", KeywordSource.MANUAL),
                intent=kw_data.get("intent"),
                cluster=kw_data.get("cluster"),
            )
            db.add(keyword)

        research.status = KeywordStatus.COMPLETED
        db.add(research)
        db.commit()
        db.refresh(research)

        if on_progress:
            await on_progress({"step": "done", "message": f"Found {len(clusters)} unique keywords"})

        return research

    except Exception as e:
        research.status = KeywordStatus.FAILED
        db.add(research)
        db.commit()
        raise


def _cluster_keywords(keywords: list[dict], seed: str) -> list[dict]:
    """Simple keyword clustering based on common terms."""
    seed_words = set(seed.lower().split())

    for kw in keywords:
        words = set(kw["keyword"].split())
        # Determine cluster name based on intent modifiers
        if any(w in words for w in ["how", "what", "why", "when", "guide", "tutorial"]):
            kw["cluster"] = "informational"
            kw.setdefault("intent", "informational")
        elif any(w in words for w in ["best", "top", "review", "compare", "vs"]):
            kw["cluster"] = "commercial"
            kw.setdefault("intent", "commercial")
        elif any(w in words for w in ["buy", "price", "deal", "discount", "cheap", "free"]):
            kw["cluster"] = "transactional"
            kw.setdefault("intent", "transactional")
        else:
            kw["cluster"] = "core"
            kw.setdefault("intent", "informational")

    return keywords
