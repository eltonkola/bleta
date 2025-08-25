# Bleta - Albanian News Archive
# Configuration file for the Albanian news aggregator

import os
from datetime import datetime

# Project configuration
PROJECT_CONFIG = {
    "name": "Bleta",
    "description": "Albanian News Archive with AI Summaries",
    "version": "1.0.0",
    "language": "sq"
}

# Albanian news sources
ALBANIAN_NEWS_SOURCES = [
    {
        "name": "Top Channel",
        "url": "https://top-channel.tv/feed/",
        "language": "sq",
        "enabled": True
    },
    {
        "name": "Koha.net",
        "url": "https://www.koha.net/rss/",
        "language": "sq",
        "enabled": True
    },
    {
        "name": "Shqip.com",
        "url": "https://www.shqip.com/rss/",
        "language": "sq",
        "enabled": True
    },
    {
        "name": "BalkanWeb",
        "url": "https://www.balkanweb.com/feed/",
        "language": "sq",
        "enabled": True
    },
    {
        "name": "Gazeta Express",
        "url": "https://www.gazetaexpress.com/feed/",
        "language": "sq",
        "enabled": True
    },
    {
        "name": "Telegrafi",
        "url": "https://telegrafi.com/feed/",
        "language": "sq",
        "enabled": True
    },
    {
        "name": "Albanian Daily News",
        "url": "https://albaniandailynews.com/feed/",
        "language": "en",
        "enabled": True
    },
    {
        "name": "Exit.al",
        "url": "https://exit.al/feed/",
        "language": "en",
        "enabled": False
    }
]

# AI configuration
AI_CONFIG = {
    "gemini_model": "gemini-1.5-flash",  # Fast and free model from Google with large context
    "max_tokens": 150,
    "temperature": 0.3,
    "summary_prompt_template": "Summarize the following Albanian news article in 1-2 concise sentences, in {language}, keeping key facts: {text}",
    "system_prompt": "You are a helpful assistant that summarizes news articles in Albanian."
}

# RSS configuration
RSS_CONFIG = {
    "max_articles_per_source": 10,
    "max_total_articles": 50,
    "feed_title": "Bleta - Albanian News Archive",
    "feed_description": "AI-summarized Albanian news from multiple sources",
    "feed_language": "sq",
    "feed_link": "https://eltonkola.github.io/bleta/",
    "feed_author": "Bleta News Aggregator"
}

# Website configuration
WEBSITE_CONFIG = {
    "title": "Bleta - Albanian News Archive",
    "description": "Daily Albanian news with AI summaries",
    "author": "Bleta News Aggregator",
    "language": "sq",
    "charset": "utf-8",
    "viewport": "width=device-width, initial-scale=1.0"
}

# File paths
PATHS = {
    "data_dir": "data",
    "archive_dir": "data/archive",
    "processed_file": "data/processed.json",
    "output_dir": "public",
    "rss_output": "public/feed.xml",
    "html_output": "public/index.html",
    "webapp_dir": "webapp"
}

# HTTP configuration
HTTP_CONFIG = {
    "timeout": 30,
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "request_delay": 1  # seconds between requests
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

def get_enabled_sources():
    """Get list of enabled news sources"""
    return [source for source in ALBANIAN_NEWS_SOURCES if source.get("enabled", True)]

def get_archive_filename(date_obj=None):
    """Generate archive filename for a given date"""
    if date_obj is None:
        date_obj = datetime.now()
    return f"{date_obj.strftime('%Y-%m-%d')}.json"

def get_archive_path(date_obj=None):
    """Get full path for archive file"""
    filename = get_archive_filename(date_obj)
    return os.path.join(PATHS["archive_dir"], filename)
