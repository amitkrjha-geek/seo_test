import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STRATEGIST = "strategist"
    WRITER = "writer"
    CLIENT = "client"


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    role: UserRole = Field(default=UserRole.WRITER)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
