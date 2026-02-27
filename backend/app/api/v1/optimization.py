import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.optimization import ContentOptimization
from ...models.content import ContentDraft
from ...models.brand_persona import BrandPersona
from ...models.project_api_key import ProjectApiKey
from ...services.optimization_service import analyze_content
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/optimization", tags=["optimization"])


class OptimizationCreate(BaseModel):
    draft_id: str
    project_id: str
    target_keyword: str
    llm_provider: str | None = None
    llm_model: str | None = None


class InlineAnalyze(BaseModel):
    content: str
    keyword: str
    project_id: str | None = None


@router.post("/analyze")
async def inline_analyze(data: InlineAnalyze, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Analyze content inline without requiring a saved draft."""
    optimization = ContentOptimization(draft_id="inline")
    db.add(optimization)
    db.commit()
    db.refresh(optimization)

    tr_key = _get_key(db, data.project_id, "textrazor") if data.project_id else None
    persona = ""
    if data.project_id:
        p = db.exec(select(BrandPersona).where(BrandPersona.project_id == data.project_id)).first()
        persona = p.to_prompt_context() if p else ""

    result = await analyze_content(db, optimization.id, data.content, data.keyword,
                                   textrazor_api_key=tr_key, persona_context=persona)
    return {
        "id": result.id,
        "readability_score": result.readability_score,
        "grade_level": result.grade_level,
        "entities": json.loads(result.entities) if result.entities else [],
        "keyword_density": json.loads(result.keyword_density) if result.keyword_density else {},
        "suggestions": json.loads(result.suggestions) if result.suggestions else [],
        "eeat_score": json.loads(result.eeat_score) if result.eeat_score else {},
    }


@router.post("", status_code=201)
def create_optimization(data: OptimizationCreate, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    draft = db.get(ContentDraft, data.draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    optimization = ContentOptimization(draft_id=data.draft_id)
    db.add(optimization)
    db.commit()
    db.refresh(optimization)

    textrazor_key = _get_key(db, data.project_id, "textrazor")
    llm_key = _get_key(db, data.project_id, data.llm_provider) if data.llm_provider else None
    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == data.project_id)).first()
    persona_context = persona.to_prompt_context() if persona else ""

    background_tasks.add_task(
        _analyze_bg, optimization.id, draft.body, data.target_keyword, textrazor_key,
        data.llm_provider, llm_key, persona_context
    )
    return {"id": optimization.id, "status": "analyzing"}


async def _analyze_bg(opt_id, content, keyword, tr_key, llm_provider, llm_key, persona):
    from ...database import get_session
    with next(get_session()) as db:
        try:
            await analyze_content(db, opt_id, content, keyword,
                                  textrazor_api_key=tr_key, llm_provider_name=llm_provider,
                                  llm_api_key=llm_key, persona_context=persona)
        except Exception:
            pass


@router.get("/{optimization_id}")
def get_optimization(optimization_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opt = db.get(ContentOptimization, optimization_id)
    if not opt:
        raise HTTPException(status_code=404, detail="Optimization not found")
    return {
        "id": opt.id,
        "draft_id": opt.draft_id,
        "readability_score": opt.readability_score,
        "grade_level": opt.grade_level,
        "entities": json.loads(opt.entities) if opt.entities else [],
        "keyword_density": json.loads(opt.keyword_density) if opt.keyword_density else {},
        "suggestions": json.loads(opt.suggestions) if opt.suggestions else [],
        "eeat_score": json.loads(opt.eeat_score) if opt.eeat_score else {},
        "created_at": opt.created_at.isoformat(),
    }


def _get_key(db: Session, project_id: str, provider: str) -> str | None:
    key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id, ProjectApiKey.provider == provider)
    ).first()
    return decrypt_api_key(key_obj.encrypted_key) if key_obj else None
