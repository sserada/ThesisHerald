# ThesisHerald

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/badge/Discord-Bot-7289DA.svg)](https://discord.com/)

A Discord bot for automated research paper collection, notification, and analysis using arXiv API and LLM integration.

## 🎬 Demo

https://github.com/user-attachments/assets/b0698b26-ebc5-47e7-b512-0723a7b352ee

## ✨ Features

### 📚 Paper Discovery & Notifications
- **Automated Daily Notifications**: Fetches new papers from arXiv based on configured categories and posts them to Discord
- **Search by Category**: Use `/search` command to find papers in specific arXiv categories (e.g., cs.AI, cs.LG)
- **Keyword Search**: Use `/keywords` command to search papers by keywords
- **Manual Trigger**: Use `/daily` command to manually trigger the daily paper notification
- **Scheduled Tasks**: Configurable daily notifications at specified times
- **Thread-Based Display**: Search results organized in Discord threads for clean channel management

### 🤖 AI-Powered Features
- **Conversational Search**: Ask natural language questions using `/ask` command
- **Paper Summarization**: Generate AI-powered summaries with `/summarize` command
  - Support for 7+ languages (English, Japanese, Chinese, Korean, Spanish, French, German)
  - Key contributions and findings extracted automatically
  - Thread-based display for organized reading
- **LLM Integration**: Powered by Anthropic Claude for intelligent paper recommendations
- **Web Search Tool**: LLM can search the web for real-time research information
- **arXiv Integration**: LLM can directly search and retrieve papers from arXiv
- **Context-Aware Responses**: Get relevant papers with AI-generated insights

### 🌍 Translation & Accessibility
- **Abstract Translation**: Optional translation of paper abstracts to your preferred language
- **Full Abstract Display**: Complete abstracts shown without truncation
- **Multi-Language Support**: Supports Japanese, Korean, Chinese, Spanish, French, German, and more
- **Configurable**: Enable/disable translation via environment variables

## Installation

### Prerequisites
- Python >= 3.11
- [Rye](https://rye-up.com/) package manager
- Discord Bot Token
- Discord Server with appropriate permissions
- Anthropic API Key (for Phase 2 LLM features)

### Discord Bot Setup

⚠️ **Important:** Before running the bot, you must enable Privileged Gateway Intents in the Discord Developer Portal.

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to the "Bot" section
4. Scroll down to "Privileged Gateway Intents"
5. Enable the following intents:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent** (Required)
6. Click "Save Changes"

**Without these intents enabled, the bot will fail to start with a `PrivilegedIntentsRequired` error.**

For detailed setup instructions, see [Deployment Guide](docs/deployment.md#discord-bot-setup).

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

   # Optional - Basic Configuration
   NOTIFICATION_TIME=09:00
   ARXIV_CATEGORIES=cs.AI,cs.LG,cs.CL
   ARXIV_MAX_RESULTS=10

   # Optional - AI Features (Phase 2)
   ANTHROPIC_API_KEY=your_anthropic_api_key
   LLM_MODEL=claude-3-5-sonnet-20241022
   LLM_MAX_TOKENS=4096

   # Optional - Translation
   ENABLE_TRANSLATION=false
   TRANSLATION_TARGET_LANG=ja
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
  - Results are displayed in a dedicated thread for organization
- `/keywords <keywords> [max_results]` - Search papers by keywords
  - Example: `/keywords machine learning, neural networks 10`
  - Comma-separated keywords supported
  - Results organized in threads
- `/daily` - Manually trigger daily paper notification
  - Creates a thread with today's papers

**AI-Powered Commands:**
- `/ask <question>` - Ask a natural language question and get AI-powered paper recommendations
  - Example: `/ask What are the latest breakthroughs in transformer architectures?`
  - Example: `/ask Can you find recent papers about multimodal learning?`
  - Example: `/ask What are the current trends in quantum computing research?`
  - The AI will search both web and arXiv to provide contextual answers with relevant papers
  - Requires `ANTHROPIC_API_KEY` to be configured

- `/summarize <arxiv_input> [language]` - Generate AI-powered summary of a research paper
  - Example: `/summarize 2010.11929` (English summary)
  - Example: `/summarize https://arxiv.org/abs/2010.11929 language:ja` (Japanese summary)
  - Example: `/summarize https://arxiv.org/pdf/2010.11929.pdf language:zh` (Chinese summary)
  - Supports multiple input formats: arXiv ID, abstract URL, PDF URL
  - Supported languages: en, ja, zh, ko, es, fr, de (default: en)
  - Summary includes main contributions and key findings
  - Results displayed in organized thread
  - Requires `ANTHROPIC_API_KEY` to be configured

### Thread-Based Results

All search commands create dedicated threads to keep your channel organized:
- Main channel shows only the summary message
- Full results are posted in the thread
- Thread names include the search query and paper count
- Threads auto-archive after 24 hours

<!-- Add screenshot of thread-based results here -->

### Configuration

Edit your `.env` file to customize:

**Basic Settings:**
- **NOTIFICATION_TIME**: Time for daily notifications (HH:MM format, default: 09:00)
- **ARXIV_CATEGORIES**: Comma-separated list of arXiv categories to monitor
- **ARXIV_MAX_RESULTS**: Maximum number of papers to fetch per notification (default: 10)

**Translation Settings:**
- **ENABLE_TRANSLATION**: Enable abstract translation (true/false, default: false)
- **TRANSLATION_TARGET_LANG**: Target language code (ISO 639-1, default: ja)
  - Supported languages: ja (Japanese), ko (Korean), zh-CN (Chinese), es (Spanish), fr (French), de (German), and more

**AI Features:**
- **ANTHROPIC_API_KEY**: Your Anthropic API key (required for `/ask` and `/summarize` commands)
- **LLM_MODEL**: Claude model to use (default: claude-sonnet-4-5-20250929)
- **LLM_MAX_TOKENS**: Maximum tokens per response (default: 4096)

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

## 🔮 Future Enhancements

We're continuously improving ThesisHerald. Upcoming features include:

- **Weekly Digests**: Automated weekly summaries of important papers in your field
- **Paper Comparison**: Compare multiple papers side-by-side
- **Enhanced Filtering**: More advanced search and filtering options
- **Performance Monitoring**: Better logging and performance tracking

For detailed development plans, see [docs/plan.md](docs/plan.md).

## 💰 API Costs

**Anthropic Claude API** (for `/ask` and `/summarize` commands):
- Claude Sonnet 4.5: ~$3 per million input tokens, ~$15 per million output tokens
- Typical `/ask` query: 1000-3000 tokens (~$0.01-0.05 per query)
- Typical `/summarize` request: 500-2000 tokens (~$0.01-0.03 per summary)
- Monitor usage in your [Anthropic dashboard](https://console.anthropic.com/)
- Set API rate limits if needed to control costs

**Google Translate** (for abstract translation):
- Free via `deep-translator` library
- Rate limits may apply for heavy usage

## 🐛 Known Issues

- Two tests skipped due to asyncio.to_thread behavior with arxiv library
- Translation may fail for very long abstracts (automatically falls back to English)

## 📝 Changelog

### v1.1.0 (2025-10-14)
- ✨ Added `/summarize` command for AI-powered paper summaries
- ✨ Multi-language support for summaries (7+ languages)
- ✨ Thread-based summary display
- 🐛 Fixed Claude model name to correct version (claude-sonnet-4-5-20250929)
- 📝 Updated documentation with summarization features

### v1.0.0 (2025-10-14)
- ✨ Initial release
- ✅ Core features: Daily notifications, search, keywords
- ✅ AI-powered conversational search with LLM
- ✅ Thread-based result organization
- ✅ Abstract translation support
- ✅ Full abstract display without truncation
- ✅ Long message handling (2000+ characters)
