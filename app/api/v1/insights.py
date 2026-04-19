import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.insight import Insight
from app.schemas.insight import InsightGenerateRequest, InsightListOut, InsightOut
from app.services import insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=InsightListOut)
async def list_insights(
    competitor_id: uuid.UUID | None = Query(None),
    insight_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    q = select(Insight)
    if competitor_id:
        q = q.where(Insight.competitor_id == competitor_id)
    if insight_type:
        q = q.where(Insight.insight_type == insight_type)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.order_by(Insight.generated_at.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return InsightListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{insight_id}", response_model=InsightOut)
async def get_insight(insight_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    insight = (await db.execute(select(Insight).where(Insight.id == insight_id))).scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight


@router.post("/generate", status_code=202)
async def generate_insight(body: InsightGenerateRequest, db: AsyncSession = Depends(get_db)):
    asyncio.create_task(
        insights_service.generate_weekly_insights(
            body.period_start,
            body.period_end,
            body.competitor_id,
            body.platform,
            body.insight_type,
            db,
        )
    )
    return {"status": "queued", "message": "Insight generation started", "estimated_seconds": 30}
