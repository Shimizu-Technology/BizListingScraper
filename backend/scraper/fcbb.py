"""
FCBB (First Choice Business Brokers) Scraper

Site: https://fcbb.com
Structure: Server-rendered pages with Angular frontend
Data Available: Price, Revenue, Total Income (Cash Flow), Category, Location

URL Pattern: https://fcbb.com/businesses-for-sale?location={STATE}&page={N}
"""
import asyncio
import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# State name mappings
STATE_NAMES = {
    "MI": "Michigan",
    "CT": "Connecticut",
}


def parse_price(text: str) -> Optional[float]:
    """Parse price string like '$60,000' to float."""
    if not text:
        return None
    
    text_clean = text.strip()
    if any(x in text_clean.lower() for x in ['call', 'confidential', 'n/a', 'not disclosed', '-']):
        return None
    
    # Extract numbers
    cleaned = re.sub(r'[^\d.]', '', text_clean)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_listing_card(card_element, soup_context) -> dict:
    """Parse a single listing card from FCBB.
    
    Structure:
    - div.listing contains a.diamond (link) with data-id
    - h3.title has the title
    - p.location has location
    - p.description has description
    - div.finance contains:
        - p.asking-price
        - p.cash-flow (multiple: Total Income, Revenue, Listing Number, Category)
    """
    data = {
        'source': 'fcbb',
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
        'listing_number': None,
    }
    
    # Get external ID from data-id attribute
    link_elem = card_element.select_one('a[data-id]')
    if link_elem:
        data['external_id'] = link_elem.get('data-id')
        href = link_elem.get('href', '')
        if href:
            data['url'] = f"https://fcbb.com{href}" if href.startswith('/') else href
    
    # Get title
    title_elem = card_element.select_one('h3.title, h2.title, .title')
    if title_elem:
        data['title'] = title_elem.get_text(strip=True)[:200]
    
    # Get description
    desc_elem = card_element.select_one('p.description')
    if desc_elem:
        data['description'] = desc_elem.get_text(strip=True)[:500]
    
    # Get location
    loc_elem = card_element.select_one('p.location')
    if loc_elem:
        location_text = loc_elem.get_text(strip=True)
        # FCBB shows state in location
        data['city'] = location_text  # Will be overwritten if we parse further
    
    # Get asking price
    price_elem = card_element.select_one('p.asking-price')
    if price_elem:
        data['asking_price'] = parse_price(price_elem.get_text(strip=True))
    
    # Get financial info from p.cash-flow elements
    cashflow_elems = card_element.select('p.cash-flow')
    for cf_elem in cashflow_elems:
        label_elem = cf_elem.select_one('span.label')
        if label_elem:
            label_text = label_elem.get_text(strip=True).lower()
            # Get value (text after the label)
            full_text = cf_elem.get_text(strip=True)
            value_text = full_text.replace(label_elem.get_text(), '').strip()
            
            if 'total income' in label_text:
                data['cash_flow'] = parse_price(value_text)
            elif 'revenue' in label_text:
                data['gross_revenue'] = parse_price(value_text)
            elif 'listing number' in label_text:
                data['listing_number'] = value_text
                # Use listing number as external_id if we don't have one
                if not data['external_id']:
                    data['external_id'] = value_text
            elif 'category' in label_text:
                data['category'] = value_text
    
    # Fallback: if no external_id, generate from title
    if not data['external_id'] and data['title']:
        import hashlib
        data['external_id'] = hashlib.md5(data['title'].encode()).hexdigest()[:12]
    
    return data


