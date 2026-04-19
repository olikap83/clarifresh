import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations import claude_client
from app.models.social_post import SocialPost

logger = logging.getLogger(__name__)


async def generate_post_summary(post_id: uuid.UUID, db: AsyncSession) -> str | None:
    post = (await db.execute(select(SocialPost).where(SocialPost.id == post_id))).scalar_one_or_none()
    if not post:
        return None

    if post.ai_summary:
        return post.ai_summary

    try:
        summary, _, _ = claude_client.generate_summary(
            platform=post.platform,
            post_type=post.post_type,
            caption=post.caption or "",
            hashtags=post.hashtags or [],
        )
    except Exception:
        logger.exception("Claude summary call failed for post %s", post_id)
        return None

    post.ai_summary = summary
    post.summary_generated_at = datetime.now(timezone.utc)
    await db.commit()
    return summary
