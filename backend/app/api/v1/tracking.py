import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.rank_tracking import RankTracker, RankSnapshot, CWVSnapshot
from ...models.project import Project
from ...models.project_api_key import ProjectApiKey
from ...services.tracking_service import check_rankings, check_core_web_vitals
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/tracking", tags=["tracking"])


class RankCheckRequest(BaseModel):
    project_id: str
    keywords: list[str]


class CWVCheckRequest(BaseModel):
    project_id: str
    url: str


@router.get("/keywords")
def list_tracked_keywords(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trackers = db.exec(
        select(RankTracker).where(RankTracker.project_id == project_id, RankTracker.is_active == True)
    ).all()
    result = []
    for t in trackers:
        latest = db.exec(
            select(RankSnapshot).where(RankSnapshot.tracker_id == t.id).order_by(RankSnapshot.created_at.desc())
        ).first()
        result.append({
            "id": t.id,
            "keyword": t.keyword,
            "latest_position": latest.position if latest else None,
            "latest_url": latest.url if latest else None,
            "last_checked": latest.created_at.isoformat() if latest else None,
        })
    return result


@router.post("/rankings")
async def check_ranks_inline(data: RankCheckRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check rankings immediately (synchronous)."""
    project = db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    serper_key = _get_key(db, data.project_id, "serper")
    rankings = await check_rankings(db, data.project_id, data.keywords, project.domain, serper_api_key=serper_key)
    return {"rankings": rankings}


@router.post("/cwv")
async def check_cwv_inline(data: CWVCheckRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check CWV immediately (synchronous)."""
    ps_key = _get_key(db, data.project_id, "pagespeed")
    result = await check_core_web_vitals(db, data.project_id, data.url, pagespeed_api_key=ps_key)
    return result


@router.post("/check-ranks", status_code=201)
def check_ranks(data: RankCheckRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.get(Project, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    serper_key = _get_key(db, data.project_id, "serper")
    background_tasks.add_task(_check_ranks_bg, data.project_id, data.keywords, project.domain, serper_key)
    return {"status": "checking", "keywords": data.keywords}


async def _check_ranks_bg(project_id, keywords, domain, serper_key):
    from ...database import get_session
    with next(get_session()) as db:
        try:
            await check_rankings(db, project_id, keywords, domain, serper_api_key=serper_key)
        except Exception:
            pass


@router.post("/check-cwv")
async def check_cwv(data: CWVCheckRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ps_key = _get_key(db, data.project_id, "pagespeed")
    result = await check_core_web_vitals(db, data.project_id, data.url, pagespeed_api_key=ps_key)
    return result


@router.get("/rank-history")
def get_rank_history(tracker_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    snapshots = db.exec(
        select(RankSnapshot).where(RankSnapshot.tracker_id == tracker_id).order_by(RankSnapshot.created_at)
    ).all()
    return [
        {"position": s.position, "url": s.url, "created_at": s.created_at.isoformat()}
        for s in snapshots
    ]


@router.get("/cwv-history")
def get_cwv_history(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    snapshots = db.exec(
        select(CWVSnapshot).where(CWVSnapshot.project_id == project_id).order_by(CWVSnapshot.created_at.desc())
    ).all()
    return [
        {"url": s.url, "lcp": s.lcp, "inp": s.inp, "cls": s.cls, "fcp": s.fcp, "ttfb": s.ttfb,
         "performance_score": s.performance_score, "created_at": s.created_at.isoformat()}
        for s in snapshots
    ]


def _get_key(db: Session, project_id: str, provider: str) -> str | None:
    key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id, ProjectApiKey.provider == provider)
    ).first()
    return decrypt_api_key(key_obj.encrypted_key) if key_obj else None
