from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ...models.user import User
from ...models.project_api_key import ProjectApiKey
from ...schemas.strategy import PillarCreate, PillarUpdate, ClusterCreate
from ...services.strategy_service import (
    list_pillars, create_pillar, update_pillar, delete_pillar,
    list_clusters, create_cluster, delete_cluster,
    generate_ai_recommendations,
)
from ...services.crypto_service import decrypt_api_key
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/strategy", tags=["strategy"])


# ---------------------------------------------------------------------------
# Pillars
# ---------------------------------------------------------------------------

@router.get("/pillars")
def get_pillars(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_pillars(db, project_id)


@router.post("/pillars", status_code=201)
def create_pillar_route(data: PillarCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_pillar(
        db,
        project_id=data.project_id,
        name=data.name,
        description=data.description,
        keywords=data.keywords,
        color=data.color,
    )


@router.put("/pillars/{pillar_id}")
def update_pillar_route(pillar_id: str, data: PillarUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = update_pillar(
        db,
        pillar_id=pillar_id,
        name=data.name,
        description=data.description,
        keywords=data.keywords,
        color=data.color,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Pillar not found")
    return result


@router.delete("/pillars/{pillar_id}", status_code=204)
def delete_pillar_route(pillar_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not delete_pillar(db, pillar_id):
        raise HTTPException(status_code=404, detail="Pillar not found")


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------

@router.get("/clusters")
def get_clusters(project_id: str, pillar_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_clusters(db, project_id, pillar_id)


@router.post("/clusters", status_code=201)
def create_cluster_route(data: ClusterCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_cluster(
        db,
        project_id=data.project_id,
        pillar_id=data.pillar_id,
        topic=data.topic,
        subtopics=data.subtopics,
        priority=data.priority,
    )


@router.delete("/clusters/{cluster_id}", status_code=204)
def delete_cluster_route(cluster_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not delete_cluster(db, cluster_id):
        raise HTTPException(status_code=404, detail="Cluster not found")


# ---------------------------------------------------------------------------
# AI Recommendations
# ---------------------------------------------------------------------------

@router.post("/ai-recommend")
async def ai_recommend(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Try to find an LLM key — prefer anthropic, then openai, then google_ai
    llm_key = None
    provider_name = "anthropic"
    for prov in ("anthropic", "openai", "google_ai"):
        key_obj = db.exec(
            select(ProjectApiKey).where(ProjectApiKey.project_id == project_id, ProjectApiKey.provider == prov)
        ).first()
        if key_obj:
            llm_key = decrypt_api_key(key_obj.encrypted_key)
            provider_name = prov
            break

    if not llm_key:
        raise HTTPException(status_code=400, detail="No LLM API key configured for this project. Add one in Settings.")

    try:
        result = await generate_ai_recommendations(db, project_id, llm_key, provider_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI recommendation failed: {str(e)}")
