import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.apify_client import ApifyClient
from app.models.comment import Comment
from app.models.competitor import Competitor
from app.models.ingestion_job import IngestionJob
from app.models.post_metrics import PostMetrics
from app.models.social_post import SocialPost
from app.services.ranking_service import RankingService

logger = logging.getLogger(__name__)
apify = ApifyClient()
ranking = RankingService()


def _normalize_tiktok(raw: dict, competitor_id: uuid.UUID) -> tuple[dict, dict, list[dict]]:
    post_id = str(raw.get("id", raw.get("videoId", "")))
    posted_at = datetime.fromtimestamp(raw.get("createTime", 0), tz=timezone.utc)

    post = {
        "competitor_id": competitor_id,
        "platform": "tiktok",
        "platform_post_id": post_id,
        "post_type": "video",
        "caption": raw.get("text", ""),
        "hashtags": [h.get("name", "") for h in raw.get("hashtags", [])],
        "url": raw.get("webVideoUrl", raw.get("url", "")),
        "thumbnail_url": raw.get("covers", {}).get("default", None),
        "posted_at": posted_at,
        "raw_payload": raw,
    }

    stats = raw.get("stats", raw.get("statsV2", {}))
    metrics = {
        "views_count": int(stats.get("playCount", stats.get("viewCount", 0))),
        "likes_count": int(stats.get("diggCount", stats.get("heartCount", 0))),
        "comments_count": int(stats.get("commentCount", 0)),
        "shares_count": int(stats.get("shareCount", 0)),
    }

    comments = []
    for c in raw.get("comments", []):
        comments.append({
            "platform_comment_id": str(c.get("id", "")),
            "author_handle": c.get("author", {}).get("uniqueId", None),
            "text": c.get("text", ""),
            "likes_count": int(c.get("diggCount", 0)),
            "posted_at": datetime.fromtimestamp(c.get("createTime", 0), tz=timezone.utc) if c.get("createTime") else None,
        })

    return post, metrics, comments


def _normalize_instagram(raw: dict, competitor_id: uuid.UUID) -> tuple[dict, dict, list[dict]]:
    post_id = str(raw.get("id", raw.get("shortCode", "")))
    posted_at_ts = raw.get("timestamp", raw.get("takenAtTimestamp", None))
    posted_at = datetime.fromisoformat(posted_at_ts) if posted_at_ts and isinstance(posted_at_ts, str) else \
        datetime.fromtimestamp(posted_at_ts, tz=timezone.utc) if posted_at_ts else datetime.now(timezone.utc)

    media_type = raw.get("type", raw.get("productType", "image"))
    type_map = {"GraphSidecar": "carousel", "GraphVideo": "reel", "GraphImage": "image"}
    post_type = type_map.get(media_type, "image")

    post = {
        "competitor_id": competitor_id,
        "platform": "instagram",
        "platform_post_id": post_id,
        "post_type": post_type,
        "caption": raw.get("caption", raw.get("alt", "")),
        "hashtags": raw.get("hashtags", []),
        "url": raw.get("url", raw.get("displayUrl", "")),
        "thumbnail_url": raw.get("displayUrl", raw.get("thumbnailUrl", None)),
        "posted_at": posted_at,
        "raw_payload": raw,
    }

    metrics = {
        "views_count": int(raw.get("videoViewCount", raw.get("videoPlayCount", 0))),
        "likes_count": int(raw.get("likesCount", 0)),
        "comments_count": int(raw.get("commentsCount", 0)),
        "saves_count": int(raw.get("savesCount", 0)) if raw.get("savesCount") else None,
    }

    comments = []
    for c in raw.get("latestComments", raw.get("comments", [])):
        comments.append({
            "platform_comment_id": str(c.get("id", "")),
            "author_handle": c.get("ownerUsername", c.get("owner", {}).get("username", None)),
            "text": c.get("text", ""),
            "likes_count": int(c.get("likesCount", 0)),
            "posted_at": datetime.fromisoformat(c["timestamp"]) if c.get("timestamp") else None,
        })

    return post, metrics, comments


