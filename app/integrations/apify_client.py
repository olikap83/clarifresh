import asyncio
import logging
from typing import Any

from apify_client import ApifyClient as _ApifyClient

from app.config import settings

logger = logging.getLogger(__name__)


class ApifyClient:
    def __init__(self):
        self._client = _ApifyClient(settings.apify_api_token)

    def _actor_id(self, platform: str) -> str:
        if platform == "tiktok":
            return settings.apify_tiktok_actor_id
        return settings.apify_instagram_actor_id

    def _build_run_input(self, platform: str, handles: list[str], hashtags: list[str], max_posts: int) -> dict:
        if platform == "tiktok":
            return {
                "profiles": handles,
                "hashtags": hashtags,
                "resultsPerPage": max_posts,
                "maxItems": max_posts * max(len(handles), 1),
            }
        return {
            "usernames": handles,
            "hashtags": hashtags,
            "resultsLimit": max_posts,
        }

    async def trigger_run(self, platform: str, handles: list[str], hashtags: list[str], max_posts: int) -> str:
        actor_id = self._actor_id(platform)
        run_input = self._build_run_input(platform, handles, hashtags, max_posts)

        loop = asyncio.get_running_loop()
        run = await loop.run_in_executor(
            None,
            lambda: self._client.actor(actor_id).call(run_input=run_input, wait_secs=0),
        )
        return run["id"]

    async def get_run_status(self, run_id: str) -> str:
        loop = asyncio.get_running_loop()
        run = await loop.run_in_executor(None, lambda: self._client.run(run_id).get())
        return run.get("status", "UNKNOWN")

    async def fetch_items(self, run_id: str) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        dataset_id = await loop.run_in_executor(
            None, lambda: self._client.run(run_id).get()["defaultDatasetId"]
        )
        items = await loop.run_in_executor(
            None, lambda: list(self._client.dataset(dataset_id).iterate_items())
        )
        return items

    async def poll_until_done(self, run_id: str) -> bool:
        terminal = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}
        elapsed = 0
        while elapsed < settings.apify_poll_timeout_seconds:
            status = await self.get_run_status(run_id)
            if status in terminal:
                return status == "SUCCEEDED"
            await asyncio.sleep(settings.apify_poll_interval_seconds)
            elapsed += settings.apify_poll_interval_seconds

        logger.error("Apify run %s timed out after %ds", run_id, elapsed)
        return False
