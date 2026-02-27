import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class Platform(str, enum.Enum):
    WORDPRESS = "wordpress"
    STRAPI = "strapi"


class PublishStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class PublishingConnection(SQLModel, table=True):
    __tablename__ = "publishing_connection"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    platform: Platform
    site_url: str = ""
    credentials_encrypted: str = Field(default="", sa_column=Column(sa.Text))  # Fernet-encrypted JSON
    is_active: bool = True
    last_synced_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PublishLog(SQLModel, table=True):
    __tablename__ = "publish_log"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    draft_id: str = Field(foreign_key="content_draft.id", index=True)
    connection_id: str = Field(foreign_key="publishing_connection.id")
    platform: Platform
    external_id: str = ""
    external_url: str = ""
    status: PublishStatus = Field(default=PublishStatus.SUCCESS)
    error_message: str = ""
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