async def _upsert_post(db: AsyncSession, post_data: dict, metrics_data: dict, comments_data: list[dict]) -> uuid.UUID:
    stmt = insert(SocialPost).values(id=uuid.uuid4(), **post_data)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_social_posts_platform_post_id",
        set_={k: stmt.excluded[k] for k in ["caption", "hashtags", "url", "thumbnail_url", "raw_payload"]},
    ).returning(SocialPost.id)

    result = await db.execute(stmt)
    post_id = result.scalar_one()

    views = metrics_data.get("views_count", 0)
    likes = metrics_data.get("likes_count", 0)
    comments_count = metrics_data.get("comments_count", 0)
    shares = metrics_data.get("shares_count")
    saves = metrics_data.get("saves_count")

    rank_score = ranking.compute_rank_score(views, likes, comments_count)
    engagement_rate = ranking.compute_engagement_rate(views, likes, comments_count, shares or 0)

    metrics_obj = PostMetrics(
        social_post_id=post_id,
        views_count=views,
        likes_count=likes,
        comments_count=comments_count,
        shares_count=shares,
        saves_count=saves,
        engagement_rate=engagement_rate,
        rank_score=rank_score,
    )
    db.add(metrics_obj)

    for c in comments_data:
        if not c.get("platform_comment_id"):
            continue
        comment_stmt = insert(Comment).values(id=uuid.uuid4(), social_post_id=post_id, **c)
        comment_stmt = comment_stmt.on_conflict_do_nothing(constraint="uq_comments_post_comment")
        await db.execute(comment_stmt)

    return post_id


async def run_ingestion_job(job_id: uuid.UUID, competitor_id: uuid.UUID | None, platform: str | None, max_posts: int):
    async with AsyncSessionLocal() as db:
        job = (await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))).scalar_one()
        job.status = "running"
        await db.commit()

        try:
            comp_q = select(Competitor).where(Competitor.is_active == True)  # noqa: E712
            if competitor_id:
                comp_q = comp_q.where(Competitor.id == competitor_id)
            if platform:
                comp_q = comp_q.where(Competitor.platform == platform)

            competitors = (await db.execute(comp_q)).scalars().all()
            platforms_to_run = {c.platform for c in competitors}

            total_posts = 0
            total_comments = 0

            for plat in platforms_to_run:
                plat_competitors = [c for c in competitors if c.platform == plat]
                handles = [c.handle for c in plat_competitors]
                hashtags = list({h for c in plat_competitors for h in (c.hashtags or [])})

                apify_run_id = await apify.trigger_run(plat, handles, hashtags, max_posts)
                job.apify_run_id = apify_run_id
                await db.commit()

                success = await apify.poll_until_done(apify_run_id)
                if not success:
                    raise RuntimeError(f"Apify run {apify_run_id} failed for platform {plat}")

                items = await apify.fetch_items(apify_run_id)
                normalizer = _normalize_tiktok if plat == "tiktok" else _normalize_instagram

                comp_map = {c.handle.lower(): c.id for c in plat_competitors}

                for raw in items:
                    author = (raw.get("authorMeta", {}).get("name") or raw.get("ownerUsername") or "").lower()
                    comp_id = comp_map.get(author)
                    if not comp_id and plat_competitors:
                        comp_id = plat_competitors[0].id

                    post_data, metrics_data, comments_data = normalizer(raw, comp_id)
                    await _upsert_post(db, post_data, metrics_data, comments_data)
                    total_posts += 1
                    total_comments += len(comments_data)

                await db.commit()

            job.status = "completed"
            job.posts_ingested = total_posts
            job.comments_ingested = total_comments
            job.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.exception("Ingestion job %s failed", job_id)
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)

        await db.commit()