async def scrape_fcbb(
    state: str = "MI",
    max_pages: int = 20,
    save_backup: bool = True,
) -> list[dict]:
    """
    Scrape FCBB listings for a given state.
    
    Args:
        state: State code (e.g., "MI", "CT")
        max_pages: Maximum pages to scrape
        save_backup: Save results to JSON file
    
    Returns:
        List of listing dictionaries
    """
    logger.info(f"Starting FCBB scrape for {state}")
    
    all_listings = []
    states = [state]  # Wrap in list for compatibility with existing loop
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
        )
        page = await context.new_page()
        
        for state_code in states:
            state_name = STATE_NAMES.get(state_code, state_code)
            logger.info(f"Scraping FCBB for {state_name}...")
            
            state_listings = []
            page_num = 1
            consecutive_empty = 0
            
            while page_num <= max_pages:
                url = f"https://fcbb.com/businesses-for-sale?location={state_name}&page={page_num}"
                logger.info(f"  Page {page_num}: {url}")
                
                try:
                    await page.goto(url, timeout=60000, wait_until='domcontentloaded')
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Get page content
                    content = await page.content()
                    soup = BeautifulSoup(content, 'lxml')
                    
                    # Find listing cards
                    cards = soup.select('div.listing')
                    
                    if not cards:
                        # Try alternative selectors
                        cards = soup.select('[class*="listing-card"], article.listing')
                    
                    if not cards:
                        consecutive_empty += 1
                        logger.info(f"    No listings found on page {page_num}")
                        if consecutive_empty >= 2:
                            logger.info(f"    Reached end of listings for {state_name}")
                            break
                    else:
                        consecutive_empty = 0
                        
                        for card in cards:
                            listing = parse_listing_card(card, soup)
                            
                            # Set state
                            listing['state'] = state_code
                            
                            # Only add if we have some data
                            if listing.get('external_id') or listing.get('title'):
                                state_listings.append(listing)
                                logger.debug(f"    Found: {listing.get('title', 'No title')[:50]}")
                        
                        logger.info(f"    Found {len(cards)} listings on page {page_num}")
                    
                    page_num += 1
                    
                except Exception as e:
                    logger.error(f"    Error on page {page_num}: {e}")
                    page_num += 1
                    continue
            
            logger.info(f"  {state_name}: {len(state_listings)} total listings")
            all_listings.extend(state_listings)
        
        await browser.close()
    
    # Save backup
    if save_backup and all_listings:
        backup_dir = Path(__file__).parent.parent / "data"
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"fcbb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump(all_listings, f, indent=2, default=str)
        logger.info(f"Backup saved to {backup_file}")
    
    logger.info(f"FCBB scrape complete: {len(all_listings)} total listings")
    return all_listings


async def scrape_and_save_fcbb(
    states: list[str] = ["MI", "CT"],
    save_to_db: bool = True,
) -> dict:
    """Scrape FCBB and save to database."""
    from scraper.upsert import bulk_upsert_listings
    
    logger.info("=" * 50)
    logger.info(f"Scraping FCBB for {states}...")
    logger.info("=" * 50)
    
    listings = await scrape_fcbb(states=states, save_backup=True)
    
    summary = {
        'total_scraped': len(listings),
        'inserted': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0,
        'by_state': {},
    }
    
    # Count by state
    for listing in listings:
        state = listing.get('state', 'Unknown')
        summary['by_state'][state] = summary['by_state'].get(state, 0) + 1
    
    if save_to_db and listings:
        logger.info(f"Saving {len(listings)} listings to database...")
        result = bulk_upsert_listings(listings, source='fcbb')
        summary['inserted'] = result.get('inserted', 0)
        summary['updated'] = result.get('updated', 0)
        summary['unchanged'] = result.get('unchanged', 0)
    
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        listings = await scrape_fcbb(states=["MI"], max_pages=5)
        print(f"\nFound {len(listings)} listings")
        for l in listings[:3]:
            print(f"\n{l.get('title', 'No title')}")
            print(f"  Price: ${l.get('asking_price', 0):,.0f}" if l.get('asking_price') else "  Price: N/A")
            print(f"  Cash Flow: ${l.get('cash_flow', 0):,.0f}" if l.get('cash_flow') else "  Cash Flow: N/A")
            print(f"  Revenue: ${l.get('gross_revenue', 0):,.0f}" if l.get('gross_revenue') else "  Revenue: N/A")
            print(f"  Category: {l.get('category', 'N/A')}")
    
    asyncio.run(test())

