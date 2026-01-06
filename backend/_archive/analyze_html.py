"""Analyze the HTML structure of BizBuySell to find correct selectors."""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

TARGET_URL = "https://www.bizbuysell.com/michigan-businesses-for-sale/"


async def analyze_page():
    print("Fetching BizBuySell page for analysis...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            "/tmp/playwright-bizbuysell",
            headless=False,
            viewport={'width': 1366, 'height': 768},
            args=['--disable-blink-features=AutomationControlled'],
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            response = await page.goto(TARGET_URL, timeout=45000)
            print(f"Status: {response.status}")
            
            # Wait for content to load
            await asyncio.sleep(5)
            
            # Try scrolling to load lazy content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(2)
            
            content = await page.content()
            print(f"Content length: {len(content)} bytes")
            
            # Save full HTML for inspection
            with open("bizbuysell_full.html", "w") as f:
                f.write(content)
            print("Saved full HTML to bizbuysell_full.html")
            
            soup = BeautifulSoup(content, 'lxml')
            
            print("\n" + "="*60)
            print("ANALYZING PAGE STRUCTURE")
            print("="*60)
            
            # Look for various patterns
            patterns = [
                # Common listing selectors
                ('a[href*="Business-Opportunity"]', 'Links containing Business-Opportunity'),
                ('a[href*="businesses-for-sale"]', 'Links containing businesses-for-sale'),
                ('[class*="listing"]', 'Elements with "listing" in class'),
                ('[class*="Listing"]', 'Elements with "Listing" in class'),
                ('[class*="card"]', 'Elements with "card" in class'),
                ('[class*="Card"]', 'Elements with "Card" in class'),
                ('[class*="result"]', 'Elements with "result" in class'),
                ('[class*="diamond"]', 'Elements with "diamond" in class'),
                ('[data-listing-id]', 'Elements with data-listing-id'),
                ('[data-id]', 'Elements with data-id'),
                
                # Price patterns
                ('[class*="price"]', 'Elements with "price" in class'),
                ('[class*="Price"]', 'Elements with "Price" in class'),
                
                # Business info
                ('[class*="business"]', 'Elements with "business" in class'),
                ('[class*="Business"]', 'Elements with "Business" in class'),
            ]
            
            for selector, description in patterns:
                elements = soup.select(selector)
                if elements:
                    print(f"\n✅ {description}: {len(elements)} found")
                    if len(elements) <= 5:
                        for el in elements[:3]:
                            classes = el.get('class', [])
                            text = el.get_text()[:100].strip().replace('\n', ' ')
                            print(f"   - classes: {classes}, text: {text[:50]}...")
            
            # Look for links that might be listings
            print("\n" + "="*60)
            print("ANALYZING LINKS")
            print("="*60)
            
            all_links = soup.find_all('a', href=True)
            print(f"Total links: {len(all_links)}")
            
            # Find unique URL patterns
            patterns_found = {}
            for link in all_links:
                href = link['href']
                # Extract pattern (replace numbers/IDs with placeholder)
                pattern = re.sub(r'/\d+', '/{ID}', href)
                if pattern not in patterns_found:
                    patterns_found[pattern] = []
                if len(patterns_found[pattern]) < 3:
                    patterns_found[pattern].append(href)
            
            # Show patterns that appear multiple times (likely listings)
            print("\nURL patterns appearing multiple times:")
            for pattern, examples in sorted(patterns_found.items(), key=lambda x: -len(x[1])):
                if len(examples) > 2 and 'javascript' not in pattern:
                    print(f"\n  Pattern: {pattern} ({len(examples)}+ occurrences)")
                    print(f"    Example: {examples[0]}")
            
            # Look specifically for listing cards
            print("\n" + "="*60)
            print("LOOKING FOR LISTING CARDS")
            print("="*60)
            
            # Common listing card structures
            possible_cards = soup.select('div[class], article[class], li[class]')
            
            # Filter to those containing price-like content
            price_pattern = re.compile(r'\$[\d,]+')
            cards_with_prices = []
            
            for card in possible_cards:
                text = card.get_text()
                if price_pattern.search(text) and len(text) > 100:
                    classes = ' '.join(card.get('class', []))
                    if len(classes) < 100:  # Skip overly complex nested elements
                        cards_with_prices.append({
                            'tag': card.name,
                            'classes': classes,
                            'text_preview': text[:150].replace('\n', ' ')
                        })
            
            print(f"Found {len(cards_with_prices)} elements with price-like content")
            
            # Group by class pattern
            class_counts = {}
            for card in cards_with_prices:
                key = f"{card['tag']}.{card['classes']}"
                class_counts[key] = class_counts.get(key, 0) + 1
            
            print("\nTop card patterns (by frequency):")
            for key, count in sorted(class_counts.items(), key=lambda x: -x[1])[:10]:
                if count > 1:
                    print(f"  {key}: {count} occurrences")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await asyncio.sleep(2)
            await context.close()


if __name__ == "__main__":
    asyncio.run(analyze_page())

