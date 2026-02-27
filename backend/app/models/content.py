import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    WRITING = "writing"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class ContentDraft(SQLModel, table=True):
    __tablename__ = "content_draft"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    brief_id: str | None = Field(default=None, foreign_key="content_brief.id")
    title: str = ""
    body: str = Field(default="", sa_column=Column(sa.Text))
    content_html: str = Field(default="", sa_column=Column(sa.Text))
    target_keyword: str = ""
    pillar_id: str | None = Field(default=None)
    meta_title: str = ""
    meta_description: str = ""
    llm_provider: str = ""  # anthropic, openai, google
    llm_model: str = ""
    seo_score: float | None = None
    word_count: int = 0
    status: ContentStatus = Field(default=ContentStatus.DRAFT)
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContentVersion(SQLModel, table=True):
    __tablename__ = "content_version"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    draft_id: str = Field(foreign_key="content_draft.id", index=True)
    version_number: int = 1
    body: str = Field(default="", sa_column=Column(sa.Text))
    seo_score: float | None = None
    change_summary: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
