import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa


class BrandPersona(SQLModel, table=True):
    __tablename__ = "brand_persona"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", unique=True, index=True)

    brand_name: str = ""
    tagline: str = ""
    voice_tone: str = ""  # e.g. "Professional but approachable"
    writing_style: str = ""  # e.g. "Short sentences. Active voice."
    target_audience: str = ""  # e.g. "CTOs at mid-size companies"
    brand_values: str = Field(default="", sa_column=Column(sa.Text))  # JSON array as string
    dos: str = Field(default="", sa_column=Column(sa.Text))  # What to always do
    donts: str = Field(default="", sa_column=Column(sa.Text))  # What to never do
    sample_content: str = Field(default="", sa_column=Column(sa.Text))  # Example brand content
    industry_keywords: str = Field(default="", sa_column=Column(sa.Text))  # JSON array as string

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_prompt_context(self) -> str:
        """Convert persona to a string for LLM system prompt injection."""
        parts = []
        if self.brand_name:
            parts.append(f"Brand: {self.brand_name}")
        if self.tagline:
            parts.append(f"Tagline: {self.tagline}")
        if self.voice_tone:
            parts.append(f"Voice & Tone: {self.voice_tone}")
        if self.writing_style:
            parts.append(f"Writing Style: {self.writing_style}")
        if self.target_audience:
            parts.append(f"Target Audience: {self.target_audience}")
        if self.brand_values:
            parts.append(f"Brand Values: {self.brand_values}")
        if self.dos:
            parts.append(f"Always Do: {self.dos}")
        if self.donts:
            parts.append(f"Never Do: {self.donts}")
        if self.industry_keywords:
            parts.append(f"Industry Keywords: {self.industry_keywords}")
        if self.sample_content:
            parts.append(f"Sample Content for Style Reference:\n{self.sample_content}")

        if not parts:
            return ""
        return "## Brand Persona\n" + "\n".join(parts)
