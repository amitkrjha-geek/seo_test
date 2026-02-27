from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ...models.user import User
from ...schemas.publishing import ConnectionCreate, PublishRequest
from ...services import publishing_service
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.get("/connections")
def list_connections(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all publishing connections for a project (credentials masked)."""
    connections = publishing_service.get_connections(db, project_id)
    return [
        {
            "id": c.id,
            "project_id": c.project_id,
            "platform": c.platform.value,
            "site_url": c.site_url,
            "is_active": c.is_active,
            "last_synced_at": c.last_synced_at.isoformat() if c.last_synced_at else None,
            "created_at": c.created_at.isoformat(),
        }
        for c in connections
    ]


@router.post("/connections", status_code=201)
def create_connection(
    data: ConnectionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new publishing connection."""
    try:
        connection = publishing_service.create_connection(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": connection.id,
        "project_id": connection.project_id,
        "platform": connection.platform.value,
        "site_url": connection.site_url,
        "is_active": connection.is_active,
        "last_synced_at": None,
        "created_at": connection.created_at.isoformat(),
    }


@router.delete("/connections/{connection_id}", status_code=204)
def delete_connection(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a publishing connection."""
    deleted = publishing_service.delete_connection(db, connection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Connection not found")
    return None


@router.post("/connections/{connection_id}/test")
async def test_connection(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test an existing publishing connection."""
    result = await publishing_service.test_connection(db, connection_id)
    return {"success": result.get("success", False), "message": result.get("message", "")}


@router.post("/publish")
async def publish_draft(
    data: PublishRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a content draft to a CMS connection."""
    try:
        log = await publishing_service.publish_draft(db, data.draft_id, data.connection_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": log.id,
        "draft_id": log.draft_id,
        "connection_id": log.connection_id,
        "platform": log.platform.value,
        "external_id": log.external_id,
        "external_url": log.external_url,
        "status": log.status.value,
        "error_message": log.error_message,
        "published_at": log.published_at.isoformat(),
    }


@router.get("/history/{draft_id}")
def get_publish_history(
    draft_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the publish history for a draft."""
    logs = publishing_service.get_publish_history(db, draft_id)
    return [
        {
            "id": log.id,
            "draft_id": log.draft_id,
            "connection_id": log.connection_id,
            "platform": log.platform.value,
            "external_id": log.external_id,
            "external_url": log.external_url,
            "status": log.status.value,
            "error_message": log.error_message,
            "published_at": log.published_at.isoformat(),
        }
        for log in logs
    ]
