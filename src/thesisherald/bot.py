"""Discord bot implementation for ThesisHerald."""

import logging
from datetime import datetime
from typing import Any

import arxiv
import discord
from discord import app_commands
from discord.ext import commands

from thesisherald.arxiv_client import ArxivClient, extract_arxiv_id
from thesisherald.config import Config
from thesisherald.llm_client import LLMClient

logger = logging.getLogger(__name__)


async def send_long_message(
    channel: discord.abc.Messageable, content: str, max_length: int = 2000
) -> None:
    """Send a message, splitting it if it exceeds Discord's character limit.

    Args:
        channel: The channel or thread to send to
        content: The message content
        max_length: Maximum length per message (Discord limit is 2000)
    """
    if len(content) <= max_length:
        await channel.send(content)
        return

    # Split by lines to avoid breaking in the middle of content
    lines = content.split("\n")
    current_chunk = ""

    for line in lines:
        # If adding this line would exceed the limit, send current chunk
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                await channel.send(current_chunk)
                current_chunk = line + "\n"
            else:
                # Single line is too long, need to split it
                for i in range(0, len(line), max_length):
                    await channel.send(line[i : i + max_length])
        else:
            current_chunk += line + "\n"

    # Send remaining content
    if current_chunk:
        await channel.send(current_chunk.rstrip())


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

        # Initialize LLM client if enabled
        self.llm_client: LLMClient | None = None
        if config.llm.enabled:
            self.llm_client = LLMClient(
                api_key=config.llm.api_key,
                model=config.llm.model,
                max_tokens=config.llm.max_tokens,
            )
            logger.info("LLM client initialized")
        else:
            logger.warning("LLM client disabled - /ask command will not be available")

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
        """Send paper notifications to a Discord channel in a thread."""
        channel = self.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            logger.error(f"Channel {channel_id} not found or not a text channel")
            return

        if not papers:
            await channel.send("No new papers found today.")
            return

        # Send header message and create thread
        today = datetime.now().strftime("%Y-%m-%d")

        header_message = await channel.send(
            f"📚 **Daily Paper Update** - Found {len(papers)} new papers:"
        )
        thread = await header_message.create_thread(
            name=f"Daily Papers: {today} ({len(papers)} papers)",
            auto_archive_duration=1440  # 24 hours
        )

        # Send each paper to the thread
        for i, paper in enumerate(papers, 1):
            try:
                formatted = paper.format_discord_message(
                    translate=self.config.translation.enabled,
                    target_lang=self.config.translation.target_language,
                )
                message = f"**[{i}/{len(papers)}]**\n{formatted}\n{'-' * 50}"
                await send_long_message(thread, message)
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
            papers = await bot.arxiv_client.search_by_category(
                categories=[category],
                max_results=min(max_results, 20)  # Limit to 20 max
            )

            if not papers:
                await interaction.followup.send(
                    f"No papers found for category '{category}'."
                )
                return

            # Send initial response
            await interaction.followup.send(
                f"📚 Found {len(papers)} papers in '{category}':"
            )

            # Get channel and send message to create thread from
            channel = interaction.channel
            if not channel or not isinstance(channel, discord.TextChannel):
                await interaction.followup.send("❌ This command must be used in a text channel.")
                return

            # Create thread from a message in the channel
            initial_message = await channel.send(
                f"Search results for **{category}**:"
            )
            thread = await initial_message.create_thread(
                name=f"Search: {category} ({len(papers)} papers)",
                auto_archive_duration=1440  # 24 hours
            )

            # Send all papers in the thread
            for i, paper in enumerate(papers, 1):
                formatted = paper.format_discord_message(
                    translate=bot.config.translation.enabled,
                    target_lang=bot.config.translation.target_language,
                )
                message = f"**[{i}/{len(papers)}]**\n{formatted}\n{'-' * 50}"
                await send_long_message(thread, message)

        except Exception as e:
            logger.exception("Error in search command")

            if isinstance(e, arxiv.HTTPError):
                await interaction.followup.send(
                    f"❌ arXiv API is temporarily unavailable (HTTP {e.status}). "
                    "Please try again in a few moments."
                )
            else:
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
            papers = await bot.arxiv_client.search_by_keywords(
                keywords=keyword_list,
                max_results=min(max_results, 20)  # Limit to 20 max
            )

            if not papers:
                await interaction.followup.send(
                    f"No papers found for keywords: {keywords}"
                )
                return

            # Send initial response
            await interaction.followup.send(
                f"📚 Found {len(papers)} papers for keywords '{keywords}':"
            )

            # Get channel and send message to create thread from
            channel = interaction.channel
            if not channel or not isinstance(channel, discord.TextChannel):
                await interaction.followup.send("❌ This command must be used in a text channel.")
                return

            # Create thread from a message in the channel
            initial_message = await channel.send(
                f"Search results for keywords: **{keywords}**"
            )
            thread = await initial_message.create_thread(
                name=f"Keywords: {keywords[:80]} ({len(papers)} papers)",
                auto_archive_duration=1440  # 24 hours
            )

            # Send all papers in the thread
            for i, paper in enumerate(papers, 1):
                formatted = paper.format_discord_message(
                    translate=bot.config.translation.enabled,
                    target_lang=bot.config.translation.target_language,
                )
                message = f"**[{i}/{len(papers)}]**\n{formatted}\n{'-' * 50}"
                await send_long_message(thread, message)

        except Exception as e:
            logger.exception("Error in keywords command")

            if isinstance(e, arxiv.HTTPError):
                await interaction.followup.send(
                    f"❌ arXiv API is temporarily unavailable (HTTP {e.status}). "
                    "Please try again in a few moments."
                )
            else:
                await interaction.followup.send(
                    f"❌ An error occurred while searching: {str(e)}"
                )

    @bot.tree.command(
        name="summarize",
        description="Generate AI-powered summary of a research paper"
    )
    @app_commands.describe(
        arxiv_input="arXiv ID or URL (e.g., 2010.11929 or https://arxiv.org/abs/2010.11929)",
        language="Language for the summary (en, ja, zh, ko, etc. Default: en)"
    )
    async def summarize(
        interaction: discord.Interaction,
        arxiv_input: str,
        language: str = "en"
    ) -> None:
        """Generate an AI-powered summary of a research paper."""
        # Check if LLM is enabled
        if not bot.llm_client:
            await interaction.response.send_message(
                "❌ LLM integration is not enabled. Please configure ANTHROPIC_API_KEY."
            )
            return

        await interaction.response.defer()

        try:
            # Extract arXiv ID from input
            arxiv_id = extract_arxiv_id(arxiv_input)
            if not arxiv_id:
                await interaction.followup.send(
                    f"❌ Invalid arXiv ID or URL format: `{arxiv_input}`\n\n"
                    "**Supported formats:**\n"
                    "• arXiv ID: `2010.11929`\n"
                    "• Abstract URL: `https://arxiv.org/abs/2010.11929`\n"
                    "• PDF URL: `https://arxiv.org/pdf/2010.11929.pdf`"
                )
                return

            # Fetch paper from arXiv
            paper = await bot.arxiv_client.get_paper_by_id(arxiv_id)
            if not paper:
                await interaction.followup.send(
                    f"❌ Paper not found: `{arxiv_id}`\n\n"
                    "Please check the arXiv ID and try again."
                )
                return

            # Generate summary using LLM with specified language
            summary = await bot.llm_client.summarize_paper(paper, language=language)

            # Create thread for the summary
            if interaction.channel:
                # Create initial message to attach thread to
                initial_msg = await interaction.channel.send(  # type: ignore[union-attr]
                    f"📝 Generating summary for: **{paper.title[:100]}...**"
                )

                # Create thread
                thread = await initial_msg.create_thread(
                    name=f"Summary: {paper.title[:80]}",
                    auto_archive_duration=1440
                )

                # Send summary in thread
                await send_long_message(thread, summary)

                # Update initial message with thread link
                await interaction.followup.send(
                    f"✅ Summary generated! View it in the thread: {thread.mention}"
                )
            else:
                # Fallback if no channel (shouldn't happen in normal usage)
                await interaction.followup.send(summary[:2000])

        except arxiv.HTTPError as e:
            logger.exception("arXiv API error in summarize command")
            await interaction.followup.send(
                f"❌ arXiv API error (HTTP {e.status}). Please try again later."
            )
        except Exception as e:
            logger.exception("Error in summarize command")
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}"
            )

    @bot.tree.command(
        name="daily",
        description="Manually trigger daily paper notification"
    )
    async def daily(interaction: discord.Interaction) -> None:
        """Manually trigger daily paper notification."""
        await interaction.response.defer()

        try:
            papers = await bot.arxiv_client.search_by_category(
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

            if isinstance(e, arxiv.HTTPError):
                await interaction.followup.send(
                    f"❌ arXiv API is temporarily unavailable (HTTP {e.status}). "
                    "Please try again in a few moments."
                )
            else:
                await interaction.followup.send(
                    f"❌ An error occurred: {str(e)}"
                )

    @bot.tree.command(
        name="digest",
        description="Generate weekly digest of important papers on a topic"
    )
    @app_commands.describe(
        topic="Research topic (e.g., 'transformer architectures', 'quantum computing')",
        language="Language for the digest (en, ja, zh, ko, etc. Default: en)"
    )
    async def digest(
        interaction: discord.Interaction,
        topic: str,
        language: str = "en"
    ) -> None:
        """Generate a weekly digest of papers on a specific topic."""
        if not bot.llm_client:
            await interaction.response.send_message(
                "❌ LLM integration is not enabled. Please configure ANTHROPIC_API_KEY."
            )
            return

        await interaction.response.defer()

        try:
            # Generate digest using LLM
            digest = await bot.llm_client.generate_weekly_digest(
                topic=topic,
                language=language
            )

            # Create thread for the digest
            if interaction.channel:
                from datetime import datetime

                # Create initial message to attach thread to
                date_str = datetime.now().strftime("%Y-%m-%d")
                initial_msg = await interaction.channel.send(  # type: ignore[union-attr]
                    f"📊 Generating weekly digest for: **{topic}**"
                )

                # Create thread
                thread = await initial_msg.create_thread(
                    name=f"Weekly Digest: {topic[:60]} - {date_str}",
                    auto_archive_duration=1440
                )

                # Send digest in thread
                await send_long_message(thread, digest)

                # Update initial message with thread link
                await interaction.followup.send(
                    f"✅ Weekly digest generated! View it in the thread: {thread.mention}"
                )
            else:
                # Fallback if no channel
                await interaction.followup.send(digest[:2000])

        except Exception as e:
            logger.exception("Error in digest command")
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}"
            )

    @bot.tree.command(
        name="ask",
        description="Ask a question and get AI-powered paper recommendations"
    )
    @app_commands.describe(
        question="Your question about research papers or topics"
    )
    async def ask(interaction: discord.Interaction, question: str) -> None:
        """Ask a natural language question with LLM-powered search."""
        if not bot.llm_client:
            await interaction.response.send_message(
                "❌ LLM integration is not enabled. Please configure ANTHROPIC_API_KEY."
            )
            return

        await interaction.response.defer()

        try:
            # Use LLM for conversational search
            response = await bot.llm_client.conversational_search(question)

            # Split response if too long for Discord (2000 char limit)
            if len(response) <= 2000:
                await interaction.followup.send(response)
            else:
                # Split into chunks
                chunks = []
                current_chunk = ""
                for line in response.split("\n"):
                    if len(current_chunk) + len(line) + 1 > 2000:
                        chunks.append(current_chunk)
                        current_chunk = line
                    else:
                        current_chunk += "\n" + line if current_chunk else line

                if current_chunk:
                    chunks.append(current_chunk)

                # Send chunks
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await interaction.followup.send(chunk)
                    else:
                        await interaction.channel.send(chunk)  # type: ignore

        except Exception as e:
            logger.exception("Error in ask command")
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}"
            )

    return bot
