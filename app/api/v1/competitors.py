import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.competitor import Competitor
from app.schemas.competitor import CompetitorCreate, CompetitorListOut, CompetitorOut, CompetitorUpdate

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("", response_model=CompetitorListOut)
async def list_competitors(
    platform: str | None = Query(None),
    is_active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    q = select(Competitor).where(Competitor.is_active == is_active)
    if platform:
        q = q.where(Competitor.platform == platform)

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar_one()
    rows = (await db.execute(q.order_by(Competitor.created_at.desc()))).scalars().all()

    return CompetitorListOut(items=rows, total=total)


@router.post("", response_model=CompetitorOut, status_code=201)
async def create_competitor(body: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(
        select(Competitor).where(Competitor.platform == body.platform, Competitor.handle == body.handle)
    )).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="Competitor with this platform and handle already exists")

    competitor = Competitor(**body.model_dump())
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.patch("/{competitor_id}", response_model=CompetitorOut)
async def update_competitor(
    competitor_id: uuid.UUID,
    body: CompetitorUpdate,
    db: AsyncSession = Depends(get_db),
):
    competitor = (await db.execute(select(Competitor).where(Competitor.id == competitor_id))).scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(competitor, field, value)

    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}", status_code=204)
async def delete_competitor(competitor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    competitor = (await db.execute(select(Competitor).where(Competitor.id == competitor_id))).scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    await db.delete(competitor)
    await db.commit()
