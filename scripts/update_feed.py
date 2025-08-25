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
        except Exception as e:
            logger.error(f"Error saving archive: {e}")
    
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
        
        logger.info(f"{PROJECT_CONFIG['name']} aggregation completed successfully")

def main():
    """Main entry point."""
    aggregator = BletaNewsAggregator()
    aggregator.run()

if __name__ == "__main__":
    main()
