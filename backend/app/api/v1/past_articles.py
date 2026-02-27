from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ...models.user import User
from ...schemas.past_article import PastArticleImport
from ...services.past_article_service import (
    import_article, list_articles, get_article, delete_article, check_refresh,
)
from ...api.deps import get_db, get_current_user

router = APIRouter(prefix="/past-articles", tags=["past-articles"])


@router.get("")
def get_past_articles(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_articles(db, project_id)


@router.post("/import", status_code=201)
async def import_article_route(data: PastArticleImport, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = await import_article(db, data.project_id, data.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import article: {str(e)}")


@router.get("/{article_id}")
def get_article_route(article_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = get_article(db, article_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return result


@router.delete("/{article_id}", status_code=204)
def delete_article_route(article_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not delete_article(db, article_id):
        raise HTTPException(status_code=404, detail="Article not found")


@router.post("/{article_id}/refresh-check")
def refresh_check_route(article_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = check_refresh(db, article_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return result
