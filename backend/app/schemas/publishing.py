from pydantic import BaseModel


class ConnectionCreate(BaseModel):
    project_id: str
    platform: str  # "wordpress" or "strapi"
    site_url: str
    username: str | None = None
    password: str | None = None
    token: str | None = None


class ConnectionResponse(BaseModel):
    id: str
    project_id: str
    platform: str
    site_url: str
    is_active: bool
    last_synced_at: str | None = None
    created_at: str


class PublishRequest(BaseModel):
    draft_id: str
    connection_id: str


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


class PublishLogResponse(BaseModel):
    id: str
    draft_id: str
    connection_id: str
    platform: str
    external_id: str
    external_url: str
    status: str
    error_message: str
    published_at: str
