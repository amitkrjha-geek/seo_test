from sqlmodel import Session
from ..models.competitor import CompetitorAnalysis, CompetitorPage, CompetitorStatus
from ..integrations.serper import search_serp
from ..core.fetcher import fetch_page
from ..core.parser import parse_html
from ..core.nlp_analyzer import analyze_text
import json
import traceback


async def run_competitor_analysis(
    db: Session,
    analysis_id: str,
    keyword: str,
    own_url: str | None = None,
    serper_api_key: str | None = None,
    on_progress: callable = None,
) -> CompetitorAnalysis:
    """Analyze SERP competitors for a given keyword."""
    analysis = db.get(CompetitorAnalysis, analysis_id)
    if not analysis:
        raise ValueError(f"Analysis {analysis_id} not found")

    analysis.status = CompetitorStatus.RUNNING
    db.add(analysis)
    db.commit()

    try:
        # Step 1: Get SERP results
        if on_progress:
            await on_progress({"step": "serp", "message": "Fetching SERP results..."})

        if not serper_api_key:
            raise ValueError("Serper API key required for competitor analysis")

        serp_data = await search_serp(serper_api_key, keyword, num=10)
        organic = serp_data.get("organic", [])

        if not organic:
            analysis.status = CompetitorStatus.FAILED
            db.add(analysis)
            db.commit()
            return analysis

        # Step 2: Analyze top competitors
        competitor_pages = []
        for i, result in enumerate(organic[:5]):  # Top 5
            comp_url = result.get("link", "")
            if on_progress:
                await on_progress({
                    "step": "analyze",
                    "message": f"Analyzing competitor {i+1}/5: {comp_url[:50]}...",
                })

            try:
                page_data = await fetch_page(comp_url)
                parsed = parse_html(page_data["html"], comp_url)

                # Extract text content for NLP
                text_content = parsed.get("text_content", "")
                nlp_data = analyze_text(text_content) if text_content else {}

                comp_page = CompetitorPage(
                    analysis_id=analysis.id,
                    url=comp_url,
                    position=result.get("position", i + 1),
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                    word_count=parsed.get("word_count", 0),
                    tfidf_data=json.dumps(nlp_data.get("keyword_density", {})),
                    entities=json.dumps(nlp_data.get("top_terms", [])),
                )
                db.add(comp_page)
                competitor_pages.append(comp_page)

            except Exception:
                continue  # Skip failed pages

        # Step 3: Content gap analysis
        if on_progress:
            await on_progress({"step": "gap", "message": "Running content gap analysis..."})

        gap_analysis = _analyze_gaps(competitor_pages, own_url)
        analysis.gap_data = json.dumps(gap_analysis, default=str)

        analysis.status = CompetitorStatus.COMPLETED
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        if on_progress:
            await on_progress({
                "step": "done",
                "message": f"Analyzed {len(competitor_pages)} competitors",
            })

        return analysis

    except Exception as e:
        analysis.status = CompetitorStatus.FAILED
        db.add(analysis)
        db.commit()
        raise


def _analyze_gaps(pages: list[CompetitorPage], own_url: str | None) -> dict:
    """Identify content gaps between competitors."""
    all_terms: dict[str, int] = {}
    avg_word_count = 0
    titles = []

    for page in pages:
        avg_word_count += page.word_count
        titles.append(page.title)

        try:
            tfidf = json.loads(page.tfidf_data) if page.tfidf_data else {}
            for term, data in tfidf.items():
                if isinstance(data, dict):
                    all_terms[term] = all_terms.get(term, 0) + 1
                else:
                    all_terms[term] = all_terms.get(term, 0) + 1
        except (json.JSONDecodeError, AttributeError):
            pass

    avg_word_count = avg_word_count // max(len(pages), 1)

    # Sort terms by frequency across competitors
    common_terms = sorted(all_terms.items(), key=lambda x: x[1], reverse=True)[:30]

    return {
        "avg_word_count": avg_word_count,
        "recommended_word_count": int(avg_word_count * 1.2),  # 20% more than average
        "common_terms": [{"term": t, "frequency": f} for t, f in common_terms],
        "competitor_count": len(pages),
        "title_patterns": titles,
    }
