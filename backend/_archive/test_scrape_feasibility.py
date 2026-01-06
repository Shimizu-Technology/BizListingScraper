"""
Test script to validate BizBuySell scraping feasibility.
Tests multiple anti-detection techniques.
"""
import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Realistic user agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

TARGET_URL = "https://www.bizbuysell.com/michigan-businesses-for-sale/"


async def test_basic_playwright():
    """Test 1: Basic Playwright request."""
    print("\n" + "="*60)
    print("TEST 1: Basic Playwright (headless)")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            response = await page.goto(TARGET_URL, timeout=30000)
            content = await page.content()
            
            print(f"Status: {response.status}")
            print(f"Content length: {len(content)}")
            
            if "Access Denied" in content:
                print("❌ BLOCKED - Access Denied")
                return False
            elif "businesses for sale" in content.lower():
                print("✅ SUCCESS - Got listing page!")
                return True
            else:
                print(f"⚠️ Unknown response - First 500 chars: {content[:500]}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            await browser.close()


async def test_stealth_playwright():
    """Test 2: Playwright with stealth techniques."""
    print("\n" + "="*60)
    print("TEST 2: Playwright with stealth techniques")
    print("="*60)
    
    async with async_playwright() as p:
        # Launch with more realistic settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/Detroit',
        )
        
        page = await context.new_page()
        
        # Remove automation indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = { runtime: {} };
        """)
        
        try:
            # Random delay before request
            await asyncio.sleep(random.uniform(1, 3))
            
            response = await page.goto(TARGET_URL, timeout=30000, wait_until='networkidle')
            
            # Simulate human behavior
            await asyncio.sleep(random.uniform(2, 4))
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await asyncio.sleep(random.uniform(0.5, 1))
            
            content = await page.content()
            
            print(f"Status: {response.status}")
            print(f"Content length: {len(content)}")
            
            if "Access Denied" in content:
                print("❌ BLOCKED - Access Denied")
                return False
            elif "businesses for sale" in content.lower() or "listing" in content.lower():
                print("✅ SUCCESS - Got listing page!")
                # Try to parse some listings
                soup = BeautifulSoup(content, 'lxml')
                # Look for common listing indicators
                listings = soup.select('[data-listing-id], .listing, .businessCard, .diamond-wrap')
                print(f"   Found {len(listings)} potential listing elements")
                return True
            else:
                print(f"⚠️ Unknown response")
                # Save for debugging
                with open("debug_response.html", "w") as f:
                    f.write(content)
                print("   Saved to debug_response.html")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            await browser.close()


async def test_headed_browser():
    """Test 3: Non-headless browser (most realistic)."""
    print("\n" + "="*60)
    print("TEST 3: Headed browser (non-headless)")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show the browser
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1366, 'height': 768},
            locale='en-US',
        )
        
        page = await context.new_page()
        
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        try:
            print("Opening browser... (you should see a Chrome window)")
            
            response = await page.goto(TARGET_URL, timeout=45000, wait_until='domcontentloaded')
            
            # Wait for potential Cloudflare/Akamai challenge
            await asyncio.sleep(5)
            
            content = await page.content()
            
            print(f"Status: {response.status}")
            print(f"Content length: {len(content)}")
            
            if "Access Denied" in content:
                print("❌ BLOCKED - Access Denied")
                return False
            elif "businesses for sale" in content.lower():
                print("✅ SUCCESS - Got listing page!")
                
                # Parse and show sample listings
                soup = BeautifulSoup(content, 'lxml')
                
                # Try various selectors
                selectors_to_try = [
                    '.diamond',
                    '.listing-card',
                    '.businessCard', 
                    '[class*="listing"]',
                    '[class*="business"]',
                    'a[href*="Business-Opportunity"]',
                ]
                
                for selector in selectors_to_try:
                    elements = soup.select(selector)
                    if elements:
                        print(f"   Found {len(elements)} elements with selector: {selector}")
                
                return True
            else:
                print(f"⚠️ Unknown response")
                with open("debug_response_headed.html", "w") as f:
                    f.write(content)
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            print("Closing browser in 3 seconds...")
            await asyncio.sleep(3)
            await browser.close()


async def main():
    print("\n" + "#"*60)
    print("# BizBuySell Scraping Feasibility Test")
    print("#"*60)
    print(f"\nTarget URL: {TARGET_URL}")
    
    results = {}
    
    # Test 1: Basic
    results['basic'] = await test_basic_playwright()
    
    # Test 2: Stealth
    results['stealth'] = await test_stealth_playwright()
    
    # Test 3: Headed (only if previous tests failed)
    if not any(results.values()):
        results['headed'] = await test_headed_browser()
    else:
        print("\n" + "="*60)
        print("TEST 3: Skipped (previous test succeeded)")
        print("="*60)
        results['headed'] = None
    
    # Summary
    print("\n" + "#"*60)
    print("# SUMMARY")
    print("#"*60)
    
    for test_name, success in results.items():
        if success is None:
            status = "SKIPPED"
        elif success:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    if any(v for v in results.values() if v):
        print("\n🎉 At least one technique works! Scraping is feasible.")
        print("   Recommendation: Use the working technique in production.")
    else:
        print("\n⚠️ All techniques blocked. Options:")
        print("   1. Use residential proxies (Bright Data, Oxylabs)")
        print("   2. Try different timing/user-agent combinations")
        print("   3. Consider if BizBuySell has an official API")


if __name__ == "__main__":
    asyncio.run(main())

