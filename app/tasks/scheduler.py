import asyncio
import logging
import uuid
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import AsyncSessionLocal
from app.models.ingestion_job import IngestionJob
from app.services import ingestion_service
from app.services.insights_service import generate_weekly_insights
from app.tasks.retention import run_retention

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def _scheduled_ingestion():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        running = (await db.execute(
            select(func.count(IngestionJob.id)).where(IngestionJob.status.in_(["pending", "running"]))
        )).scalar_one()

        if running > 0:
            logger.info("Skipping scheduled ingestion — job already active")
            return

        job = IngestionJob(
            id=uuid.uuid4(),
            trigger_type="scheduled",
            triggered_by="scheduler",
            status="pending",
        )
        db.add(job)
        await db.commit()

    asyncio.create_task(ingestion_service.run_ingestion_job(job.id, None, None, 50))
    logger.info("Scheduled ingestion started: job %s", job.id)


async def _scheduled_insights():
    today = date.today()
    period_end = today - timedelta(days=today.weekday() + 1)
    period_start = period_end - timedelta(days=6)

    async with AsyncSessionLocal() as db:
        await generate_weekly_insights(period_start, period_end, None, None, "weekly_summary", db)

    logger.info("Scheduled weekly insights generated for %s to %s", period_start, period_end)


def start_scheduler():
    scheduler.add_job(_scheduled_ingestion, "cron", hour=6, minute=0, id="daily_ingestion")
    scheduler.add_job(_scheduled_insights, "cron", day_of_week="sun", hour=2, minute=0, id="weekly_insights")
    scheduler.add_job(run_retention, "cron", hour=3, minute=0, id="daily_retention")
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped")
