"""
Publishing service for managing CMS connections and publishing drafts.
"""

import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from ..models.publishing import PublishingConnection, PublishLog, Platform, PublishStatus
from ..models.content import ContentDraft
from ..services.crypto_service import encrypt_api_key, decrypt_api_key
from ..integrations import wordpress as wp
from ..integrations import strapi as strapi_client
from ..schemas.publishing import ConnectionCreate


def create_connection(db: Session, data: ConnectionCreate) -> PublishingConnection:
    """
    Create a new publishing connection with encrypted credentials.

    For WordPress: credentials = { "username": ..., "password": ... }
    For Strapi: credentials = { "token": ... }
    """
    # Build credentials dict based on platform
    if data.platform == Platform.WORDPRESS.value:
        creds = {
            "username": data.username or "",
            "password": data.password or "",
        }
    elif data.platform == Platform.STRAPI.value:
        creds = {
            "token": data.token or "",
        }
    else:
        raise ValueError(f"Unsupported platform: {data.platform}")

    encrypted = encrypt_api_key(json.dumps(creds))

    connection = PublishingConnection(
        project_id=data.project_id,
        platform=Platform(data.platform),
        site_url=data.site_url.rstrip("/"),
        credentials_encrypted=encrypted,
        is_active=True,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


def _decrypt_credentials(connection: PublishingConnection) -> dict:
    """Decrypt and parse credentials JSON from a connection."""
    raw = decrypt_api_key(connection.credentials_encrypted)
    return json.loads(raw)


async def test_connection(db: Session, connection_id: str) -> dict:
    """
    Test an existing publishing connection.

    Returns:
        dict with success (bool) and message (str).
    """
    connection = db.get(PublishingConnection, connection_id)
    if not connection:
        return {"success": False, "message": "Connection not found"}

    creds = _decrypt_credentials(connection)

    if connection.platform == Platform.WORDPRESS:
        result = await wp.test_connection(
            site_url=connection.site_url,
            username=creds.get("username", ""),
            app_password=creds.get("password", ""),
        )
    elif connection.platform == Platform.STRAPI:
        result = await strapi_client.test_connection(
            site_url=connection.site_url,
            bearer_token=creds.get("token", ""),
        )
    else:
        return {"success": False, "message": f"Unsupported platform: {connection.platform}"}

    # Update connection active status based on test result
    if result.get("success"):
        connection.is_active = True
        connection.last_synced_at = datetime.now(timezone.utc)
    else:
        connection.is_active = False

    db.add(connection)
    db.commit()

    return result


async def publish_draft(db: Session, draft_id: str, connection_id: str) -> PublishLog:
    """
    Publish a content draft to the specified CMS connection.

    Returns:
        PublishLog entry with the result.
    """
    draft = db.get(ContentDraft, draft_id)
    if not draft:
        raise ValueError("Draft not found")

    connection = db.get(PublishingConnection, connection_id)
    if not connection:
        raise ValueError("Connection not found")

    creds = _decrypt_credentials(connection)

    # Publish based on platform
    if connection.platform == Platform.WORDPRESS:
        result = await wp.publish_post(
            site_url=connection.site_url,
            username=creds.get("username", ""),
            app_password=creds.get("password", ""),
            title=draft.title,
            content_html=draft.content_html or draft.body,
        )
    elif connection.platform == Platform.STRAPI:
        # Default Strapi content type is "articles"
        result = await strapi_client.publish_entry(
            site_url=connection.site_url,
            bearer_token=creds.get("token", ""),
            content_type="articles",
            data={
                "title": draft.title,
                "content": draft.content_html or draft.body,
                "meta_title": draft.meta_title,
                "meta_description": draft.meta_description,
            },
        )
    else:
        result = {"error": f"Unsupported platform: {connection.platform}"}

    # Create publish log entry
    if "error" in result:
        log = PublishLog(
            draft_id=draft_id,
            connection_id=connection_id,
            platform=connection.platform,
            status=PublishStatus.FAILED,
            error_message=result["error"],
        )
    else:
        log = PublishLog(
            draft_id=draft_id,
            connection_id=connection_id,
            platform=connection.platform,
            external_id=result.get("external_id", ""),
            external_url=result.get("external_url", ""),
            status=PublishStatus.SUCCESS,
        )
        # Update connection last_synced_at
        connection.last_synced_at = datetime.now(timezone.utc)
        db.add(connection)

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_publish_history(db: Session, draft_id: str) -> list[PublishLog]:
    """List all publish logs for a given draft, newest first."""
    return list(
        db.exec(
            select(PublishLog)
            .where(PublishLog.draft_id == draft_id)
            .order_by(PublishLog.published_at.desc())
        ).all()
    )


def get_connections(db: Session, project_id: str) -> list[PublishingConnection]:
    """List all publishing connections for a project."""
    return list(
        db.exec(
            select(PublishingConnection)
            .where(PublishingConnection.project_id == project_id)
            .order_by(PublishingConnection.created_at.desc())
        ).all()
    )


def delete_connection(db: Session, connection_id: str) -> bool:
    """Delete a publishing connection. Returns True if deleted."""
    connection = db.get(PublishingConnection, connection_id)
    if not connection:
        return False
    db.delete(connection)
    db.commit()
    return True
