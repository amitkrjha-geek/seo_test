import uuid
from datetime import date, datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class RankTracker(SQLModel, table=True):
    __tablename__ = "rank_tracker"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    keyword: str
    target_url: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RankSnapshot(SQLModel, table=True):
    __tablename__ = "rank_snapshot"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tracker_id: str = Field(foreign_key="rank_tracker.id", index=True)
    position: int | None = None
    url: str = ""
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CWVSnapshot(SQLModel, table=True):
    __tablename__ = "cwv_snapshot"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    url: str
    lcp: float | None = None
    inp: float | None = None
    cls: float | None = None
    fcp: float | None = None
    ttfb: float | None = None
    performance_score: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
