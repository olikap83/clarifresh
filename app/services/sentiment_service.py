import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations import claude_client
from app.models.comment import Comment
from app.models.sentiment_result import SentimentResult
from app.models.social_post import SocialPost

logger = logging.getLogger(__name__)

MIN_COMMENTS = 3


async def analyze_post_sentiment(post_id: uuid.UUID, db: AsyncSession) -> SentimentResult | None:
    post = (await db.execute(select(SocialPost).where(SocialPost.id == post_id))).scalar_one_or_none()
    if not post:
        return None

    cache_cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.sentiment_cache_hours)
    cached = (await db.execute(
        select(SentimentResult)
        .where(SentimentResult.social_post_id == post_id, SentimentResult.analyzed_at >= cache_cutoff)
        .order_by(desc(SentimentResult.analyzed_at))
        .limit(1)
    )).scalar_one_or_none()

    if cached:
        return cached

    comments = (await db.execute(
        select(Comment)
        .where(Comment.social_post_id == post_id)
        .order_by(desc(Comment.likes_count))
        .limit(200)
    )).scalars().all()

    if len(comments) < MIN_COMMENTS:
        logger.info("Post %s has only %d comments, skipping sentiment", post_id, len(comments))
        return None

    texts = [c.text for c in comments]
    try:
        result_data, prompt_tokens, completion_tokens = claude_client.analyze_sentiment(texts)
    except Exception:
        logger.exception("Claude sentiment call failed for post %s", post_id)
        return None

    sentiment = SentimentResult(
        social_post_id=post_id,
        overall_sentiment=result_data["overall_sentiment"],
        positive_score=result_data["positive_score"],
        negative_score=result_data["negative_score"],
        neutral_score=result_data["neutral_score"],
        comment_count_analyzed=len(comments),
        key_themes=result_data.get("key_themes"),
        sentiment_summary=result_data.get("sentiment_summary"),
        raw_claude_response=result_data,
        model_used=settings.claude_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    db.add(sentiment)
    await db.commit()
    await db.refresh(sentiment)
    return sentiment
