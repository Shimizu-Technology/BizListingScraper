"""BusinessesForSale.com scraper."""
import asyncio
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# State URL slugs
STATE_SLUGS = {
    'MI': 'michigan',
    'CT': 'connecticut',
}


def parse_price(text: str) -> float | None:
    """Parse price from text like '$1,500,000'."""
    if not text:
        return None
    # Remove currency and clean
    cleaned = text.replace('$', '').replace(',', '').strip()
    match = re.search(r'([\d.]+)', cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def parse_location(text: str) -> tuple[str | None, str | None]:
    """Parse city/county, state from location text like 'Berrien County, Michigan, US'."""
    if not text:
        return None, None
    
    parts = [p.strip() for p in text.split(',')]
    
    if len(parts) >= 2:
        city_or_county = parts[0]
        # Try to extract state abbreviation
        for i, part in enumerate(parts):
            if part.lower() in ['michigan', 'mi']:
                return city_or_county, 'MI'
            elif part.lower() in ['connecticut', 'ct']:
                return city_or_county, 'CT'
        return city_or_county, parts[1][:2].upper() if len(parts[1]) >= 2 else None
    
    return text.strip(), None


def parse_listing_page(html: str) -> list[dict]:
    """Parse listings from BusinessesForSale search results page."""
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    
    # Find all result divs
    cards = soup.select('div.result')
    
    for card in cards:
        try:
            listing = parse_single_listing(card)
            if listing and listing.get('external_id'):
                listings.append(listing)
        except Exception as e:
            logger.debug(f"Error parsing listing: {e}")
    
    return listings


def parse_single_listing(card) -> dict | None:
    """Parse a single listing card from BusinessesForSale."""
    data = {
        'source': 'businessesforsale',
        'external_id': None,
        'url': None,
        'title': None,
        'asking_price': None,
        'cash_flow': None,
        'gross_revenue': None,
        'ebitda': None,
        'city': None,
        'state': None,
        'county': None,
        'description': None,
        'category': None,
    }
    
    # Title and URL
    title_link = card.select_one('h2 a')
    if title_link:
        data['title'] = title_link.get_text(strip=True)
        href = title_link.get('href', '')
        if href:
            data['url'] = href if href.startswith('http') else f"https://us.businessesforsale.com{href}"
            # Generate external ID from URL
            slug = href.split('/')[-1].replace('.aspx', '')
            data['external_id'] = hashlib.md5(slug.encode()).hexdigest()[:16]
    
    if not data['external_id']:
        return None
    
    # Location
    loc_el = card.select_one('tr.t-loc td')
    if loc_el:
        loc_text = loc_el.get_text(strip=True)
        city, state = parse_location(loc_text)
        data['city'] = city
        data['state'] = state
    
    # Description
    desc_el = card.select_one('tr.t-desc td p')
    if desc_el:
        data['description'] = desc_el.get_text(strip=True)[:500]
    
    # Financial data is in table rows: <th>Label:</th><td>Value</td>
    table_rows = card.select('tr')
    for row in table_rows:
        th = row.select_one('th')
        td = row.select_one('td')
        if th and td:
            label = th.get_text(strip=True).lower()
            value = td.get_text(strip=True)
            
            if 'asking price' in label:
                data['asking_price'] = parse_price(value)
            elif 'cash flow' in label or 'net profit' in label:
                data['cash_flow'] = parse_price(value)
            elif 'revenue' in label or 'turnover' in label:
                data['gross_revenue'] = parse_price(value)
            elif 'ebitda' in label:
                data['ebitda'] = parse_price(value)
    
    return data


async def scrape_businessesforsale(
    state: str = 'MI',
    max_pages: int = 50,
    save_backup: bool = False
) -> list[dict]:
    """
    Scrape BusinessesForSale.com listings.
    
    Args:
        state: State code (e.g., 'MI', 'CT')
        max_pages: Maximum number of pages to scrape
        save_backup: Whether to save HTML backups
    
    Returns:
        List of listing dictionaries
    """
    if state not in STATE_SLUGS:
        logger.error(f"Unknown state: {state}. Known: {list(STATE_SLUGS.keys())}")
        return []
    
    state_slug = STATE_SLUGS[state]
    base_url = f"https://us.businessesforsale.com/us/search/businesses-for-sale-in-{state_slug}"
    
    all_listings = []
    seen_ids = set()
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        logger.info(f"Starting BusinessesForSale scrape for {state}...")
        
        page_num = 1
        consecutive_empty = 0
        
        while page_num <= max_pages:
            # Construct URL (page 1 has no suffix)
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}-{page_num}"
            
            logger.info(f"Processing page {page_num}: {url}")
            
            try:
                await page.goto(url, timeout=60000)
                await asyncio.sleep(3)
                
                # Check for Cloudflare
                text = await page.evaluate("() => document.body.innerText")
                if "Just a moment" in text or "Checking your browser" in text:
                    logger.info("Waiting for Cloudflare verification...")
                    await asyncio.sleep(10)
                
                # Get HTML
                html = await page.content()
                
                if save_backup:
                    backup_path = f"/tmp/bfs_{state}_page{page_num}.html"
                    with open(backup_path, 'w') as f:
                        f.write(html)
                
                # Parse listings
                page_listings = parse_listing_page(html)
                
                # Filter duplicates
                new_listings = []
                for l in page_listings:
                    if l.get('external_id') and l['external_id'] not in seen_ids:
                        seen_ids.add(l['external_id'])
                        l['state'] = state  # Ensure state is set correctly
                        new_listings.append(l)
                
                logger.info(f"  Page {page_num}: {len(page_listings)} found, {len(new_listings)} new")
                all_listings.extend(new_listings)
                
                if len(new_listings) == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        logger.info("No new listings for 2 pages - stopping")
                        break
                else:
                    consecutive_empty = 0
                
                # Add delay between pages
                await asyncio.sleep(2)
                page_num += 1
                
            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                break
        
        await browser.close()
    
    logger.info(f"BusinessesForSale {state} complete: {len(all_listings)} listings")
    return all_listings


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    state = sys.argv[1] if len(sys.argv) > 1 else 'MI'
    
    async def main():
        listings = await scrape_businessesforsale(state=state, max_pages=5, save_backup=True)
        print(f"\nFound {len(listings)} listings for {state}")
        
        if listings:
            # Stats
            with_price = sum(1 for l in listings if l.get('asking_price'))
            with_cf = sum(1 for l in listings if l.get('cash_flow'))
            with_rev = sum(1 for l in listings if l.get('gross_revenue'))
            
            print(f"\nData availability:")
            print(f"  Price: {with_price}/{len(listings)} ({100*with_price/len(listings):.0f}%)")
            print(f"  Cash Flow: {with_cf}/{len(listings)} ({100*with_cf/len(listings):.0f}%)")
            print(f"  Revenue: {with_rev}/{len(listings)} ({100*with_rev/len(listings):.0f}%)")
            
            print("\nSample listings:")
            for l in listings[:5]:
                print(f"  - {l['title'][:50] if l['title'] else 'No title'}")
                print(f"    Price: ${l['asking_price']:,.0f}" if l['asking_price'] else "    Price: N/A")
                print(f"    Cash Flow: ${l['cash_flow']:,.0f}" if l['cash_flow'] else "    Cash Flow: N/A")
                print(f"    Revenue: ${l['gross_revenue']:,.0f}" if l['gross_revenue'] else "    Revenue: N/A")
                print(f"    Location: {l['city']}, {l['state']}")
                print()
    
    asyncio.run(main())

