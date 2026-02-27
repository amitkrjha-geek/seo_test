import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class CompetitorStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CompetitorAnalysis(SQLModel, table=True):
    __tablename__ = "competitor_analysis"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    target_keyword: str
    status: CompetitorStatus = CompetitorStatus.PENDING
    gap_data: str | None = Field(default=None, sa_column=Column(sa.Text))  # JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CompetitorPage(SQLModel, table=True):
    __tablename__ = "competitor_page"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    analysis_id: str = Field(foreign_key="competitor_analysis.id", index=True)
    url: str
    title: str = ""
    snippet: str = ""
    position: int = 0
    word_count: int = 0
    tfidf_data: str | None = Field(default=None, sa_column=Column(sa.Text))  # JSON
    entities: str | None = Field(default=None, sa_column=Column(sa.Text))  # JSON
