from pydantic import BaseModel


class PastArticleImport(BaseModel):
    project_id: str
    url: str
