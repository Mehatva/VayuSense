"""Background scheduler — auto-refreshes AQI data every hour."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


async def refresh_aqi_data():
    """Fetches latest AQI from OpenAQ and stores in DB."""
    logger.info("⏰ Scheduled AQI refresh triggered")
    # In production: call OpenAQFetcher and write to TimescaleDB
    # For demo: data is fetched on-demand per request


async def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_aqi_data,
        trigger=IntervalTrigger(minutes=60),
        id="aqi_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — AQI refresh every 60 minutes")
    return scheduler
