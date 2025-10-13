"""arXiv API client for fetching research papers."""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime

import arxiv
from deep_translator import GoogleTranslator  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def extract_arxiv_id(input_string: str) -> str | None:
    """Extract arXiv ID from various input formats.

    Supports:
    - Plain ID: 2010.11929, 2010.11929v1
    - Abstract URL: https://arxiv.org/abs/2010.11929
    - PDF URL: https://arxiv.org/pdf/2010.11929.pdf
    - Old format: arxiv:2010.11929

    Args:
        input_string: User input (ID or URL)

    Returns:
        Extracted arXiv ID without version, or None if invalid
    """
    input_string = input_string.strip()

    # Pattern for arXiv ID: YYMM.NNNNN or YYMM.NNNNNvN
    arxiv_id_pattern = r"(\d{4}\.\d{4,5})(v\d+)?"

    # Try direct ID format
    match = re.fullmatch(arxiv_id_pattern, input_string)
    if match:
        return match.group(1)  # Return without version

    # Try arxiv: prefix format
    if input_string.startswith("arxiv:"):
        match = re.search(arxiv_id_pattern, input_string)
        if match:
            return match.group(1)

    # Try URL formats
    match = re.search(r"/(?:abs|pdf)/(" + arxiv_id_pattern + r")", input_string)
    if match:
        return match.group(1)  # Return ID without version

    return None


@dataclass
class Paper:
    """Represents a research paper from arXiv."""

    title: str
    authors: list[str]
    summary: str
    arxiv_id: str
    pdf_url: str
    published: datetime
    updated: datetime
    categories: list[str]
    primary_category: str

    @classmethod
    def from_arxiv_result(cls, result: arxiv.Result) -> "Paper":
        """Create Paper instance from arxiv.Result."""
        return cls(
            title=result.title,
            authors=[author.name for author in result.authors],
            summary=result.summary,
            arxiv_id=result.entry_id.split("/")[-1],
            pdf_url=result.pdf_url,
            published=result.published,
            updated=result.updated,
            categories=result.categories,
            primary_category=result.primary_category,
        )

    def format_discord_message(
        self, translate: bool = False, target_lang: str = "ja"
    ) -> str:
        """Format paper information for Discord message.

        Args:
            translate: Whether to translate the abstract
            target_lang: Target language code (ISO 639-1)
        """
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += f" et al. ({len(self.authors)} authors)"

        # Clean up summary (remove newlines but don't truncate)
        summary = self.summary.replace("\n", " ")

        message = f"""**{self.title}**
**Authors:** {authors_str}
**Published:** {self.published.strftime('%Y-%m-%d')}
**Categories:** {', '.join(self.categories[:3])}
**arXiv ID:** {self.arxiv_id}
**PDF:** {self.pdf_url}

**Abstract:**
{summary}
"""

        # Add translation if enabled
        if translate:
            try:
                translator = GoogleTranslator(source="auto", target=target_lang)
                translated_summary = translator.translate(summary)

                # Add translated version with language-specific label
                lang_labels = {
                    "ja": "要約",
                    "ko": "요약",
                    "zh-CN": "摘要",
                    "zh-TW": "摘要",
                    "es": "Resumen",
                    "fr": "Résumé",
                    "de": "Zusammenfassung",
                }
                label = lang_labels.get(target_lang, f"Abstract ({target_lang})")

                message += f"\n**{label}:**\n{translated_summary}\n"
            except Exception as e:
                logger.error(f"Translation failed for paper {self.arxiv_id}: {e}")
                # Continue without translation if it fails

        return message


class ArxivClient:
    """Client for interacting with arXiv API."""

    def __init__(self, max_results: int = 10) -> None:
        """Initialize arXiv client."""
        self.max_results = max_results
        self.client = arxiv.Client()

    def _search_by_category_sync(
        self,
        categories: list[str],
        max_results: int | None = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
    ) -> list[Paper]:
        """Synchronous helper for searching papers by categories."""
        results_limit = max_results or self.max_results

        # Build query for multiple categories
        if len(categories) == 1:
            query = f"cat:{categories[0]}"
        else:
            category_queries = [f"cat:{cat}" for cat in categories]
            query = " OR ".join(category_queries)

        search = arxiv.Search(
            query=query,
            max_results=results_limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        papers = []
        for result in self.client.results(search):
            papers.append(Paper.from_arxiv_result(result))

        return papers

    async def search_by_category(
        self,
        categories: list[str],
        max_results: int | None = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
    ) -> list[Paper]:
        """Search papers by categories (async)."""
        # Run sync operation in thread pool to avoid blocking event loop
        return await asyncio.to_thread(
            self._search_by_category_sync,
            categories,
            max_results,
            sort_by,
            sort_order,
        )

    def _search_by_keywords_sync(
        self,
        keywords: list[str],
        categories: list[str] | None = None,
        max_results: int | None = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
    ) -> list[Paper]:
        """Synchronous helper for searching papers by keywords."""
        results_limit = max_results or self.max_results

        # Build keyword query
        keyword_queries = [f'all:"{kw}"' for kw in keywords]
        query = " AND ".join(keyword_queries)

        # Add category filter if provided
        if categories:
            if len(categories) == 1:
                query += f" AND cat:{categories[0]}"
            else:
                category_queries = [f"cat:{cat}" for cat in categories]
                query += f" AND ({' OR '.join(category_queries)})"

        search = arxiv.Search(
            query=query,
            max_results=results_limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        papers = []
        for result in self.client.results(search):
            papers.append(Paper.from_arxiv_result(result))

        return papers

    async def search_by_keywords(
        self,
        keywords: list[str],
        categories: list[str] | None = None,
        max_results: int | None = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
    ) -> list[Paper]:
        """Search papers by keywords and optional categories (async)."""
        # Run sync operation in thread pool to avoid blocking event loop
        return await asyncio.to_thread(
            self._search_by_keywords_sync,
            keywords,
            categories,
            max_results,
            sort_by,
            sort_order,
        )

    def _get_paper_by_id_sync(self, arxiv_id: str) -> Paper | None:
        """Synchronous helper for getting a paper by ID."""
        search = arxiv.Search(id_list=[arxiv_id])

        try:
            result = next(self.client.results(search))
            return Paper.from_arxiv_result(result)
        except StopIteration:
            return None

    async def get_paper_by_id(self, arxiv_id: str) -> Paper | None:
        """Get a specific paper by its arXiv ID (async)."""
        # Run sync operation in thread pool to avoid blocking event loop
        return await asyncio.to_thread(self._get_paper_by_id_sync, arxiv_id)
