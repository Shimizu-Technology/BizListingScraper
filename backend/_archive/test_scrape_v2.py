"""
Test script v2 - Additional techniques.
"""
import asyncio
import random
import httpx
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

TARGET_URL = "https://www.bizbuysell.com/michigan-businesses-for-sale/"


async def test_firefox():
    """Test with Firefox browser."""
    print("\n" + "="*60)
    print("TEST: Firefox browser (non-headless)")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            locale='en-US',
        )
        
        page = await context.new_page()
        
        try:
            print("Opening Firefox...")
            response = await page.goto(TARGET_URL, timeout=45000)
            
            # Wait for any challenge
            await asyncio.sleep(5)
            
            content = await page.content()
            
            print(f"Status: {response.status}")
            print(f"Content length: {len(content)}")
            
            if "Access Denied" in content:
                print("❌ BLOCKED - Access Denied")
                return False
            elif "businesses" in content.lower():
                print("✅ SUCCESS!")
                return True
            else:
                with open("debug_firefox.html", "w") as f:
                    f.write(content)
                print("⚠️ Saved to debug_firefox.html")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            await asyncio.sleep(2)
            await browser.close()


async def check_robots_txt():
    """Check their robots.txt for guidance."""
    print("\n" + "="*60)
    print("CHECKING: robots.txt")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.bizbuysell.com/robots.txt",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("robots.txt content:")
                print("-"*40)
                print(response.text[:1000])
                print("-"*40)
            else:
                print(f"Status: {response.status_code}")
                
    except Exception as e:
        print(f"Error: {e}")


async def check_sitemap():
    """Check for sitemap."""
    print("\n" + "="*60)
    print("CHECKING: Sitemap")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.bizbuysell.com/sitemap.xml",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Sitemap exists! Length: {len(response.text)}")
                print("First 500 chars:")
                print(response.text[:500])
            else:
                print(f"Status: {response.status_code}")
                
    except Exception as e:
        print(f"Error: {e}")


async def test_alternative_url():
    """Test if we can access individual listing pages directly."""
    print("\n" + "="*60)
    print("TEST: Direct listing URL access")
    print("="*60)
    
    # Try a direct listing page (these IDs are examples)
    test_urls = [
        "https://www.bizbuysell.com/Business-Opportunity/",
        "https://www.bizbuysell.com/franchise/",
        "https://www.bizbuysell.com/buy/",
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        for url in test_urls:
            try:
                print(f"\nTrying: {url}")
                response = await page.goto(url, timeout=15000)
                print(f"  Status: {response.status}")
                
                content = await page.content()
                if "Access Denied" in content:
                    print("  ❌ Blocked")
                else:
                    print(f"  ✅ Accessible ({len(content)} bytes)")
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        await browser.close()


async def test_with_cookies():
    """Test accessing with a pre-loaded session from a real browser."""
    print("\n" + "="*60)
    print("TEST: Persistent user data directory")
    print("="*60)
    
    async with async_playwright() as p:
        # Use a persistent context that saves state
        context = await p.chromium.launch_persistent_context(
            "/tmp/playwright-bizbuysell",
            headless=False,
            viewport={'width': 1366, 'height': 768},
            args=['--disable-blink-features=AutomationControlled'],
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            print("Using persistent context...")
            print("If this works, cookies/session will be saved for future requests")
            
            response = await page.goto(TARGET_URL, timeout=45000)
            
            # Wait for potential CAPTCHA or challenge
            print("\nWaiting 10 seconds for any challenges to complete...")
            print("(If you see a CAPTCHA, solve it manually)")
            await asyncio.sleep(10)
            
            content = await page.content()
            
            print(f"\nStatus: {response.status}")
            print(f"Content length: {len(content)}")
            
            if "Access Denied" in content:
                print("❌ BLOCKED")
                return False
            elif "businesses" in content.lower() or "listing" in content.lower():
                print("✅ SUCCESS!")
                
                # Parse listings
                soup = BeautifulSoup(content, 'lxml')
                links = soup.select('a[href*="/Business-Opportunity/"]')
                print(f"Found {len(links)} listing links")
                
                if links:
                    print("\nSample listings:")
                    for link in links[:5]:
                        print(f"  - {link.get('href')}")
                
                return True
            else:
                with open("debug_persistent.html", "w") as f:
                    f.write(content)
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            await asyncio.sleep(3)
            await context.close()


async def main():
    print("\n" + "#"*60)
    print("# BizBuySell Scraping - Advanced Tests")
    print("#"*60)
    
    # Check robots.txt first
    await check_robots_txt()
    
    # Check sitemap
    await check_sitemap()
    
    # Test with persistent context (most realistic)
    result = await test_with_cookies()
    
    if not result:
        # Try Firefox as backup
        await test_firefox()
    
    print("\n" + "#"*60)
    print("# TEST COMPLETE")
    print("#"*60)


if __name__ == "__main__":
    asyncio.run(main())

