import json
from datetime import datetime, timezone
from sqlmodel import Session, select

from ..models.strategy import ContentPillar, TopicCluster, ContentStrategySettings, ClusterPriority
from ..models.keyword import KeywordResearch, Keyword
from ..models.brand_persona import BrandPersona
from ..llm.factory import get_provider


# ---------------------------------------------------------------------------
# Pillars CRUD
# ---------------------------------------------------------------------------

def list_pillars(db: Session, project_id: str) -> list[dict]:
    pillars = db.exec(
        select(ContentPillar)
        .where(ContentPillar.project_id == project_id)
        .order_by(ContentPillar.created_at.desc())
    ).all()
    results = []
    for p in pillars:
        results.append(_pillar_to_dict(p))
    return results


def create_pillar(db: Session, project_id: str, name: str,
                  description: str | None = None,
                  keywords: list[str] | None = None,
                  color: str | None = None) -> dict:
    pillar = ContentPillar(
        project_id=project_id,
        name=name,
        description=description or "",
        keywords=json.dumps(keywords or []),
        color=color or "#6366f1",
    )
    db.add(pillar)
    db.commit()
    db.refresh(pillar)
    return _pillar_to_dict(pillar)


def update_pillar(db: Session, pillar_id: str,
                  name: str | None = None,
                  description: str | None = None,
                  keywords: list[str] | None = None,
                  color: str | None = None) -> dict | None:
    pillar = db.get(ContentPillar, pillar_id)
    if not pillar:
        return None
    if name is not None:
        pillar.name = name
    if description is not None:
        pillar.description = description
    if keywords is not None:
        pillar.keywords = json.dumps(keywords)
    if color is not None:
        pillar.color = color
    pillar.updated_at = datetime.now(timezone.utc)
    db.add(pillar)
    db.commit()
    db.refresh(pillar)
    return _pillar_to_dict(pillar)


def delete_pillar(db: Session, pillar_id: str) -> bool:
    pillar = db.get(ContentPillar, pillar_id)
    if not pillar:
        return False
    # Also delete associated clusters
    clusters = db.exec(
        select(TopicCluster).where(TopicCluster.pillar_id == pillar_id)
    ).all()
    for c in clusters:
        db.delete(c)
    db.delete(pillar)
    db.commit()
    return True


def _pillar_to_dict(p: ContentPillar) -> dict:
    keywords = []
    try:
        keywords = json.loads(p.keywords) if p.keywords else []
    except (json.JSONDecodeError, TypeError):
        keywords = []
    return {
        "id": p.id,
        "project_id": p.project_id,
        "name": p.name,
        "description": p.description,
        "keywords": keywords,
        "color": p.color,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Clusters CRUD
# ---------------------------------------------------------------------------

def list_clusters(db: Session, project_id: str, pillar_id: str | None = None) -> list[dict]:
    query = select(TopicCluster).where(TopicCluster.project_id == project_id)
    if pillar_id:
        query = query.where(TopicCluster.pillar_id == pillar_id)
    query = query.order_by(TopicCluster.created_at.desc())
    clusters = db.exec(query).all()
    return [_cluster_to_dict(c) for c in clusters]


def create_cluster(db: Session, project_id: str, pillar_id: str, topic: str,
                   subtopics: list[str] | None = None,
                   priority: str | None = None) -> dict:
    cluster = TopicCluster(
        project_id=project_id,
        pillar_id=pillar_id,
        topic=topic,
        subtopics=json.dumps(subtopics or []),
        priority=ClusterPriority(priority) if priority else ClusterPriority.MEDIUM,
    )
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return _cluster_to_dict(cluster)


def delete_cluster(db: Session, cluster_id: str) -> bool:
    cluster = db.get(TopicCluster, cluster_id)
    if not cluster:
        return False
    db.delete(cluster)
    db.commit()
    return True


def _cluster_to_dict(c: TopicCluster) -> dict:
    subtopics = []
    try:
        subtopics = json.loads(c.subtopics) if c.subtopics else []
    except (json.JSONDecodeError, TypeError):
        subtopics = []
    return {
        "id": c.id,
        "pillar_id": c.pillar_id,
        "project_id": c.project_id,
        "topic": c.topic,
        "subtopics": subtopics,
        "status": c.status.value if hasattr(c.status, "value") else c.status,
        "priority": c.priority.value if hasattr(c.priority, "value") else c.priority,
        "created_at": c.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# AI Recommendations
# ---------------------------------------------------------------------------

STRATEGY_SYSTEM_PROMPT = """You are an expert SEO content strategist. Based on the provided keywords and brand context, suggest a content strategy with content pillars and topic clusters.

Return your response as valid JSON with the following structure:
{
  "pillars": [
    {
      "name": "Pillar Name",
      "description": "Brief description of this content pillar",
      "topics": ["Topic 1", "Topic 2", "Topic 3"]
    }
  ]
}

Guidelines:
- Suggest 3-5 content pillars that cover the brand's key areas
- Each pillar should have 3-5 topic clusters
- Topics should be specific enough to write articles about
- Consider search intent and keyword clustering
- Align recommendations with the brand persona if provided
- Return ONLY valid JSON, no markdown formatting or extra text"""


async def generate_ai_recommendations(
    db: Session,
    project_id: str,
    llm_api_key: str,
    llm_provider_name: str = "anthropic",
) -> dict:
    """Use LLM to suggest content pillars and topic clusters based on existing keyword research."""

    # Gather existing keywords from KeywordResearch + Keyword models
    researches = db.exec(
        select(KeywordResearch).where(KeywordResearch.project_id == project_id)
    ).all()
    all_keywords: list[str] = []
    for r in researches:
        keywords = db.exec(
            select(Keyword).where(Keyword.research_id == r.id)
        ).all()
        all_keywords.extend([kw.keyword for kw in keywords])

    # Remove duplicates, take top 50
    unique_keywords = list(dict.fromkeys(all_keywords))[:50]

    # Get brand persona if available
    persona = db.exec(
        select(BrandPersona).where(BrandPersona.project_id == project_id)
    ).first()
    persona_context = persona.to_prompt_context() if persona else ""

    # Get existing pillars for context
    existing_pillars = db.exec(
        select(ContentPillar).where(ContentPillar.project_id == project_id)
    ).all()
    existing_names = [p.name for p in existing_pillars]

    user_prompt_parts = []
    if unique_keywords:
        user_prompt_parts.append(f"Existing keywords from research:\n{', '.join(unique_keywords)}")
    if existing_names:
        user_prompt_parts.append(f"Already existing pillars (suggest different ones or expand): {', '.join(existing_names)}")
    if persona_context:
        user_prompt_parts.append(f"\n{persona_context}")
    if not user_prompt_parts:
        user_prompt_parts.append("No keywords researched yet. Suggest general SEO content pillars for a new website.")

    user_prompt = "\n\n".join(user_prompt_parts)

    provider = get_provider(llm_provider_name, llm_api_key)
    raw = await provider.complete(STRATEGY_SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    # Parse the JSON response
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Remove opening fence
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(cleaned[start:end])
        else:
            result = {"pillars": []}

    # Save recommendations to strategy settings
    settings = db.exec(
        select(ContentStrategySettings).where(ContentStrategySettings.project_id == project_id)
    ).first()
    if not settings:
        settings = ContentStrategySettings(project_id=project_id)
    settings.ai_recommendations = json.dumps(result.get("pillars", []))
    settings.updated_at = datetime.now(timezone.utc)
    db.add(settings)
    db.commit()

    return result
