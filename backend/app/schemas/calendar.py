from pydantic import BaseModel
from ..models.calendar import CalendarItemStatus


class CalendarItemCreate(BaseModel):
    project_id: str
    title: str
    target_keyword: str | None = None
    pillar_id: str | None = None
    scheduled_date: str | None = None
    status: CalendarItemStatus = CalendarItemStatus.IDEA
    assignee_id: str | None = None
    notes: str | None = None
    color: str | None = None


class CalendarItemUpdate(BaseModel):
    title: str | None = None
    target_keyword: str | None = None
    pillar_id: str | None = None
    scheduled_date: str | None = None
    status: CalendarItemStatus | None = None
    assignee_id: str | None = None
    notes: str | None = None
    color: str | None = None


class RescheduleData(BaseModel):
    scheduled_date: str
