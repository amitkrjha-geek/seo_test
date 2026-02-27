from fastapi import APIRouter
from .auth import router as auth_router
from .projects import router as projects_router
from .users import router as users_router
from .audits import router as audits_router
from .keywords import router as keywords_router
from .competitors import router as competitors_router
from .briefs import router as briefs_router
from .content import router as content_router
from .optimization import router as optimization_router
from .tracking import router as tracking_router
from .llm import router as llm_router
from .dashboard import router as dashboard_router
from .calendar import router as calendar_router
from .strategy import router as strategy_router
from .past_articles import router as past_articles_router
from .publishing import router as publishing_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(users_router)
api_router.include_router(audits_router)
api_router.include_router(keywords_router)
api_router.include_router(competitors_router)
api_router.include_router(briefs_router)
api_router.include_router(content_router)
api_router.include_router(optimization_router)
api_router.include_router(tracking_router)
api_router.include_router(llm_router)
api_router.include_router(dashboard_router)
api_router.include_router(calendar_router)
api_router.include_router(strategy_router)
api_router.include_router(past_articles_router)
api_router.include_router(publishing_router)
