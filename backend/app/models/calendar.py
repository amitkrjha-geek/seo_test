import enum
import uuid
from datetime import datetime, date, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class CalendarItemStatus(str, enum.Enum):
    IDEA = "idea"
    PLANNED = "planned"
    WRITING = "writing"
    REVIEW = "review"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


class CalendarItem(SQLModel, table=True):
    __tablename__ = "calendar_item"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    draft_id: str | None = Field(default=None, foreign_key="content_draft.id")
    title: str = ""
    target_keyword: str = ""
    pillar_id: str | None = Field(default=None, foreign_key="content_pillar.id")
    scheduled_date: date | None = None
    status: CalendarItemStatus = Field(default=CalendarItemStatus.IDEA)
    assignee_id: str | None = Field(default=None, foreign_key="user.id")
    notes: str = ""
    color: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecurringSlot(SQLModel, table=True):
    __tablename__ = "recurring_slot"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    day_of_week: int = 0  # 0=Monday ... 6=Sunday
    time: str = "09:00"
    pillar_id: str | None = Field(default=None, foreign_key="content_pillar.id")
    label: str = ""
    is_active: bool = True
