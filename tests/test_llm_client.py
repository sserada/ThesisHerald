"""Tests for LLM client."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from thesisherald.llm_client import LLMClient


class TestLLMClient:
    """Test cases for LLMClient."""

    def test_client_initialization(self) -> None:
        """Test that client initializes correctly."""
        client = LLMClient(api_key="test_key", model="claude-3-sonnet", max_tokens=1000)

        assert client.model == "claude-3-sonnet"
        assert client.max_tokens == 1000

    def test_web_search_tool_definition(self) -> None:
        """Test web search tool definition."""
        client = LLMClient(api_key="test_key")
        tool = client._web_search_tool_definition()

        assert tool["name"] == "web_search"
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["properties"]["query"]["type"] == "string"

    def test_arxiv_search_tool_definition(self) -> None:
        """Test arXiv search tool definition."""
        client = LLMClient(api_key="test_key")
        tool = client._arxiv_search_tool_definition()

        assert tool["name"] == "arxiv_search"
        assert "description" in tool
        assert "input_schema" in tool
        assert "query" in tool["input_schema"]["properties"]
        assert "categories" in tool["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_execute_web_search_with_results(self) -> None:
        """Test web search execution with results."""
        client = LLMClient(api_key="test_key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "AbstractText": "Test abstract about machine learning",
            "AbstractURL": "https://example.com/ml",
            "RelatedTopics": [
                {"Text": "Related topic 1"},
                {"Text": "Related topic 2"},
            ],
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await client._execute_web_search("machine learning")

            assert "Test abstract about machine learning" in result
            assert "https://example.com/ml" in result
            assert "Related topic 1" in result

    @pytest.mark.asyncio
    async def test_execute_web_search_no_results(self) -> None:
        """Test web search with no results."""
        client = LLMClient(api_key="test_key")

        mock_response = Mock()
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await client._execute_web_search("nonexistent query")

            assert result == "No results found."

    @pytest.mark.asyncio
    async def test_execute_web_search_error_handling(self) -> None:
        """Test web search error handling."""
        client = LLMClient(api_key="test_key")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Network error")
            mock_client_class.return_value = mock_client

            result = await client._execute_web_search("test query")

            assert "Error performing web search" in result
            assert "Network error" in result

    async def test_execute_arxiv_search(self) -> None:
        """Test arXiv search execution."""
        client = LLMClient(api_key="test_key")

        with patch.object(client.arxiv_client, "search_by_keywords") as mock_search:
            from datetime import datetime

            from thesisherald.arxiv_client import Paper

            mock_papers = [
                Paper(
                    title="Test Paper 1",
                    authors=["Author 1", "Author 2"],
                    summary="This is a test summary for paper 1.",
                    arxiv_id="2023.12345",
                    pdf_url="https://arxiv.org/pdf/2023.12345",
                    published=datetime(2023, 1, 1),
                    updated=datetime(2023, 1, 1),
                    categories=["cs.AI"],
                    primary_category="cs.AI",
                ),
            ]
            mock_search.return_value = mock_papers

            result = await client._execute_arxiv_search("machine learning", max_results=5)

            assert "Found 1 papers" in result
            assert "Test Paper 1" in result
            assert "Author 1" in result
            assert "2023.12345" in result

    async def test_execute_arxiv_search_no_results(self) -> None:
        """Test arXiv search with no results."""
        client = LLMClient(api_key="test_key")

        with patch.object(client.arxiv_client, "search_by_keywords") as mock_search:
            mock_search.return_value = []

            result = await client._execute_arxiv_search("nonexistent topic")

            assert "No papers found" in result

    async def test_execute_arxiv_search_error_handling(self) -> None:
        """Test arXiv search error handling."""
        client = LLMClient(api_key="test_key")

        with patch.object(client.arxiv_client, "search_by_keywords") as mock_search:
            mock_search.side_effect = Exception("API error")

            result = await client._execute_arxiv_search("test query")

            assert "Error searching arXiv" in result
            assert "API error" in result
