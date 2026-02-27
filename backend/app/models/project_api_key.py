import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class ProjectApiKey(SQLModel, table=True):
    __tablename__ = "project_api_key"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    provider: str  # anthropic, openai, google_ai, serper, textrazor, google_nlp, google_search_console, pagespeed
    encrypted_key: str  # Fernet-encrypted API key
    label: str = ""  # Optional display label
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
