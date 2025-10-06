"""LLM client for conversational search and paper analysis."""

import logging
from typing import Any

import httpx
from anthropic import Anthropic
from anthropic.types import Message, TextBlock, ToolUseBlock

from thesisherald.arxiv_client import ArxivClient

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM APIs (Anthropic Claude)."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ) -> None:
        """Initialize LLM client."""
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.arxiv_client = ArxivClient()

    def _web_search_tool_definition(self) -> dict[str, Any]:
        """Define web search tool for LLM."""
        return {
            "name": "web_search",
            "description": (
                "Search the web for current information about research papers, "
                "topics, or trends. Use this when you need up-to-date information "
                "or want to find research papers on a specific topic."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information",
                    }
                },
                "required": ["query"],
            },
        }

    def _arxiv_search_tool_definition(self) -> dict[str, Any]:
        """Define arXiv search tool for LLM."""
        return {
            "name": "arxiv_search",
            "description": (
                "Search for research papers on arXiv by category or keywords. "
                "Returns paper titles, authors, abstracts, and PDF links."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords or topic to search for",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional arXiv categories to filter by (e.g., cs.AI, cs.LG)"
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of papers to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }

    async def _execute_web_search(self, query: str) -> str:
        """Execute web search using a search API."""
        # Simple web search implementation using DuckDuckGo API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json"},
                    timeout=10.0,
                )
                data = response.json()

                results = []
                if data.get("AbstractText"):
                    results.append(f"Summary: {data['AbstractText']}")
                if data.get("AbstractURL"):
                    results.append(f"Source: {data['AbstractURL']}")

                # Add related topics
                if data.get("RelatedTopics"):
                    topics = data["RelatedTopics"][:3]
                    for topic in topics:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append(f"- {topic['Text']}")

                return "\n".join(results) if results else "No results found."

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Error performing web search: {str(e)}"

    def _execute_arxiv_search(
        self, query: str, categories: list[str] | None = None, max_results: int = 5
    ) -> str:
        """Execute arXiv search."""
        try:
            keywords = [kw.strip() for kw in query.split(",")]
            papers = self.arxiv_client.search_by_keywords(
                keywords=keywords,
                categories=categories,
                max_results=max_results,
            )

            if not papers:
                return "No papers found for the given query."

            results = [f"Found {len(papers)} papers:\n"]
            for i, paper in enumerate(papers, 1):
                results.append(
                    f"\n{i}. **{paper.title}**\n"
                    f"   Authors: {', '.join(paper.authors[:3])}"
                    f"{' et al.' if len(paper.authors) > 3 else ''}\n"
                    f"   Published: {paper.published.strftime('%Y-%m-%d')}\n"
                    f"   arXiv: {paper.arxiv_id}\n"
                    f"   PDF: {paper.pdf_url}\n"
                    f"   Summary: {paper.summary[:200]}..."
                )

            return "\n".join(results)

        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return f"Error searching arXiv: {str(e)}"

    async def conversational_search(self, user_query: str) -> str:
        """
        Perform conversational search using LLM with tool calling.

        Args:
            user_query: Natural language query from user

        Returns:
            LLM response with paper recommendations
        """
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": user_query,
            }
        ]

        tools = [
            self._web_search_tool_definition(),
            self._arxiv_search_tool_definition(),
        ]

        # Iterative tool use loop
        max_iterations = 5
        for _ in range(max_iterations):
            try:
                response: Message = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=messages,  # type: ignore[arg-type]
                    tools=tools,  # type: ignore[arg-type]
                )

                # Check if we need to execute tools
                if response.stop_reason == "tool_use":
                    # Add assistant response to messages
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.content,
                        }
                    )

                    # Execute all tool calls
                    tool_results = []
                    for block in response.content:
                        if isinstance(block, ToolUseBlock):
                            tool_name = block.name
                            tool_input = block.input

                            logger.info(
                                f"Executing tool: {tool_name} with input: {tool_input}"
                            )

                            # Execute the tool
                            if tool_name == "web_search":
                                result = await self._execute_web_search(
                                    tool_input["query"]  # type: ignore[index]
                                )
                            elif tool_name == "arxiv_search":
                                result = self._execute_arxiv_search(
                                    query=tool_input["query"],  # type: ignore[index]
                                    categories=tool_input.get("categories"),  # type: ignore[attr-defined]
                                    max_results=tool_input.get("max_results", 5),  # type: ignore[attr-defined]
                                )
                            else:
                                result = f"Unknown tool: {tool_name}"

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result,
                                }
                            )

                    # Add tool results to messages
                    messages.append({"role": "user", "content": tool_results})

                elif response.stop_reason == "end_turn":
                    # Extract final text response
                    text_content = []
                    for block in response.content:
                        if isinstance(block, TextBlock):
                            text_content.append(block.text)

                    return "\n".join(text_content)

                else:
                    logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                    return "Unable to complete the request."

            except Exception as e:
                logger.exception(f"Error in conversational search: {e}")
                return f"An error occurred: {str(e)}"

        return "Maximum iterations reached. Please try a simpler query."
