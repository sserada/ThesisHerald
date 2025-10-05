"""Main entry point for ThesisHerald bot."""

import asyncio
import logging
import signal
import sys

from thesisherald.bot import create_bot
from thesisherald.config import Config
from thesisherald.scheduler import TaskScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("thesisherald.log"),
    ],
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function to run the bot."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config.load()

        # Create bot instance
        logger.info("Creating bot instance...")
        bot = create_bot(config)

        # Create scheduler
        scheduler = TaskScheduler(bot, config)

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig: int, frame: object) -> None:
            logger.info(f"Received signal {sig}, shutting down...")
            scheduler.stop()
            asyncio.create_task(bot.close())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Schedule the daily task
        scheduler.schedule_daily_task()

        # Start both the bot and scheduler
        logger.info("Starting bot and scheduler...")
        async with bot:
            # Start the scheduler in the background
            scheduler_task = asyncio.create_task(scheduler.run())

            try:
                # Start the bot
                await bot.start(config.bot.discord_token)
            finally:
                # Ensure scheduler is stopped
                scheduler.stop()
                await scheduler_task

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
