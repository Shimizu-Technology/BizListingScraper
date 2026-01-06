"""Murphy Business scraper."""
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


async def scrape_murphybusiness(
    state: str = 'MI',
    max_pages: int = 10,
    save_backup: bool = False
) -> list[dict]:
    """Scrape Murphy Business listings."""
    state_name = 'Michigan' if state == 'MI' else 'Connecticut'
    url = "https://murphybusiness.com/business-brokerage/view-our-listings/"
    
    all_listings = []
    seen_ids = set()
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        
        logger.info(f"Starting Murphy Business scrape for {state}...")
        
        try:
            await page.goto(url, timeout=60000)
            await asyncio.sleep(3)
            
            # Select state from dropdown
            location_select = await page.query_selector('select[name*="location"], select:has-text("Michigan")')
            if location_select:
                await location_select.select_option(label=state_name)
                await asyncio.sleep(1)
            else:
                # Try typing in location field
                location_input = await page.query_selector('input[placeholder*="location" i]')
                if location_input:
                    await location_input.fill(state_name)
                    await asyncio.sleep(1)
            
            # Click search
            search_btn = await page.query_selector('button:has-text("Search"), input[type="submit"]')
            if search_btn:
                await search_btn.click()
                await asyncio.sleep(3)
            
            # Wait for results
            try:
                await page.wait_for_selector('text=SDE', timeout=10000)
            except Exception:
                pass
            
            html = await page.content()
            
            if save_backup:
                with open(f'/tmp/murphybusiness_{state}.html', 'w') as f:
                    f.write(html)
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Murphy Business uses card-body structure
            cards = soup.select('.card-body')
            
            for card in cards:
                text = card.get_text(separator='|', strip=True)
                if 'SDE' not in text:
                    continue
                
                try:
                    data = {
                        'source': 'murphybusiness',
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
                    
                    # Title
                    title_el = card.select_one('.card-title, h5')
                    if title_el:
                        data['title'] = title_el.get_text(strip=True)
                    
                    if not data['title']:
                        continue
                    
                    data['external_id'] = hashlib.md5(data['title'].encode()).hexdigest()[:16]
                    
                    # URL
                    link = card.select_one('a.btn[href*="detail"]')
                    if link:
                        data['url'] = link.get('href', '')
                    
                    # Price
                    price_el = card.select_one('.price')
                    if price_el:
                        data['asking_price'] = parse_price(price_el.get_text(strip=True))
                    
                    # SDE/Cash Flow
                    sde_match = re.search(r'SDE[:\s]*\$?([\d,]+)', text, re.I)
                    if sde_match:
                        data['cash_flow'] = parse_price(sde_match.group(1))
                    
                    # Location from li
                    loc_li = card.select('li')
                    for li in loc_li:
                        li_text = li.get_text(strip=True)
                        if state_name in li_text:
                            data['city'] = li_text
                    
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
        listings = await scrape_murphybusiness(state=state, save_backup=True)
        print(f"\nFound {len(listings)} listings for {state}")
        for l in listings[:5]:
            print(f"  - {l['title'][:50] if l['title'] else 'N/A'}")
            print(f"    Price: ${l['asking_price']:,.0f}" if l['asking_price'] else "    Price: N/A")
    
    asyncio.run(main())

