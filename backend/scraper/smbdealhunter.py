"""SMB Deal Hunter scraper."""
import asyncio
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


def parse_price(text: str) -> float | None:
    """Parse price from text like '$2,200,000'."""
    if not text or text == '-':
        return None
    # Handle M suffix (millions)
    if 'M' in text.upper():
        match = re.search(r'\$?([\d.]+)\s*M', text, re.I)
        if match:
            return float(match.group(1)) * 1_000_000
    # Regular price
    cleaned = re.sub(r'[^\d.]', '', text)
    if cleaned:
        try:
            return float(cleaned)
        except ValueError:
            pass
    return None


def parse_listing_page(html: str, state: str) -> list[dict]:
    """Parse listings from SMB Deal Hunter page."""
    listings = []
    
    # SMB Deal Hunter uses Softr with embedded data
    # Try to extract from the visible DOM elements
    soup = BeautifulSoup(html, 'lxml')
    
    # The listings are in a specific structure with labels
    # Find all elements that have "Asking Price" label followed by value
    all_text = soup.get_text(separator='\n')
    
    # Split into potential listings by looking for "Asking Price" patterns
    parts = all_text.split('Asking Price')
    
    for i, part in enumerate(parts[1:], 1):  # Skip first part before any listing
        lines = part.split('\n')
        
        # Look for the structure: price on next line, then Cash Flow, Location, Date
        try:
            data = {
                'source': 'smbdealhunter',
                'external_id': None,
                'url': 'https://app.smbdealhunter.xyz/',
                'title': None,
                'asking_price': None,
                'cash_flow': None,
                'gross_revenue': None,
                'ebitda': None,
                'city': None,
                'state': state,
                'description': None,
            }
            
            # Find title - it's usually before "Asking Price" in the previous chunk
            if i > 0 and i < len(parts):
                prev_part = parts[i-1] if i > 0 else ''
                prev_lines = [l.strip() for l in prev_part.split('\n') if l.strip()]
                # Title is usually the last meaningful line before "Asking Price"
                for line in reversed(prev_lines[-5:]):
                    if len(line) > 10 and '$' not in line and not any(x in line.lower() for x in ['asking', 'cash', 'location', 'date']):
                        data['title'] = line[:100]
                        break
            
            # Parse the current part for financial data
            for j, line in enumerate(lines[:15]):
                line = line.strip()
                
                # Price (usually first $X line)
                if line.startswith('$') and not data['asking_price']:
                    data['asking_price'] = parse_price(line)
                    continue
                
                # Cash Flow/EBITDA value
                if 'Cash Flow' in lines[j-1] if j > 0 else False:
                    if line.startswith('$'):
                        data['cash_flow'] = parse_price(line)
                        
                # Location
                if 'Location' in (lines[j-1] if j > 0 else ''):
                    if state.lower() in line.lower() or 'michigan' in line.lower() or 'connecticut' in line.lower():
                        data['city'] = line
                        if 'michigan' in line.lower():
                            data['state'] = 'MI'
                        elif 'connecticut' in line.lower():
                            data['state'] = 'CT'
            
            if data['title']:
                data['external_id'] = hashlib.md5(data['title'].encode()).hexdigest()[:16]
                
                # Only include if matches state filter
                if state.lower() in (data.get('city') or '').lower() or \
                   ('michigan' in (data.get('city') or '').lower() and state == 'MI') or \
                   ('connecticut' in (data.get('city') or '').lower() and state == 'CT'):
                    listings.append(data)
                    
        except Exception as e:
            logger.debug(f"Error parsing listing part: {e}")
    
    return listings


def parse_single_listing(card, text: str, state: str) -> dict | None:
    """Parse a single SMB Deal Hunter listing."""
    data = {
        'source': 'smbdealhunter',
        'external_id': None,
        'url': 'https://app.smbdealhunter.xyz/',
        'title': None,
        'asking_price': None,
        'cash_flow': None,
        'gross_revenue': None,
        'ebitda': None,
        'city': None,
        'state': state,
        'description': None,
        'category': None,
        'date_added': None,
    }
    
    # Title - find text that's NOT a label or value
    # Looking at screenshot: titles like "Sign Manufacturer", "Roofing Company", "Moving Company"
    title_el = card.select_one('h1, h2, h3, h4, h5')
    if title_el:
        title_text = title_el.get_text(strip=True)
        if title_text and 'Asking' not in title_text and '$' not in title_text:
            data['title'] = title_text
    
    if not data['title']:
        # Look for title-like elements
        for el in card.select('[class*="title"], [class*="heading"], strong, b'):
            t = el.get_text(strip=True)
            if len(t) > 5 and len(t) < 100 and 'Asking' not in t and '$' not in t and 'Location' not in t and 'Date' not in t:
                data['title'] = t
                break
    
    if not data['title']:
        # Fallback: find text between separators that looks like a title
        parts = text.split('|')
        for part in parts:
            part = part.strip()
            if len(part) > 5 and len(part) < 80 and 'Asking' not in part and '$' not in part and 'Cash' not in part and 'Location' not in part and 'Date' not in part and 'VIEW' not in part:
                data['title'] = part
                break
    
    if not data['title']:
        return None
    
    # Generate external ID from title + state for uniqueness
    data['external_id'] = hashlib.md5(f"{data['title']}-{state}".encode()).hexdigest()[:16]
    
    # URL - look for VIEW DETAILS link
    link = card.select_one('a[href*="detail"]')
    if not link:
        # Find any link that says VIEW DETAILS
        for a in card.select('a'):
            if 'VIEW' in a.get_text().upper():
                link = a
                break
    if link:
        href = link.get('href', '')
        if href and not href.startswith('#'):
            data['url'] = href if href.startswith('http') else f"https://app.smbdealhunter.xyz{href}"
    
    # Asking Price - pattern: "Asking Price|$X,XXX,XXX"
    price_match = re.search(r'Asking Price[:\s|]*\$?([\d,]+(?:\.\d+)?)', text, re.I)
    if price_match:
        data['asking_price'] = parse_price('$' + price_match.group(1))
    
    # Also try to find standalone price after "Asking Price" label
    if not data['asking_price']:
        price_match = re.search(r'\|(\$[\d,]+)\|', text)
        if price_match:
            data['asking_price'] = parse_price(price_match.group(1))
    
    # Cash Flow/EBITDA - pattern: "Cash Flow/EBITDA|$XXX,XXX"
    cf_match = re.search(r'Cash Flow/?EBITDA[:\s|]*\$?([\d,]+(?:\.\d+)?)', text, re.I)
    if cf_match:
        data['cash_flow'] = parse_price('$' + cf_match.group(1))
    
    # Location - pattern: "Location|Michigan"
    loc_match = re.search(r'Location[:\s|]*([A-Za-z\s]+?)(?:\||Date|$)', text, re.I)
    if loc_match:
        loc = loc_match.group(1).strip()
        if 'Michigan' in loc:
            data['state'] = 'MI'
            data['city'] = 'Michigan'
        elif 'Connecticut' in loc:
            data['state'] = 'CT'
            data['city'] = 'Connecticut'
        else:
            data['city'] = loc
    
    # Date Added - pattern: "Date Added|M/D/YYYY"
    date_match = re.search(r'Date Added[:\s|]*(\d{1,2}/\d{1,2}/\d{4})', text, re.I)
    if date_match:
        data['date_added'] = date_match.group(1)
    
    return data


