import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.competitor import Competitor
from app.models.ingestion_job import IngestionJob
from app.schemas.ingestion import IngestionJobListOut, IngestionJobOut, IngestionTriggerOut, IngestionTriggerRequest
from app.services import ingestion_service

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/trigger", response_model=IngestionTriggerOut, status_code=202)
async def trigger_ingestion(body: IngestionTriggerRequest, db: AsyncSession = Depends(get_db)):
    comp_q = select(func.count(Competitor.id)).where(Competitor.is_active == True)  # noqa: E712
    if body.competitor_id:
        comp_q = comp_q.where(Competitor.id == body.competitor_id)
    if body.platform:
        comp_q = comp_q.where(Competitor.platform == body.platform)
    targeted = (await db.execute(comp_q)).scalar_one()

    if targeted == 0:
        raise HTTPException(status_code=404, detail="No active competitors found matching the filter")

    job = IngestionJob(
        id=uuid.uuid4(),
        trigger_type="manual",
        triggered_by="api",
        platform=body.platform,
        competitor_id=body.competitor_id,
        status="pending",
    )
    db.add(job)
    await db.commit()

    asyncio.create_task(
        ingestion_service.run_ingestion_job(job.id, body.competitor_id, body.platform, body.max_posts_per_competitor)
    )

    return IngestionTriggerOut(
        job_id=job.id,
        status="pending",
        message="Ingestion job queued",
        competitors_targeted=targeted,
    )


@router.get("/jobs", response_model=IngestionJobListOut)
async def list_jobs(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(IngestionJob)
    if status:
        q = q.where(IngestionJob.status == status)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    jobs = (await db.execute(q.order_by(IngestionJob.started_at.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return IngestionJobListOut(items=jobs, total=total)


@router.get("/jobs/{job_id}", response_model=IngestionJobOut)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = (await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return job
