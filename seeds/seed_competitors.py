"""
Seed script — populates the competitors table with known ag-tech rivals.
Run after alembic upgrade head:

    python seeds/seed_competitors.py

Handles below are best-guess based on public profiles.
Verify each one exists before triggering a live ingestion run.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

COMPETITORS = [
    # ── Your original list ─────────────────────────────────────────────────
    {
        "name": "Agrinorm",
        "platform": "instagram",
        "handle": "agrinorm",
        "hashtags": ["#agrinorm", "#agtech", "#producequality"],
    },
    {
        "name": "Agrinorm",
        "platform": "tiktok",
        "handle": "agrinorm",
        "hashtags": ["#agrinorm", "#agtech"],
    },
    {
        "name": "AgShift",
        "platform": "instagram",
        "handle": "agshift",
        "hashtags": ["#agshift", "#foodtech", "#aiinspection"],
    },
    {
        "name": "AgShift",
        "platform": "tiktok",
        "handle": "agshift",
        "hashtags": ["#agshift", "#foodtech"],
    },
    {
        "name": "Neolithics",
        "platform": "instagram",
        "handle": "neolithics",
        "hashtags": ["#neolithics", "#producesorting", "#agtech"],
    },
    {
        "name": "Neolithics",
        "platform": "tiktok",
        "handle": "neolithics",
        "hashtags": ["#neolithics", "#agtech"],
    },
    {
        "name": "QC One",
        "platform": "instagram",
        "handle": "qcone.ai",
        "hashtags": ["#qcone", "#qualitycontrol", "#foodtech"],
    },
    {
        "name": "QC One",
        "platform": "tiktok",
        "handle": "qcone.ai",
        "hashtags": ["#qcone", "#foodtech"],
    },
    {
        "name": "Intello Labs",
        "platform": "instagram",
        "handle": "intellolabs",
        "hashtags": ["#intellolabs", "#aiagtech", "#producequality"],
    },
    {
        "name": "Intello Labs",
        "platform": "tiktok",
        "handle": "intellolabs",
        "hashtags": ["#intellolabs", "#agtech"],
    },
    {
        "name": "OneThird",
        "platform": "instagram",
        "handle": "onethird.ai",
        "hashtags": ["#onethird", "#foodwaste", "#shelflife"],
    },
    {
        "name": "OneThird",
        "platform": "tiktok",
        "handle": "onethird.ai",
        "hashtags": ["#onethird", "#foodwaste"],
    },
    # ── Recommended additions ───────────────────────────────────────────────
    {
        "name": "Apeel Sciences",
        "platform": "instagram",
        "handle": "apeelsciences",
        "hashtags": ["#apeel", "#foodwaste", "#fresher"],
    },
    {
        "name": "Apeel Sciences",
        "platform": "tiktok",
        "handle": "apeelsciences",
        "hashtags": ["#apeel", "#foodwaste"],
    },
    {
        "name": "Afresh Technologies",
        "platform": "instagram",
        "handle": "afresh_tech",
        "hashtags": ["#afresh", "#freshfood", "#grocerytech"],
    },
    {
        "name": "Afresh Technologies",
        "platform": "tiktok",
        "handle": "afreshtech",
        "hashtags": ["#afresh", "#grocerytech"],
    },
    {
        "name": "Hazel Technologies",
        "platform": "instagram",
        "handle": "hazeltechnologies",
        "hashtags": ["#hazeltech", "#producefreshness", "#agtech"],
    },
    {
        "name": "Hazel Technologies",
        "platform": "tiktok",
        "handle": "hazeltechnologies",
        "hashtags": ["#hazeltech", "#agtech"],
    },
]

INSERT_SQL = text("""
    INSERT INTO competitors (id, name, platform, handle, hashtags, is_active, created_at, updated_at)
    VALUES (:id, :name, :platform, :handle, :hashtags, true, :now, :now)
    ON CONFLICT (platform, handle) DO NOTHING
""")


async def seed():
    engine = create_async_engine(settings.database_url, echo=False)
    now = datetime.now(timezone.utc)

    async with engine.begin() as conn:
        inserted = 0
        for c in COMPETITORS:
            result = await conn.execute(
                INSERT_SQL,
                {
                    "id": str(uuid.uuid4()),
                    "name": c["name"],
                    "platform": c["platform"],
                    "handle": c["handle"],
                    "hashtags": c["hashtags"],
                    "now": now,
                },
            )
            inserted += result.rowcount

    await engine.dispose()
    print(f"Seeded {inserted} competitor rows ({len(COMPETITORS) - inserted} already existed).")


if __name__ == "__main__":
    asyncio.run(seed())
