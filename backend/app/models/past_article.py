import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class PastArticle(SQLModel, table=True):
    __tablename__ = "past_article"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    url: str = ""
    title: str = ""
    body: str = Field(default="", sa_column=Column(sa.Text))
    word_count: int = 0
    publish_date: datetime | None = None
    seo_score: float | None = None
    performance_data: str = Field(default="{}", sa_column=Column(sa.Text))  # JSON
    needs_refresh: bool = False
    refresh_suggestions: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON
    crawled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
