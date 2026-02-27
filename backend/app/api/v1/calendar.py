from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ...models.user import User
from ...schemas.calendar import CalendarItemCreate, CalendarItemUpdate, RescheduleData
from ...services.calendar_service import (
    list_items,
    create_item,
    update_item,
    delete_item,
    reschedule,
)
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("")
def get_calendar_items(
    project_id: str = Query(...),
    year: int | None = Query(None),
    month: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List calendar items for a project, optionally filtered by year+month."""
    items = list_items(db, project_id, year, month)
    return [
        {
            "id": it.id,
            "project_id": it.project_id,
            "draft_id": it.draft_id,
            "title": it.title,
            "target_keyword": it.target_keyword,
            "pillar_id": it.pillar_id,
            "scheduled_date": it.scheduled_date.isoformat() if it.scheduled_date else None,
            "status": it.status.value,
            "assignee_id": it.assignee_id,
            "notes": it.notes,
            "color": it.color,
            "created_at": it.created_at.isoformat(),
        }
        for it in items
    ]


@router.post("/items", status_code=201)
def create_calendar_item(
    data: CalendarItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new calendar item."""
    item = create_item(db, data)
    return {
        "id": item.id,
        "project_id": item.project_id,
        "draft_id": item.draft_id,
        "title": item.title,
        "target_keyword": item.target_keyword,
        "pillar_id": item.pillar_id,
        "scheduled_date": item.scheduled_date.isoformat() if item.scheduled_date else None,
        "status": item.status.value,
        "assignee_id": item.assignee_id,
        "notes": item.notes,
        "color": item.color,
        "created_at": item.created_at.isoformat(),
    }


@router.put("/items/{item_id}")
def update_calendar_item(
    item_id: str,
    data: CalendarItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing calendar item."""
    item = update_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Calendar item not found")
    return {
        "id": item.id,
        "project_id": item.project_id,
        "draft_id": item.draft_id,
        "title": item.title,
        "target_keyword": item.target_keyword,
        "pillar_id": item.pillar_id,
        "scheduled_date": item.scheduled_date.isoformat() if item.scheduled_date else None,
        "status": item.status.value,
        "assignee_id": item.assignee_id,
        "notes": item.notes,
        "color": item.color,
        "created_at": item.created_at.isoformat(),
    }


@router.delete("/items/{item_id}", status_code=204)
def delete_calendar_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a calendar item."""
    deleted = delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Calendar item not found")
    return None


@router.put("/items/{item_id}/reschedule")
def reschedule_calendar_item(
    item_id: str,
    data: RescheduleData,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update only the scheduled_date of a calendar item (drag-and-drop)."""
    item = reschedule(db, item_id, data.scheduled_date)
    if not item:
        raise HTTPException(status_code=404, detail="Calendar item not found")
    return {
        "id": item.id,
        "project_id": item.project_id,
        "draft_id": item.draft_id,
        "title": item.title,
        "target_keyword": item.target_keyword,
        "pillar_id": item.pillar_id,
        "scheduled_date": item.scheduled_date.isoformat() if item.scheduled_date else None,
        "status": item.status.value,
        "assignee_id": item.assignee_id,
        "notes": item.notes,
        "color": item.color,
        "created_at": item.created_at.isoformat(),
    }
