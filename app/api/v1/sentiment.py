import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.sentiment_result import SentimentResult
from app.models.social_post import SocialPost
from app.schemas.sentiment import SentimentResultOut, SentimentTriggerOut
from app.services import sentiment_service, summary_service

router = APIRouter(prefix="/posts", tags=["sentiment"])


@router.get("/{post_id}/sentiment", response_model=SentimentResultOut)
async def get_sentiment(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = (await db.execute(
        select(SentimentResult)
        .where(SentimentResult.social_post_id == post_id)
        .order_by(desc(SentimentResult.analyzed_at))
        .limit(1)
    )).scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail="No sentiment analysis found for this post")

    return result


@router.post("/{post_id}/sentiment/analyze", response_model=SentimentTriggerOut, status_code=202)
async def trigger_sentiment(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(select(SocialPost.id).where(SocialPost.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    asyncio.create_task(sentiment_service.analyze_post_sentiment(post_id, db))

    return SentimentTriggerOut(status="queued", message="Sentiment analysis queued")


@router.post("/{post_id}/summary/generate", status_code=202)
async def trigger_summary(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(select(SocialPost.id).where(SocialPost.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    asyncio.create_task(summary_service.generate_post_summary(post_id, db))

    return {"status": "queued", "message": "Summary generation queued", "ai_summary": None}
