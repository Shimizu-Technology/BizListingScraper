"""Transworld Business Advisors scraper."""
import asyncio
import hashlib
import json
import logging
import re
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# State codes used by Transworld
STATE_CODES = {
    'MI': {'value': 38, 'name': 'Michigan'},
    'CT': {'value': 14, 'name': 'Connecticut'},
    # Add more as needed
}


def parse_price(text: str) -> float | None:
    """Parse price from text like '$1,500,000'."""
    if not text or text == '--':
        return None
    match = re.search(r'\$?([\d,]+)', text.replace(',', '').replace(' ', ''))
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except ValueError:
            pass
    return None


def parse_location(text: str) -> tuple[str | None, str | None]:
    """Parse city, state from location text like 'Genesee County, Michigan'."""
    if not text:
        return None, None
    
    # Pattern: "County, State" or "City, State"
    parts = text.split(',')
    if len(parts) >= 2:
        city_or_county = parts[0].strip()
        state = parts[-1].strip()
        return city_or_county, state
    
    return text.strip(), None


def parse_listing_html(html: str, state_code: str) -> list[dict]:
    """Parse listings from Transworld search results page."""
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    
    # Find all listing anchor tags - they contain 'buy-a-business/listings' in href
    listing_links = soup.select('a[href*="buy-a-business/listings"]')
    
    for link in listing_links:
        try:
            listing = parse_single_listing(link, state_code)
            if listing and listing.get('external_id'):
                listings.append(listing)
        except Exception as e:
            logger.debug(f"Error parsing listing: {e}")
    
    return listings


def parse_single_listing(link_el, state_code: str) -> dict | None:
    """Parse a single listing card from Transworld."""
    data = {
        'source': 'transworld',
        'external_id': None,
        'url': None,
        'title': None,
        'asking_price': None,
        'cash_flow': None,
        'gross_revenue': None,
        'ebitda': None,
        'city': None,
        'state': state_code,
        'county': None,
        'description': None,
        'category': None,
        'down_payment': None,
    }
    
    # URL
    href = link_el.get('href', '')
    if not href or 'buy-a-business/listings' not in href:
        return None
    
    if href.startswith('/'):
        data['url'] = f"https://www.tworld.com{href.split('?')[0]}"
    else:
        data['url'] = href.split('?')[0]
    
    # Extract external ID from URL (title slug -> hash to keep it short)
    url_path = href.split('?')[0]
    if '/listings/' in url_path:
        slug = url_path.split('/listings/')[-1].rstrip('/')
        # Use first 16 chars of hash to keep ID short but unique
        data['external_id'] = hashlib.md5(slug.encode()).hexdigest()[:16]
    
    # Title - look for h1 inside the card
    title_el = link_el.select_one('h1')
    if title_el:
        data['title'] = title_el.get_text(strip=True)
    
    # Look for data in nested divs with labels
    text_content = link_el.get_text(separator='|', strip=True)
    
    # Location
    loc_match = re.search(r'Location:\s*\|?\s*([^|]+)', text_content)
    if loc_match:
        loc_text = loc_match.group(1).strip()
        city, state = parse_location(loc_text)
        data['city'] = city  # This might be county name
        if state and state in ['Michigan', 'Connecticut']:
            data['state'] = 'MI' if state == 'Michigan' else 'CT'
    
    # Asking Price
    price_match = re.search(r'Asking Price:\s*\|?\s*\$?([\d,]+)', text_content)
    if price_match:
        data['asking_price'] = parse_price(price_match.group(1))
    
    # Down Payment
    down_match = re.search(r'Down Payment:\s*\|?\s*\$?([\d,]+)', text_content)
    if down_match:
        data['down_payment'] = parse_price(down_match.group(1))
    
    # Sellers Discretionary Earnings (Cash Flow)
    sde_match = re.search(r'Sellers Discretionary Earnings:\s*\|?\s*\$?([\d,]+)', text_content)
    if sde_match:
        data['cash_flow'] = parse_price(sde_match.group(1))
    
    return data


async def scrape_transworld(
    state: str = 'MI',
    max_pages: int = 20,
    save_backup: bool = False
) -> list[dict]:
    """
    Scrape Transworld Business Advisors listings.
    
    Args:
        state: State code (e.g., 'MI', 'CT')
        max_pages: Maximum number of pages to scrape
        save_backup: Whether to save HTML backups
    
    Returns:
        List of listing dictionaries
    """
    if state not in STATE_CODES:
        logger.error(f"Unknown state: {state}. Known: {list(STATE_CODES.keys())}")
        return []
    
    state_info = STATE_CODES[state]
    
    # Construct the search URL with JSON query
    search_query = {
        "country": {"value": 4, "name": "United States"},
        "state": {"value": state_info['value'], "name": state_info['name']},
        "sort": {"value": "-c_listing_price__c", "name": "Price ($$$ to $)"}
    }
    
    base_url = f"https://www.tworld.com/buy-a-business/business-listing-search?listing={quote(json.dumps(search_query))}"
    
    all_listings = []
    seen_ids = set()
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        logger.info(f"Starting Transworld scrape for {state}...")
        
        try:
            page_num = 1
            consecutive_empty = 0
            
            while page_num <= max_pages:
                # Construct URL with page parameter
                page_url = f"{base_url}&page={page_num}"
                
                logger.info(f"Processing page {page_num}...")
                
                await page.goto(page_url, timeout=60000, wait_until='domcontentloaded')
                
                # Wait for listings to appear (SPA needs time to render)
                try:
                    await page.wait_for_selector('a[href*="buy-a-business/listings"]', timeout=15000)
                except Exception:
                    logger.debug("No listing selector found, waiting longer...")
                    await asyncio.sleep(5)
                
                # Get page HTML
                html = await page.content()
                
                if save_backup:
                    backup_path = f"/tmp/transworld_{state}_page{page_num}.html"
                    with open(backup_path, 'w') as f:
                        f.write(html)
                
                # Parse listings
                page_listings = parse_listing_html(html, state)
                
                # Filter duplicates
                new_listings = []
                for l in page_listings:
                    if l.get('external_id') and l['external_id'] not in seen_ids:
                        seen_ids.add(l['external_id'])
                        new_listings.append(l)
                
                logger.info(f"  Page {page_num}: {len(page_listings)} found, {len(new_listings)} new")
                all_listings.extend(new_listings)
                
                # If no listings on page, we've reached the end
                if len(page_listings) == 0:
                    logger.info("No listings on page - reached end")
                    break
                
                if len(new_listings) == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        logger.info("No new listings for 2 pages - stopping")
                        break
                else:
                    consecutive_empty = 0
                
                page_num += 1
                
                # Small delay between pages
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error during scrape: {e}")
        finally:
            await browser.close()
    
    logger.info(f"Transworld {state} complete: {len(all_listings)} listings")
    return all_listings


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    state = sys.argv[1] if len(sys.argv) > 1 else 'MI'
    
    async def main():
        listings = await scrape_transworld(state=state, save_backup=True)
        print(f"\nFound {len(listings)} listings for {state}")
        
        if listings:
            print("\nSample listings:")
            for l in listings[:5]:
                print(f"  - {l['title'][:50] if l['title'] else 'No title'}")
                print(f"    Price: ${l['asking_price']:,.0f}" if l['asking_price'] else "    Price: N/A")
                print(f"    Cash Flow: ${l['cash_flow']:,.0f}" if l['cash_flow'] else "    Cash Flow: N/A")
                print(f"    Location: {l['city']}, {l['state']}")
                print()
    
    asyncio.run(main())

