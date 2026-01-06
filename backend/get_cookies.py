"""
Get cookies from a manual browser session.
Opens browser, lets you visit the site, then saves cookies for reuse.
"""
import asyncio
import json
from playwright.async_api import async_playwright

COOKIES_FILE = "bizbuysell_cookies.json"


async def get_cookies_manually():
    """
    Opens a browser for you to manually visit BizBuySell.
    After you browse, cookies are saved for automated reuse.
    """
    print("="*60)
    print("COOKIE HARVESTER")
    print("="*60)
    print()
    print("This will open a browser window.")
    print("1. The browser will load BizBuySell")
    print("2. Browse around naturally (click a few listings)")
    print("3. Come back here and press Enter when done")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Opening BizBuySell...")
        await page.goto("https://www.bizbuysell.com/michigan-businesses-for-sale/")
        
        print()
        print("👆 Browser opened! Browse around naturally.")
        print("   Click on a few listings, scroll, etc.")
        print()
        input("Press Enter when you're done browsing...")
        
        # Get all cookies
        cookies = await context.cookies()
        
        # Save cookies
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"\n✅ Saved {len(cookies)} cookies to {COOKIES_FILE}")
        
        await browser.close()
    
    return cookies


async def test_with_cookies():
    """Test scraping with saved cookies."""
    print("\n" + "="*60)
    print("TESTING WITH SAVED COOKIES")
    print("="*60)
    
    # Load cookies
    try:
        with open(COOKIES_FILE, 'r') as f:
            cookies = json.load(f)
        print(f"Loaded {len(cookies)} cookies")
    except FileNotFoundError:
        print("No cookies file found. Run get_cookies_manually() first.")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        
        # Add cookies before navigating
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        print("Navigating with cookies...")
        response = await page.goto(
            "https://www.bizbuysell.com/michigan-businesses-for-sale/?q=bHQ9MzAsNDAsODA%3D",
            timeout=30000
        )
        
        print(f"Status: {response.status}")
        
        await asyncio.sleep(3)
        content = await page.content()
        
        if "Access Denied" in content:
            print("❌ Still blocked even with cookies")
        elif "Businesses For Sale" in content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'lxml')
            listings = soup.select('a.diamond, a.showcase, div.listing')
            print(f"✅ Success! Found {len(listings)} listings")
        
        await browser.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_with_cookies())
    else:
        asyncio.run(get_cookies_manually())
        print("\nNow run: python get_cookies.py test")

