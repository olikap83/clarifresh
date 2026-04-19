import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, text

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.social_post import SocialPost

logger = logging.getLogger(__name__)


async def run_retention():
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(SocialPost).where(SocialPost.ingested_at < cutoff)
        )
        deleted = result.rowcount
        await db.commit()
        logger.info("Retention: deleted %d posts ingested before %s", deleted, cutoff.isoformat())
