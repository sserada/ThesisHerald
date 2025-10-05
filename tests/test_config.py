"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from thesisherald.config import ArxivConfig, BotConfig, Config


class TestBotConfig:
    """Test cases for BotConfig."""

    def test_from_env_with_all_values(self) -> None:
        """Test loading config with all environment variables set."""
        env_vars = {
            "DISCORD_TOKEN": "test_token_123",
            "DISCORD_GUILD_ID": "123456789",
            "NOTIFICATION_CHANNEL_ID": "987654321",
            "NOTIFICATION_TIME": "10:30",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = BotConfig.from_env()

        assert config.discord_token == "test_token_123"
        assert config.guild_id == 123456789
        assert config.notification_channel_id == 987654321
        assert config.notification_time == "10:30"

    def test_from_env_without_guild_id(self) -> None:
        """Test loading config without guild ID."""
        env_vars = {
            "DISCORD_TOKEN": "test_token_123",
            "NOTIFICATION_CHANNEL_ID": "987654321",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = BotConfig.from_env()

        assert config.discord_token == "test_token_123"
        assert config.guild_id is None
        assert config.notification_time == "09:00"  # Default value

    def test_from_env_missing_token_raises_error(self) -> None:
        """Test that missing token raises ValueError."""
        env_vars = {
            "NOTIFICATION_CHANNEL_ID": "987654321",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="DISCORD_TOKEN"):
                BotConfig.from_env()

    def test_from_env_missing_channel_id_raises_error(self) -> None:
        """Test that missing channel ID raises ValueError."""
        env_vars = {
            "DISCORD_TOKEN": "test_token_123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="NOTIFICATION_CHANNEL_ID"):
                BotConfig.from_env()


class TestArxivConfig:
    """Test cases for ArxivConfig."""

    def test_from_env_with_defaults(self) -> None:
        """Test loading config with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = ArxivConfig.from_env()

        assert config.default_categories == ["cs.AI", "cs.LG", "cs.CL"]
        assert config.default_max_results == 10
        assert config.default_sort_by == "submittedDate"
        assert config.default_sort_order == "descending"

    def test_from_env_with_custom_values(self) -> None:
        """Test loading config with custom values."""
        env_vars = {
            "ARXIV_CATEGORIES": "cs.CV,cs.RO",
            "ARXIV_MAX_RESULTS": "20",
            "ARXIV_SORT_BY": "lastUpdatedDate",
            "ARXIV_SORT_ORDER": "ascending",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ArxivConfig.from_env()

        assert config.default_categories == ["cs.CV", "cs.RO"]
        assert config.default_max_results == 20
        assert config.default_sort_by == "lastUpdatedDate"
        assert config.default_sort_order == "ascending"

    def test_from_env_categories_with_spaces(self) -> None:
        """Test that category list handles spaces correctly."""
        env_vars = {
            "ARXIV_CATEGORIES": "cs.AI, cs.LG , cs.CL",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = ArxivConfig.from_env()

        # Should strip spaces
        assert config.default_categories == ["cs.AI", "cs.LG", "cs.CL"]


class TestConfig:
    """Test cases for main Config class."""

    def test_load_creates_all_configs(self) -> None:
        """Test that load creates both bot and arxiv configs."""
        env_vars = {
            "DISCORD_TOKEN": "test_token",
            "NOTIFICATION_CHANNEL_ID": "123456",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = Config.load()

        assert isinstance(config.bot, BotConfig)
        assert isinstance(config.arxiv, ArxivConfig)
        assert config.bot.discord_token == "test_token"
        assert config.arxiv.default_max_results == 10
