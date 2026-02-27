from datetime import date, datetime, timezone
from sqlmodel import Session, select

from ..models.calendar import CalendarItem, CalendarItemStatus
from ..schemas.calendar import CalendarItemCreate, CalendarItemUpdate


def list_items(
    db: Session,
    project_id: str,
    year: int | None = None,
    month: int | None = None,
) -> list[CalendarItem]:
    """Return calendar items for a project, optionally filtered by year+month."""
    stmt = select(CalendarItem).where(CalendarItem.project_id == project_id)

    if year and month:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)
        stmt = stmt.where(
            CalendarItem.scheduled_date >= start,
            CalendarItem.scheduled_date < end,
        )

    stmt = stmt.order_by(CalendarItem.scheduled_date.asc())
    return list(db.exec(stmt).all())


def create_item(db: Session, data: CalendarItemCreate) -> CalendarItem:
    """Create a new calendar item."""
    item = CalendarItem(
        project_id=data.project_id,
        title=data.title,
        target_keyword=data.target_keyword or "",
        pillar_id=data.pillar_id,
        scheduled_date=date.fromisoformat(data.scheduled_date) if data.scheduled_date else None,
        status=data.status,
        assignee_id=data.assignee_id,
        notes=data.notes or "",
        color=data.color or "",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item_id: str, data: CalendarItemUpdate) -> CalendarItem | None:
    """Update fields on an existing calendar item. Returns None if not found."""
    item = db.get(CalendarItem, item_id)
    if not item:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # Convert scheduled_date string to date object if present
    if "scheduled_date" in update_data and update_data["scheduled_date"] is not None:
        update_data["scheduled_date"] = date.fromisoformat(update_data["scheduled_date"])

    for key, value in update_data.items():
        setattr(item, key, value)

    item.updated_at = datetime.now(timezone.utc)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: str) -> bool:
    """Delete a calendar item. Returns False if not found."""
    item = db.get(CalendarItem, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def reschedule(db: Session, item_id: str, new_date: str) -> CalendarItem | None:
    """Update only the scheduled_date on a calendar item. Returns None if not found."""
    item = db.get(CalendarItem, item_id)
    if not item:
        return None

    item.scheduled_date = date.fromisoformat(new_date)
    item.updated_at = datetime.now(timezone.utc)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
