from datetime import datetime
from pydantic import BaseModel
from ..models.project import BusinessType, ProjectMemberRole


class ProjectCreate(BaseModel):
    name: str
    domain: str
    description: str | None = None
    business_type: BusinessType = BusinessType.OTHER


class ProjectUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    description: str | None = None
    business_type: BusinessType | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    domain: str
    description: str | None
    business_type: BusinessType
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberAdd(BaseModel):
    user_id: str | None = None
    email: str | None = None
    role: ProjectMemberRole = ProjectMemberRole.WRITER


class ProjectMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: ProjectMemberRole
    user_email: str | None = None
    user_name: str | None = None

    model_config = {"from_attributes": True}


class BrandPersonaUpdate(BaseModel):
    brand_name: str | None = None
    tagline: str | None = None
    voice_tone: str | None = None
    writing_style: str | None = None
    target_audience: str | None = None
    brand_values: str | None = None
    dos: str | None = None
    donts: str | None = None
    sample_content: str | None = None
    industry_keywords: str | None = None


class BrandPersonaResponse(BaseModel):
    id: str
    project_id: str
    brand_name: str
    tagline: str
    voice_tone: str
    writing_style: str
    target_audience: str
    brand_values: str
    dos: str
    donts: str
    sample_content: str
    industry_keywords: str

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    provider: str
    api_key: str
    label: str = ""


class ApiKeyResponse(BaseModel):
    id: str
    provider: str
    label: str
    masked_key: str
    created_at: datetime

    model_config = {"from_attributes": True}
