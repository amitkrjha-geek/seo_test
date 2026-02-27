from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from ...models.user import User
from ...models.audit import SiteAudit, AuditStatus
from ...models.keyword import KeywordResearch, Keyword
from ...models.content import ContentDraft
from ...models.rank_tracking import RankTracker, RankSnapshot
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Latest audit health score
    latest_audit = db.exec(
        select(SiteAudit).where(
            SiteAudit.project_id == project_id,
            SiteAudit.status == AuditStatus.COMPLETED,
        ).order_by(SiteAudit.created_at.desc())
    ).first()
    health_score = latest_audit.health_score if latest_audit else None

    # Keyword count
    keyword_count = db.exec(
        select(func.count()).select_from(RankTracker).where(
            RankTracker.project_id == project_id, RankTracker.is_active == True
        )
    ).one()

    # Content counts
    total_drafts = db.exec(
        select(func.count()).select_from(ContentDraft).where(ContentDraft.project_id == project_id)
    ).one()
    published_drafts = db.exec(
        select(func.count()).select_from(ContentDraft).where(
            ContentDraft.project_id == project_id, ContentDraft.status == "published"
        )
    ).one()

    # Audit count
    audit_count = db.exec(
        select(func.count()).select_from(SiteAudit).where(SiteAudit.project_id == project_id)
    ).one()

    # Recent audits
    recent_audits = db.exec(
        select(SiteAudit).where(SiteAudit.project_id == project_id).order_by(SiteAudit.created_at.desc()).limit(5)
    ).all()

    return {
        "health_score": health_score,
        "keyword_count": keyword_count,
        "total_drafts": total_drafts,
        "published_drafts": published_drafts,
        "audit_count": audit_count,
        "recent_audits": [
            {"id": a.id, "url": a.url, "status": a.status, "health_score": a.health_score,
             "created_at": a.created_at.isoformat()}
            for a in recent_audits
        ],
    }
