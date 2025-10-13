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

    async def _execute_arxiv_search(
        self, query: str, categories: list[str] | None = None, max_results: int = 5
    ) -> str:
        """Execute arXiv search."""
        try:
            keywords = [kw.strip() for kw in query.split(",")]
            papers = await self.arxiv_client.search_by_keywords(
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
                                result = await self._execute_arxiv_search(
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

    async def summarize_paper(self, paper: Any, language: str = "en") -> str:
        """Generate an AI-powered summary of a research paper.

        Args:
            paper: Paper object with title, authors, abstract, etc.
            language: Target language for the summary (e.g., 'en', 'ja', 'zh', 'ko')

        Returns:
            Formatted summary with key points
        """
        # Language-specific instructions
        language_instructions = {
            "en": "in English",
            "ja": "in Japanese (日本語)",
            "zh": "in Chinese (中文)",
            "ko": "in Korean (한국어)",
            "es": "in Spanish (Español)",
            "fr": "in French (Français)",
            "de": "in German (Deutsch)",
        }

        lang_instruction = language_instructions.get(
            language.lower(), f"in {language}"
        )

        # Prepare paper information for the LLM
        paper_info = f"""
Title: {paper.title}
Authors: {', '.join(paper.authors[:5])}{'...' if len(paper.authors) > 5 else ''}
Published: {paper.published.strftime('%Y-%m-%d')}
arXiv ID: {paper.arxiv_id}
Categories: {', '.join(paper.categories)}

Abstract:
{paper.summary}
"""

        prompt = f"""You are a research paper analysis assistant. Please provide a concise \
summary of the following research paper {lang_instruction}.

{paper_info}

Please provide:
1. A brief summary (3-5 sentences) explaining the main contribution and findings
2. Key contributions as bullet points (3-5 points)

Format your response as:
**Summary:**
[Your 3-5 sentence summary]

**Key Contributions:**
• [Point 1]
• [Point 2]
• [Point 3]

Keep the language technical but accessible. Focus on the core innovation and results. \
Write your entire response {lang_instruction}."""

        try:
            response: Message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text content
            text_content = []
            for block in response.content:
                if isinstance(block, TextBlock):
                    text_content.append(block.text)

            summary = "\n".join(text_content)

            # Format final output
            result = f"""📄 **Paper Summary**

**Title:** {paper.title}
**Authors:** {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}
**Published:** {paper.published.strftime('%Y-%m-%d')}
**arXiv ID:** {paper.arxiv_id}
**PDF:** {paper.pdf_url}

{summary}
"""
            return result

        except Exception as e:
            logger.exception(f"Error generating paper summary: {e}")
            return f"❌ Failed to generate summary: {str(e)}"

    async def generate_weekly_digest(
        self, topic: str, language: str = "en", days: int = 7
    ) -> str:
        """Generate a weekly digest of important papers on a specific topic.

        Args:
            topic: Research topic to generate digest for
            language: Target language for the digest
            days: Number of days to look back for papers (default: 7)

        Returns:
            Formatted digest with topic overview and top papers
        """
        # Language-specific instructions
        language_instructions = {
            "en": "in English",
            "ja": "in Japanese (日本語)",
            "zh": "in Chinese (中文)",
            "ko": "in Korean (한국어)",
            "es": "in Spanish (Español)",
            "fr": "in French (Français)",
            "de": "in German (Deutsch)",
        }

        lang_instruction = language_instructions.get(
            language.lower(), f"in {language}"
        )

        try:
            # Search for recent papers on the topic
            papers = await self.arxiv_client.search_by_keywords(
                keywords=[topic],
                max_results=20,  # Get more papers for LLM to analyze
            )

            if not papers:
                return f"📭 No papers found for topic: **{topic}**"

            # Prepare papers information for LLM
            papers_info = []
            for i, paper in enumerate(papers[:20], 1):
                paper_info = f"""{i}. **{paper.title}**
   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}
   Published: {paper.published.strftime('%Y-%m-%d')}
   arXiv ID: {paper.arxiv_id}
   Categories: {', '.join(paper.categories[:3])}
   Abstract: {paper.summary[:300]}..."""
                papers_info.append(paper_info)

            papers_list = "\n\n".join(papers_info)

            prompt = f"""You are a research digest curator. Analyze the following recent papers \
on the topic "{topic}" and create a weekly digest {lang_instruction}.

RECENT PAPERS:
{papers_list}

Please provide:
1. **Topic Overview** (2-3 sentences): Current trends and developments in this field
2. **Top Papers** (5-7 papers): Select the most important/impactful papers and for each provide:
   - Paper number from the list (e.g., #3)
   - Brief summary (2-3 sentences)
   - Key contributions (2-3 bullet points)
   - Why it's important

Format your response as:
📊 **Weekly Digest: [Topic Name]**

**🔍 Topic Overview:**
[Your 2-3 sentence overview of current trends]

**📚 Top Papers:**

**#[number] - [Paper Title]**
**Summary:** [2-3 sentence summary]
**Key Contributions:**
• [Contribution 1]
• [Contribution 2]
**Why It Matters:** [1-2 sentences]
**Link:** https://arxiv.org/abs/[arxiv_id]

[Repeat for each top paper]

Focus on papers with novel contributions, practical impact, or significant advancement. \
Write your entire response {lang_instruction}."""

            response: Message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text content
            text_content = []
            for block in response.content:
                if isinstance(block, TextBlock):
                    text_content.append(block.text)

            digest = "\n".join(text_content)

            # Add metadata footer
            from datetime import datetime

            footer = f"\n\n---\n*Generated on {datetime.now().strftime('%Y-%m-%d')} \
| Analyzed {len(papers)} recent papers*"
            return digest + footer

        except Exception as e:
            logger.exception(f"Error generating weekly digest: {e}")
            return f"❌ Failed to generate digest for topic '{topic}': {str(e)}"
