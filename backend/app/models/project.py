import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class BusinessType(str, enum.Enum):
    SAAS = "saas"
    LOCAL = "local"
    ECOMMERCE = "ecommerce"
    PUBLISHER = "publisher"
    AGENCY = "agency"
    OTHER = "other"


class ProjectMemberRole(str, enum.Enum):
    ADMIN = "admin"
    STRATEGIST = "strategist"
    WRITER = "writer"
    CLIENT = "client"


class Project(SQLModel, table=True):
    __tablename__ = "project"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    domain: str
    description: str | None = None
    business_type: BusinessType = Field(default=BusinessType.OTHER)
    owner_id: str = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_member"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    role: ProjectMemberRole = Field(default=ProjectMemberRole.WRITER)
