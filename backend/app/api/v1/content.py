import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.content import ContentDraft, ContentVersion
from ...models.content_brief import ContentBrief
from ...models.brand_persona import BrandPersona
from ...models.project_api_key import ProjectApiKey
from ...services.content_service import write_content, stream_content, stream_inline_edit
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/content", tags=["content"])


class ContentCreate(BaseModel):
    project_id: str
    brief_id: str | None = None
    target_keyword: str
    llm_provider: str = "anthropic"
    llm_model: str | None = None


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    content_html: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    status: str | None = None
    seo_score: int | None = None


class ContentRewrite(BaseModel):
    instructions: str
    llm_provider: str = "anthropic"
    llm_model: str | None = None


@router.get("")
def list_content(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drafts = db.exec(
        select(ContentDraft).where(ContentDraft.project_id == project_id).order_by(ContentDraft.updated_at.desc())
    ).all()
    return [
        {"id": d.id, "title": d.title, "status": d.status, "seo_score": d.seo_score,
         "llm_provider": d.llm_provider, "word_count": d.word_count, "updated_at": d.updated_at.isoformat()}
        for d in drafts
    ]


@router.post("", status_code=201)
def create_content(data: ContentCreate, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get brief content if provided
    brief_json = "{}"
    if data.brief_id:
        brief = db.get(ContentBrief, data.brief_id)
        if brief:
            brief_json = brief.outline or "{}"

    draft = ContentDraft(
        project_id=data.project_id,
        brief_id=data.brief_id,
        title=data.target_keyword,
        llm_provider=data.llm_provider,
        created_by=user.id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    llm_key = _get_key(db, data.project_id, data.llm_provider)
    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == data.project_id)).first()
    persona_context = persona.to_prompt_context() if persona else ""

    background_tasks.add_task(
        _write_bg, draft.id, brief_json, data.target_keyword, data.llm_provider, llm_key or "", data.llm_model, persona_context
    )
    return {"id": draft.id, "status": "writing"}


async def _write_bg(draft_id, brief_json, keyword, provider, key, model, persona):
    from ...database import get_session
    with next(get_session()) as db:
        try:
            await write_content(db, draft_id, brief_json, keyword,
                                llm_provider_name=provider, llm_api_key=key,
                                llm_model=model, persona_context=persona)
        except Exception:
            pass


@router.get("/ai-inline")
async def ai_inline(
    project_id: str,
    text: str,
    action: str = "improve",
    provider: str = "anthropic",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE stream for inline AI text editing (improve, shorten, expand, fix_grammar)."""
    llm_key = _get_key(db, project_id, provider)
    if not llm_key:
        raise HTTPException(status_code=400, detail=f"No {provider} API key configured")

    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == project_id)).first()
    persona_context = persona.to_prompt_context() if persona else ""

    async def event_stream():
        async for chunk in stream_inline_edit(
            text, action, llm_provider_name=provider,
            llm_api_key=llm_key, persona_context=persona_context
        ):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{draft_id}")
def get_content(draft_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    draft = db.get(ContentDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {
        "id": draft.id,
        "title": draft.title,
        "body": draft.body,
        "content_html": draft.content_html,
        "meta_title": draft.meta_title,
        "meta_description": draft.meta_description,
        "status": draft.status,
        "seo_score": draft.seo_score,
        "llm_provider": draft.llm_provider,
        "word_count": draft.word_count,
        "created_at": draft.created_at.isoformat(),
        "updated_at": draft.updated_at.isoformat(),
    }


@router.put("/{draft_id}")
def update_content(draft_id: str, data: ContentUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    draft = db.get(ContentDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    update_data = data.model_dump(exclude_unset=True)
    if "body" in update_data:
        update_data["word_count"] = len(update_data["body"].split()) if update_data["body"] else 0
    for key, value in update_data.items():
        setattr(draft, key, value)
    from datetime import datetime, timezone
    draft.updated_at = datetime.now(timezone.utc)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return {
        "id": draft.id, "title": draft.title, "body": draft.body,
        "status": draft.status, "seo_score": draft.seo_score,
        "word_count": draft.word_count, "updated_at": draft.updated_at.isoformat(),
    }


@router.get("/{draft_id}/stream")
async def stream_write(
    draft_id: str,
    project_id: str,
    keyword: str,
    provider: str = "anthropic",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE stream for real-time content writing."""
    llm_key = _get_key(db, project_id, provider)
    if not llm_key:
        raise HTTPException(status_code=400, detail=f"No {provider} API key configured")

    brief = None
    draft = db.get(ContentDraft, draft_id)
    if draft and draft.brief_id:
        brief_obj = db.get(ContentBrief, draft.brief_id)
        brief = brief_obj.outline if brief_obj else "{}"

    persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == project_id)).first()
    persona_context = persona.to_prompt_context() if persona else ""

    async def event_stream():
        async for chunk in stream_content(
            brief or "{}", keyword, llm_provider_name=provider,
            llm_api_key=llm_key, persona_context=persona_context
        ):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{draft_id}/versions")
def list_versions(draft_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    versions = db.exec(
        select(ContentVersion).where(ContentVersion.draft_id == draft_id).order_by(ContentVersion.version_number.desc())
    ).all()
    return [
        {"id": v.id, "version_number": v.version_number, "seo_score": v.seo_score,
         "change_summary": v.change_summary, "created_at": v.created_at.isoformat()}
        for v in versions
    ]


def _get_key(db: Session, project_id: str, provider: str) -> str | None:
    key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id, ProjectApiKey.provider == provider)
    ).first()
    return decrypt_api_key(key_obj.encrypted_key) if key_obj else None
