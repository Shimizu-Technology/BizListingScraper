# BizListingScraper - Complete Project Documentation

A Python-based web scraper for business listing sites (BizBuySell, etc.) with automated daily updates, deduplication, and a React dashboard.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Product Requirements Document (PRD)](#product-requirements-document-prd)
3. [Technical Architecture](#technical-architecture)
4. [Crawl4AI Complete Guide](#crawl4ai-complete-guide)
5. [Database Design (Neon/PostgreSQL)](#database-design-neonpostgresql)
6. [FastAPI Backend](#fastapi-backend)
7. [Deduplication Strategy](#deduplication-strategy)
8. [Automation & Scheduling](#automation--scheduling)
9. [React Frontend](#react-frontend)
10. [Deployment Guide](#deployment-guide)
11. [Project Structure](#project-structure)
12. [Development Setup](#development-setup)
13. [Cost Estimates](#cost-estimates)
14. [Timeline & Milestones](#timeline--milestones)

---

## Project Overview

### The Problem

A business buyer/broker needs to monitor multiple business-for-sale listing sites (like BizBuySell) daily to find new opportunities. Manually checking these sites is:
- Time-consuming
- Easy to miss new listings
- No way to track price changes
- No centralized view across multiple sites

### The Solution

An automated scraping system that:
1. **Scrapes daily** - Runs automatically every morning
2. **Deduplicates intelligently** - Only stores new/changed listings
3. **Tracks changes** - Logs when prices change, listings removed, etc.
4. **Provides a dashboard** - Simple web UI to browse, filter, and export listings
5. **Alerts (optional)** - Email notifications for new listings matching criteria

---

## Product Requirements Document (PRD)

### 1. Executive Summary

**Product Name:** BizListingScraper  
**Client:** [Client Name]  
**Developer:** Shimizu Technology  
**Target Launch:** [Date]  

**Objective:** Build an automated system to scrape business listings from BizBuySell (and potentially other sites), store them in a database with change tracking, and provide a web interface for browsing listings.

### 2. User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-1 | Business buyer | See all Michigan business listings in one place | I don't have to check multiple pages |
| US-2 | Business buyer | Know which listings are new today | I can act quickly on new opportunities |
| US-3 | Business buyer | See when a listing's price changed | I can identify motivated sellers |
| US-4 | Business buyer | Filter by price, category, location | I can focus on relevant opportunities |
| US-5 | Business buyer | Export listings to CSV/Excel | I can analyze or share with partners |
| US-6 | Business buyer | Get email alerts for new listings | I don't have to check the dashboard daily |
| US-7 | Business buyer | See listings that were recently removed | I can understand market activity |

### 3. Functional Requirements

#### 3.1 Scraping Engine

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1 | Scrape BizBuySell Michigan listings | P0 (Must) | Primary data source |
| FR-2 | Extract: title, price, cash flow, location, category, description | P0 | Core listing fields |
| FR-3 | Follow pagination (all pages, not just first) | P0 | Complete coverage |
| FR-4 | Handle JavaScript-rendered content | P0 | Use headless browser |
| FR-5 | Rate limit to avoid blocking | P0 | 2-3 second delays |
| FR-6 | Log errors and failures | P1 (Should) | For debugging |
| FR-7 | Support additional sites (LoopNet, BusinessBroker.net) | P2 (Could) | Future expansion |
| FR-8 | Scrape individual listing pages for full details | P1 | More complete data |

#### 3.2 Data Storage

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-10 | Store listings in PostgreSQL (Neon) | P0 | Cloud-hosted, reliable |
| FR-11 | Unique constraint on listing external ID | P0 | Prevent duplicates |
| FR-12 | Track first_seen and last_seen timestamps | P0 | Know when listing appeared |
| FR-13 | Detect and flag content changes | P0 | Price changes, etc. |
| FR-14 | Store change history | P1 | See what changed over time |
| FR-15 | Mark listings as inactive when not seen | P1 | Track removed listings |
| FR-16 | Store raw scraped data as JSON | P1 | Debugging, future use |

#### 3.3 API Backend

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-20 | GET /listings - List all active listings | P0 | Main data endpoint |
| FR-21 | Support filtering: state, price range, category | P0 | Narrow results |
| FR-22 | Support sorting: date, price, cash flow | P0 | Order results |
| FR-23 | Support pagination | P0 | Handle large datasets |
| FR-24 | GET /listings/{id} - Single listing detail | P0 | Full info view |
| FR-25 | GET /listings/{id}/history - Change history | P1 | Track changes |
| FR-26 | GET /stats - Dashboard statistics | P1 | Summary metrics |
| FR-27 | POST /scrape/trigger - Manual scrape trigger | P2 | On-demand refresh |
| FR-28 | Basic API key authentication | P1 | Prevent abuse |

#### 3.4 Web Dashboard

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-30 | Display listings in a table | P0 | Main view |
| FR-31 | Filter sidebar (price, location, category) | P0 | Narrow results |
| FR-32 | Sort by columns | P0 | Reorder |
| FR-33 | "New Today" badge on fresh listings | P1 | Visual indicator |
| FR-34 | "Price Changed" indicator | P1 | Track changes |
| FR-35 | Click to expand listing details | P0 | Full info |
| FR-36 | Link to original listing on BizBuySell | P0 | Verification |
| FR-37 | Export to CSV | P1 | Data portability |
| FR-38 | Mobile responsive | P1 | View on phone |
| FR-39 | Dark mode | P2 | Nice to have |

#### 3.5 Automation

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-40 | Run scraper daily at 6 AM | P0 | Fresh data each morning |
| FR-41 | Send summary email after scrape | P1 | New/changed counts |
| FR-42 | Alert on scrape failures | P0 | Know when broken |
| FR-43 | Retry logic for transient failures | P1 | Resilience |

### 4. Non-Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| NFR-1 | Scrape completes in < 30 minutes | Reasonable runtime |
| NFR-2 | API response time < 500ms | Fast dashboard |
| NFR-3 | 99% uptime for dashboard | Reliable access |
| NFR-4 | Data retained for 1 year | Historical analysis |
| NFR-5 | HTTPS for all endpoints | Security |
| NFR-6 | Respect robots.txt | Ethical scraping |

### 5. Out of Scope (v1)

- User accounts / multi-tenant
- Saved searches / custom alerts per user
- AI-powered listing analysis
- Mobile native app
- Real-time push notifications

### 6. Success Metrics

| Metric | Target |
|--------|--------|
| Daily scrape success rate | > 95% |
| New listings detected within 24 hours | 100% |
| Dashboard load time | < 2 seconds |
| Client satisfaction | Happy client! |

### 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| BizBuySell blocks scraper | Medium | High | Rate limiting, proxy rotation, user-agent rotation |
| Site structure changes | Medium | Medium | Modular parsing, quick fix turnaround |
| Large data volume | Low | Low | Pagination, archiving old data |
| API rate limits | Low | Low | Caching, efficient queries |

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │   GitHub    │    │   Python     │    │   Neon DB       │    │
│  │   Actions   │───▶│   Scraper    │───▶│   (PostgreSQL)  │    │
│  │   (Cron)    │    │   Crawl4AI   │    │                 │    │
│  └─────────────┘    └──────────────┘    └────────┬────────┘    │
│                                                   │             │
│                                                   ▼             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │   Vercel/   │◀───│   FastAPI    │◀───│   Connection    │    │
│  │   Netlify   │    │   Backend    │    │   Pooler        │    │
│  │   (React)   │    │   (Render)   │    │                 │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Scraper | Python + Crawl4AI | Fetch and parse listings |
| Database | Neon (PostgreSQL) | Store listings, history, metadata |
| Backend API | FastAPI | Serve data to frontend |
| Frontend | React + Tailwind | User interface |
| Scheduler | GitHub Actions | Daily cron trigger |
| Hosting (API) | Render / Railway | Run FastAPI server |
| Hosting (Frontend) | Vercel / Netlify | Serve React app |

---

## Crawl4AI Complete Guide

### What is Crawl4AI?

Crawl4AI is a Python library for web scraping that uses a headless browser (Playwright) to render JavaScript-heavy pages. It automatically converts HTML to clean Markdown.

**Key Features:**
- Async/await based (fast, non-blocking)
- Handles JavaScript rendering
- Automatic markdown conversion
- Link extraction
- Screenshot capability
- Session management

### Installation

```bash
# Install with uv (recommended)
uv add crawl4ai

# Or with pip
pip install crawl4ai

# Install browser dependencies (first time only)
crawl4ai-setup
```

### Basic Usage

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def simple_crawl():
    # Configure the browser
    browser_config = BrowserConfig(
        headless=True,          # Run without visible browser
        verbose=False,          # Reduce logging
        # browser_type="chromium"  # chromium, firefox, or webkit
    )
    
    # Configure the crawl
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # Don't use cached results
        # wait_for="css:.listing",    # Wait for element before scraping
        # js_code="window.scrollTo(0, document.body.scrollHeight)",  # Execute JS
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.bizbuysell.com/michigan-businesses-for-sale/",
            config=run_config
        )
        
        if result.success:
            print(f"Title: {result.metadata.get('title')}")
            print(f"Markdown length: {len(result.markdown)}")
            print(f"Internal links: {len(result.links.get('internal', []))}")
            print(f"External links: {len(result.links.get('external', []))}")
            
            # The markdown content
            print(result.markdown[:1000])
        else:
            print(f"Failed: {result.error_message}")

asyncio.run(simple_crawl())
```

### Advanced Configuration

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Full browser configuration
browser_config = BrowserConfig(
    headless=True,
    verbose=False,
    browser_type="chromium",
    
    # Viewport settings
    viewport_width=1920,
    viewport_height=1080,
    
    # User agent (rotate to avoid detection)
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    
    # Proxy configuration (if needed)
    # proxy="http://user:pass@proxy.example.com:8080",
)

# Full run configuration
run_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    
    # Wait for content to load
    wait_for="css:.listing-card",  # Wait for CSS selector
    # wait_for="js:() => document.querySelectorAll('.listing').length > 0",
    
    # Page timeout
    page_timeout=60000,  # 60 seconds
    
    # Execute JavaScript before scraping
    js_code="""
        // Scroll to load lazy content
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 2000));
    """,
    
    # Block unnecessary resources (faster)
    excluded_tags=["script", "style", "iframe"],
    
    # Only follow links matching pattern
    # include_links_on_page=True,
)
```

### Crawl4AI Result Object

```python
result = await crawler.arun(url=url, config=config)

# Available properties
result.success          # bool - Did the crawl succeed?
result.url              # str - Final URL (after redirects)
result.html             # str - Raw HTML content
result.markdown         # str - Converted markdown
result.cleaned_html     # str - HTML with scripts/styles removed
result.links            # dict - {"internal": [...], "external": [...]}
result.media            # dict - {"images": [...], "videos": [...]}
result.metadata         # dict - Page metadata (title, description, etc.)
result.error_message    # str - Error description if failed
result.status_code      # int - HTTP status code
```

### Handling Pagination

```python
async def crawl_all_pages(base_url: str, max_pages: int = 50):
    """Crawl multiple pages with pagination."""
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    all_results = []
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            # Construct paginated URL
            url = f"{base_url}?page={page}" if page > 1 else base_url
            
            print(f"Crawling page {page}...")
            result = await crawler.arun(url=url, config=run_config)
            
            if not result.success:
                print(f"Failed on page {page}: {result.error_message}")
                break
            
            # Parse listings from this page
            listings = parse_listings_from_markdown(result.markdown)
            
            if not listings:
                print(f"No listings on page {page}, stopping")
                break
            
            all_results.extend(listings)
            
            # Rate limiting - IMPORTANT!
            await asyncio.sleep(2)  # 2 second delay between pages
    
    return all_results
```

### Session Management (For Login-Required Sites)

```python
async def crawl_with_session():
    """Maintain session across multiple requests."""
    browser_config = BrowserConfig(headless=True)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First request - login
        login_result = await crawler.arun(
            url="https://example.com/login",
            config=CrawlerRunConfig(
                js_code="""
                    document.querySelector('#email').value = 'user@example.com';
                    document.querySelector('#password').value = 'password';
                    document.querySelector('form').submit();
                """,
                wait_for="css:.dashboard"  # Wait for login to complete
            )
        )
        
        # Subsequent requests maintain the session (cookies, etc.)
        dashboard = await crawler.arun(
            url="https://example.com/dashboard",
            config=CrawlerRunConfig()
        )
```

### Common Patterns for BizBuySell

```python
import re
from bs4 import BeautifulSoup

def parse_listings_from_html(html: str) -> list[dict]:
    """Parse BizBuySell listing cards from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    
    # Find all listing cards (inspect the actual page to get correct selectors)
    for card in soup.select('.listing-card, .business-card'):
        try:
            listing = {
                'external_id': extract_listing_id(card),
                'title': card.select_one('.listing-title, h3')?.text.strip(),
                'url': card.select_one('a[href*="/Business-Opportunity"]')?.get('href'),
                'asking_price': parse_price(card.select_one('.asking-price')?.text),
                'cash_flow': parse_price(card.select_one('.cash-flow')?.text),
                'location': card.select_one('.location')?.text.strip(),
                'category': card.select_one('.category')?.text.strip(),
                'description': card.select_one('.description')?.text.strip(),
            }
            listings.append(listing)
        except Exception as e:
            print(f"Error parsing listing: {e}")
            continue
    
    return listings

def extract_listing_id(card) -> str:
    """Extract unique listing ID from URL or data attribute."""
    link = card.select_one('a[href*="/Business-Opportunity"]')
    if link:
        href = link.get('href', '')
        # URL pattern: /Business-Opportunity/title-slug/1234567
        match = re.search(r'/(\d+)/?$', href)
        if match:
            return match.group(1)
    return None

def parse_price(text: str) -> float | None:
    """Parse price string like '$250,000' to float."""
    if not text:
        return None
    # Remove $, commas, and other non-numeric characters
    cleaned = re.sub(r'[^\d.]', '', text)
    try:
        return float(cleaned)
    except ValueError:
        return None
```

### Error Handling & Retries

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def crawl_with_retry(url: str, max_retries: int = 3):
    """Crawl with automatic retry on failure."""
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    for attempt in range(max_retries):
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                
                if result.success:
                    return result
                
                print(f"Attempt {attempt + 1} failed: {result.error_message}")
                
        except Exception as e:
            print(f"Attempt {attempt + 1} exception: {e}")
        
        # Exponential backoff
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            print(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    return None  # All retries failed
```

---

## Database Design (Neon/PostgreSQL)

### What is Neon?

Neon is a serverless PostgreSQL provider with:
- Free tier (500MB storage, 100 hours compute)
- Automatic scaling
- Branching (like git for databases)
- Connection pooling built-in

### Setup Neon

1. Go to https://neon.tech
2. Create a free account
3. Create a new project
4. Get your connection string:
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
   ```

### Schema Design

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main listings table
CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) NOT NULL UNIQUE,  -- BizBuySell's listing ID
    source VARCHAR(50) NOT NULL DEFAULT 'bizbuysell',  -- Which site
    url TEXT NOT NULL,
    
    -- Core listing data
    title TEXT NOT NULL,
    asking_price DECIMAL(15, 2),
    cash_flow DECIMAL(15, 2),
    gross_revenue DECIMAL(15, 2),
    ebitda DECIMAL(15, 2),
    
    -- Location
    city VARCHAR(100),
    state VARCHAR(2),
    county VARCHAR(100),
    zip_code VARCHAR(10),
    
    -- Category
    category VARCHAR(200),
    subcategory VARCHAR(200),
    
    -- Description
    description TEXT,
    highlights TEXT,
    
    -- Seller info
    broker_name VARCHAR(200),
    broker_company VARCHAR(200),
    broker_phone VARCHAR(50),
    broker_email VARCHAR(200),
    
    -- Raw data (for debugging/future use)
    raw_data JSONB,
    
    -- Change tracking
    content_hash VARCHAR(64) NOT NULL,  -- SHA256 of key fields
    
    -- Timestamps
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE,  -- When content changed
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',  -- active, sold, withdrawn, expired
    
    -- Indexes
    CONSTRAINT listings_external_source_unique UNIQUE (external_id, source)
);

-- Indexes for common queries
CREATE INDEX idx_listings_state ON listings(state);
CREATE INDEX idx_listings_asking_price ON listings(asking_price);
CREATE INDEX idx_listings_category ON listings(category);
CREATE INDEX idx_listings_first_seen ON listings(first_seen_at);
CREATE INDEX idx_listings_is_active ON listings(is_active);
CREATE INDEX idx_listings_source ON listings(source);

-- Change history table
CREATE TABLE listing_history (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_type VARCHAR(20) NOT NULL,  -- 'created', 'updated', 'deactivated'
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[]  -- Which fields changed
);

CREATE INDEX idx_listing_history_listing_id ON listing_history(listing_id);
CREATE INDEX idx_listing_history_changed_at ON listing_history(changed_at);

-- Scrape runs table (track each scrape job)
CREATE TABLE scrape_runs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running',  -- running, completed, failed
    
    -- Statistics
    pages_scraped INTEGER DEFAULT 0,
    listings_found INTEGER DEFAULT 0,
    listings_inserted INTEGER DEFAULT 0,
    listings_updated INTEGER DEFAULT 0,
    listings_unchanged INTEGER DEFAULT 0,
    listings_deactivated INTEGER DEFAULT 0,
    
    -- Errors
    error_message TEXT,
    error_details JSONB
);

CREATE INDEX idx_scrape_runs_started_at ON scrape_runs(started_at);

-- Daily statistics (for dashboard)
CREATE TABLE daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    source VARCHAR(50) NOT NULL,
    
    total_active_listings INTEGER DEFAULT 0,
    new_listings INTEGER DEFAULT 0,
    updated_listings INTEGER DEFAULT 0,
    removed_listings INTEGER DEFAULT 0,
    
    avg_asking_price DECIMAL(15, 2),
    median_asking_price DECIMAL(15, 2),
    total_listings_value DECIMAL(20, 2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_daily_stats_date ON daily_stats(date);
```

### Python Database Connection

```python
# database.py
import os
import psycopg
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Connection pool for better performance
pool = ConnectionPool(
    DATABASE_URL,
    min_size=1,
    max_size=10,
    kwargs={"autocommit": True}
)

def get_connection():
    """Get a connection from the pool."""
    return pool.connection()

# For async usage with FastAPI
import psycopg
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_connection():
    """Get an async connection."""
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()
```

---

## Deduplication Strategy

### Content Hashing

```python
# deduplication.py
import hashlib
import json
from datetime import datetime
from typing import Optional

def compute_content_hash(listing: dict) -> str:
    """
    Compute a hash of the listing's key fields.
    Only these fields trigger an "update" if changed.
    """
    # Fields that matter for content changes
    key_fields = {
        'title': listing.get('title', ''),
        'asking_price': str(listing.get('asking_price', '')),
        'cash_flow': str(listing.get('cash_flow', '')),
        'description': listing.get('description', ''),
        'category': listing.get('category', ''),
        'city': listing.get('city', ''),
        'state': listing.get('state', ''),
        'broker_name': listing.get('broker_name', ''),
    }
    
    # Sort keys for consistent hashing
    content = json.dumps(key_fields, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def find_changed_fields(old_listing: dict, new_listing: dict) -> list[str]:
    """Identify which fields changed between two versions."""
    changed = []
    
    compare_fields = [
        'title', 'asking_price', 'cash_flow', 'gross_revenue',
        'description', 'category', 'city', 'state', 'broker_name'
    ]
    
    for field in compare_fields:
        old_val = old_listing.get(field)
        new_val = new_listing.get(field)
        
        if old_val != new_val:
            changed.append(field)
    
    return changed
```

### Upsert Logic

```python
# upsert.py
import json
from datetime import datetime
from database import get_connection
from deduplication import compute_content_hash, find_changed_fields

def upsert_listing(listing: dict) -> str:
    """
    Insert or update a listing with change tracking.
    
    Returns: 'inserted', 'updated', or 'unchanged'
    """
    external_id = listing['external_id']
    source = listing.get('source', 'bizbuysell')
    new_hash = compute_content_hash(listing)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if listing exists
            cur.execute("""
                SELECT id, content_hash, raw_data::text
                FROM listings
                WHERE external_id = %s AND source = %s
            """, (external_id, source))
            
            existing = cur.fetchone()
            
            if existing is None:
                # NEW LISTING - Insert
                cur.execute("""
                    INSERT INTO listings (
                        external_id, source, url, title, asking_price, cash_flow,
                        gross_revenue, city, state, category, description,
                        broker_name, broker_company, broker_phone, broker_email,
                        raw_data, content_hash, first_seen_at, last_seen_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    ) RETURNING id
                """, (
                    external_id, source, listing.get('url'),
                    listing.get('title'), listing.get('asking_price'),
                    listing.get('cash_flow'), listing.get('gross_revenue'),
                    listing.get('city'), listing.get('state'),
                    listing.get('category'), listing.get('description'),
                    listing.get('broker_name'), listing.get('broker_company'),
                    listing.get('broker_phone'), listing.get('broker_email'),
                    json.dumps(listing), new_hash
                ))
                
                new_id = cur.fetchone()[0]
                
                # Log creation in history
                cur.execute("""
                    INSERT INTO listing_history (listing_id, change_type, new_values)
                    VALUES (%s, 'created', %s)
                """, (new_id, json.dumps(listing)))
                
                return 'inserted'
            
            else:
                existing_id, existing_hash, existing_raw = existing
                
                if existing_hash == new_hash:
                    # NO CHANGES - Just update last_seen
                    cur.execute("""
                        UPDATE listings
                        SET last_seen_at = NOW(), is_active = TRUE
                        WHERE id = %s
                    """, (existing_id,))
                    
                    return 'unchanged'
                
                else:
                    # CONTENT CHANGED - Update and log
                    old_data = json.loads(existing_raw) if existing_raw else {}
                    changed_fields = find_changed_fields(old_data, listing)
                    
                    cur.execute("""
                        UPDATE listings
                        SET title = %s, asking_price = %s, cash_flow = %s,
                            gross_revenue = %s, city = %s, state = %s,
                            category = %s, description = %s,
                            broker_name = %s, broker_company = %s,
                            broker_phone = %s, broker_email = %s,
                            raw_data = %s, content_hash = %s,
                            last_seen_at = NOW(), last_updated_at = NOW(),
                            is_active = TRUE
                        WHERE id = %s
                    """, (
                        listing.get('title'), listing.get('asking_price'),
                        listing.get('cash_flow'), listing.get('gross_revenue'),
                        listing.get('city'), listing.get('state'),
                        listing.get('category'), listing.get('description'),
                        listing.get('broker_name'), listing.get('broker_company'),
                        listing.get('broker_phone'), listing.get('broker_email'),
                        json.dumps(listing), new_hash, existing_id
                    ))
                    
                    # Log changes in history
                    cur.execute("""
                        INSERT INTO listing_history (
                            listing_id, change_type, old_values, new_values, changed_fields
                        ) VALUES (%s, 'updated', %s, %s, %s)
                    """, (
                        existing_id,
                        existing_raw,
                        json.dumps(listing),
                        changed_fields
                    ))
                    
                    return 'updated'


def mark_stale_listings(source: str = 'bizbuysell', days_threshold: int = 3):
    """Mark listings not seen in X days as inactive."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE listings
                SET is_active = FALSE, status = 'stale'
                WHERE source = %s
                  AND is_active = TRUE
                  AND last_seen_at < NOW() - INTERVAL '%s days'
                RETURNING id
            """, (source, days_threshold))
            
            deactivated_ids = [row[0] for row in cur.fetchall()]
            
            # Log deactivations
            for listing_id in deactivated_ids:
                cur.execute("""
                    INSERT INTO listing_history (listing_id, change_type)
                    VALUES (%s, 'deactivated')
                """, (listing_id,))
            
            return len(deactivated_ids)
```

---

## FastAPI Backend

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings and environment
│   ├── database.py       # Database connection
│   ├── models.py         # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── listings.py   # Listing endpoints
│   │   └── stats.py      # Statistics endpoints
│   └── services/
│       ├── __init__.py
│       └── listing_service.py
├── scraper/
│   ├── __init__.py
│   ├── main.py           # Scraper entry point
│   ├── bizbuysell.py     # BizBuySell scraper
│   ├── parser.py         # HTML parsing
│   └── upsert.py         # Database upsert logic
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### FastAPI Implementation

```python
# app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os

from .routers import listings, stats
from .database import pool

app = FastAPI(
    title="BizListingScraper API",
    description="API for browsing scraped business listings",
    version="1.0.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "https://your-frontend.vercel.app",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(listings.router, prefix="/api/listings", tags=["Listings"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown():
    pool.close()
```

```python
# app/routers/listings.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ListingResponse(BaseModel):
    id: int
    external_id: str
    url: str
    title: str
    asking_price: Optional[float]
    cash_flow: Optional[float]
    city: Optional[str]
    state: Optional[str]
    category: Optional[str]
    description: Optional[str]
    broker_name: Optional[str]
    first_seen_at: datetime
    last_seen_at: datetime
    last_updated_at: Optional[datetime]
    is_new_today: bool = False
    has_price_change: bool = False

class ListingsResponse(BaseModel):
    listings: list[ListingResponse]
    total: int
    page: int
    per_page: int
    pages: int

@router.get("", response_model=ListingsResponse)
async def get_listings(
    state: Optional[str] = Query(None, description="Filter by state (e.g., 'MI')"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum asking price"),
    max_price: Optional[float] = Query(None, description="Maximum asking price"),
    min_cash_flow: Optional[float] = Query(None, description="Minimum cash flow"),
    new_today: Optional[bool] = Query(None, description="Only new listings from today"),
    is_active: bool = Query(True, description="Only active listings"),
    sort_by: str = Query("first_seen_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """Get paginated list of business listings with filters."""
    from ..database import get_connection
    
    # Build query dynamically
    conditions = []
    params = []
    
    if is_active:
        conditions.append("is_active = TRUE")
    
    if state:
        conditions.append("state = %s")
        params.append(state.upper())
    
    if category:
        conditions.append("category ILIKE %s")
        params.append(f"%{category}%")
    
    if min_price is not None:
        conditions.append("asking_price >= %s")
        params.append(min_price)
    
    if max_price is not None:
        conditions.append("asking_price <= %s")
        params.append(max_price)
    
    if min_cash_flow is not None:
        conditions.append("cash_flow >= %s")
        params.append(min_cash_flow)
    
    if new_today:
        conditions.append("DATE(first_seen_at) = CURRENT_DATE")
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    # Validate sort_by
    allowed_sort = ['first_seen_at', 'last_seen_at', 'asking_price', 'cash_flow', 'title']
    if sort_by not in allowed_sort:
        sort_by = 'first_seen_at'
    
    sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    offset = (page - 1) * per_page
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get total count
            cur.execute(f"SELECT COUNT(*) FROM listings WHERE {where_clause}", params)
            total = cur.fetchone()[0]
            
            # Get listings
            cur.execute(f"""
                SELECT id, external_id, url, title, asking_price, cash_flow,
                       city, state, category, description, broker_name,
                       first_seen_at, last_seen_at, last_updated_at,
                       DATE(first_seen_at) = CURRENT_DATE as is_new_today,
                       last_updated_at IS NOT NULL AND last_updated_at > first_seen_at as has_price_change
                FROM listings
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            
            rows = cur.fetchall()
    
    listings = [
        ListingResponse(
            id=row[0], external_id=row[1], url=row[2], title=row[3],
            asking_price=row[4], cash_flow=row[5], city=row[6], state=row[7],
            category=row[8], description=row[9], broker_name=row[10],
            first_seen_at=row[11], last_seen_at=row[12], last_updated_at=row[13],
            is_new_today=row[14], has_price_change=row[15]
        )
        for row in rows
    ]
    
    pages = (total + per_page - 1) // per_page
    
    return ListingsResponse(
        listings=listings,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: int):
    """Get a single listing by ID."""
    from ..database import get_connection
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, external_id, url, title, asking_price, cash_flow,
                       city, state, category, description, broker_name,
                       first_seen_at, last_seen_at, last_updated_at,
                       DATE(first_seen_at) = CURRENT_DATE as is_new_today,
                       last_updated_at IS NOT NULL as has_price_change
                FROM listings
                WHERE id = %s
            """, (listing_id,))
            
            row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return ListingResponse(
        id=row[0], external_id=row[1], url=row[2], title=row[3],
        asking_price=row[4], cash_flow=row[5], city=row[6], state=row[7],
        category=row[8], description=row[9], broker_name=row[10],
        first_seen_at=row[11], last_seen_at=row[12], last_updated_at=row[13],
        is_new_today=row[14], has_price_change=row[15]
    )

@router.get("/{listing_id}/history")
async def get_listing_history(listing_id: int):
    """Get change history for a listing."""
    from ..database import get_connection
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, changed_at, change_type, old_values, new_values, changed_fields
                FROM listing_history
                WHERE listing_id = %s
                ORDER BY changed_at DESC
            """, (listing_id,))
            
            rows = cur.fetchall()
    
    return [
        {
            "id": row[0],
            "changed_at": row[1],
            "change_type": row[2],
            "old_values": row[3],
            "new_values": row[4],
            "changed_fields": row[5]
        }
        for row in rows
    ]
```

```python
# app/routers/stats.py
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import date

router = APIRouter()

class StatsResponse(BaseModel):
    total_active_listings: int
    new_today: int
    updated_today: int
    removed_this_week: int
    avg_asking_price: float
    total_value: float
    listings_by_category: dict
    listings_by_state: dict

@router.get("", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics."""
    from ..database import get_connection
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total active
            cur.execute("SELECT COUNT(*) FROM listings WHERE is_active = TRUE")
            total_active = cur.fetchone()[0]
            
            # New today
            cur.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE DATE(first_seen_at) = CURRENT_DATE
            """)
            new_today = cur.fetchone()[0]
            
            # Updated today
            cur.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE DATE(last_updated_at) = CURRENT_DATE
                  AND last_updated_at > first_seen_at
            """)
            updated_today = cur.fetchone()[0]
            
            # Removed this week
            cur.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE is_active = FALSE
                  AND last_seen_at > NOW() - INTERVAL '7 days'
            """)
            removed_week = cur.fetchone()[0]
            
            # Average price
            cur.execute("""
                SELECT COALESCE(AVG(asking_price), 0), COALESCE(SUM(asking_price), 0)
                FROM listings 
                WHERE is_active = TRUE AND asking_price > 0
            """)
            avg_price, total_value = cur.fetchone()
            
            # By category
            cur.execute("""
                SELECT category, COUNT(*) 
                FROM listings 
                WHERE is_active = TRUE AND category IS NOT NULL
                GROUP BY category 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            by_category = {row[0]: row[1] for row in cur.fetchall()}
            
            # By state
            cur.execute("""
                SELECT state, COUNT(*) 
                FROM listings 
                WHERE is_active = TRUE AND state IS NOT NULL
                GROUP BY state 
                ORDER BY COUNT(*) DESC
            """)
            by_state = {row[0]: row[1] for row in cur.fetchall()}
    
    return StatsResponse(
        total_active_listings=total_active,
        new_today=new_today,
        updated_today=updated_today,
        removed_this_week=removed_week,
        avg_asking_price=float(avg_price),
        total_value=float(total_value),
        listings_by_category=by_category,
        listings_by_state=by_state
    )
```

---

## Automation & Scheduling

### GitHub Actions (Recommended)

```yaml
# .github/workflows/daily-scrape.yml
name: Daily Scrape

on:
  schedule:
    # Run at 6 AM UTC every day
    - cron: '0 6 * * *'
  
  # Allow manual trigger
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          crawl4ai-setup
      
      - name: Run scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          python -m scraper.main
      
      - name: Send notification on failure
        if: failure()
        run: |
          # Send email, Slack, or other notification
          echo "Scrape failed!"
```

### Scraper Main Script

```python
# scraper/main.py
import asyncio
import logging
from datetime import datetime
from .bizbuysell import scrape_bizbuysell
from .upsert import upsert_listing, mark_stale_listings
from database import get_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main scraper entry point."""
    start_time = datetime.now()
    logger.info(f"Starting scrape at {start_time}")
    
    # Initialize scrape run record
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scrape_runs (source, started_at, status)
                VALUES ('bizbuysell', NOW(), 'running')
                RETURNING id
            """)
            run_id = cur.fetchone()[0]
    
    stats = {
        'pages_scraped': 0,
        'listings_found': 0,
        'inserted': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0
    }
    
    try:
        # Scrape all listings
        listings = await scrape_bizbuysell(
            state="MI",
            max_pages=100
        )
        
        stats['listings_found'] = len(listings)
        logger.info(f"Found {len(listings)} listings")
        
        # Upsert each listing
        for listing in listings:
            try:
                result = upsert_listing(listing)
                stats[result] = stats.get(result, 0) + 1
            except Exception as e:
                logger.error(f"Error upserting {listing.get('external_id')}: {e}")
                stats['errors'] += 1
        
        # Mark stale listings as inactive
        deactivated = mark_stale_listings('bizbuysell', days_threshold=3)
        stats['deactivated'] = deactivated
        
        # Update scrape run record
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE scrape_runs
                    SET completed_at = NOW(),
                        status = 'completed',
                        pages_scraped = %s,
                        listings_found = %s,
                        listings_inserted = %s,
                        listings_updated = %s,
                        listings_unchanged = %s,
                        listings_deactivated = %s
                    WHERE id = %s
                """, (
                    stats['pages_scraped'],
                    stats['listings_found'],
                    stats.get('inserted', 0),
                    stats.get('updated', 0),
                    stats.get('unchanged', 0),
                    stats.get('deactivated', 0),
                    run_id
                ))
        
        duration = datetime.now() - start_time
        logger.info(f"Scrape completed in {duration}")
        logger.info(f"Stats: {stats}")
        
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        
        # Update scrape run with error
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE scrape_runs
                    SET completed_at = NOW(),
                        status = 'failed',
                        error_message = %s
                    WHERE id = %s
                """, (str(e), run_id))
        
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

---

## React Frontend

### Project Setup

```bash
# Create React project with Vite
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# Install dependencies
npm install @tanstack/react-query axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Key Components

```typescript
// src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ListingsPage } from './pages/ListingsPage'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-100">
        <header className="bg-blue-600 text-white p-4">
          <h1 className="text-2xl font-bold">BizListingScraper</h1>
        </header>
        <main className="container mx-auto p-4">
          <ListingsPage />
        </main>
      </div>
    </QueryClientProvider>
  )
}

export default App
```

```typescript
// src/hooks/useListings.ts
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Listing {
  id: number
  external_id: string
  url: string
  title: string
  asking_price: number | null
  cash_flow: number | null
  city: string | null
  state: string | null
  category: string | null
  description: string | null
  first_seen_at: string
  is_new_today: boolean
  has_price_change: boolean
}

interface ListingsResponse {
  listings: Listing[]
  total: number
  page: number
  per_page: number
  pages: number
}

interface ListingsParams {
  state?: string
  category?: string
  min_price?: number
  max_price?: number
  new_today?: boolean
  page?: number
  per_page?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export function useListings(params: ListingsParams = {}) {
  return useQuery({
    queryKey: ['listings', params],
    queryFn: async () => {
      const { data } = await axios.get<ListingsResponse>(`${API_URL}/api/listings`, {
        params
      })
      return data
    }
  })
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_URL}/api/stats`)
      return data
    }
  })
}
```

```typescript
// src/pages/ListingsPage.tsx
import { useState } from 'react'
import { useListings, useStats } from '../hooks/useListings'

export function ListingsPage() {
  const [filters, setFilters] = useState({
    state: 'MI',
    min_price: undefined,
    max_price: undefined,
    category: '',
    new_today: false,
    page: 1,
    per_page: 25,
    sort_by: 'first_seen_at',
    sort_order: 'desc' as const
  })
  
  const { data, isLoading, error } = useListings(filters)
  const { data: stats } = useStats()
  
  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading listings</div>
  
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <StatsCard title="Active Listings" value={stats.total_active_listings} />
          <StatsCard title="New Today" value={stats.new_today} highlight />
          <StatsCard title="Updated Today" value={stats.updated_today} />
          <StatsCard 
            title="Avg Price" 
            value={`$${stats.avg_asking_price.toLocaleString()}`} 
          />
        </div>
      )}
      
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex gap-4 flex-wrap">
          <select
            value={filters.state}
            onChange={(e) => setFilters({...filters, state: e.target.value, page: 1})}
            className="border rounded px-3 py-2"
          >
            <option value="">All States</option>
            <option value="MI">Michigan</option>
            <option value="OH">Ohio</option>
            {/* Add more states */}
          </select>
          
          <input
            type="number"
            placeholder="Min Price"
            value={filters.min_price || ''}
            onChange={(e) => setFilters({
              ...filters, 
              min_price: e.target.value ? Number(e.target.value) : undefined,
              page: 1
            })}
            className="border rounded px-3 py-2 w-32"
          />
          
          <input
            type="number"
            placeholder="Max Price"
            value={filters.max_price || ''}
            onChange={(e) => setFilters({
              ...filters, 
              max_price: e.target.value ? Number(e.target.value) : undefined,
              page: 1
            })}
            className="border rounded px-3 py-2 w-32"
          />
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={filters.new_today}
              onChange={(e) => setFilters({...filters, new_today: e.target.checked, page: 1})}
            />
            New Today Only
          </label>
        </div>
      </div>
      
      {/* Results */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">Title</th>
              <th className="px-4 py-3 text-left">Location</th>
              <th className="px-4 py-3 text-right">Asking Price</th>
              <th className="px-4 py-3 text-right">Cash Flow</th>
              <th className="px-4 py-3 text-left">Category</th>
              <th className="px-4 py-3 text-left">Added</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.listings.map((listing) => (
              <tr key={listing.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {listing.is_new_today && (
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded">
                        NEW
                      </span>
                    )}
                    {listing.has_price_change && (
                      <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded">
                        PRICE CHANGED
                      </span>
                    )}
                    <a 
                      href={listing.url} 
                      target="_blank" 
                      className="text-blue-600 hover:underline"
                    >
                      {listing.title}
                    </a>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {listing.city}, {listing.state}
                </td>
                <td className="px-4 py-3 text-right">
                  {listing.asking_price 
                    ? `$${listing.asking_price.toLocaleString()}`
                    : 'N/A'
                  }
                </td>
                <td className="px-4 py-3 text-right">
                  {listing.cash_flow 
                    ? `$${listing.cash_flow.toLocaleString()}`
                    : 'N/A'
                  }
                </td>
                <td className="px-4 py-3">{listing.category || 'N/A'}</td>
                <td className="px-4 py-3">
                  {new Date(listing.first_seen_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {/* Pagination */}
        {data && (
          <div className="px-4 py-3 bg-gray-50 flex justify-between items-center">
            <span>
              Showing {(filters.page - 1) * filters.per_page + 1} to{' '}
              {Math.min(filters.page * filters.per_page, data.total)} of{' '}
              {data.total} listings
            </span>
            <div className="flex gap-2">
              <button
                disabled={filters.page <= 1}
                onClick={() => setFilters({...filters, page: filters.page - 1})}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <button
                disabled={filters.page >= data.pages}
                onClick={() => setFilters({...filters, page: filters.page + 1})}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function StatsCard({ 
  title, 
  value, 
  highlight = false 
}: { 
  title: string
  value: string | number
  highlight?: boolean 
}) {
  return (
    <div className={`p-4 rounded-lg ${highlight ? 'bg-green-50 border border-green-200' : 'bg-white shadow'}`}>
      <div className="text-sm text-gray-500">{title}</div>
      <div className={`text-2xl font-bold ${highlight ? 'text-green-600' : ''}`}>
        {value}
      </div>
    </div>
  )
}
```

---

## Deployment Guide

### 1. Neon Database

1. Create account at https://neon.tech
2. Create new project
3. Copy connection string
4. Run schema migration

### 2. Backend (Render)

1. Create new Web Service on Render
2. Connect GitHub repo
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `DATABASE_URL` = Neon connection string

### 3. Frontend (Vercel)

1. Import GitHub repo to Vercel
2. Framework: Vite
3. Add environment variable:
   - `VITE_API_URL` = Render backend URL

### 4. GitHub Actions

1. Add secrets to repo:
   - `DATABASE_URL` = Neon connection string
2. Workflow file already in `.github/workflows/`

---

## Project Structure

```
BizListingScraper/
├── .github/
│   └── workflows/
│       └── daily-scrape.yml      # GitHub Actions cron job
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app
│   │   ├── config.py             # Settings
│   │   ├── database.py           # DB connection
│   │   ├── models.py             # Pydantic models
│   │   └── routers/
│   │       ├── listings.py       # Listing endpoints
│   │       └── stats.py          # Stats endpoints
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── main.py               # Scraper entry point
│   │   ├── bizbuysell.py         # BizBuySell crawler
│   │   ├── parser.py             # HTML parsing
│   │   ├── deduplication.py      # Hash comparison
│   │   └── upsert.py             # DB upsert logic
│   ├── migrations/
│   │   └── 001_initial.sql       # Schema
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   └── ListingsPage.tsx
│   │   ├── hooks/
│   │   │   └── useListings.ts
│   │   └── components/
│   ├── package.json
│   └── vite.config.ts
├── .env.example
├── README.md
└── PROJECT_DOCUMENTATION.md      # This file
```

---

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (or Neon account)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install Crawl4AI browser
crawl4ai-setup

# Set up environment
cp ../.env.example .env
# Edit .env with your DATABASE_URL

# Run migrations
psql $DATABASE_URL < migrations/001_initial.sql

# Start development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

### Run Scraper Manually

```bash
cd backend
python -m scraper.main
```

---

## Cost Estimates

### Monthly Hosting Costs

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| Neon | Free | $0 | 500MB storage, 100 compute hours |
| Render | Free | $0 | Backend, sleeps after 15 min inactivity |
| Vercel | Free | $0 | Frontend |
| GitHub Actions | Free | $0 | 2000 min/month for private repos |
| **Total** | | **$0** | Free tier is sufficient for this use case |

### Upgraded Tiers (If Needed)

| Service | Tier | Cost | When Needed |
|---------|------|------|-------------|
| Neon | Launch | $19/mo | >500MB data, always-on |
| Render | Starter | $7/mo | No sleep, faster cold starts |
| Vercel | Pro | $20/mo | Team features, analytics |

---

## Timeline & Milestones

### Phase 1: Foundation (Week 1)
- [ ] Set up project structure
- [ ] Configure Neon database
- [ ] Create database schema
- [ ] Build basic Crawl4AI scraper for BizBuySell
- [ ] Test parsing logic

### Phase 2: Core Scraping (Week 2)
- [ ] Implement pagination handling
- [ ] Add deduplication logic
- [ ] Create upsert functions
- [ ] Add change history tracking
- [ ] Test end-to-end scrape

### Phase 3: API (Week 3)
- [ ] Build FastAPI backend
- [ ] Implement listing endpoints
- [ ] Add filtering and pagination
- [ ] Add stats endpoint
- [ ] Deploy to Render

### Phase 4: Frontend (Week 4)
- [ ] Create React app
- [ ] Build listings table
- [ ] Add filter sidebar
- [ ] Add pagination
- [ ] Deploy to Vercel

### Phase 5: Automation & Polish (Week 5)
- [ ] Set up GitHub Actions cron
- [ ] Add error notifications
- [ ] Testing and bug fixes
- [ ] Documentation
- [ ] Handoff to client

---

## Appendix: Environment Variables

```bash
# .env.example

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Scraper Settings
SCRAPE_DELAY_SECONDS=2
MAX_PAGES_PER_SCRAPE=100
STALE_THRESHOLD_DAYS=3

# Optional: Proxy for scraping (if needed)
# PROXY_URL=http://user:pass@proxy.example.com:8080

# Optional: Email notifications
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your@email.com
# SMTP_PASS=app-password
# NOTIFY_EMAIL=recipient@email.com
```

---

## Contact & Support

**Developer:** Shimizu Technology  
**Project:** BizListingScraper  
**Documentation Version:** 1.0  
**Last Updated:** [Date]

---

*This document serves as both the PRD and technical documentation for the BizListingScraper project.*
