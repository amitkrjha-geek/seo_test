import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.competitor import CompetitorAnalysis, CompetitorPage, CompetitorStatus
from ...models.project_api_key import ProjectApiKey
from ...services.competitor_service import run_competitor_analysis
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/competitors", tags=["competitors"])


class CompetitorCreate(BaseModel):
    project_id: str
    target_keyword: str
    own_url: str | None = None


@router.get("")
def list_analyses(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analyses = db.exec(
        select(CompetitorAnalysis).where(CompetitorAnalysis.project_id == project_id).order_by(CompetitorAnalysis.created_at.desc())
    ).all()
    return [{"id": a.id, "target_keyword": a.target_keyword, "status": a.status, "created_at": a.created_at.isoformat()} for a in analyses]


@router.post("", status_code=201)
def create_analysis(data: CompetitorCreate, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = CompetitorAnalysis(project_id=data.project_id, target_keyword=data.target_keyword)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    serper_key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == data.project_id, ProjectApiKey.provider == "serper")
    ).first()
    serper_key = decrypt_api_key(serper_key_obj.encrypted_key) if serper_key_obj else None

    background_tasks.add_task(_run_analysis_bg, analysis.id, data.target_keyword, data.own_url, serper_key)
    return {"id": analysis.id, "status": "pending"}


async def _run_analysis_bg(analysis_id: str, keyword: str, own_url: str | None, serper_key: str | None):
    from ...database import get_session
    with next(get_session()) as db:
        try:
            await run_competitor_analysis(db, analysis_id, keyword, own_url=own_url, serper_api_key=serper_key)
        except Exception:
            pass


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.get(CompetitorAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    pages = db.exec(select(CompetitorPage).where(CompetitorPage.analysis_id == analysis_id).order_by(CompetitorPage.position)).all()
    return {
        "id": analysis.id,
        "target_keyword": analysis.target_keyword,
        "status": analysis.status,
        "gap_data": json.loads(analysis.gap_data) if analysis.gap_data else None,
        "pages": [
            {"id": p.id, "url": p.url, "title": p.title, "snippet": p.snippet, "position": p.position,
             "word_count": p.word_count}
            for p in pages
        ],
    }
