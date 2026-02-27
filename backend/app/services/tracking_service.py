from sqlmodel import Session, select
from ..models.rank_tracking import RankTracker, RankSnapshot, CWVSnapshot
from ..integrations.pagespeed import analyze as pagespeed_analyze
from ..integrations.crux import get_crux_data
from ..integrations.serper import search_serp
import json
from datetime import datetime, timezone


async def check_rankings(
    db: Session,
    project_id: str,
    keywords: list[str],
    domain: str,
    serper_api_key: str | None = None,
    on_progress: callable = None,
) -> list[dict]:
    """Check current rankings for keywords."""
    results = []

    if not serper_api_key:
        return results

    for i, keyword in enumerate(keywords):
        if on_progress:
            await on_progress({
                "step": "rank",
                "message": f"Checking ranking {i+1}/{len(keywords)}: {keyword}",
            })

        try:
            serp_data = await search_serp(serper_api_key, keyword, num=20)
            position = None
            found_url = None

            for result in serp_data.get("organic", []):
                if domain.lower() in result.get("link", "").lower():
                    position = result.get("position", 0)
                    found_url = result.get("link", "")
                    break

            # Get or create tracker
            tracker = db.exec(
                select(RankTracker).where(
                    RankTracker.project_id == project_id,
                    RankTracker.keyword == keyword,
                )
            ).first()

            if not tracker:
                tracker = RankTracker(project_id=project_id, keyword=keyword)
                db.add(tracker)
                db.commit()
                db.refresh(tracker)

            # Create snapshot
            snapshot = RankSnapshot(
                tracker_id=tracker.id,
                position=position,
                url=found_url or "",
            )
            db.add(snapshot)
            db.commit()

            results.append({
                "keyword": keyword,
                "position": position,
                "url": found_url,
                "tracked_at": datetime.now(timezone.utc).isoformat(),
            })

        except Exception as e:
            results.append({
                "keyword": keyword,
                "position": None,
                "error": str(e),
            })

    return results


async def check_core_web_vitals(
    db: Session,
    project_id: str,
    url: str,
    pagespeed_api_key: str | None = None,
    on_progress: callable = None,
) -> dict:
    """Check Core Web Vitals using PageSpeed and CrUX APIs."""
    result = {"url": url, "lab_data": None, "field_data": None}

    # Lab data from PageSpeed
    if on_progress:
        await on_progress({"step": "pagespeed", "message": "Running PageSpeed analysis..."})
    try:
        ps_data = await pagespeed_analyze(url, api_key=pagespeed_api_key)
        result["lab_data"] = ps_data
    except Exception:
        pass

    # Field data from CrUX
    if on_progress:
        await on_progress({"step": "crux", "message": "Fetching Chrome UX Report data..."})
    try:
        crux_data = await get_crux_data(url, api_key=pagespeed_api_key)
        result["field_data"] = crux_data
    except Exception:
        pass

    # Save CWV snapshot
    lab = result.get("lab_data") or {}
    field = result.get("field_data") or {}

    snapshot = CWVSnapshot(
        project_id=project_id,
        url=url,
        lcp=lab.get("lcp") or field.get("lcp_p75"),
        inp=lab.get("inp") or field.get("inp_p75"),
        cls=lab.get("cls") or field.get("cls_p75"),
        fcp=lab.get("fcp"),
        ttfb=lab.get("ttfb"),
        performance_score=lab.get("performance_score"),
    )
    db.add(snapshot)
    db.commit()

    if on_progress:
        await on_progress({"step": "done", "message": "Core Web Vitals check complete!"})

    return result
