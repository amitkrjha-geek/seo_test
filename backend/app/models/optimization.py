import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class ContentOptimization(SQLModel, table=True):
    __tablename__ = "content_optimization"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    draft_id: str = Field(default="", index=True)  # may be a draft ID or "inline"
    readability_score: float = 0.0  # Flesch Reading Ease
    grade_level: float = 0.0  # Flesch-Kincaid Grade
    entities: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON
    keyword_density: str = Field(default="{}", sa_column=Column(sa.Text))  # JSON
    suggestions: str = Field(default="[]", sa_column=Column(sa.Text))  # JSON array
    eeat_score: str = Field(default="{}", sa_column=Column(sa.Text))  # JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
