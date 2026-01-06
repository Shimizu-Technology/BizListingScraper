"""
BizBuySell Scraping - Proof of Concept
This validates that we can successfully scrape business listings.
"""
import asyncio
import re
import json
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def scrape_michigan_listings(max_pages: int = 3) -> list[dict]:
    """
    Scrape BizBuySell Michigan listings.
    
    Returns list of parsed listing dictionaries.
    """
    base_url = "https://www.bizbuysell.com/michigan-businesses-for-sale/"
    all_listings = []
    
    async with async_playwright() as p:
        # Use persistent context with anti-detection
        # NOTE: headless=False is required for BizBuySell
        # They detect headless browsers and block them
        context = await p.chromium.launch_persistent_context(
            "/tmp/playwright-bizbuysell",
            headless=False,  # Must be False - BizBuySell blocks headless
            viewport={'width': 1366, 'height': 768},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-first-run',
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Remove webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        try:
            for page_num in range(1, max_pages + 1):
                # Build URL
                if page_num == 1:
                    url = base_url
                else:
                    url = f"{base_url}?q=&page={page_num}"
                
                print(f"\n📄 Scraping page {page_num}: {url}")
                
                # Navigate
                response = await page.goto(url, timeout=45000, wait_until='domcontentloaded')
                
                if response.status != 200:
                    print(f"  ❌ Got status {response.status}")
                    break
                
                # Wait for content
                await asyncio.sleep(3)
                
                # Get content
                content = await page.content()
                
                # Check for block
                if "Access Denied" in content:
                    print("  ❌ Access Denied - blocked")
                    break
                
                # Parse listings - a.diamond wraps the listing content
                soup = BeautifulSoup(content, 'lxml')
                listing_links = soup.select('a.diamond')
                
                print(f"  ✅ Found {len(listing_links)} listings")
                
                if not listing_links:
                    print("  No more listings, stopping pagination")
                    break
                
                # Parse each listing
                for idx, listing_link in enumerate(listing_links):
                    parsed = parse_listing_from_link(listing_link)
                    if parsed and parsed.get('external_id'):
                        all_listings.append(parsed)
                    elif idx < 2:  # Debug first few failures
                        print(f"    ⚠️ Failed to parse listing {idx}")
                
                # Rate limiting
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await context.close()
    
    return all_listings


def parse_listing_from_link(listing_link) -> dict | None:
    """
    Parse a listing from the a.diamond element.
    The a.diamond wraps the entire listing content.
    """
    data = {
        'source': 'bizbuysell',
        'scraped_at': datetime.now().isoformat()
    }
    
    # Get URL and ID from the link itself
    href = listing_link.get('href', '')
    data['url'] = href
    
    # External ID from URL or id attribute
    external_id = listing_link.get('id')
    if not external_id:
        match = re.search(r'/(\d+)/?$', href)
        if match:
            external_id = match.group(1)
    
    data['external_id'] = external_id
    
    if not data.get('external_id'):
        return None
    
    # Title - from the title attribute or .title element
    title = listing_link.get('title')
    if not title:
        title_el = listing_link.select_one('.title')
        if title_el:
            title = title_el.get_text(strip=True)
    data['title'] = title or 'Unknown'
    
    # Asking Price
    price_el = listing_link.select_one('.asking-price')
    if price_el:
        price_text = price_el.get_text(strip=True)
        data['asking_price_raw'] = price_text
        data['asking_price'] = parse_price(price_text)
    
    # Cash Flow
    cf_el = listing_link.select_one('.cash-flow')
    if cf_el:
        cf_text = cf_el.get_text(strip=True)
        data['cash_flow_raw'] = cf_text
        # Remove "Cash Flow:" prefix
        cf_clean = re.sub(r'Cash Flow:\s*', '', cf_text)
        data['cash_flow'] = parse_price(cf_clean)
    
    # Location
    loc_el = listing_link.select_one('.location')
    if loc_el:
        location_text = loc_el.get_text(strip=True)
        data['location_raw'] = location_text
        city, state = parse_location(location_text)
        data['city'] = city
        data['state'] = state
    
    # Description (from .text element)
    desc_el = listing_link.select_one('.description, .text')
    if desc_el:
        data['description'] = desc_el.get_text(strip=True)[:500]
    
    # Real estate included indicator
    if listing_link.select_one('.real-estate-included'):
        data['real_estate_included'] = True
    
    return data


def parse_price(text: str) -> float | None:
    """Parse price string like '$250,000' to float."""
    if not text:
        return None
    
    text_lower = text.lower()
    if 'call' in text_lower or 'confidential' in text_lower or 'n/a' in text_lower:
        return None
    
    # Remove everything except digits and decimal point
    cleaned = re.sub(r'[^\d.]', '', text)
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_location(text: str) -> tuple[str | None, str | None]:
    """Parse 'Detroit, MI' into (city, state)."""
    if not text:
        return None, None
    
    parts = text.split(',')
    if len(parts) >= 2:
        city = parts[0].strip()
        state = parts[1].strip()[:2].upper()
        return city, state
    
    return text.strip(), None


async def main():
    print("="*60)
    print("BizBuySell Scraping - Proof of Concept")
    print("="*60)
    
    start = datetime.now()
    
    listings = await scrape_michigan_listings(max_pages=2)
    
    duration = datetime.now() - start
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"Total listings scraped: {len(listings)}")
    print(f"Time taken: {duration}")
    
    if listings:
        # Show sample
        print("\n--- Sample Listings ---")
        for listing in listings[:5]:
            print(f"\n📍 {listing.get('title', 'N/A')[:60]}...")
            print(f"   External ID: {listing.get('external_id')}")
            print(f"   Price: ${listing.get('asking_price', 'N/A'):,.0f}" if listing.get('asking_price') else "   Price: N/A")
            print(f"   Cash Flow: ${listing.get('cash_flow', 'N/A'):,.0f}" if listing.get('cash_flow') else "   Cash Flow: N/A")
            print(f"   Location: {listing.get('city')}, {listing.get('state')}")
            print(f"   URL: {listing.get('url')}")
        
        # Save to JSON
        output_file = "scraped_listings_poc.json"
        with open(output_file, "w") as f:
            json.dump(listings, f, indent=2)
        print(f"\n✅ All listings saved to {output_file}")
        
        # Show stats
        prices = [l['asking_price'] for l in listings if l.get('asking_price')]
        if prices:
            print(f"\n📊 Price Stats:")
            print(f"   Min: ${min(prices):,.0f}")
            print(f"   Max: ${max(prices):,.0f}")
            print(f"   Avg: ${sum(prices)/len(prices):,.0f}")
        
        print("\n🎉 SCRAPING FEASIBILITY CONFIRMED!")
        print("   The project is viable. Ready to build production scraper.")
    else:
        print("\n⚠️ No listings extracted. Check the logs above.")


if __name__ == "__main__":
    asyncio.run(main())

