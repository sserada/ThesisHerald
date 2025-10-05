# ThesisHerald

A Discord bot for automated research paper collection, notification, and analysis using arXiv API and LLM integration.

## Features

### Phase 1 ✅
- **Automated Daily Notifications**: Fetches new papers from arXiv based on configured categories and posts them to Discord
- **Search by Category**: Use `/search` command to find papers in specific arXiv categories (e.g., cs.AI, cs.LG)
- **Keyword Search**: Use `/keywords` command to search papers by keywords
- **Manual Trigger**: Use `/daily` command to manually trigger the daily paper notification
- **Scheduled Tasks**: Configurable daily notifications at specified times

### Phase 2 (Current) ✅
- **AI-Powered Conversational Search**: Ask natural language questions using `/ask` command
- **LLM Integration**: Powered by Anthropic Claude for intelligent paper recommendations
- **Web Search Tool**: LLM can search the web for real-time research information
- **arXiv Integration**: LLM can directly search and retrieve papers from arXiv
- **Context-Aware Responses**: Get relevant papers with AI-generated insights

### Upcoming Features
- **Phase 3**: Paper summarization and automatic digest generation
- **Phase 4**: Production deployment and monitoring

## Installation

### Prerequisites
- Python >= 3.11
- [Rye](https://rye-up.com/) package manager
- Discord Bot Token
- Discord Server with appropriate permissions
- Anthropic API Key (for Phase 2 LLM features)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sserada/ThesisHerald.git
   cd ThesisHerald
   ```

2. **Install dependencies**
   ```bash
   rye sync
   ```

3. **Configure environment variables**

   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   ```env
   # Required
   DISCORD_TOKEN=your_discord_bot_token
   NOTIFICATION_CHANNEL_ID=your_channel_id

   # Optional
   NOTIFICATION_TIME=09:00
   ARXIV_CATEGORIES=cs.AI,cs.LG,cs.CL
   ARXIV_MAX_RESULTS=10

   # Phase 2: LLM Features (Optional)
   ANTHROPIC_API_KEY=your_anthropic_api_key
   LLM_MODEL=claude-3-5-sonnet-20241022
   LLM_MAX_TOKENS=4096
   ```

4. **Run the bot**
   ```bash
   rye run python -m thesisherald.main
   ```

## Usage

### Discord Commands

**Basic Commands:**
- `/ping` - Check if the bot is responsive
- `/search <category> [max_results]` - Search papers by arXiv category
  - Example: `/search cs.AI 5`
- `/keywords <keywords> [max_results]` - Search papers by keywords
  - Example: `/keywords machine learning, neural networks 10`
- `/daily` - Manually trigger daily paper notification

**Phase 2: AI-Powered Commands:**
- `/ask <question>` - Ask a natural language question and get AI-powered paper recommendations
  - Example: `/ask What are the latest breakthroughs in transformer architectures?`
  - Example: `/ask Can you find recent papers about multimodal learning?`
  - Example: `/ask What are the current trends in quantum computing research?`
  - The AI will search both web and arXiv to provide contextual answers with relevant papers

### Configuration

Edit your `.env` file to customize:

- **NOTIFICATION_TIME**: Time for daily notifications (HH:MM format)
- **ARXIV_CATEGORIES**: Comma-separated list of arXiv categories to monitor
- **ARXIV_MAX_RESULTS**: Maximum number of papers to fetch per notification

### Supported arXiv Categories

Common categories:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CL` - Computation and Language
- `cs.CV` - Computer Vision
- `cs.RO` - Robotics
- See [arXiv Category Taxonomy](https://arxiv.org/category_taxonomy) for full list

## Development

### Project Structure

```
ThesisHerald/
├── src/thesisherald/
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── bot.py            # Discord bot implementation
│   ├── config.py         # Configuration management
│   ├── arxiv_client.py   # arXiv API client
│   └── scheduler.py      # Task scheduling
├── tests/
│   ├── test_arxiv_client.py
│   └── test_config.py
├── .env.example          # Example environment variables
├── pyproject.toml        # Project configuration
└── README.md
```

### Running Tests

```bash
rye run pytest
```

With coverage:
```bash
rye run pytest --cov=src/thesisherald --cov-report=html
```

### Code Quality

Format code:
```bash
rye run ruff format
```

Lint code:
```bash
rye run ruff check
```

Type check:
```bash
rye run mypy src/
```

## Contributing

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for detailed contribution guidelines.

## License

This project is open source and available under the MIT License.

## Roadmap

See [docs/plan.md](docs/plan.md) for the detailed development plan.

- [x] Phase 1: Basic notification and search functionality
- [x] Phase 2: LLM integration for conversational search
- [ ] Phase 3: Paper summarization and digest generation
- [ ] Phase 4: Production deployment and monitoring

## API Costs

Phase 2 uses Anthropic Claude API which incurs costs based on usage:
- Claude 3.5 Sonnet: ~$3 per million input tokens, ~$15 per million output tokens
- Typical `/ask` query: 1000-3000 tokens (~$0.01-0.05 per query)
- Monitor usage in your Anthropic dashboard
- Set API rate limits if needed to control costs
