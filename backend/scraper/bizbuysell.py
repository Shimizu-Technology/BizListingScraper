"""
BizBuySell scraper with robust error handling and browser fallback.

KEY LEARNINGS FROM DEVELOPMENT:
1. Firefox bypasses detection better than Chromium
2. Use headless=True for CI/production (required for GitHub Actions)
3. Pagination requires query param: ?q=bHQ9MzAsNDAsODA%3D
4. Homepage warm-up helps establish natural session
5. Rate limiting occurs after ~50 rapid requests
6. Always save to file before database insert
"""

import asyncio
import json
import random
import re
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup

from .stealth import (
    get_random_user_agent,
    get_random_viewport,
    human_delay,
    simulate_human_behavior,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State URL mapping
STATE_URLS = {
    "MI": "https://www.bizbuysell.com/michigan-businesses-for-sale/",
    "CT": "https://www.bizbuysell.com/connecticut-businesses-for-sale/",
    "OH": "https://www.bizbuysell.com/ohio-businesses-for-sale/",
    "IN": "https://www.bizbuysell.com/indiana-businesses-for-sale/",
    "IL": "https://www.bizbuysell.com/illinois-businesses-for-sale/",
    "WI": "https://www.bizbuysell.com/wisconsin-businesses-for-sale/",
    "FL": "https://www.bizbuysell.com/florida-businesses-for-sale/",
    "TX": "https://www.bizbuysell.com/texas-businesses-for-sale/",
    "CA": "https://www.bizbuysell.com/california-businesses-for-sale/",
    "NY": "https://www.bizbuysell.com/new-york-businesses-for-sale/",
    "PA": "https://www.bizbuysell.com/pennsylvania-businesses-for-sale/",
}

# Query param that enables full pagination
DEFAULT_QUERY_PARAM = "bHQ9MzAsNDAsODA%3D"


class ScrapeResult:
    """Container for scrape results with metrics."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.listings: list = []
        self.pages_scraped: int = 0
        self.errors: int = 0
        self.browser_used: str = ""
        self.state: str = ""
        self.blocked: bool = False
    
    def finish(self):
        self.end_time = datetime.now()
    
    @property
    def duration_seconds(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def duration_formatted(self) -> str:
        secs = int(self.duration_seconds)
        mins, secs = divmod(secs, 60)
        return f"{mins}m {secs}s"
    
    def __str__(self) -> str:
        return (
            f"State: {self.state} | "
            f"Pages: {self.pages_scraped} | "
            f"Listings: {len(self.listings)} | "
            f"Time: {self.duration_formatted} | "
            f"Browser: {self.browser_used} | "
            f"Errors: {self.errors}"
        )


async def launch_browser(playwright, preferred: str = "firefox") -> tuple[Browser, BrowserContext, Page, str]:
    """
    Launch browser with fallback.
    
    Returns: (browser, context, page, browser_name)
    """
    browsers = [preferred, "chromium" if preferred == "firefox" else "firefox"]
    
    for browser_name in browsers:
        try:
            logger.info(f"Launching {browser_name}...")
            viewport = get_random_viewport()
            
            if browser_name == "firefox":
                browser = await playwright.firefox.launch(headless=True)
                context = await browser.new_context(viewport=viewport, locale='en-US')
            else:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = await browser.new_context(
                    viewport=viewport,
                    user_agent=get_random_user_agent(),
                    locale='en-US',
                )
                await context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
            
            page = await context.new_page()
            logger.info(f"{browser_name} launched successfully")
            return browser, context, page, browser_name
            
        except Exception as e:
            logger.warning(f"{browser_name} failed: {e}")
    
    raise RuntimeError("All browsers failed to launch")


async def scrape_bizbuysell(
    state: str = "MI",
    max_pages: int = 100,
    stealth_mode: bool = True,
    warm_up: bool = True,
    browser_type: str = "firefox",
    save_backup: bool = True,
) -> list[dict]:
    """
    Scrape BizBuySell listings for a specific state.
    
    Args:
        state: Two-letter state code (e.g., "MI")
        max_pages: Maximum pages to scrape
        stealth_mode: Use anti-detection techniques
        warm_up: Visit homepage first
        browser_type: "firefox" (recommended) or "chromium"
        save_backup: Save listings to JSON file as backup
    
    Returns:
        List of listing dictionaries
    """
    result = ScrapeResult()
    result.state = state
    
    base_url = STATE_URLS.get(state.upper())
    if not base_url:
        state_name = state.lower()
        base_url = f"https://www.bizbuysell.com/{state_name}-businesses-for-sale/"
        logger.warning(f"Unknown state {state}, trying URL: {base_url}")
    
    logger.info(f"=" * 60)
    logger.info(f"Starting BizBuySell scrape for {state}")
    logger.info(f"Max pages: {max_pages}")
    logger.info(f"=" * 60)
    
    async with async_playwright() as p:
        try:
            browser, context, page, browser_name = await launch_browser(p, browser_type)
            result.browser_used = browser_name
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            result.errors += 1
            result.finish()
            return []
        
        try:
            # Warm up
            if warm_up:
                logger.info("Warming up: visiting homepage...")
                try:
                    await page.goto("https://www.bizbuysell.com/", timeout=30000)
                    await human_delay(2, 4)
                    if stealth_mode:
                        await simulate_human_behavior(page)
                except Exception as e:
                    logger.warning(f"Warm up failed: {e}")
            
            # Scrape pages
            for page_num in range(1, max_pages + 1):
                # Build URL
                base = base_url.rstrip('/')
                if page_num == 1:
                    url = f"{base}/?q={DEFAULT_QUERY_PARAM}"
                else:
                    url = f"{base}/{page_num}/?q={DEFAULT_QUERY_PARAM}"
                
                logger.info(f"Scraping page {page_num}: {url}")
                
                try:
                    response = await page.goto(url, timeout=45000, wait_until='domcontentloaded')
                    
                    if response is None or response.status != 200:
                        status = response.status if response else "None"
                        logger.error(f"Got status {status} on page {page_num}")
                        result.errors += 1
                        if response and response.status == 403:
                            result.blocked = True
                            break
                        continue
                    
                    # Wait for content
                    try:
                        await page.wait_for_selector('a.diamond, a.showcase', timeout=10000)
                    except:
                        pass
                    
                    # Human behavior
                    if stealth_mode:
                        await human_delay(1, 3)
                        await simulate_human_behavior(page)
                    else:
                        await asyncio.sleep(2)
                    
                    content = await page.content()
                    
                    # Check for block
                    if "Access Denied" in content:
                        logger.error("Access Denied - blocked")
                        result.blocked = True
                        break
                    
                    # Parse listings
                    page_listings = parse_listing_page(content)
                    
                    if not page_listings:
                        logger.info(f"No listings on page {page_num} - end of results")
                        break
                    
                    logger.info(f"Found {len(page_listings)} listings on page {page_num}")
                    result.listings.extend(page_listings)
                    result.pages_scraped += 1
                    
                    # Occasional longer pause to avoid rate limiting
                    if random.random() < 0.15:
                        logger.info("Taking a brief pause...")
                        await human_delay(5, 10)
                    
                except Exception as e:
                    logger.error(f"Error on page {page_num}: {e}")
                    result.errors += 1
                    if result.errors >= 3:
                        logger.error("Too many errors, stopping")
                        break
            
        finally:
            await context.close()
            await browser.close()
    
    result.finish()
    
    # Log summary
    logger.info(f"=" * 60)
    logger.info(f"Scrape complete: {result}")
    logger.info(f"=" * 60)
    
    # Save backup
    if save_backup and result.listings:
        backup_path = f"/tmp/bizbuysell_{state}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_path, 'w') as f:
            json.dump(result.listings, f, indent=2)
        logger.info(f"Backup saved to {backup_path}")
    
    return result.listings


def parse_listing_page(html: str) -> list[dict]:
    """Parse a BizBuySell search results page.
    
    Handles BOTH structures:
    1. Old-style: a.diamond, a.showcase
    2. Angular SPA: a containing .listing.flex (used on later pages)
    """
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    seen_ids = set()  # Track to avoid duplicates
    
    # Method 1: Old-style listing cards (diamond = featured, showcase = regular)
    old_style_cards = soup.select('a.diamond, a.showcase')
    for card in old_style_cards:
        try:
            listing = parse_single_listing(card)
            if listing and listing.get('external_id'):
                if listing['external_id'] not in seen_ids:
                    listings.append(listing)
                    seen_ids.add(listing['external_id'])
        except Exception as e:
            logger.debug(f"Error parsing old-style listing: {e}")
    
    # Method 2: Angular-style listing cards (used on later pages)
    # These are <a> tags that contain .listing.flex divs
    angular_cards = soup.select('a:has(.listing.flex)')
    for card in angular_cards:
        try:
            listing = parse_angular_listing(card)
            if listing and listing.get('external_id'):
                if listing['external_id'] not in seen_ids:
                    listings.append(listing)
                    seen_ids.add(listing['external_id'])
        except Exception as e:
            logger.debug(f"Error parsing Angular listing: {e}")
    
    logger.debug(f"Parsed {len(listings)} listings (old-style: {len(old_style_cards)}, angular: {len(angular_cards)})")
    return listings


def parse_angular_listing(card) -> dict:
    """Parse an Angular-style listing card (used on later pages)."""
    data = {
        'source': 'bizbuysell',
        'external_id': None,
        'url': None,
        'title': None,
        'asking_price': None,
        'cash_flow': None,
        'gross_revenue': None,
        'ebitda': None,
        'city': None,
        'state': None,
        'description': None,
        'category': None,
        'listing_type': 'angular',  # Mark as Angular-sourced
        'photo_count': None,
        'real_estate_included': None,
    }
    
    # URL and external ID from the wrapping <a> tag
    href = card.get('href', '')
    if href:
        data['url'] = href if href.startswith('http') else f"https://www.bizbuysell.com{href}"
        # Extract ID from URL like /business-opportunity/value-add-liquor-store-2-buildings/2450957/
        match = re.search(r'/(\d+)/?(?:\?|$)', href)
        if match:
            data['external_id'] = match.group(1)
    
    # Title from .title or h3
    title_el = card.select_one('.title, h3, span.title')
    if title_el:
        data['title'] = title_el.get_text(strip=True)
    
    # Price from .asking-price
    price_el = card.select_one('.asking-price')
    if price_el:
        data['asking_price'] = parse_price(price_el.get_text(strip=True))
    
    # Cash flow from .cash-flow
    cf_el = card.select_one('.cash-flow')
    if cf_el:
        data['cash_flow'] = parse_price(cf_el.get_text(strip=True))
    
    # Location from .location
    loc_el = card.select_one('.location, p.location')
    if loc_el:
        city, state = parse_location(loc_el.get_text(strip=True))
        data['city'] = city
        data['state'] = state
    
    # Description from .description
    desc_el = card.select_one('.description, p.description')
    if desc_el:
        data['description'] = desc_el.get_text(strip=True)[:500]
    
    return data


def parse_single_listing(card) -> dict:
    """Parse a single listing card (old-style a.diamond/a.showcase)."""
    data = {
        'source': 'bizbuysell',
        'external_id': None,
        'url': None,
        'title': None,
        'asking_price': None,
        'cash_flow': None,
        'gross_revenue': None,
        'ebitda': None,
        'city': None,
        'state': None,
        'description': None,
        'category': None,
        'listing_type': None,
        'photo_count': None,
        'real_estate_included': None,
    }
    
    # URL and external ID
    href = card.get('href', '')
    if href:
        data['url'] = href if href.startswith('http') else f"https://www.bizbuysell.com{href}"
        # Extract ID from URL
        match = re.search(r'/(\d+)/?(?:\?|$)', href)
        if match:
            data['external_id'] = match.group(1)
    
    # Listing type
    if 'diamond' in card.get('class', []):
        data['listing_type'] = 'diamond'
    elif 'showcase' in card.get('class', []):
        data['listing_type'] = 'showcase'
    
    # Title
    title_el = card.select_one('.title, h3, h4')
    if title_el:
        data['title'] = title_el.get_text(strip=True)
    
    # Price
    price_el = card.select_one('.asking-price, .price')
    if price_el:
        data['asking_price'] = parse_price(price_el.get_text(strip=True))
    
    # Cash flow
    cf_el = card.select_one('.cash-flow')
    if cf_el:
        data['cash_flow'] = parse_price(cf_el.get_text(strip=True))
    
    # Location
    loc_el = card.select_one('.location')
    if loc_el:
        city, state = parse_location(loc_el.get_text(strip=True))
        data['city'] = city
        data['state'] = state
    
    # Description
    desc_el = card.select_one('.text, .description, p')
    if desc_el:
        data['description'] = desc_el.get_text(strip=True)[:500]
    
    # Category
    cat_el = card.select_one('.category, .industry')
    if cat_el:
        data['category'] = cat_el.get_text(strip=True)
    
    return data


def parse_price(text: str) -> Optional[float]:
    """Parse price string like '$250,000' to float."""
    if not text:
        return None
    
    text_lower = text.lower()
    if any(x in text_lower for x in ['call', 'confidential', 'n/a', 'not disclosed']):
        return None
    
    cleaned = re.sub(r'[^\d.]', '', text)
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_location(text: str) -> tuple[Optional[str], Optional[str]]:
    """Parse location like 'Detroit, MI' to (city, state)."""
    if not text:
        return None, None
    
    parts = text.split(',')
    if len(parts) >= 2:
        city = parts[0].strip()
        state = parts[1].strip()[:2].upper()
        return city, state
    
    return text.strip(), None


def parse_detail_page(html: str, listing: dict) -> dict:
    """
    Parse a detail page to extract Revenue, EBITDA, etc.
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # BizBuySell uses <p> elements with <span class="title"> for labels
    for row in soup.select('p:has(span.title)'):
        title_el = row.select_one('span.title')
        if not title_el:
            continue
        
        title_text = title_el.get_text(strip=True).lower()
        
        # Find value span
        value_el = row.select_one('span.normal, span.flex-center.g4')
        if not value_el:
            value_el = title_el.find_next_sibling('span')
        
        if not value_el:
            continue
        
        value_text = value_el.get_text(strip=True)
        
        if 'not disclosed' in value_text.lower():
            continue
        
        if 'gross revenue' in title_text:
            listing['gross_revenue'] = parse_price(value_text)
        elif 'ebitda' in title_text:
            listing['ebitda'] = parse_price(value_text)
        elif 'cash flow' in title_text or 'sde' in title_text:
            if not listing.get('cash_flow'):
                listing['cash_flow'] = parse_price(value_text)
    
    return listing


async def scrape_with_details(
    state: str = "MI",
    max_pages: int = 25,
    max_details: int = 100,
) -> list[dict]:
    """
    Scrape listings AND their detail pages for Revenue/EBITDA.
    
    WARNING: This is slow! ~3 seconds per detail page.
    For 500 listings = ~25 minutes per state.
    """
    logger.info(f"Starting DETAIL scrape for {state}")
    logger.info(f"Will scrape up to {max_pages} pages, then {max_details} detail pages")
    
    start_time = datetime.now()
    
    # First get listings from search pages
    listings = await scrape_bizbuysell(
        state=state,
        max_pages=max_pages,
        stealth_mode=True,
        warm_up=True,
    )
    
    if not listings:
        return []
    
    logger.info(f"Found {len(listings)} listings, now visiting detail pages...")
    
    # Visit detail pages
    async with async_playwright() as p:
        browser, context, page, _ = await launch_browser(p, "firefox")
        
        try:
            details_scraped = 0
            
            for i, listing in enumerate(listings[:max_details]):
                url = listing.get('url')
                if not url:
                    continue
                
                logger.info(f"[{i+1}/{min(len(listings), max_details)}] {url[:60]}...")
                
                try:
                    response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                    
                    if response and response.status == 200:
                        await human_delay(1, 2)
                        content = await page.content()
                        
                        if "Access Denied" not in content:
                            parse_detail_page(content, listing)
                            details_scraped += 1
                            
                            if listing.get('gross_revenue'):
                                logger.info(f"  Found Revenue: ${listing['gross_revenue']:,.0f}")
                        else:
                            logger.warning("Access Denied on detail page")
                            break
                    
                    # Random pause
                    if random.random() < 0.1:
                        await human_delay(5, 10)
                    
                except Exception as e:
                    logger.warning(f"Error on detail page: {e}")
            
        finally:
            await context.close()
            await browser.close()
    
    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    with_revenue = sum(1 for l in listings if l.get('gross_revenue'))
    with_ebitda = sum(1 for l in listings if l.get('ebitda'))
    
    logger.info(f"=" * 60)
    logger.info(f"Detail scrape complete in {duration/60:.1f} minutes")
    logger.info(f"Revenue: {with_revenue}/{len(listings)} ({100*with_revenue/len(listings):.1f}%)")
    logger.info(f"EBITDA: {with_ebitda}/{len(listings)} ({100*with_ebitda/len(listings):.1f}%)")
    logger.info(f"=" * 60)
    
    return listings


# Quick test
if __name__ == "__main__":
    async def test():
        listings = await scrape_bizbuysell(state="MI", max_pages=1)
        print(f"Found {len(listings)} listings")
        for l in listings[:3]:
            print(f"  - {l.get('title', 'Unknown')[:50]}")
    
    asyncio.run(test())
