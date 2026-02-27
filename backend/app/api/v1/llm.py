import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from ...models.user import User
from ...models.project_api_key import ProjectApiKey
from ...models.brand_persona import BrandPersona
from ...llm.factory import get_provider, PROVIDERS
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/llm", tags=["llm"])


class ChatRequest(BaseModel):
    project_id: str
    provider: str = "anthropic"
    model: str | None = None
    system_prompt: str = ""
    user_prompt: str
    temperature: float = 0.7
    max_tokens: int = 4096
    include_persona: bool = True


@router.get("/providers")
def list_providers():
    return {"providers": list(PROVIDERS.keys())}


@router.post("/chat")
async def chat(data: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    key = _get_key(db, data.project_id, data.provider)
    if not key:
        raise HTTPException(status_code=400, detail=f"No {data.provider} API key configured for this project")

    system = data.system_prompt
    if data.include_persona:
        persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == data.project_id)).first()
        if persona:
            system = f"{system}\n\n{persona.to_prompt_context()}" if system else persona.to_prompt_context()

    provider = get_provider(data.provider, key, data.model)
    result = await provider.complete(system, data.user_prompt, data.temperature, data.max_tokens)
    return {"response": result, "provider": data.provider, "model": provider.model}


@router.post("/chat/stream")
async def chat_stream(data: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    key = _get_key(db, data.project_id, data.provider)
    if not key:
        raise HTTPException(status_code=400, detail=f"No {data.provider} API key configured")

    system = data.system_prompt
    if data.include_persona:
        persona = db.exec(select(BrandPersona).where(BrandPersona.project_id == data.project_id)).first()
        if persona:
            system = f"{system}\n\n{persona.to_prompt_context()}" if system else persona.to_prompt_context()

    provider = get_provider(data.provider, key, data.model)

    async def event_stream():
        async for chunk in provider.stream(system, data.user_prompt, data.temperature, data.max_tokens):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _get_key(db: Session, project_id: str, provider: str) -> str | None:
    key_obj = db.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id, ProjectApiKey.provider == provider)
    ).first()
    return decrypt_api_key(key_obj.encrypted_key) if key_obj else None
