import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.keyword import KeywordResearch, Keyword, KeywordStatus
from ...models.project_api_key import ProjectApiKey
from ...services.keyword_service import run_keyword_research
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/keywords", tags=["keywords"])


class KeywordResearchCreate(BaseModel):
    project_id: str
    seed_keyword: str


@router.get("")
def list_research(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    researches = db.exec(
        select(KeywordResearch).where(KeywordResearch.project_id == project_id).order_by(KeywordResearch.created_at.desc())
    ).all()
    return [{"id": r.id, "seed_keyword": r.seed_keyword, "status": r.status, "created_at": r.created_at.isoformat()} for r in researches]


@router.post("", status_code=201)
def create_research(data: KeywordResearchCreate, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    research = KeywordResearch(project_id=data.project_id, seed_keyword=data.seed_keyword)
    db.add(research)
    db.commit()
    db.refresh(research)

    serper_key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == data.project_id, ProjectApiKey.provider == "serper")
    ).first()
    serper_key = decrypt_api_key(serper_key_obj.encrypted_key) if serper_key_obj else None

    background_tasks.add_task(_run_research_bg, research.id, data.seed_keyword, serper_key)
    return {"id": research.id, "status": "pending"}


async def _run_research_bg(research_id: str, seed_keyword: str, serper_key: str | None):
    from ...database import get_session
    with next(get_session()) as db:
        try:
            await run_keyword_research(db, research_id, seed_keyword, serper_api_key=serper_key)
        except Exception:
            pass


@router.get("/{research_id}")
def get_research(research_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    research = db.get(KeywordResearch, research_id)
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    keywords = db.exec(select(Keyword).where(Keyword.research_id == research_id)).all()
    return {
        "id": research.id,
        "seed_keyword": research.seed_keyword,
        "status": research.status,
        "keywords": [
            {"id": k.id, "keyword": k.keyword, "source": k.source, "search_volume": k.search_volume,
             "difficulty": k.difficulty, "intent": k.intent, "cluster": k.cluster}
            for k in keywords
        ],
    }


@router.get("/{research_id}/keywords")
def list_keywords(research_id: str, cluster: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Keyword).where(Keyword.research_id == research_id)
    if cluster:
        query = query.where(Keyword.cluster == cluster)
    keywords = db.exec(query).all()
    return [
        {"id": k.id, "keyword": k.keyword, "source": k.source, "search_volume": k.search_volume,
         "difficulty": k.difficulty, "intent": k.intent, "cluster": k.cluster, "is_selected": k.is_selected}
        for k in keywords
    ]
