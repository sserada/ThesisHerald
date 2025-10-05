"""arXiv API client for fetching research papers."""

from dataclasses import dataclass
from datetime import datetime

import arxiv


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

    def format_discord_message(self) -> str:
        """Format paper information for Discord message."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += f" et al. ({len(self.authors)} authors)"

        # Truncate summary if too long
        summary = self.summary.replace("\n", " ")
        if len(summary) > 300:
            summary = summary[:297] + "..."

        message = f"""**{self.title}**
**Authors:** {authors_str}
**Published:** {self.published.strftime('%Y-%m-%d')}
**Categories:** {', '.join(self.categories[:3])}
**arXiv ID:** {self.arxiv_id}
**PDF:** {self.pdf_url}

{summary}
"""
        return message


class ArxivClient:
    """Client for interacting with arXiv API."""

    def __init__(self, max_results: int = 10) -> None:
        """Initialize arXiv client."""
        self.max_results = max_results
        self.client = arxiv.Client()

    def search_by_category(
        self,
        categories: list[str],
        max_results: int | None = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
    ) -> list[Paper]:
        """Search papers by categories."""
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

    def search_by_keywords(
        self,
        keywords: list[str],
        categories: list[str] | None = None,
        max_results: int | None = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
    ) -> list[Paper]:
        """Search papers by keywords and optional categories."""
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

    def get_paper_by_id(self, arxiv_id: str) -> Paper | None:
        """Get a specific paper by its arXiv ID."""
        search = arxiv.Search(id_list=[arxiv_id])

        try:
            result = next(self.client.results(search))
            return Paper.from_arxiv_result(result)
        except StopIteration:
            return None
