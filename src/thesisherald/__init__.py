"""ThesisHerald - Discord bot for research paper notifications and analysis."""

__version__ = "0.1.0"

from thesisherald.arxiv_client import ArxivClient, Paper
from thesisherald.bot import ThesisHeraldBot, create_bot
from thesisherald.config import ArxivConfig, BotConfig, Config

__all__ = [
    "ArxivClient",
    "Paper",
    "ThesisHeraldBot",
    "create_bot",
    "Config",
    "BotConfig",
    "ArxivConfig",
]
