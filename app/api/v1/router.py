from fastapi import APIRouter

from app.api.v1 import analytics, competitors, health, ingestion, insights, posts, sentiment

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(competitors.router)
router.include_router(posts.router)
router.include_router(sentiment.router)
router.include_router(ingestion.router)
router.include_router(insights.router)
router.include_router(analytics.router)
