import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class KeywordSource(str, enum.Enum):
    AUTOCOMPLETE = "autocomplete"
    SERPER = "serper"
    PYTRENDS = "pytrends"
    NLP = "nlp"
    MANUAL = "manual"


class SearchIntent(str, enum.Enum):
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    TRANSACTIONAL = "transactional"
    COMMERCIAL = "commercial"


class KeywordStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class KeywordResearch(SQLModel, table=True):
    __tablename__ = "keyword_research"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    seed_keyword: str
    status: KeywordStatus = KeywordStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Keyword(SQLModel, table=True):
    __tablename__ = "keyword"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    research_id: str = Field(foreign_key="keyword_research.id", index=True)
    keyword: str = Field(index=True)
    source: KeywordSource
    search_volume: int | None = None
    difficulty: float | None = None
    cpc: float | None = None
    trend_data: str | None = Field(default=None, sa_column=Column(sa.Text))  # JSON array
    intent: SearchIntent | None = None
    cluster: str | None = None
    is_selected: bool = False
