import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class ContentType(str, enum.Enum):
    BLOG_POST = "blog_post"
    LANDING_PAGE = "landing_page"
    PRODUCT_PAGE = "product_page"
    SERVICE_PAGE = "service_page"
    COMPARISON = "comparison"


class BriefStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    APPROVED = "approved"
    FAILED = "failed"


class ContentBrief(SQLModel, table=True):
    __tablename__ = "content_brief"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    keyword_id: str | None = Field(default=None, foreign_key="keyword.id")
    title: str = ""
    target_keyword: str
    secondary_keywords: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON
    target_word_count: int = 1500
    target_audience: str = ""
    content_type: ContentType = Field(default=ContentType.BLOG_POST)
    outline: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON structured headings
    serp_insights: str = Field(default="{}", sa_column=Column(sa.Text))  # JSON
    competitor_gaps: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON
    tone_guidelines: str = Field(default="", sa_column=Column(sa.Text))
    status: BriefStatus = Field(default=BriefStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
