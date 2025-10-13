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
class LLMConfig:
    """Configuration for LLM API."""

    api_key: str
    model: str
    max_tokens: int
    enabled: bool

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        enabled = bool(api_key)

        model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

        return cls(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            enabled=enabled,
        )


@dataclass
class TranslationConfig:
    """Configuration for abstract translation."""

    enabled: bool
    target_language: str

    @classmethod
    def from_env(cls) -> "TranslationConfig":
        """Load configuration from environment variables."""
        enabled_str = os.getenv("ENABLE_TRANSLATION", "false").lower()
        enabled = enabled_str in ("true", "1", "yes")

        target_language = os.getenv("TRANSLATION_TARGET_LANG", "ja")

        return cls(
            enabled=enabled,
            target_language=target_language,
        )


@dataclass
class DigestConfig:
    """Configuration for weekly digest feature."""

    enabled: bool
    topics: list[str]
    day_of_week: int  # 0=Monday, 6=Sunday
    time: str  # Format: "HH:MM"
    channel_id: int
    language: str

    @classmethod
    def from_env(cls) -> "DigestConfig":
        """Load configuration from environment variables."""
        enabled_str = os.getenv("DIGEST_ENABLED", "false").lower()
        enabled = enabled_str in ("true", "1", "yes")

        topics_str = os.getenv("DIGEST_TOPICS", "")
        topics = [topic.strip() for topic in topics_str.split(",") if topic.strip()]

        day_of_week = int(os.getenv("DIGEST_DAY", "0"))
        time = os.getenv("DIGEST_TIME", "09:00")

        # Use NOTIFICATION_CHANNEL_ID as fallback
        channel_id_str = os.getenv(
            "DIGEST_CHANNEL_ID", os.getenv("NOTIFICATION_CHANNEL_ID", "")
        )
        channel_id = int(channel_id_str) if channel_id_str else 0

        language = os.getenv("DIGEST_LANGUAGE", "en")

        return cls(
            enabled=enabled,
            topics=topics,
            day_of_week=day_of_week,
            time=time,
            channel_id=channel_id,
            language=language,
        )


@dataclass
class Config:
    """Main configuration container."""

    bot: BotConfig
    arxiv: ArxivConfig
    llm: LLMConfig
    translation: TranslationConfig
    digest: DigestConfig

    @classmethod
    def load(cls) -> "Config":
        """Load all configurations."""
        return cls(
            bot=BotConfig.from_env(),
            arxiv=ArxivConfig.from_env(),
            llm=LLMConfig.from_env(),
            translation=TranslationConfig.from_env(),
            digest=DigestConfig.from_env(),
        )
