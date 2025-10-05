"""Configuration module for ThesisHerald bot."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Configuration for Discord bot."""

    discord_token: str
    guild_id: int | None
    notification_channel_id: int
    notification_time: str  # Format: "HH:MM"

    @classmethod
    def from_env(cls) -> "BotConfig":
        """Load configuration from environment variables."""
        discord_token = os.getenv("DISCORD_TOKEN")
        if not discord_token:
            raise ValueError("DISCORD_TOKEN environment variable is required")

        guild_id_str = os.getenv("DISCORD_GUILD_ID")
        guild_id = int(guild_id_str) if guild_id_str else None

        channel_id_str = os.getenv("NOTIFICATION_CHANNEL_ID")
        if not channel_id_str:
            raise ValueError("NOTIFICATION_CHANNEL_ID environment variable is required")

        notification_time = os.getenv("NOTIFICATION_TIME", "09:00")

        return cls(
            discord_token=discord_token,
            guild_id=guild_id,
            notification_channel_id=int(channel_id_str),
            notification_time=notification_time,
        )


@dataclass
class ArxivConfig:
    """Configuration for arXiv API searches."""

    default_categories: list[str]
    default_max_results: int
    default_sort_by: str
    default_sort_order: str

    @classmethod
    def from_env(cls) -> "ArxivConfig":
        """Load configuration from environment variables."""
        categories_str = os.getenv("ARXIV_CATEGORIES", "cs.AI,cs.LG,cs.CL")
        categories = [cat.strip() for cat in categories_str.split(",")]

        max_results = int(os.getenv("ARXIV_MAX_RESULTS", "10"))
        sort_by = os.getenv("ARXIV_SORT_BY", "submittedDate")
        sort_order = os.getenv("ARXIV_SORT_ORDER", "descending")

        return cls(
            default_categories=categories,
            default_max_results=max_results,
            default_sort_by=sort_by,
            default_sort_order=sort_order,
        )


@dataclass
class Config:
    """Main configuration container."""

    bot: BotConfig
    arxiv: ArxivConfig

    @classmethod
    def load(cls) -> "Config":
        """Load all configurations."""
        return cls(
            bot=BotConfig.from_env(),
            arxiv=ArxivConfig.from_env(),
        )
