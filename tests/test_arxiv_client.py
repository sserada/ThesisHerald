"""Tests for arXiv client."""

import pytest

from thesisherald.arxiv_client import ArxivClient, Paper


class TestArxivClient:
    """Test cases for ArxivClient."""

    def test_client_initialization(self) -> None:
        """Test that client initializes correctly."""
        client = ArxivClient(max_results=5)
        assert client.max_results == 5

    def test_search_by_category(self) -> None:
        """Test searching papers by category."""
        client = ArxivClient(max_results=2)
        papers = client.search_by_category(categories=["cs.AI"])

        assert isinstance(papers, list)
        assert len(papers) <= 2
        for paper in papers:
            assert isinstance(paper, Paper)
            assert paper.title
            assert paper.arxiv_id
            assert paper.pdf_url

    def test_search_by_multiple_categories(self) -> None:
        """Test searching papers by multiple categories."""
        client = ArxivClient(max_results=3)
        papers = client.search_by_category(categories=["cs.AI", "cs.LG"])

        assert isinstance(papers, list)
        assert len(papers) <= 3

    def test_search_by_keywords(self) -> None:
        """Test searching papers by keywords."""
        client = ArxivClient(max_results=2)
        papers = client.search_by_keywords(keywords=["machine learning"])

        assert isinstance(papers, list)
        assert len(papers) <= 2
        for paper in papers:
            assert isinstance(paper, Paper)

    def test_get_paper_by_id(self) -> None:
        """Test getting a specific paper by ID."""
        client = ArxivClient()
        # Use a known arXiv paper ID
        paper = client.get_paper_by_id("2010.11929")  # CLIP paper

        assert paper is not None
        assert isinstance(paper, Paper)
        assert paper.arxiv_id == "2010.11929"
        assert paper.title

    def test_get_paper_by_invalid_id(self) -> None:
        """Test getting a paper with invalid ID."""
        client = ArxivClient()
        paper = client.get_paper_by_id("invalid_id_123456789")

        assert paper is None


class TestPaper:
    """Test cases for Paper dataclass."""

    def test_format_discord_message(self) -> None:
        """Test formatting paper for Discord."""
        from datetime import datetime

        paper = Paper(
            title="Test Paper Title",
            authors=["Author One", "Author Two"],
            summary="This is a test summary for the paper.",
            arxiv_id="2010.11929",
            pdf_url="https://arxiv.org/pdf/2010.11929",
            published=datetime(2020, 10, 23),
            updated=datetime(2020, 10, 23),
            categories=["cs.AI", "cs.LG"],
            primary_category="cs.AI",
        )

        message = paper.format_discord_message()

        assert "Test Paper Title" in message
        assert "Author One" in message
        assert "2020-10-23" in message
        assert "2010.11929" in message
        assert "https://arxiv.org/pdf/2010.11929" in message
        assert "cs.AI" in message

    def test_format_discord_message_truncates_long_summary(self) -> None:
        """Test that long summaries are truncated."""
        from datetime import datetime

        long_summary = "a" * 500  # Summary longer than 300 chars

        paper = Paper(
            title="Test Paper",
            authors=["Author"],
            summary=long_summary,
            arxiv_id="1234.5678",
            pdf_url="https://arxiv.org/pdf/1234.5678",
            published=datetime(2020, 1, 1),
            updated=datetime(2020, 1, 1),
            categories=["cs.AI"],
            primary_category="cs.AI",
        )

        message = paper.format_discord_message()
        # The summary in the message should be truncated
        assert len(message) < len(long_summary) + 200  # Some buffer for other fields
        assert "..." in message  # Should have ellipsis

    def test_format_discord_message_many_authors(self) -> None:
        """Test formatting with many authors."""
        from datetime import datetime

        authors = [f"Author {i}" for i in range(10)]

        paper = Paper(
            title="Test Paper",
            authors=authors,
            summary="Test summary",
            arxiv_id="1234.5678",
            pdf_url="https://arxiv.org/pdf/1234.5678",
            published=datetime(2020, 1, 1),
            updated=datetime(2020, 1, 1),
            categories=["cs.AI"],
            primary_category="cs.AI",
        )

        message = paper.format_discord_message()
        assert "et al." in message
        assert "10 authors" in message
