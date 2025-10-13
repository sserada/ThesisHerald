"""Task scheduler for automated paper notifications."""

import asyncio
import logging

import arxiv
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
            papers = await self.bot.arxiv_client.search_by_category(
                categories=self.config.arxiv.default_categories,
                max_results=self.config.arxiv.default_max_results,
            )

            channel_id = self.config.bot.notification_channel_id
            await self.bot.send_papers_to_channel(channel_id, papers)

            logger.info(
                f"Successfully sent {len(papers)} papers to channel {channel_id}"
            )
        except arxiv.HTTPError as e:
            logger.error(
                f"arXiv API error in daily notification (HTTP {e.status}): {e}"
            )
        except Exception as e:
            logger.exception(f"Error in daily paper notification: {e}")

    async def weekly_digest_notification(self) -> None:
        """Task to send weekly digest notifications."""
        logger.info("Running weekly digest notification task...")

        if not self.config.digest.enabled:
            logger.info("Weekly digest is disabled, skipping")
            return

        if not self.config.digest.topics:
            logger.warning("No digest topics configured, skipping")
            return

        if not self.bot.llm_client:
            logger.error("LLM client not available, cannot generate digest")
            return

        try:
            from datetime import datetime

            channel = self.bot.get_channel(self.config.digest.channel_id)
            if not channel:
                logger.error(
                    f"Digest channel {self.config.digest.channel_id} not found"
                )
                return

            # Generate digest for each configured topic
            for topic in self.config.digest.topics:
                logger.info(f"Generating digest for topic: {topic}")

                digest = await self.bot.llm_client.generate_weekly_digest(
                    topic=topic,
                    language=self.config.digest.language
                )

                # Create message and thread
                date_str = datetime.now().strftime("%Y-%m-%d")
                initial_msg = await channel.send(  # type: ignore[union-attr]
                    f"📊 Weekly digest for: **{topic}**"
                )

                thread = await initial_msg.create_thread(
                    name=f"Weekly Digest: {topic[:60]} - {date_str}",
                    auto_archive_duration=1440
                )

                # Send digest in thread
                from thesisherald.bot import send_long_message

                await send_long_message(thread, digest)

                logger.info(f"Successfully sent digest for topic: {topic}")

        except Exception as e:
            logger.exception(f"Error in weekly digest notification: {e}")

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

    def schedule_weekly_digest(self) -> None:
        """Schedule the weekly digest notification task."""
        if not self.config.digest.enabled:
            logger.info("Weekly digest is disabled, skipping scheduling")
            return

        digest_time = self.config.digest.time
        day_of_week = self.config.digest.day_of_week

        day_names = ["monday", "tuesday", "wednesday", "thursday",
                     "friday", "saturday", "sunday"]
        day_name = day_names[day_of_week] if 0 <= day_of_week < 7 else "monday"

        logger.info(
            f"Scheduling weekly digest on {day_name} at {digest_time}"
        )

        # Wrap the async function to run in the bot's event loop
        def run_digest_task() -> None:
            asyncio.run_coroutine_threadsafe(
                self.weekly_digest_notification(),
                self.bot.loop
            )

        # Schedule based on day of week
        getattr(schedule.every(), day_name).at(digest_time).do(run_digest_task)

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
