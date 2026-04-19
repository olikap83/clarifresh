import uuid
from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db
from app.models.comment import Comment
from app.models.competitor import Competitor
from app.models.post_metrics import PostMetrics
from app.models.sentiment_result import SentimentResult
from app.models.social_post import SocialPost
from app.schemas.comment import CommentListOut, CommentOut
from app.schemas.social_post import PostMetricsSummary, SocialPostListOut, SocialPostOut

router = APIRouter(prefix="/posts", tags=["posts"])


def _build_post_out(post: SocialPost, competitor_name: str | None = None) -> SocialPostOut:
    latest_metrics = sorted(post.metrics, key=lambda m: m.snapshot_at, reverse=True)[0] if post.metrics else None
    latest_sentiment = sorted(post.sentiment_results, key=lambda s: s.analyzed_at, reverse=True)[0] if post.sentiment_results else None

    metrics_out = None
    if latest_metrics:
        metrics_out = PostMetricsSummary(
            views_count=latest_metrics.views_count,
            likes_count=latest_metrics.likes_count,
            comments_count=latest_metrics.comments_count,
            shares_count=latest_metrics.shares_count,
            saves_count=latest_metrics.saves_count,
            engagement_rate=latest_metrics.engagement_rate,
            rank_score=latest_metrics.rank_score,
        )

    return SocialPostOut(
        id=post.id,
        competitor_id=post.competitor_id,
        competitor_name=competitor_name or (post.competitor.name if post.competitor else None),
        platform=post.platform,
        platform_post_id=post.platform_post_id,
        post_type=post.post_type,
        caption=post.caption,
        hashtags=post.hashtags,
        url=post.url,
        thumbnail_url=post.thumbnail_url,
        posted_at=post.posted_at,
        ingested_at=post.ingested_at,
        metrics=metrics_out,
        has_sentiment=latest_sentiment is not None,
        has_summary=post.ai_summary is not None,
        ai_summary=post.ai_summary,
        summary_generated_at=post.summary_generated_at,
    )


@router.get("", response_model=SocialPostListOut)
async def list_posts(
    competitor_id: uuid.UUID | None = Query(None),
    platform: str | None = Query(None),
    sort_by: str = Query("rank_score", pattern="^(rank_score|views|likes|comments|posted_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    if from_date is None:
        from_date = datetime.now(timezone.utc) - timedelta(days=14)

    q = (
        select(SocialPost)
        .options(
            selectinload(SocialPost.metrics),
            selectinload(SocialPost.sentiment_results),
            selectinload(SocialPost.competitor),
        )
        .where(SocialPost.ingested_at >= from_date)
    )
    if to_date:
        q = q.where(SocialPost.ingested_at <= to_date)
    if competitor_id:
        q = q.where(SocialPost.competitor_id == competitor_id)
    if platform:
        q = q.where(SocialPost.platform == platform)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()

    sort_map = {
        "rank_score": PostMetrics.rank_score,
        "views": PostMetrics.views_count,
        "likes": PostMetrics.likes_count,
        "comments": PostMetrics.comments_count,
        "posted_at": SocialPost.posted_at,
    }
    sort_col = sort_map[sort_by]
    if sort_by != "posted_at":
        q = q.join(PostMetrics, PostMetrics.social_post_id == SocialPost.id, isouter=True)

    q = q.order_by(desc(sort_col) if order == "desc" else sort_col)
    q = q.offset((page - 1) * page_size).limit(page_size)

    posts = (await db.execute(q)).scalars().unique().all()
    items = [_build_post_out(p) for p in posts]

    return SocialPostListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{post_id}", response_model=SocialPostOut)
async def get_post(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(
        select(SocialPost)
        .options(
            selectinload(SocialPost.metrics),
            selectinload(SocialPost.sentiment_results),
            selectinload(SocialPost.competitor),
        )
        .where(SocialPost.id == post_id)
    )).scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return _build_post_out(post)


@router.get("/{post_id}/comments", response_model=CommentListOut)
async def list_comments(
    post_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    post_exists = (await db.execute(select(SocialPost.id).where(SocialPost.id == post_id))).scalar_one_or_none()
    if not post_exists:
        raise HTTPException(status_code=404, detail="Post not found")

    total = (await db.execute(select(func.count(Comment.id)).where(Comment.social_post_id == post_id))).scalar_one()
    comments = (await db.execute(
        select(Comment)
        .where(Comment.social_post_id == post_id)
        .order_by(desc(Comment.likes_count))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return CommentListOut(
        items=[CommentOut.model_validate(c) for c in comments],
        total=total,
        page=page,
        page_size=page_size,
    )
