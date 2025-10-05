"""Task scheduler for automated paper notifications."""

import asyncio
import logging
from typing import Callable

import schedule

from thesisherald.bot import ThesisHeraldBot
from thesisherald.config import Config

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled tasks for the bot."""

    def __init__(self, bot: ThesisHeraldBot, config: Config) -> None:
        """Initialize the scheduler."""
        self.bot = bot
        self.config = config
        self._running = False

    async def daily_paper_notification(self) -> None:
        """Task to send daily paper notifications."""
        logger.info("Running daily paper notification task...")

        try:
            papers = self.bot.arxiv_client.search_by_category(
                categories=self.config.arxiv.default_categories,
                max_results=self.config.arxiv.default_max_results,
            )

            channel_id = self.config.bot.notification_channel_id
            await self.bot.send_papers_to_channel(channel_id, papers)

            logger.info(
                f"Successfully sent {len(papers)} papers to channel {channel_id}"
            )
        except Exception as e:
            logger.exception(f"Error in daily paper notification: {e}")

    def schedule_daily_task(self) -> None:
        """Schedule the daily paper notification task."""
        notification_time = self.config.bot.notification_time
        logger.info(f"Scheduling daily notification at {notification_time}")

        # Wrap the async function to run in the bot's event loop
        def run_daily_task() -> None:
            asyncio.run_coroutine_threadsafe(
                self.daily_paper_notification(),
                self.bot.loop
            )

        schedule.every().day.at(notification_time).do(run_daily_task)

    async def run(self) -> None:
        """Run the scheduler loop."""
        self._running = True
        logger.info("Scheduler started")

        while self._running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute

    def stop(self) -> None:
        """Stop the scheduler."""
        logger.info("Stopping scheduler...")
        self._running = False
        schedule.clear()
