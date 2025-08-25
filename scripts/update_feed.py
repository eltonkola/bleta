#!/usr/bin/env python3
"""
Bleta - Albanian News Archive
Main script for fetching, processing, and archiving Albanian news with AI summaries.
"""

import os
import json
import logging
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import google.generativeai as genai
from bs4 import BeautifulSoup
import time
import sys
import os

# Add parent directory to Python path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config import (
    PROJECT_CONFIG, ALBANIAN_NEWS_SOURCES, AI_CONFIG, RSS_CONFIG, 
    WEBSITE_CONFIG, PATHS, HTTP_CONFIG, LOGGING_CONFIG,
    get_enabled_sources, get_archive_path
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"]
)
logger = logging.getLogger(__name__)

class BletaNewsAggregator:
    """Main class for Bleta news aggregation and archiving."""
    
    def __init__(self):
        """Initialize the news aggregator."""
        self.processed_file = PATHS["processed_file"]
        self.archive_dir = PATHS["archive_dir"]
        self.output_dir = PATHS["output_dir"]
        
        # Ensure directories exist
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.processed_file), exist_ok=True)
        
        # Initialize AI client
        self._init_ai_client()
        
        # Load processed articles for deduplication
        self.processed_articles = self._load_processed_articles()
        
    def _init_ai_client(self):
        """Initialize the AI client for summarization."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found. AI summarization will be disabled.")
            self.ai_client = None
            return
            
        try:
            genai.configure(api_key=api_key)
            self.ai_client = genai.GenerativeModel(AI_CONFIG["gemini_model"])
            logger.info(f"AI client initialized with model: {AI_CONFIG['gemini_model']}")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            self.ai_client = None
    
    def _load_processed_articles(self) -> Dict[str, Any]:
        """Load processed articles from JSON file."""
        if os.path.exists(self.processed_file):
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading processed articles: {e}")
        
        return {"processed_ids": [], "last_updated": datetime.now().isoformat()}
    
    def _save_processed_articles(self):
        """Save processed articles to JSON file."""
        self.processed_articles["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_articles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed articles: {e}")
    
    def _generate_article_id(self, article: Dict[str, Any]) -> str:
        """Generate a unique ID for an article."""
        # Use URL as primary identifier, fallback to title + published date
        if article.get('link'):
            return article['link']
        elif article.get('title') and article.get('published'):
            return f"{article['title']}_{article['published']}"
        else:
            return f"{article.get('title', 'unknown')}_{datetime.now().isoformat()}"
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Parse HTML and extract text
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Basic cleaning
        text = text.strip()
        text = ' '.join(text.split())  # Normalize whitespace
        
        return text
    
    def _summarize_with_gemini(self, text: str, language: str = "sq") -> str:
        """Summarize text using Google Gemini AI."""
        if not self.ai_client or not text:
            return text[:200] + "..." if len(text) > 200 else text
        
        try:
            prompt = AI_CONFIG["summary_prompt_template"].format(
                language=language, 
                text=text[:4000]  # Limit input length
            )
            
            response = self.ai_client.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return text[:200] + "..." if len(text) > 200 else text
                
        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            return text[:200] + "..." if len(text) > 200 else text
    
    def _fetch_rss_feed(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed from a news source."""
        articles = []
        
        try:
            logger.info(f"Fetching RSS from: {source['name']} ({source['url']})")
            
            response = requests.get(
                source['url'], 
                headers=HTTP_CONFIG["headers"],
                timeout=HTTP_CONFIG["timeout"]
            )
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:RSS_CONFIG["max_articles_per_source"]]:
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('description', ''),
                    'published': entry.get('published', ''),
                    'source': source['name'],
                    'source_url': source['url'],
                    'language': source['language'],
                    'guid': entry.get('id', entry.get('link', '')),
                    'fetched_at': datetime.now().isoformat()
                }
                
                # Clean text content
                article['title'] = self._clean_text(article['title'])
                article['description'] = self._clean_text(article['description'])
                
                articles.append(article)
                
            logger.info(f"Fetched {len(articles)} articles from {source['name']}")
            
        except Exception as e:
            logger.error(f"Error fetching RSS from {source['name']}: {e}")
        
        return articles
    
    def _process_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process articles: deduplicate, summarize, and filter."""
        processed_articles = []
        processed_ids = set(self.processed_articles.get("processed_ids", []))
        
        for article in articles:
            article_id = self._generate_article_id(article)
            
            # Skip if already processed
            if article_id in processed_ids:
                continue
            
            # Add AI summary
            if article.get('description'):
                article['ai_summary'] = self._summarize_with_gemini(
                    article['description'], 
                    article.get('language', 'sq')
                )
            else:
                article['ai_summary'] = self._summarize_with_gemini(
                    article['title'], 
                    article.get('language', 'sq')
                )
            
            # Add to processed list
            processed_articles.append(article)
            processed_ids.add(article_id)
        
        # Update processed articles
        self.processed_articles["processed_ids"] = list(processed_ids)
        
        return processed_articles
    
    def _save_daily_archive(self, articles: List[Dict[str, Any]]):
        """Save articles to daily JSON archive file."""
        if not articles:
            logger.info("No new articles to archive")
            return
        
        today = datetime.now()
        archive_path = get_archive_path(today)
        
        archive_data = {
            "date": today.strftime("%Y-%m-%d"),
            "timestamp": today.isoformat(),
            "project": PROJECT_CONFIG,
            "articles": articles,
            "total_articles": len(articles),
            "sources": [article['source'] for article in articles]
        }
        
        try:
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(articles)} articles to {archive_path}")
            
            # Also save to public directory for GitHub Pages
            public_archive_path = os.path.join(self.output_dir, "archive", f"{today.strftime('%Y-%m-%d')}.json")
            os.makedirs(os.path.dirname(public_archive_path), exist_ok=True)
            with open(public_archive_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(articles)} articles to {public_archive_path}")
            
            # Generate static HTML page for today only (as index.html)
            self._generate_today_html_page(archive_data, today)
            
            # Generate RSS feed with latest news
            self._generate_rss_feed(articles)
            
        except Exception as e:
            logger.error(f"Error saving archive: {e}")
    
    def _generate_today_html_page(self, archive_data: Dict[str, Any], date_obj: datetime):
        """Generate a static HTML page for today's news as index.html."""
        html_template = """
<!DOCTYPE html>
<html lang="sq">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bleta - Albanian News Archive</title>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }

        /* Header */
        .header {
            background: linear-gradient(135deg, #1a1a1a 0%, #2c2c2c 100%);
            color: white;
            padding: 15px 0;
            border-bottom: 4px solid #d4af37;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: bold;
            font-family: 'Times New Roman', serif;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1rem;
            opacity: 0.9;
            margin-top: 5px;
        }

        .header-date {
            text-align: right;
            font-size: 0.9rem;
            opacity: 0.8;
        }

        /* Navigation */
        .nav {
            background: #2c2c2c;
            padding: 10px 0;
            border-bottom: 1px solid #444;
        }

        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .nav-controls {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .nav-button {
            padding: 8px 16px;
            background: #d4af37;
            color: #1a1a1a;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            transition: background 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .nav-button:hover {
            background: #f0c040;
        }

        /* Main Content */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Newspaper Layout */
        .newspaper {
            background: white;
            box-shadow: 0 5px 25px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        .newspaper-header {
            background: linear-gradient(135deg, #1a1a1a 0%, #2c2c2c 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-bottom: 3px solid #d4af37;
        }

        .newspaper-title {
            font-size: 3.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            font-family: 'Times New Roman', serif;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .newspaper-subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 15px;
        }

        .newspaper-date {
            font-size: 1.1rem;
            color: #d4af37;
            font-weight: bold;
        }

        /* Articles Grid */
        .articles-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 0;
            min-height: 600px;
        }

        .main-content {
            padding: 30px;
            border-right: 1px solid #eee;
        }

        .sidebar {
            padding: 30px;
            background: #f8f9fa;
        }

        /* Article Styles */
        .article {
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 1px solid #eee;
        }

        .article:last-child {
            border-bottom: none;
        }

        .article.featured {
            border-bottom: 3px solid #d4af37;
            padding-bottom: 30px;
            margin-bottom: 40px;
        }

        .article-source {
            color: #d4af37;
            font-weight: bold;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .article-title {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 15px;
            line-height: 1.3;
            color: #1a1a1a;
        }

        .article.featured .article-title {
            font-size: 2.5rem;
        }

        .article-summary {
            font-size: 1.1rem;
            color: #555;
            margin-bottom: 20px;
            line-height: 1.7;
        }

        .article-meta {
            font-size: 0.85rem;
            color: #888;
            margin-bottom: 20px;
            padding: 10px 0;
            border-top: 1px solid #eee;
        }

        .article-link {
            display: inline-block;
            background: #1a1a1a;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            transition: background 0.3s ease;
            font-size: 0.9rem;
        }

        .article-link:hover {
            background: #333;
        }

        /* Sidebar Articles */
        .sidebar-article {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }

        .sidebar-article:last-child {
            border-bottom: none;
        }

        .sidebar-article .article-title {
            font-size: 1.3rem;
            margin-bottom: 10px;
        }

        .sidebar-article .article-summary {
            font-size: 0.95rem;
            margin-bottom: 15px;
        }

        /* Footer */
        .footer {
            background: #1a1a1a;
            color: white;
            text-align: center;
            padding: 30px 20px;
            margin-top: 40px;
        }

        .footer-content {
            max-width: 1400px;
            margin: 0 auto;
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            .articles-grid {
                grid-template-columns: 1fr;
            }
            
            .main-content {
                border-right: none;
                border-bottom: 1px solid #eee;
            }
        }

        @media (max-width: 768px) {
            .header-container {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }

            .header h1 {
                font-size: 2rem;
            }

            .nav-container {
                flex-direction: column;
                gap: 15px;
            }

            .nav-controls {
                flex-direction: column;
                width: 100%;
            }

            .newspaper-title {
                font-size: 2.5rem;
            }

            .article.featured .article-title {
                font-size: 1.8rem;
            }

            .article-title {
                font-size: 1.5rem;
            }

            .main-container {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-container">
            <div>
                <h1>🐝 BLETA</h1>
                <p>Albanian News Archive with AI Summaries</p>
            </div>
            <div class="header-date">{current_date}</div>
        </div>
    </div>

    <div class="nav">
        <div class="nav-container">
            <div class="nav-controls">
                <a href="webapp/" class="nav-button">Arkivi i Lajmeve</a>
                <a href="feed.xml" class="nav-button">RSS Feed</a>
            </div>
        </div>
    </div>

    <div class="main-container">
        <div class="newspaper">
            <div class="newspaper-header">
                <div class="newspaper-title">BLETA</div>
                <div class="newspaper-subtitle">Albanian News Archive</div>
                <div class="newspaper-date">{formatted_date} • {total_articles} artikuj</div>
            </div>
            <div class="articles-grid">
                <div class="main-content">
                    {featured_article}
                    {main_articles}
                </div>
                <div class="sidebar">
                    <h3 style="margin-bottom: 20px; color: #1a1a1a; border-bottom: 2px solid #d4af37; padding-bottom: 10px;">Lajme të tjera</h3>
                    {sidebar_articles}
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-content">
            <p>Powered by AI • Bleta News Archive • Albanian News with AI Summaries</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Format date strings
        date_str = date_obj.strftime("%Y-%m-%d")
        current_date = datetime.now().strftime("%A, %d %B %Y")
        
        # Format date for display
        date_obj_for_display = date_obj
        formatted_date = date_obj_for_display.strftime("%A, %d %B %Y")
        
        # Split articles
        articles = archive_data["articles"]
        if not articles:
            featured_article = '<div class="article"><h2>Nuk ka lajme për këtë datë</h2></div>'
            main_articles = ""
            sidebar_articles = ""
        else:
            featured_article = self._generate_article_html(articles[0], featured=True)
            regular_articles = articles[1:6]  # Next 5 articles
            sidebar_articles_list = articles[6:]  # Rest for sidebar
            
            main_articles = "".join([self._generate_article_html(article) for article in regular_articles])
            sidebar_articles = "".join([self._generate_sidebar_article_html(article) for article in sidebar_articles_list])
        
        # Generate HTML
        html_content = html_template.format(
            date=date_str,
            current_date=current_date,
            formatted_date=formatted_date,
            total_articles=len(articles),
            featured_article=featured_article,
            main_articles=main_articles,
            sidebar_articles=sidebar_articles
        )
        
        # Save as index.html
        html_path = os.path.join(self.output_dir, "index.html")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated today's HTML page: {html_path}")
    
    def _generate_rss_feed(self, articles: List[Dict[str, Any]]):
        """Generate RSS feed with the latest news."""
        try:
            from feedgen.feed import FeedGenerator
            
            fg = FeedGenerator()
            fg.title(RSS_CONFIG["feed_title"])
            fg.description(RSS_CONFIG["feed_description"])
            fg.language(RSS_CONFIG["feed_language"])
            fg.link(href=RSS_CONFIG["feed_link"])
            fg.author(name=RSS_CONFIG["feed_author"])
            fg.lastBuildDate(datetime.now())
            
            # Add articles to feed
            for article in articles[:RSS_CONFIG["max_total_articles"]]:
                fe = fg.add_entry()
                fe.title(article['title'])
                fe.description(article.get('ai_summary', article.get('description', '')))
                fe.link(href=article['link'])
                fe.author(name=article['source'])
                
                # Parse and set publication date
                if article.get('published'):
                    try:
                        pub_date = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
                        fe.published(pub_date)
                    except:
                        fe.published(datetime.now())
                else:
                    fe.published(datetime.now())
                
                fe.id(article.get('guid', article['link']))
            
            # Save RSS feed
            rss_path = os.path.join(self.output_dir, "feed.xml")
            fg.rss_file(rss_path)
            
            logger.info(f"Generated RSS feed: {rss_path}")
            
        except ImportError:
            logger.warning("feedgen not available, skipping RSS feed generation")
        except Exception as e:
            logger.error(f"Error generating RSS feed: {e}")
    
    def _generate_favicon(self):
        """Generate favicon from SVG."""
        try:
            from scripts.generate_favicon import create_ico_from_svg
            create_ico_from_svg()
            logger.info("Generated favicon.ico")
        except Exception as e:
            logger.warning(f"Could not generate favicon: {e}")
    
    def _generate_article_html(self, article: Dict[str, Any], featured: bool = False) -> str:
        """Generate HTML for a single article."""
        featured_class = " featured" if featured else ""
        
        return f"""
        <div class="article{featured_class}">
            <div class="article-source">{article['source']}</div>
            <h2 class="article-title">{article['title']}</h2>
            <div class="article-summary">{article.get('ai_summary', article.get('description', ''))}</div>
            <div class="article-meta">
                <strong>Burimi:</strong> {article['source']} | 
                <strong>Gjuha:</strong> {article['language']} |
                <strong>Koha:</strong> {self._format_time(article.get('published', ''))}
            </div>
            <a href="{article['link']}" class="article-link" target="_blank">Lexo më shumë</a>
        </div>
        """
    
    def _generate_sidebar_article_html(self, article: Dict[str, Any]) -> str:
        """Generate HTML for a sidebar article."""
        return f"""
        <div class="sidebar-article">
            <div class="article-source">{article['source']}</div>
            <h3 class="article-title">{article['title']}</h3>
            <div class="article-summary">{article.get('ai_summary', article.get('description', ''))}</div>
            <div class="article-meta">
                <strong>Koha:</strong> {self._format_time(article.get('published', ''))}
            </div>
            <a href="{article['link']}" class="article-link" target="_blank">Lexo më shumë</a>
        </div>
        """
    
    def _format_time(self, time_string: str) -> str:
        """Format time string for display."""
        if not time_string:
            return 'E panjohur'
        
        try:
            date = datetime.fromisoformat(time_string.replace('Z', '+00:00'))
            return date.strftime("%d/%m/%Y %H:%M")
        except:
            return time_string
    
    def run(self):
        """Main execution method."""
        logger.info(f"Starting {PROJECT_CONFIG['name']} news aggregation")
        
        # Fetch articles from all enabled sources
        all_articles = []
        enabled_sources = get_enabled_sources()
        
        for source in enabled_sources:
            articles = self._fetch_rss_feed(source)
            all_articles.extend(articles)
            
            # Respect rate limiting
            time.sleep(HTTP_CONFIG["request_delay"])
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        
        # Process articles
        processed_articles = self._process_articles(all_articles)
        logger.info(f"New articles processed: {len(processed_articles)}")
        
        # Save to daily archive
        self._save_daily_archive(processed_articles)
        
        # Save processed articles for deduplication
        self._save_processed_articles()
        
        # Generate favicon
        self._generate_favicon()
        
        logger.info(f"{PROJECT_CONFIG['name']} aggregation completed successfully")

def main():
    """Main entry point."""
    aggregator = BletaNewsAggregator()
    aggregator.run()

if __name__ == "__main__":
    main()
