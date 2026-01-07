"""Main scraper entry point - runs all scrapers for MI and CT."""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_pool, reset_pool, get_connection
from scraper.bizbuysell import scrape_bizbuysell
from scraper.bizquest import scrape_bizquest
from scraper.businessesforsale import scrape_businessesforsale
from scraper.transworld import scrape_transworld
from scraper.fcbb import scrape_fcbb
from scraper.synergybb import scrape_synergybb
from scraper.smbdealhunter import scrape_smbdealhunter
from scraper.upsert import bulk_upsert_listings, mark_stale_listings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get which state to scrape from environment variable (set by GitHub Actions)
# Options: 'MI', 'CT', 'ALL' (default)
SCRAPE_STATE = os.environ.get('SCRAPE_STATE', 'ALL').upper()

# States to scrape based on environment variable
if SCRAPE_STATE == 'MI':
    STATES = ['MI']
elif SCRAPE_STATE == 'CT':
    STATES = ['CT']
else:
    STATES = ['MI', 'CT']

# Note: Rate limiting is now handled by running MI and CT 12 hours apart
# via GitHub Actions schedule (6 AM UTC for MI, 6 PM UTC for CT)

# All scrapers with their configs
SCRAPERS = [
    ('bizquest', scrape_bizquest, {'max_pages': 50}),
    ('bizbuysell', scrape_bizbuysell, {'max_pages': 30}),
    ('businessesforsale', scrape_businessesforsale, {'max_pages': 5}),  # Cloudflare blocks after page 1
    ('transworld', scrape_transworld, {'max_pages': 20}),
    ('synergybb', scrape_synergybb, {}),
    ('smbdealhunter', scrape_smbdealhunter, {'max_clicks': 50}),
    ('fcbb', scrape_fcbb, {}),
]


async def main():
    """Run all scrapers for all states."""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Starting scrape at {start_time}")
    logger.info(f"SCRAPE_STATE env: {SCRAPE_STATE}")
    logger.info(f"States to scrape: {STATES}")
    logger.info(f"Scrapers: {[s[0] for s in SCRAPERS]}")
    logger.info("=" * 60)
    
    # Initialize connection pool
    init_pool()
    
    total_stats = {
        'found': 0,
        'inserted': 0,
        'updated': 0,
        'unchanged': 0,
        'deactivated': 0,
        'sources_completed': [],
        'sources_failed': []
    }
    
    for source_name, scraper_func, kwargs in SCRAPERS:
        try:
            logger.info(f"\n{'='*40}")
            logger.info(f"Starting {source_name}...")
            logger.info(f"{'='*40}")
            
            source_listings = []
            
            for i, state in enumerate(STATES):
                logger.info(f"  Scraping {source_name} for {state}...")
                reset_pool()
                try:
                    listings = await scraper_func(state=state, **kwargs)
                    source_listings.extend(listings)
                    logger.info(f"  Found {len(listings)} listings for {state}")
                except Exception as e:
                    logger.error(f"  Error scraping {source_name} {state}: {e}")
                
                # Add cooldown between states if scraping multiple states
                if i < len(STATES) - 1:
                    cooldown = 30
                    logger.info(f"  Cooling down for {cooldown}s before next state...")
                    await asyncio.sleep(cooldown)
            
            if source_listings:
                logger.info(f"Upserting {len(source_listings)} listings from {source_name}...")
                reset_pool()
                result = bulk_upsert_listings(source_listings, source=source_name)
                total_stats['found'] += len(source_listings)
                total_stats['inserted'] += result.get('inserted', 0)
                total_stats['updated'] += result.get('updated', 0)
                total_stats['unchanged'] += result.get('unchanged', 0)
                logger.info(f"  Inserted: {result.get('inserted', 0)}, Updated: {result.get('updated', 0)}")
            
            # Mark stale listings for this source
            reset_pool()
            deactivated = mark_stale_listings(source_name, days_threshold=7)
            total_stats['deactivated'] += deactivated
            logger.info(f"  Deactivated {deactivated} stale listings")
            
            total_stats['sources_completed'].append(source_name)
            
        except Exception as e:
            logger.error(f"Failed to scrape {source_name}: {e}")
            total_stats['sources_failed'].append(source_name)
    
    duration = datetime.now() - start_time
    logger.info("\n" + "=" * 60)
    logger.info(f"Full scrape completed in {duration}")
    logger.info("Final Stats:")
    logger.info(f"  - Total found: {total_stats['found']}")
    logger.info(f"  - Inserted: {total_stats['inserted']}")
    logger.info(f"  - Updated: {total_stats['updated']}")
    logger.info(f"  - Unchanged: {total_stats['unchanged']}")
    logger.info(f"  - Deactivated: {total_stats['deactivated']}")
    logger.info(f"  - Completed: {total_stats['sources_completed']}")
    logger.info(f"  - Failed: {total_stats['sources_failed']}")
    logger.info("=" * 60)
    
    return total_stats


if __name__ == "__main__":
    asyncio.run(main())
