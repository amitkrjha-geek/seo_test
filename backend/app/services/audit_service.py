from sqlmodel import Session
from ..models.audit import SiteAudit, AuditIssue, AuditStatus
from ..core.fetcher import fetch_page
from ..core.parser import parse_html
from ..core.scoring import calculate_health_score
from ..integrations.pagespeed import analyze as pagespeed_analyze
import json
import traceback


async def run_audit(
    db: Session,
    audit_id: str,
    url: str,
    pagespeed_api_key: str | None = None,
    on_progress: callable = None,
) -> SiteAudit:
    """Run a full site audit. Updates the audit record as it progresses."""
    audit = db.get(SiteAudit, audit_id)
    if not audit:
        raise ValueError(f"Audit {audit_id} not found")

    audit.status = AuditStatus.RUNNING
    db.add(audit)
    db.commit()

    try:
        # Step 1: Fetch page
        if on_progress:
            await on_progress({"step": "fetch", "message": "Fetching page..."})
        page_data = await fetch_page(url)

        if page_data["status_code"] >= 400:
            audit.status = AuditStatus.FAILED
            audit.results_json = json.dumps({"error": f"HTTP {page_data['status_code']}"})
            db.add(audit)
            db.commit()
            return audit

        # Step 2: Parse HTML
        if on_progress:
            await on_progress({"step": "parse", "message": "Analyzing HTML structure..."})
        parsed = parse_html(page_data["html"], url)

        # Step 3: PageSpeed analysis (optional)
        pagespeed_data = None
        if pagespeed_api_key or True:  # PageSpeed works without key too
            if on_progress:
                await on_progress({"step": "pagespeed", "message": "Running PageSpeed analysis..."})
            try:
                pagespeed_data = await pagespeed_analyze(url, api_key=pagespeed_api_key)
            except Exception:
                pass  # PageSpeed is optional

        # Step 4: Calculate score
        if on_progress:
            await on_progress({"step": "scoring", "message": "Calculating SEO health score..."})
        score, issues = calculate_health_score(parsed, pagespeed_data)

        # Step 5: Save results
        audit.health_score = score
        audit.status = AuditStatus.COMPLETED
        audit.results_json = json.dumps({
            "parsed": parsed,
            "pagespeed": pagespeed_data,
            "page_meta": {
                "status_code": page_data["status_code"],
                "content_length": page_data["content_length"],
                "url": page_data["url"],
            },
        }, default=str)
        db.add(audit)

        # Save individual issues
        for issue_data in issues:
            issue = AuditIssue(
                audit_id=audit.id,
                category=issue_data["category"],
                severity=issue_data["severity"],
                title=issue_data["title"],
                description=issue_data.get("description", ""),
                recommendation=issue_data.get("recommendation", ""),
            )
            db.add(issue)

        db.commit()
        db.refresh(audit)

        if on_progress:
            await on_progress({"step": "done", "message": f"Audit complete. Score: {score}/100", "score": score})

        return audit

    except Exception as e:
        audit.status = AuditStatus.FAILED
        audit.results_json = json.dumps({"error": str(e), "traceback": traceback.format_exc()})
        db.add(audit)
        db.commit()
        raise
