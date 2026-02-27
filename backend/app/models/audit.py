import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class AuditStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    PASS = "pass"


class SiteAudit(SQLModel, table=True):
    __tablename__ = "site_audit"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    initiated_by: str = ""  # user ID or "mcp"
    url: str
    status: AuditStatus = Field(default=AuditStatus.PENDING)
    health_score: int | None = None
    results_json: str = Field(default="{}", sa_column=Column(sa.Text))
    pages_crawled: int = 0
    issues_found: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class AuditIssue(SQLModel, table=True):
    __tablename__ = "audit_issue"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    audit_id: str = Field(foreign_key="site_audit.id", index=True)
    category: str  # technical, content, schema, performance, images, geo
    severity: IssueSeverity
    title: str
    description: str = Field(default="", sa_column=Column(sa.Text))
    recommendation: str = Field(default="", sa_column=Column(sa.Text))
    page_url: str | None = None
