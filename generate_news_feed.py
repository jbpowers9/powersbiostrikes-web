#!/usr/bin/env python3
"""
News Feed Generator for PowersBioStrikes Website
=================================================
Generates news.json with aggregated biotech news for:
1. All upcoming catalyst tickers (from calendar)
2. Current position tickers
3. Watchlist tickers

Run after catalyst_collector or on a schedule (e.g., every 4 hours).

Usage:
    python generate_news_feed.py
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'news.json')

# Database path (shared with scanner) - handle both Windows and WSL
import platform
if platform.system() == 'Windows':
    DB_PATH = r'C:\biotech-options-v2\biotech_options.db'
else:
    DB_PATH = '/mnt/c/biotech-options-v2/biotech_options.db'

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    print("WARNING: yfinance not installed. Run: pip install yfinance")
    YFINANCE_AVAILABLE = False


# ============================================================================
# NEWS CATEGORIZATION
# ============================================================================

FDA_KEYWORDS = [
    'fda', 'pdufa', 'approval', 'approved', 'nda', 'bla', 'snda', 'sbla',
    'complete response', 'crl', 'refuse to file', 'rtf', 'adcom', 'advisory committee',
    'breakthrough therapy', 'fast track', 'priority review', 'accelerated approval',
    'orphan drug', 'label expansion', 'supplemental', 'warning letter'
]

CLINICAL_KEYWORDS = [
    'phase 1', 'phase 2', 'phase 3', 'phase i', 'phase ii', 'phase iii',
    'pivotal', 'clinical trial', 'data readout', 'topline', 'top-line',
    'primary endpoint', 'secondary endpoint', 'efficacy', 'safety',
    'enrollment', 'enrolled', 'dosing', 'first patient', 'last patient',
    'interim analysis', 'futility', 'dsmb', 'data safety'
]

NEGATIVE_KEYWORDS = [
    'fail', 'failed', 'miss', 'missed', 'discontinue', 'terminated',
    'adverse', 'death', 'deaths', 'serious adverse', 'sae',
    'clinical hold', 'halted', 'suspended', 'negative', 'disappointing',
    'crl', 'complete response letter', 'refuse to file', 'rejection'
]

POSITIVE_KEYWORDS = [
    'approval', 'approved', 'positive', 'success', 'successful', 'met',
    'exceeded', 'breakthrough', 'accelerated', 'priority', 'fast track',
    'strong', 'robust', 'significant', 'favorable', 'encouraging'
]


def categorize_news(title: str, summary: str = "") -> Dict[str, Any]:
    """Categorize news based on keywords."""
    text = (title + " " + summary).lower()

    categories = []
    tags = []
    sentiment = 'neutral'
    priority = 0

    # Check FDA keywords
    fda_matches = [kw for kw in FDA_KEYWORDS if kw in text]
    if fda_matches:
        categories.append('fda')
        tags.extend(fda_matches[:3])
        priority += 3

    # Check clinical keywords
    clinical_matches = [kw for kw in CLINICAL_KEYWORDS if kw in text]
    if clinical_matches:
        categories.append('clinical')
        tags.extend(clinical_matches[:3])
        priority += 2

    # Determine sentiment
    positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

    if negative_count > positive_count:
        sentiment = 'negative'
        priority += 2
    elif positive_count > negative_count:
        sentiment = 'positive'
        priority += 1

    if not categories:
        categories.append('general')

    tags = list(dict.fromkeys(tags))[:5]

    return {
        'categories': categories,
        'tags': tags,
        'sentiment': sentiment,
        'priority': priority
    }


# ============================================================================
# DATA FETCHING
# ============================================================================

def get_calendar_tickers(days: int = 60) -> List[str]:
    """Get tickers from upcoming catalysts."""
    tickers = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        future = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT DISTINCT ticker FROM catalyst_research
            WHERE catalyst_date BETWEEN ? AND ?
            AND excluded = 0
            ORDER BY catalyst_date
        """, (today, future))

        tickers = [r[0] for r in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error getting calendar tickers: {e}")
    return tickers


def get_position_tickers() -> List[str]:
    """Get tickers from open positions."""
    tickers = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ticker FROM positions
            WHERE status = 'OPEN'
        """)
        tickers = [r[0] for r in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error getting position tickers: {e}")
    return tickers


def get_watchlist_tickers() -> List[str]:
    """Get tickers marked as WATCH."""
    tickers = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ticker FROM opportunity_flags
            WHERE flag = 'WATCH'
        """)
        tickers = [r[0] for r in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error getting watchlist tickers: {e}")
    return tickers


def get_catalyst_info(ticker: str) -> Optional[Dict]:
    """Get catalyst info for a ticker."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT ticker, catalyst_date, catalyst_event, drug_name, indication
            FROM catalyst_research
            WHERE ticker = ? AND catalyst_date >= ?
            AND excluded = 0
            ORDER BY catalyst_date ASC
            LIMIT 1
        """, (ticker, today))

        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except:
        return None


