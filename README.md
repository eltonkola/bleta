# 🐝 Bleta - Albanian News Archive

A comprehensive Albanian news aggregator that collects RSS feeds from multiple sources, summarizes articles using AI, and provides a beautiful newspaper-style web interface to browse archived news by date.

## Features

- **📰 Daily News Archiving**: Saves all collected news as JSON files organized by date
- **🤖 AI Summarization**: Uses Google Gemini AI to create concise summaries of articles
- **📱 Newspaper-Style Web App**: Beautiful, responsive interface to browse news by date
- **🔄 Automated Updates**: Runs every 2 hours via GitHub Actions
- **📊 Multiple Sources**: Aggregates news from major Albanian media outlets
- **🌐 GitHub Pages Hosting**: Automatically deployed and accessible online

## Project Structure

```
Bleta/
├── data/
│   ├── archive/           # Daily JSON files (YYYY-MM-DD.json)
│   └── processed.json     # Deduplication tracking
├── scripts/
│   ├── update_feed.py     # Main aggregation script
│   └── test_feed.py       # RSS feed testing
├── webapp/
│   └── index.html         # Newspaper-style web interface
├── config.py              # Centralized configuration
├── requirements.txt       # Python dependencies
└── .github/workflows/     # GitHub Actions automation
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key
- Git

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Bleta.git
   cd Bleta
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key**
   ```bash
   # Create .env file
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```

4. **Run the aggregator**
   ```bash
   python scripts/update_feed.py
   ```

5. **Open the web app**
   ```bash
   # Open webapp/index.html in your browser
   # Or serve it with a local server:
   python -m http.server 8000
   # Then visit http://localhost:8000/webapp/
   ```

## 🐝 Features

- **AI-Powered Summaries**: Uses Google Gemini AI to summarize news articles
- **Daily Archives**: JSON-based archive system for efficient storage
- **Static HTML**: Fast-loading static pages for today's news
- **RSS Feed**: Subscribe to latest news updates
- **Responsive Design**: Works on desktop and mobile devices
- **Bee Favicon**: Custom bee-themed favicon for brand identity

## GitHub Pages Setup

1. **Enable GitHub Pages**
   - Go to your repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: / (root)

2. **Add API Key Secret**
   - Go to Settings → Secrets and variables → Actions
   - Add new repository secret: `GOOGLE_API_KEY`

3. **Run the Workflow**
   - Go to Actions tab
   - Run "Update Bleta News Archive" workflow manually

## Configuration

### News Sources

Edit `config.py` to add or modify news sources:

```python
ALBANIAN_NEWS_SOURCES = [
    {
        "name": "Top Channel",
        "url": "https://top-channel.tv/feed/",
        "language": "sq",
        "enabled": True
    },
    # Add more sources...
]
```

### AI Settings

Configure AI summarization in `config.py`:

```python
AI_CONFIG = {
    "gemini_model": "gemini-1.5-flash",
    "max_tokens": 150,
    "temperature": 0.3,
    "summary_prompt_template": "Summarize the following Albanian news article in 1-2 concise sentences, in {language}, keeping key facts: {text}"
}
```

## Web App Features

The newspaper-style web interface (`webapp/index.html`) provides:

- **📅 Date Selection**: Browse news from any archived date
- **📰 Newspaper Layout**: Clean, readable article presentation
- **🔍 Article Details**: Source, language, publication time
- **📱 Responsive Design**: Works on desktop and mobile
- **🌐 Albanian Interface**: Localized in Albanian

## Archive Structure

Daily news is saved in `data/archive/YYYY-MM-DD.json`:

```json
{
  "date": "2024-01-15",
  "timestamp": "2024-01-15T10:30:00",
  "project": {
    "name": "Bleta",
    "version": "1.0.0"
  },
  "articles": [
    {
      "title": "Article Title",
      "link": "https://source.com/article",
      "description": "Original description",
      "ai_summary": "AI-generated summary",
      "source": "Source Name",
      "language": "sq",
      "published": "2024-01-15T09:00:00",
      "fetched_at": "2024-01-15T10:30:00"
    }
  ],
  "total_articles": 25,
  "sources": ["Top Channel", "Koha.net", "Shqip.com"]
}
```

## Dependencies

- `feedparser`: RSS feed parsing
- `requests`: HTTP requests
- `google-generativeai`: Google Gemini AI integration
- `beautifulsoup4`: HTML parsing and cleaning
- `lxml`: XML/HTML processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the [Actions tab](https://github.com/your-username/Bleta/actions) for workflow status
- Review the logs for error details

---

**Bleta** - Keeping Albanian news organized and accessible with AI-powered insights. 🐝📰
