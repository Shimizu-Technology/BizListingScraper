"""Synergy Business Brokers scraper."""
import asyncio
import hashlib
import logging
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


def parse_price(text: str) -> float | None:
    """Parse price from text."""
    if not text:
        return None
    cleaned = re.sub(r'[^\d.]', '', text.replace(',', ''))
    if cleaned:
        try:
            return float(cleaned)
        except ValueError:
            pass
    return None


async def scrape_synergybb(
    state: str = 'MI',
    max_pages: int = 10,
    save_backup: bool = False
) -> list[dict]:
    """Scrape Synergy Business Brokers listings."""
    state_name = 'michigan' if state == 'MI' else 'connecticut'
    url = f"https://synergybb.com/businesses-for-sale/?_listing_location_multi={state_name}"
    
    all_listings = []
    seen_ids = set()
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        logger.info(f"Starting Synergy BB scrape for {state}...")
        
        try:
            await page.goto(url, timeout=60000)
            await asyncio.sleep(5)
            
            # Wait for listings
            try:
                await page.wait_for_selector('text=Asking Price', timeout=10000)
            except Exception:
                pass
            
            html = await page.content()
            
            if save_backup:
                with open(f'/tmp/synergybb_{state}.html', 'w') as f:
                    f.write(html)
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Find listing cards - Synergy uses 'sale-list-item' class
            cards = soup.select('div.sale-list-item')
            
            for card in cards:
                try:
                    data = {
                        'source': 'synergybb',
                        'external_id': None,
                        'url': None,
                        'title': None,
                        'asking_price': None,
                        'cash_flow': None,
                        'gross_revenue': None,
                        'ebitda': None,
                        'city': None,
                        'state': state,
                        'description': None,
                    }
                    
                    # Title and URL
                    title_el = card.select_one('a.sale-list-item-title')
                    if title_el:
                        data['title'] = title_el.get_text(strip=True)
                        data['url'] = title_el.get('href', '')
                    
                    if not data['title']:
                        continue
                    
                    data['external_id'] = hashlib.md5(data['title'].encode()).hexdigest()[:16]
                    
                    # Price
                    price_el = card.select_one('.sale-list-item-price')
                    if price_el:
                        data['asking_price'] = parse_price(price_el.get_text(strip=True))
                    
                    # Revenue and Cash Flow from spans
                    text = card.get_text(separator='|', strip=True)
                    
                    rev_match = re.search(r'Annual Revenue[:\s]*\$?([\d,]+)', text, re.I)
                    if rev_match:
                        data['gross_revenue'] = parse_price(rev_match.group(1))
                    
                    cf_match = re.search(r'Net Cash Flow[:\s]*\$?([\d,]+)', text, re.I)
                    if cf_match:
                        data['cash_flow'] = parse_price(cf_match.group(1))
                    
                    # Description
                    desc_el = card.select_one('.sale-list-item-content-dsec p')
                    if desc_el:
                        data['description'] = desc_el.get_text(strip=True)[:500]
                    
                    if data['external_id'] not in seen_ids:
                        seen_ids.add(data['external_id'])
                        all_listings.append(data)
                        
                except Exception as e:
                    logger.debug(f"Error parsing: {e}")
            
            logger.info(f"Found {len(all_listings)} listings for {state}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            await browser.close()
    
    return all_listings


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    state = sys.argv[1] if len(sys.argv) > 1 else 'MI'
    
    async def main():
        listings = await scrape_synergybb(state=state, save_backup=True)
        print(f"\nFound {len(listings)} listings for {state}")
        for l in listings[:5]:
            print(f"  - {l['title'][:50] if l['title'] else 'N/A'}")
            print(f"    Price: ${l['asking_price']:,.0f}" if l['asking_price'] else "    Price: N/A")
    
    asyncio.run(main())

