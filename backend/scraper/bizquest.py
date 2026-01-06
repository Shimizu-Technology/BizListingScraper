"""
BizQuest scraper - extracts structured JSON data embedded in pages.

KEY DIFFERENCES FROM BIZBUYSELL:
1. Data is embedded as JSON in <script> tags - no HTML parsing needed
2. Cash Flow and EBITDA available on listing cards
3. Uses Angular SPA with JavaScript filtering
4. State filtering via UI interaction (not URL-based)
"""

import asyncio
import json
import re
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path
from playwright.async_api import async_playwright, Page

from .stealth import (
    get_random_viewport,
    human_delay,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State name mapping for filtering
STATE_NAMES = {
    "MI": "Michigan",
    "CT": "Connecticut",
    "OH": "Ohio",
    "IN": "Indiana",
    "IL": "Illinois",
    "WI": "Wisconsin",
    "FL": "Florida",
    "TX": "Texas",
    "CA": "California",
    "NY": "New York",
    "PA": "Pennsylvania",
}

# Region ID mapping (from BizQuest's internal data)
STATE_REGION_IDS = {
    "MI": 38,  # Michigan
    "CT": 22,  # Connecticut
    "OH": 49,  # Ohio
    "FL": 25,  # Florida
    # Add more as discovered
}


class BizQuestScrapeResult:
    """Container for BizQuest scrape results."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.listings: list = []
        self.pages_scraped: int = 0
        self.errors: int = 0
        self.state: str = ""
    
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
            f"BizQuest {self.state} | "
            f"Pages: {self.pages_scraped} | "
            f"Listings: {len(self.listings)} | "
            f"Time: {self.duration_formatted} | "
            f"Errors: {self.errors}"
        )


def extract_json_data(html: str) -> Optional[list]:
    """
    Extract the embedded JSON listing data from BizQuest page.
    
    BizQuest embeds listing data in a "value" array within the page HTML.
    The data is part of Angular's server-side rendered content.
    """
    import json
    
    # Find the start of listing data by looking for the first listing object
    # Pattern: look for {"header":" which starts a listing
    idx = html.find('{"header":"')
    if idx < 0:
        return None
    
    # Find the array start (go backwards to find '[')
    array_start = html.rfind('[', 0, idx)
    if array_start < 0:
        return None
    
    # Find matching closing bracket using depth counting
    depth = 0
    array_end = array_start
    for i, char in enumerate(html[array_start:array_start + 1000000]):
        if char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                array_end = array_start + i + 1
                break
    
    listings_json = html[array_start:array_end]
    
    try:
        listings = json.loads(listings_json)
        # Filter to real listings only (type >= 0 and has header)
        return [l for l in listings if l.get('type', 0) >= 0 and l.get('header')]
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}")
        return None


def parse_bizquest_listing(raw: dict, state: str) -> Optional[dict]:
    """
    Parse a single BizQuest listing from JSON data.
    
    Maps BizQuest's JSON structure to our database schema.
    """
    try:
        # Skip franchises and broker listings (type -1 or -2)
        listing_type = raw.get('type', 0)
        if listing_type < 0:
            return None
        
        # Extract list number for unique ID
        list_number = raw.get('listNumber') or raw.get('specificId')
        if not list_number:
            return None
        
        # Build source URL
        url_stub = raw.get('urlStub', '')
        if url_stub and not url_stub.startswith('http'):
            source_url = f"https://www.bizquest.com{url_stub}"
        else:
            source_url = url_stub or f"https://www.bizquest.com/business-for-sale/{list_number}/"
        
        # Parse location
        location = raw.get('location', '')
        city, location_state = '', state
        if location:
            parts = location.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                location_state = parts[-1].strip()
            elif len(parts) == 1:
                city = parts[0].strip()
        
        # Get diamond metadata if available
        diamond = raw.get('diamondMetaData') or {}
        
        # Determine listing type label
        listing_type_id = raw.get('listingTypeId', 0)
        type_label = "Business"
        if listing_type_id == 40:
            type_label = "Business for Sale"
        elif listing_type_id == -1:
            type_label = "Franchise"
        
        # Return in database-compatible format
        # Note: 'external_id' is what the upsert function expects
        return {
            'source': 'bizquest',
            'external_id': f"bq-{list_number}",  # Prefixed to avoid collision with bizbuysell
            'url': source_url,
            'title': raw.get('header', ''),
            'description': raw.get('description', ''),
            'asking_price': raw.get('price'),
            'cash_flow': raw.get('cashFlow'),
            'gross_revenue': None,  # Not typically on card
            'ebitda': raw.get('ebitda'),
            'city': city,
            'state': location_state if len(location_state) == 2 else state,
            'listing_type': type_label,
            'real_estate_included': raw.get('realEstateIncludedInAskingPrice', False),
            'category': diamond.get('bqPrimaryBizTypeName', ''),
            'is_active': True,
        }
    except Exception as e:
        logger.warning(f"Error parsing listing: {e}")
        return None


async def extract_listings_from_dom(page, state: str) -> list[dict]:
    """Extract listings from visible DOM elements."""
    raw_listings = await page.evaluate('''
        () => {
            const listings = [];
            const cards = document.querySelectorAll("div.listing");
            
            for (const card of cards) {
                const titleEl = card.querySelector("h3.title, h2.title");
                const priceEl = card.querySelector("p.asking-price, .asking-price");
                const cfEl = card.querySelector("p.cash-flow, .cash-flow");
                const ebitdaEl = card.querySelector(".ebitda, [class*='ebitda']");
                const locationEl = card.querySelector(".location");
                
                // Extract list number from image URL if available
                let listNumber = null;
                const imgEl = card.querySelector("img[src*='/listings/']");
                if (imgEl && imgEl.src) {
                    const match = imgEl.src.match(/\\/listings\\/\\d+\\/(\\d+)\\//);
                    if (match) {
                        listNumber = match[1];
                    }
                }
                
                if (titleEl) {
                    listings.push({
                        title: titleEl.textContent.trim(),
                        priceText: priceEl ? priceEl.textContent.trim() : null,
                        cashFlowText: cfEl ? cfEl.textContent.trim() : null,
                        ebitdaText: ebitdaEl ? ebitdaEl.textContent.trim() : null,
                        location: locationEl ? locationEl.textContent.trim() : null,
                        listNumber: listNumber,  // May be null for non-premium listings
                    });
                }
            }
            return listings;
        }
    ''')
    
    # Parse raw listings into database format
    parsed = []
    for raw in raw_listings:
        if not raw.get('title'):
            continue
        
        title = raw['title']
        list_num = raw.get('listNumber')
        
        # Generate external ID and URL
        if list_num:
            external_id = f"bq-{list_num}"
            title_slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
            url = f"https://www.bizquest.com/business-for-sale/{title_slug}/BW{list_num}/"
        else:
            # Use title hash for non-premium listings
            title_hash = abs(hash(title)) % (10**10)
            external_id = f"bq-h{title_hash}"
            # Use search URL as fallback (can't link directly without list number)
            url = f"https://www.bizquest.com/businesses-for-sale-in-{state.lower()}-{state.lower()}/"
        
        # Parse price
        price = None
        if raw.get('priceText'):
            price_match = re.search(r'\$[\d,]+', raw['priceText'])
            if price_match:
                price = int(re.sub(r'[^\d]', '', price_match.group()))
        
        # Parse cash flow
        cash_flow = None
        if raw.get('cashFlowText'):
            cf_match = re.search(r'\$[\d,]+', raw['cashFlowText'])
            if cf_match:
                cash_flow = int(re.sub(r'[^\d]', '', cf_match.group()))
        
        # Parse EBITDA
        ebitda = None
        if raw.get('ebitdaText'):
            ebitda_match = re.search(r'\$[\d,]+', raw['ebitdaText'])
            if ebitda_match:
                ebitda = int(re.sub(r'[^\d]', '', ebitda_match.group()))
        
        # Parse location
        city = raw.get('location', '').replace(state, '').strip().strip(',')
        
        parsed.append({
            'source': 'bizquest',
            'external_id': external_id,
            'url': url,
            'title': title,
            'asking_price': price,
            'cash_flow': cash_flow,
            'ebitda': ebitda,
            'city': city,
            'state': state,
            'is_active': True,
        })
    
    return parsed


async def scrape_bizquest(
    state: str = "MI",
    max_pages: int = 10,
    save_backup: bool = True,
) -> list[dict]:
    """
    Scrape BizQuest listings for a specific state using DOM-based pagination.
    
    Uses Angular's ngx-pagination to navigate through all pages.
    Extracts ~50-60 listings per page.
    
    Args:
        state: Two-letter state code (e.g., "MI", "CT")
        max_pages: Maximum pages to scrape
        save_backup: Save listings to JSON file as backup
    
    Returns:
        List of parsed listing dictionaries
    """
    result = BizQuestScrapeResult()
    result.state = state
    state_name = STATE_NAMES.get(state, state)
    state_lower = state_name.lower().replace(' ', '-')
    
    logger.info(f"Starting BizQuest scrape for {state_name}...")
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport=get_random_viewport(),
            locale='en-US',
        )
        page = await context.new_page()
        
        try:
            # Navigate to state-specific URL
            state_url = f'https://www.bizquest.com/businesses-for-sale-in-{state_lower}-{state.lower()}/'
            logger.info(f"Navigating to {state_url}")
            await page.goto(state_url, wait_until='domcontentloaded', timeout=60000)
            await human_delay(3, 5)
            
            all_listings = []
            seen_titles = set()
            page_num = 1
            consecutive_empty = 0
            
            while page_num <= max_pages:
                logger.info(f"Processing page {page_num}...")
                
                # For page 2+, navigate via URL (more reliable than clicking)
                if page_num > 1:
                    page_url = f'https://www.bizquest.com/businesses-for-sale-in-{state_lower}-{state.lower()}/page-{page_num}/'
                    try:
                        response = await page.goto(page_url, wait_until='domcontentloaded', timeout=30000)
                        await human_delay(2, 4)
                        
                        # Check for redirect (page doesn't exist)
                        if response and response.url != page_url:
                            logger.info(f"Page {page_num} redirected - reached end")
                            break
                    except Exception as e:
                        logger.info(f"Failed to navigate to page {page_num}: {e}")
                        break
                
                # Extract from DOM
                page_listings = await extract_listings_from_dom(page, state)
                
                # Filter duplicates
                new_listings = []
                for l in page_listings:
                    if l['title'] not in seen_titles:
                        seen_titles.add(l['title'])
                        new_listings.append(l)
                
                logger.info(f"Page {page_num}: {len(page_listings)} visible, {len(new_listings)} new")
                all_listings.extend(new_listings)
                result.pages_scraped += 1
                
                if len(new_listings) == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        logger.info("Multiple empty pages - reached end")
                        break
                else:
                    consecutive_empty = 0
                
                page_num += 1
            
            result.listings = all_listings
            
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            result.errors += 1
        finally:
            await browser.close()
    
    result.finish()
    logger.info(str(result))
    
    # Save backup
    if save_backup and result.listings:
        backup_dir = Path(__file__).parent.parent / 'data'
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f'bizquest_{state}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(result.listings, f, indent=2, default=str)
        logger.info(f"Backup saved to {backup_file}")
    
    return result.listings


async def test_bizquest_extraction():
    """
    Quick test to verify JSON extraction works.
    """
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto('https://www.bizquest.com/businesses-for-sale/')
            await asyncio.sleep(5)
            
            html = await page.content()
            
            # Find all JSON-like content
            print(f"Page length: {len(html)} chars")
            
            # Check for listing data
            if '"listings"' in html:
                print("✓ Found 'listings' key in page")
            if '"cashFlow"' in html:
                print("✓ Found 'cashFlow' key in page")
            if '"ebitda"' in html:
                print("✓ Found 'ebitda' key in page")
            
            # Try extraction
            data = extract_json_data(html)
            if data:
                print(f"✓ Extracted {len(data)} listings")
                if data:
                    print(f"Sample: {json.dumps(data[0], indent=2)[:500]}")
            else:
                print("✗ Could not extract JSON data")
                # Debug: print script tags
                import re
                scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
                for i, script in enumerate(scripts):
                    if 'listings' in script.lower():
                        print(f"Script {i} contains 'listings' ({len(script)} chars)")
            
        finally:
            await browser.close()


async def scrape_and_save_bizquest(
    states: list[str] = ["MI", "CT"],
    save_to_db: bool = True,
) -> dict:
    """
    Scrape BizQuest listings for multiple states and save to database.
    
    Args:
        states: List of state codes to scrape
        save_to_db: Whether to save to database
    
    Returns:
        Summary dict with counts
    """
    from .upsert import bulk_upsert_listings
    from app.database import init_pool
    import time
    
    if save_to_db:
        init_pool()
    
    summary = {
        'total_scraped': 0,
        'inserted': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0,
        'by_state': {},
    }
    
    for state in states:
        logger.info(f"\n{'='*50}")
        logger.info(f"Scraping BizQuest for {state}...")
        logger.info(f"{'='*50}")
        
        listings = await scrape_bizquest(state=state, max_pages=100, save_backup=True)  # 100 = get ALL pages
        summary['by_state'][state] = len(listings)
        summary['total_scraped'] += len(listings)
        
        if save_to_db and listings:
            logger.info(f"Bulk saving {len(listings)} {state} listings to database...")
            start = time.time()
            
            try:
                result = bulk_upsert_listings(listings, source='bizquest')
                summary['inserted'] += result['inserted']
                summary['updated'] += result['updated']
                summary['unchanged'] += result['unchanged']
                summary['errors'] += result['errors']
                
                elapsed = time.time() - start
                logger.info(f"DB save completed in {elapsed:.1f}s - Inserted: {result['inserted']}, Updated: {result['updated']}, Unchanged: {result['unchanged']}")
            except Exception as e:
                logger.error(f"Bulk upsert error for {state}: {e}")
                summary['errors'] += len(listings)
    
    logger.info(f"\n{'='*50}")
    logger.info(f"BizQuest Scrape Complete!")
    logger.info(f"Total scraped: {summary['total_scraped']}")
    logger.info(f"Inserted: {summary['inserted']}, Updated: {summary['updated']}, Unchanged: {summary['unchanged']}")
    logger.info(f"Errors: {summary['errors']}")
    logger.info(f"{'='*50}")
    
    return summary


if __name__ == "__main__":
    # Run full scrape
    asyncio.run(scrape_and_save_bizquest(states=["MI", "CT"], save_to_db=True))

