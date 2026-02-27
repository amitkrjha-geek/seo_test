import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.content_brief import ContentBrief
from ...models.brand_persona import BrandPersona
from ...models.project_api_key import ProjectApiKey
from ...services.brief_service import generate_brief
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/briefs", tags=["briefs"])


class BriefCreate(BaseModel):
    project_id: str
    target_keyword: str
    llm_provider: str = "anthropic"
    llm_model: str | None = None


@router.get("")
def list_briefs(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    briefs = db.exec(
        select(ContentBrief).where(ContentBrief.project_id == project_id).order_by(ContentBrief.created_at.desc())
    ).all()
    return [
        {"id": b.id, "target_keyword": b.target_keyword, "status": b.status, "created_at": b.created_at.isoformat()}
        for b in briefs
    ]


@router.post("", status_code=201)
def create_brief(data: BriefCreate, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    brief = ContentBrief(project_id=data.project_id, target_keyword=data.target_keyword)
    db.add(brief)
    db.commit()
    db.refresh(brief)

    # Get API keys
    serper_key = _get_key(db, data.project_id, "serper")
    llm_key = _get_key(db, data.project_id, data.llm_provider)

    # Get persona
    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == data.project_id)).first()
    persona_context = persona.to_prompt_context() if persona else ""

    background_tasks.add_task(
        _gen_brief_bg, brief.id, data.target_keyword, serper_key, data.llm_provider, llm_key or "", data.llm_model, persona_context
    )
    return {"id": brief.id, "status": "draft"}


async def _gen_brief_bg(brief_id, keyword, serper_key, llm_provider, llm_key, llm_model, persona_context):
    from ...database import get_session
    with next(get_session()) as db:
        try:
            await generate_brief(db, brief_id, keyword, serper_api_key=serper_key,
                                 llm_provider_name=llm_provider, llm_api_key=llm_key,
                                 llm_model=llm_model, persona_context=persona_context)
        except Exception:
            pass


@router.get("/{brief_id}")
def get_brief(brief_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    brief = db.get(ContentBrief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return {
        "id": brief.id,
        "target_keyword": brief.target_keyword,
        "status": brief.status,
        "outline": json.loads(brief.outline) if brief.outline else None,
        "serp_insights": json.loads(brief.serp_insights) if brief.serp_insights else None,
        "created_at": brief.created_at.isoformat(),
    }


def _get_key(db: Session, project_id: str, provider: str) -> str | None:
    key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id, ProjectApiKey.provider == provider)
    ).first()
    return decrypt_api_key(key_obj.encrypted_key) if key_obj else None
