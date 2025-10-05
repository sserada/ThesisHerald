# ThesisHerald

A Discord bot for automated research paper collection, notification, and analysis using arXiv API and LLM integration.

## Features

### Phase 1 (Current) ✅
- **Automated Daily Notifications**: Fetches new papers from arXiv based on configured categories and posts them to Discord
- **Search by Category**: Use `/search` command to find papers in specific arXiv categories (e.g., cs.AI, cs.LG)
- **Keyword Search**: Use `/keywords` command to search papers by keywords
- **Manual Trigger**: Use `/daily` command to manually trigger the daily paper notification
- **Scheduled Tasks**: Configurable daily notifications at specified times

### Upcoming Features
- **Phase 2**: LLM-powered conversational search using OpenAI/Claude API
- **Phase 3**: Paper summarization and automatic digest generation
- **Phase 4**: Production deployment and monitoring

## Installation

### Prerequisites
- Python >= 3.11
- [Rye](https://rye-up.com/) package manager
- Discord Bot Token
- Discord Server with appropriate permissions

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
   DISCORD_TOKEN=your_discord_bot_token
   NOTIFICATION_CHANNEL_ID=your_channel_id
   NOTIFICATION_TIME=09:00
   ARXIV_CATEGORIES=cs.AI,cs.LG,cs.CL
   ARXIV_MAX_RESULTS=10
   ```

4. **Run the bot**
   ```bash
   rye run python -m thesisherald.main
   ```

## Usage

### Discord Commands

- `/ping` - Check if the bot is responsive
- `/search <category> [max_results]` - Search papers by arXiv category
  - Example: `/search cs.AI 5`
- `/keywords <keywords> [max_results]` - Search papers by keywords
  - Example: `/keywords machine learning, neural networks 10`
- `/daily` - Manually trigger daily paper notification

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
- [ ] Phase 2: LLM integration for conversational search
- [ ] Phase 3: Paper summarization and digest generation
- [ ] Phase 4: Production deployment and monitoring
