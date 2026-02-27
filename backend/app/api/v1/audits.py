import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.audit import SiteAudit, AuditIssue, AuditStatus
from ...models.project_api_key import ProjectApiKey
from ...services.audit_service import run_audit
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/audits", tags=["audits"])


class AuditCreate(BaseModel):
    project_id: str
    url: str


@router.get("")
def list_audits(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audits = db.exec(select(SiteAudit).where(SiteAudit.project_id == project_id).order_by(SiteAudit.created_at.desc())).all()
    return [{"id": a.id, "url": a.url, "status": a.status, "health_score": a.health_score, "created_at": a.created_at.isoformat()} for a in audits]


@router.post("", status_code=201)
def create_audit(data: AuditCreate, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = SiteAudit(project_id=data.project_id, url=data.url, initiated_by=user.id)
    db.add(audit)
    db.commit()
    db.refresh(audit)

    # Get pagespeed key if available
    ps_key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == data.project_id, ProjectApiKey.provider == "pagespeed")
    ).first()
    ps_key = decrypt_api_key(ps_key_obj.encrypted_key) if ps_key_obj else None

    background_tasks.add_task(_run_audit_bg, audit.id, data.url, ps_key)
    return {"id": audit.id, "status": "pending"}


async def _run_audit_bg(audit_id: str, url: str, pagespeed_key: str | None):
    from ...database import get_session
    with next(get_session()) as db:
        try:
            await run_audit(db, audit_id, url, pagespeed_api_key=pagespeed_key)
        except Exception:
            pass


@router.get("/{audit_id}")
def get_audit(audit_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.get(SiteAudit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    issues = db.exec(select(AuditIssue).where(AuditIssue.audit_id == audit_id)).all()
    return {
        "id": audit.id,
        "url": audit.url,
        "status": audit.status,
        "health_score": audit.health_score,
        "results": json.loads(audit.results_json) if audit.results_json else None,
        "issues": [
            {"id": i.id, "category": i.category, "severity": i.severity, "title": i.title, "description": i.description, "recommendation": i.recommendation}
            for i in issues
        ],
        "created_at": audit.created_at.isoformat(),
    }


@router.get("/{audit_id}/issues")
def get_audit_issues(audit_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    issues = db.exec(select(AuditIssue).where(AuditIssue.audit_id == audit_id)).all()
    return [
        {"id": i.id, "audit_id": i.audit_id, "category": i.category, "severity": i.severity,
         "title": i.title, "description": i.description, "recommendation": i.recommendation}
        for i in issues
    ]


@router.get("/{audit_id}/stream")
async def stream_audit(audit_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """SSE stream for audit progress."""
    audit = db.get(SiteAudit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    async def event_stream():
        while True:
            db.refresh(audit)
            yield f"data: {json.dumps({'status': audit.status, 'health_score': audit.health_score})}\n\n"
            if audit.status in [AuditStatus.COMPLETED, AuditStatus.FAILED]:
                yield "data: [DONE]\n\n"
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
