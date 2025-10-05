"""Discord bot implementation for ThesisHerald."""

import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from thesisherald.arxiv_client import ArxivClient
from thesisherald.config import Config

logger = logging.getLogger(__name__)


class ThesisHeraldBot(commands.Bot):
    """Discord bot for research paper notifications and searches."""

    def __init__(self, config: Config) -> None:
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

        self.config = config
        self.arxiv_client = ArxivClient(
            max_results=config.arxiv.default_max_results
        )

    async def setup_hook(self) -> None:
        """Setup hook called when bot is starting."""
        logger.info("Setting up bot...")
        # Sync commands with Discord
        if self.config.bot.guild_id:
            guild = discord.Object(id=self.config.bot.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands to guild {self.config.bot.guild_id}")
        else:
            await self.tree.sync()
            logger.info("Synced commands globally")

    async def on_ready(self) -> None:
        """Called when bot is ready."""
        if self.user:
            logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Bot is ready!")

    async def on_error(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Handle errors."""
        logger.exception(f"Error in {event}")

    async def send_papers_to_channel(
        self, channel_id: int, papers: list[Any]
    ) -> None:
        """Send paper notifications to a Discord channel."""
        channel = self.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            logger.error(f"Channel {channel_id} not found or not a text channel")
            return

        if not papers:
            await channel.send("No new papers found today.")
            return

        # Send header message
        await channel.send(
            f"📚 **Daily Paper Update** - Found {len(papers)} new papers:\n"
        )

        # Send each paper as a separate message to avoid Discord's character limit
        for i, paper in enumerate(papers, 1):
            try:
                message = f"**[{i}/{len(papers)}]**\n{paper.format_discord_message()}"
                await channel.send(message)
            except discord.HTTPException as e:
                logger.error(f"Failed to send paper {paper.arxiv_id}: {e}")


def create_bot(config: Config) -> ThesisHeraldBot:
    """Create and configure the bot instance."""
    bot = ThesisHeraldBot(config)

    @bot.tree.command(name="ping", description="Check if the bot is responsive")
    async def ping(interaction: discord.Interaction) -> None:
        """Ping command to check bot status."""
        await interaction.response.send_message("🏓 Pong!")

    @bot.tree.command(
        name="search",
        description="Search for papers by category"
    )
    @app_commands.describe(
        category="arXiv category (e.g., cs.AI, cs.LG)",
        max_results="Maximum number of results (default: 10)"
    )
    async def search(
        interaction: discord.Interaction,
        category: str,
        max_results: int = 10
    ) -> None:
        """Search for papers by category."""
        await interaction.response.defer()

        try:
            papers = bot.arxiv_client.search_by_category(
                categories=[category],
                max_results=min(max_results, 20)  # Limit to 20 max
            )

            if not papers:
                await interaction.followup.send(
                    f"No papers found for category '{category}'."
                )
                return

            await interaction.followup.send(
                f"📚 Found {len(papers)} papers in '{category}':"
            )

            for i, paper in enumerate(papers, 1):
                message = f"**[{i}/{len(papers)}]**\n{paper.format_discord_message()}"
                await interaction.followup.send(message)

        except Exception as e:
            logger.exception("Error in search command")
            await interaction.followup.send(
                f"❌ An error occurred while searching: {str(e)}"
            )

    @bot.tree.command(
        name="keywords",
        description="Search for papers by keywords"
    )
    @app_commands.describe(
        keywords="Keywords to search for (comma-separated)",
        max_results="Maximum number of results (default: 10)"
    )
    async def keywords(
        interaction: discord.Interaction,
        keywords: str,
        max_results: int = 10
    ) -> None:
        """Search for papers by keywords."""
        await interaction.response.defer()

        try:
            keyword_list = [kw.strip() for kw in keywords.split(",")]
            papers = bot.arxiv_client.search_by_keywords(
                keywords=keyword_list,
                max_results=min(max_results, 20)  # Limit to 20 max
            )

            if not papers:
                await interaction.followup.send(
                    f"No papers found for keywords: {keywords}"
                )
                return

            await interaction.followup.send(
                f"📚 Found {len(papers)} papers for keywords '{keywords}':"
            )

            for i, paper in enumerate(papers, 1):
                message = f"**[{i}/{len(papers)}]**\n{paper.format_discord_message()}"
                await interaction.followup.send(message)

        except Exception as e:
            logger.exception("Error in keywords command")
            await interaction.followup.send(
                f"❌ An error occurred while searching: {str(e)}"
            )

    @bot.tree.command(
        name="daily",
        description="Manually trigger daily paper notification"
    )
    async def daily(interaction: discord.Interaction) -> None:
        """Manually trigger daily paper notification."""
        await interaction.response.defer()

        try:
            papers = bot.arxiv_client.search_by_category(
                categories=bot.config.arxiv.default_categories,
                max_results=bot.config.arxiv.default_max_results
            )

            channel_id = bot.config.bot.notification_channel_id
            await bot.send_papers_to_channel(channel_id, papers)

            await interaction.followup.send(
                f"✅ Sent {len(papers)} papers to <#{channel_id}>"
            )

        except Exception as e:
            logger.exception("Error in daily command")
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}"
            )

    return bot
