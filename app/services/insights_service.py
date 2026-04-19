import json
import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations import claude_client
from app.models.competitor import Competitor
from app.models.insight import Insight
from app.models.post_metrics import PostMetrics
from app.models.sentiment_result import SentimentResult
from app.models.social_post import SocialPost

logger = logging.getLogger(__name__)


async def generate_weekly_insights(
    period_start: date,
    period_end: date,
    competitor_id: uuid.UUID | None,
    platform: str | None,
    insight_type: str,
    db: AsyncSession,
) -> Insight | None:
    start_dt = datetime(period_start.year, period_start.month, period_start.day, tzinfo=timezone.utc)
    end_dt = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, tzinfo=timezone.utc)

    q = (
        select(SocialPost)
        .options(selectinload(SocialPost.metrics), selectinload(SocialPost.sentiment_results), selectinload(SocialPost.competitor))
        .where(SocialPost.posted_at >= start_dt, SocialPost.posted_at <= end_dt)
    )
    if competitor_id:
        q = q.where(SocialPost.competitor_id == competitor_id)
    if platform:
        q = q.where(SocialPost.platform == platform)

    posts = (await db.execute(q)).scalars().unique().all()

    if not posts:
        logger.warning("No posts found for insight generation period %s to %s", period_start, period_end)
        return None

    def latest_metrics(post: SocialPost) -> PostMetrics | None:
        return sorted(post.metrics, key=lambda m: m.snapshot_at, reverse=True)[0] if post.metrics else None

    def latest_sentiment(post: SocialPost) -> SentimentResult | None:
        return sorted(post.sentiment_results, key=lambda s: s.analyzed_at, reverse=True)[0] if post.sentiment_results else None

    scored = [(p, float(lm.rank_score or 0)) for p in posts if (lm := latest_metrics(p)) is not None]
    scored.sort(key=lambda x: x[1], reverse=True)

    n = len(scored)
    top_quartile = scored[:max(1, n // 4)]
    flop_quartile = scored[max(1, n * 3 // 4):]

    post_summaries = []
    for post, score in scored[:50]:
        sm = latest_sentiment(post)
        lm = latest_metrics(post)
        post_summaries.append({
            "id": str(post.id),
            "competitor": post.competitor.name if post.competitor else "unknown",
            "platform": post.platform,
            "posted_at": post.posted_at.isoformat(),
            "caption_preview": (post.caption or "")[:200],
            "hashtags": post.hashtags or [],
            "ai_summary": post.ai_summary or "",
            "rank_score": score,
            "views": int(lm.views_count) if lm else 0,
            "likes": int(lm.likes_count) if lm else 0,
            "overall_sentiment": sm.overall_sentiment if sm else None,
            "key_themes": sm.key_themes if sm else [],
        })

    posts_data = json.dumps(post_summaries, indent=2)

    try:
        result_data, prompt_tokens, completion_tokens = claude_client.generate_insights(posts_data)
    except Exception:
        logger.exception("Claude insights call failed")
        return None

    insight = Insight(
        period_start=period_start,
        period_end=period_end,
        platform=platform,
        competitor_id=competitor_id,
        insight_type=insight_type,
        title=result_data.get("title", "Weekly Insight Report"),
        body=result_data.get("body", ""),
        top_post_ids=[uuid.UUID(i) for i in result_data.get("top_post_ids", []) if i],
        flop_post_ids=[uuid.UUID(i) for i in result_data.get("flop_post_ids", []) if i],
        recommendations=result_data.get("recommendations", []),
        model_used=settings.claude_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight
