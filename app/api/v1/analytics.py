import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db
from app.models.competitor import Competitor
from app.models.post_metrics import PostMetrics
from app.models.sentiment_result import SentimentResult
from app.models.social_post import SocialPost
from app.schemas.social_post import PostMetricsSummary, SocialPostOut

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-posts")
async def top_posts(
    platform: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    metric: str = Query("rank_score", pattern="^(rank_score|views|engagement_rate)$"),
    db: AsyncSession = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)

    q = (
        select(SocialPost, PostMetrics)
        .join(PostMetrics, PostMetrics.social_post_id == SocialPost.id)
        .options(selectinload(SocialPost.competitor))
        .where(SocialPost.ingested_at >= cutoff)
    )
    if platform:
        q = q.where(SocialPost.platform == platform)

    sort_col = {
        "rank_score": PostMetrics.rank_score,
        "views": PostMetrics.views_count,
        "engagement_rate": PostMetrics.engagement_rate,
    }[metric]

    rows = (await db.execute(q.order_by(desc(sort_col)).limit(limit))).all()

    posts = []
    for i, (post, metrics) in enumerate(rows):
        posts.append({
            "rank": i + 1,
            "post_id": str(post.id),
            "competitor_name": post.competitor.name if post.competitor else None,
            "platform": post.platform,
            "url": post.url,
            "thumbnail_url": post.thumbnail_url,
            "caption_preview": (post.caption or "")[:200],
            "posted_at": post.posted_at.isoformat(),
            "views_count": metrics.views_count,
            "likes_count": metrics.likes_count,
            "comments_count": metrics.comments_count,
            "rank_score": float(metrics.rank_score or 0),
            "engagement_rate": float(metrics.engagement_rate or 0),
        })

    return {
        "window_start": cutoff.isoformat(),
        "window_end": datetime.now(timezone.utc).isoformat(),
        "metric": metric,
        "posts": posts,
    }


@router.get("/sentiment-overview")
async def sentiment_overview(
    competitor_id: uuid.UUID | None = Query(None),
    platform: str | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if from_date is None:
        from_date = datetime.now(timezone.utc) - timedelta(days=14)

    post_q = select(SocialPost.id).where(SocialPost.ingested_at >= from_date)
    if to_date:
        post_q = post_q.where(SocialPost.ingested_at <= to_date)
    if competitor_id:
        post_q = post_q.where(SocialPost.competitor_id == competitor_id)
    if platform:
        post_q = post_q.where(SocialPost.platform == platform)

    post_ids = (await db.execute(post_q)).scalars().all()
    total_posts = len(post_ids)

    if not post_ids:
        return {"period": {"from": from_date.isoformat(), "to": (to_date or datetime.now(timezone.utc)).isoformat()},
                "post_count": 0, "analyzed_post_count": 0, "sentiment_distribution": {}, "top_themes": [], "by_competitor": []}

    sentiments = (await db.execute(
        select(SentimentResult)
        .where(SentimentResult.social_post_id.in_(post_ids))
        .order_by(desc(SentimentResult.analyzed_at))
    )).scalars().all()

    seen_posts: set[uuid.UUID] = set()
    unique_sentiments = []
    for s in sentiments:
        if s.social_post_id not in seen_posts:
            unique_sentiments.append(s)
            seen_posts.add(s.social_post_id)

    dist: dict[str, int] = {}
    all_themes: list[str] = []
    for s in unique_sentiments:
        dist[s.overall_sentiment] = dist.get(s.overall_sentiment, 0) + 1
        all_themes.extend(s.key_themes or [])

    analyzed = len(unique_sentiments)
    dist_pct = {k: round(v / analyzed, 4) for k, v in dist.items()} if analyzed else {}

    theme_counts: dict[str, int] = {}
    for t in all_themes:
        theme_counts[t] = theme_counts.get(t, 0) + 1
    top_themes = sorted(theme_counts, key=lambda x: theme_counts[x], reverse=True)[:10]

    competitors = (await db.execute(
        select(Competitor).where(Competitor.is_active == True)  # noqa: E712
    )).scalars().all()

    by_competitor = []
    for comp in competitors:
        comp_sentiments = [s for s in unique_sentiments if True]
        by_competitor.append({
            "competitor_id": str(comp.id),
            "competitor_name": comp.name,
            "overall_sentiment": max(dist, key=lambda k: dist.get(k, 0)) if dist else "neutral",
            "post_count": sum(1 for pid in post_ids if True),
        })

    return {
        "period": {"from": from_date.isoformat(), "to": (to_date or datetime.now(timezone.utc)).isoformat()},
        "post_count": total_posts,
        "analyzed_post_count": analyzed,
        "sentiment_distribution": dist_pct,
        "top_themes": top_themes,
        "by_competitor": by_competitor,
    }