async def scrape_smbdealhunter(
    state: str = 'MI',
    max_clicks: int = 50,
    save_backup: bool = False
) -> list[dict]:
    """
    Scrape SMB Deal Hunter listings.
    
    Args:
        state: State to search for ('MI' or 'CT')
        max_clicks: Maximum "See more" button clicks
        save_backup: Whether to save HTML backups
    
    Returns:
        List of listing dictionaries
    """
    state_name = 'Michigan' if state == 'MI' else 'Connecticut'
    
    all_listings = []
    seen_ids = set()
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        logger.info(f"Starting SMB Deal Hunter scrape for {state}...")
        
        try:
            # Load the deals page
            await page.goto('https://app.smbdealhunter.xyz/', timeout=60000)
            await asyncio.sleep(4)
            
            # Wait for listings to appear
            try:
                await page.wait_for_selector('text=Asking Price', timeout=15000)
            except Exception:
                logger.warning("No 'Asking Price' text found initially")
            
            # Click "See more" button repeatedly to load all listings
            click_count = 0
            while click_count < max_clicks:
                try:
                    # Look for "See more" button
                    see_more = await page.query_selector('button:has-text("See more"), a:has-text("See more"), [class*="load-more"]:has-text("See more")')
                    if not see_more:
                        # Try more generic selector
                        see_more = await page.query_selector('text="See more"')
                    
                    if see_more:
                        is_visible = await see_more.is_visible()
                        if is_visible:
                            await see_more.click()
                            click_count += 1
                            logger.debug(f"Clicked 'See more' ({click_count})")
                            await asyncio.sleep(2)  # Wait for content to load
                        else:
                            logger.info("'See more' button no longer visible - all listings loaded")
                            break
                    else:
                        logger.info("No 'See more' button found - all listings loaded")
                        break
                except Exception as e:
                    logger.debug(f"See more click issue: {e}")
                    break
            
            logger.info(f"Clicked 'See more' {click_count} times")
            
            # Get final page HTML
            html = await page.content()
            
            if save_backup:
                with open(f'/tmp/smbdealhunter_{state}.html', 'w') as f:
                    f.write(html)
            
            # Parse listings from DOM
            soup = BeautifulSoup(html, 'lxml')
            
            # Find all listing cards - they have the structure with Asking Price, Cash Flow, Location, etc.
            # Look for containers that have "Asking Price" and "Location" text
            all_text_containers = soup.find_all(['div', 'article', 'section'])
            
            for container in all_text_containers:
                text = container.get_text(separator='|', strip=True)
                
                # Must have Asking Price and Location to be a listing card
                if 'Asking Price' not in text or 'Location' not in text:
                    continue
                
                # Skip if it's a large container (parent of multiple listings)
                if text.count('Asking Price') > 1:
                    continue
                
                # Check if this listing is for our target state
                if state_name not in text:
                    continue
                
                listing = parse_single_listing(container, text, state)
                if listing and listing.get('external_id'):
                    if listing['external_id'] not in seen_ids:
                        seen_ids.add(listing['external_id'])
                        all_listings.append(listing)
            
            logger.info(f"Found {len(all_listings)} {state} listings")
            
        except Exception as e:
            logger.error(f"Error during scrape: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
    
    logger.info(f"SMB Deal Hunter {state} complete: {len(all_listings)} listings")
    return all_listings


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    state = sys.argv[1] if len(sys.argv) > 1 else 'MI'
    
    async def main():
        listings = await scrape_smbdealhunter(state=state, save_backup=True)
        print(f"\nFound {len(listings)} listings for {state}")
        
        for l in listings[:5]:
            print(f"\n- {l['title']}")
            print(f"  Price: ${l['asking_price']:,.0f}" if l['asking_price'] else "  Price: N/A")
            print(f"  Cash Flow: ${l['cash_flow']:,.0f}" if l['cash_flow'] else "  Cash Flow: N/A")
            print(f"  Location: {l['city']}, {l['state']}")
    
    asyncio.run(main())

