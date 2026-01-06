"""Extract and display sample listings from the saved HTML."""
from bs4 import BeautifulSoup
import re
import json

# Read the saved HTML
with open("bizbuysell_full.html", "r") as f:
    content = f.read()

soup = BeautifulSoup(content, 'lxml')

# Find all listing divs
listings = soup.select('div.listing')
print(f"Found {len(listings)} listings")

if listings:
    print("\n" + "="*60)
    print("SAMPLE LISTING STRUCTURE")
    print("="*60)
    
    # Analyze first listing
    sample = listings[0]
    
    print("\n--- Raw HTML of first listing ---")
    print(str(sample)[:2000])
    
    print("\n--- Extracted Data ---")
    
    # Try to find key elements
    title_el = sample.select_one('.title, h3, h2, a')
    print(f"Title element: {title_el}")
    
    # Find all links
    links = sample.select('a')
    print(f"\nLinks in listing ({len(links)}):")
    for link in links:
        print(f"  - href: {link.get('href', 'N/A')}")
        print(f"    text: {link.get_text(strip=True)[:50]}")
    
    # Find price
    price_el = sample.select_one('.price, [class*="price"]')
    if price_el:
        print(f"\nPrice element: {price_el.get_text(strip=True)}")
    
    # Look for specific patterns
    print("\n--- Searching for specific patterns ---")
    
    patterns = {
        'asking_price': sample.select_one('.asking-price'),
        'cash_flow': sample.select_one('.cash-flow'),
        'price_group': sample.select_one('.price-group'),
        'location': sample.select_one('.location, .city-state'),
        'category': sample.select_one('.category, .industry'),
        'diamond': sample.select_one('.diamond'),
    }
    
    for name, el in patterns.items():
        if el:
            print(f"  {name}: {el.get_text(strip=True)[:50]}")
    
    print("\n" + "="*60)
    print("ALL CLASSES IN LISTING")
    print("="*60)
    
    # Get all unique classes in the listing
    all_classes = set()
    for el in sample.select('[class]'):
        classes = el.get('class', [])
        all_classes.update(classes)
    
    for cls in sorted(all_classes):
        print(f"  .{cls}")
    
    print("\n" + "="*60)
    print("PARSING ALL LISTINGS")
    print("="*60)
    
    extracted_listings = []
    
    for listing in listings[:10]:  # First 10
        data = {}
        
        # Try to get the diamond wrapper which contains the details
        diamond = listing.select_one('.diamond')
        if diamond:
            # Get the link
            link = diamond.get('href')
            if link:
                data['url'] = 'https://www.bizbuysell.com' + link if link.startswith('/') else link
                # Extract ID from URL
                match = re.search(r'/(\d+)/?$', link)
                if match:
                    data['external_id'] = match.group(1)
        
        # Title
        title = listing.select_one('.title')
        if title:
            data['title'] = title.get_text(strip=True)
        
        # Price
        asking = listing.select_one('.asking-price')
        if asking:
            data['asking_price'] = asking.get_text(strip=True)
        
        # Cash flow
        cf = listing.select_one('.cash-flow')
        if cf:
            data['cash_flow'] = cf.get_text(strip=True)
        
        # Location
        loc = listing.select_one('.location')
        if loc:
            data['location'] = loc.get_text(strip=True)
        
        # Category/Industry
        cat = listing.select_one('.category, .industry, .business-type')
        if cat:
            data['category'] = cat.get_text(strip=True)
        
        # Description
        desc = listing.select_one('.text')
        if desc:
            data['description'] = desc.get_text(strip=True)[:200]
        
        extracted_listings.append(data)
    
    print(f"\nExtracted {len(extracted_listings)} listings:")
    for i, listing in enumerate(extracted_listings, 1):
        print(f"\n--- Listing {i} ---")
        for key, value in listing.items():
            print(f"  {key}: {value[:80] if isinstance(value, str) else value}...")

