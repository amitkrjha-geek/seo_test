from pydantic import BaseModel


class PillarCreate(BaseModel):
    project_id: str
    name: str
    description: str | None = None
    keywords: list[str] | None = None
    color: str | None = None


class PillarUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    keywords: list[str] | None = None
    color: str | None = None


class ClusterCreate(BaseModel):
    project_id: str
    pillar_id: str
    topic: str
    subtopics: list[str] | None = None
    priority: str | None = None
