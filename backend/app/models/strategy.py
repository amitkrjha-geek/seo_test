import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class ClusterStatus(str, enum.Enum):
    IDEA = "idea"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class ClusterPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContentPillar(SQLModel, table=True):
    __tablename__ = "content_pillar"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    name: str = ""
    description: str = ""
    keywords: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON array
    color: str = "#6366f1"  # default indigo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TopicCluster(SQLModel, table=True):
    __tablename__ = "topic_cluster"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    pillar_id: str = Field(foreign_key="content_pillar.id", index=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    topic: str = ""
    subtopics: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON array
    status: ClusterStatus = Field(default=ClusterStatus.IDEA)
    priority: ClusterPriority = Field(default=ClusterPriority.MEDIUM)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContentStrategySettings(SQLModel, table=True):
    __tablename__ = "content_strategy_settings"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True, unique=True)
    publishing_frequency: str = ""  # e.g. "3 per week"
    goals: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON array
    target_audience_notes: str = ""
    ai_recommendations: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON array
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