def fetch_news_for_ticker(ticker: str) -> List[Dict]:
    """Fetch news from Yahoo Finance for a ticker."""
    if not YFINANCE_AVAILABLE:
        return []

    news_items = []
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news or []

        for item in raw_news[:10]:  # Limit per ticker
            # Handle multiple yfinance API formats
            title = (
                item.get('title') or
                item.get('headline') or
                ''
            )

            if not title:
                continue

            link = (
                item.get('link') or
                item.get('url') or
                '#'
            )

            publisher = (
                item.get('publisher') or
                item.get('source') or
                'Yahoo Finance'
            )

            # Timestamp
            pub_time = (
                item.get('providerPublishTime') or
                item.get('publishedAt') or
                0
            )

            pub_date = datetime.now()
            if pub_time:
                try:
                    if isinstance(pub_time, (int, float)):
                        pub_date = datetime.fromtimestamp(pub_time)
                    elif isinstance(pub_time, str):
                        pub_date = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                except:
                    pass

            summary = item.get('summary') or item.get('description') or ''

            # Categorize
            analysis = categorize_news(title, summary)

            news_items.append({
                'ticker': ticker,
                'title': title,
                'link': link,
                'publisher': publisher,
                'published': pub_date.isoformat(),
                'published_unix': int(pub_date.timestamp()),
                'summary': summary[:300] if summary else '',
                **analysis
            })

    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")

    return news_items


# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate_news_feed():
    """Generate the complete news feed."""
    print("=" * 60)
    print("POWERSBIOSTRIKES NEWS FEED GENERATOR")
    print("=" * 60)

    # Collect all tickers
    calendar_tickers = get_calendar_tickers(days=60)
    position_tickers = get_position_tickers()
    watchlist_tickers = get_watchlist_tickers()

    # Combine and dedupe
    all_tickers = list(set(calendar_tickers + position_tickers + watchlist_tickers))
    all_tickers.sort()

    print(f"\nTickers to fetch news for:")
    print(f"  Calendar (60d): {len(calendar_tickers)}")
    print(f"  Positions: {len(position_tickers)}")
    print(f"  Watchlist: {len(watchlist_tickers)}")
    print(f"  Total unique: {len(all_tickers)}")

    if not all_tickers:
        print("\nNo tickers found. Generating empty feed.")
        all_tickers = []

    # Fetch news for each ticker
    all_news = []
    for i, ticker in enumerate(all_tickers):
        print(f"\n[{i+1}/{len(all_tickers)}] Fetching news for {ticker}...")
        news = fetch_news_for_ticker(ticker)
        print(f"  Found {len(news)} news items")

        # Add catalyst context
        catalyst = get_catalyst_info(ticker)
        for item in news:
            item['catalyst'] = catalyst
            # Mark source type
            item['source_type'] = []
            if ticker in position_tickers:
                item['source_type'].append('position')
            if ticker in watchlist_tickers:
                item['source_type'].append('watchlist')
            if ticker in calendar_tickers:
                item['source_type'].append('calendar')

        all_news.extend(news)

    # Sort by priority (high first), then by date (recent first)
    all_news.sort(key=lambda x: (-x.get('priority', 0), -x.get('published_unix', 0)))

    # Separate high priority items
    high_priority = [n for n in all_news if n.get('priority', 0) >= 3 or n.get('sentiment') == 'negative']

    # Build output structure
    output = {
        'generated_at': datetime.now().isoformat(),
        'ticker_count': len(all_tickers),
        'news_count': len(all_news),
        'high_priority_count': len(high_priority),

        'summary': {
            'total': len(all_news),
            'fda': sum(1 for n in all_news if 'fda' in n.get('categories', [])),
            'clinical': sum(1 for n in all_news if 'clinical' in n.get('categories', [])),
            'positive': sum(1 for n in all_news if n.get('sentiment') == 'positive'),
            'negative': sum(1 for n in all_news if n.get('sentiment') == 'negative'),
        },

        'high_priority': high_priority[:20],  # Top 20 alerts
        'recent': all_news[:50],  # Most recent 50
        'by_ticker': {},
    }

    # Group by ticker for stock detail pages
    for ticker in all_tickers:
        ticker_news = [n for n in all_news if n['ticker'] == ticker]
        if ticker_news:
            output['by_ticker'][ticker] = ticker_news[:10]  # Max 10 per ticker

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"NEWS FEED GENERATED SUCCESSFULLY")
    print(f"{'=' * 60}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Total news items: {len(all_news)}")
    print(f"High priority alerts: {len(high_priority)}")
    print(f"Tickers covered: {len(all_tickers)}")


if __name__ == "__main__":
    generate_news_feed()
