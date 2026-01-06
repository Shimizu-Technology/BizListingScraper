"""Main scraper entry point."""
import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_connection, init_pool, reset_pool
from app.config import TARGET_STATE, MAX_PAGES_PER_SCRAPE, STALE_THRESHOLD_DAYS
from scraper.bizbuysell import scrape_bizbuysell
from scraper.upsert import batch_upsert_listings, mark_stale_listings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Backup directory for scraped data
BACKUP_DIR = Path(__file__).parent.parent / "_backups"


def save_backup(listings: list[dict], state: str) -> Path:
    """Save scraped listings to a backup JSON file."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"scrape_{state}_{timestamp}.json"
    
    with open(backup_path, 'w') as f:
        json.dump(listings, f, indent=2, default=str)
    
    logger.info(f"Saved backup: {backup_path}")
    return backup_path


async def main(
    state: str = None,
    max_pages: int = None,
    browser_type: str = "firefox"
):
    """
    Main scraper entry point.
    
    Args:
        state: Target state (default from config)
        max_pages: Max pages to scrape (default from config)
        browser_type: Browser to use ('firefox' recommended)
    """
    state = state or TARGET_STATE
    max_pages = max_pages or MAX_PAGES_PER_SCRAPE
    
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Starting BizBuySell scrape at {start_time}")
    logger.info(f"Target state: {state}")
    logger.info(f"Max pages: {max_pages}")
    logger.info(f"Browser: {browser_type}")
    logger.info("=" * 60)
    
    # Initialize connection pool
    init_pool()
    
    # Create scrape run record
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scrape_runs (source, started_at, status)
                VALUES ('bizbuysell', NOW(), 'running')
                RETURNING id
            """)
            run_id = cur.fetchone()[0]
            conn.commit()
    
    logger.info(f"Scrape run ID: {run_id}")
    
    stats = {
        'pages_scraped': 0,
        'listings_found': 0,
        'inserted': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0,
        'deactivated': 0
    }
    
    try:
        # Scrape all listings
        listings = await scrape_bizbuysell(
            state=state,
            max_pages=max_pages,
            browser_type=browser_type
        )
        
        stats['listings_found'] = len(listings)
        stats['pages_scraped'] = max_pages
        logger.info(f"Found {len(listings)} listings total")
        
        # Save backup immediately after scraping
        if listings:
            save_backup(listings, state)
        
        # Reset connection pool before upsert phase
        logger.info("Starting database upsert...")
        reset_pool()
        
        # Batch upsert with progress callback
        def on_progress(processed, total, batch_stats):
            logger.info(f"Processed {processed}/{total} - Batch: +{batch_stats['inserted']} new, {batch_stats['updated']} updated")
        
        upsert_stats = batch_upsert_listings(
            listings,
            batch_size=50,
            on_progress=on_progress
        )
        
        stats.update(upsert_stats)
        
        # Mark stale listings as inactive
        logger.info("Marking stale listings...")
        reset_pool()  # Fresh connection for stale check
        deactivated = mark_stale_listings('bizbuysell', days_threshold=STALE_THRESHOLD_DAYS)
        stats['deactivated'] = deactivated
        logger.info(f"Deactivated {deactivated} stale listings")
        
        # Update scrape run record - success
        reset_pool()  # Fresh connection for final update
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE scrape_runs
                    SET completed_at = NOW(),
                        status = 'completed',
                        pages_scraped = %s,
                        listings_found = %s,
                        listings_inserted = %s,
                        listings_updated = %s,
                        listings_unchanged = %s,
                        listings_deactivated = %s
                    WHERE id = %s
                """, (
                    stats['pages_scraped'],
                    stats['listings_found'],
                    stats.get('inserted', 0),
                    stats.get('updated', 0),
                    stats.get('unchanged', 0),
                    stats.get('deactivated', 0),
                    run_id
                ))
                conn.commit()
        
        duration = datetime.now() - start_time
        logger.info("=" * 60)
        logger.info(f"Scrape completed successfully in {duration}")
        logger.info("Stats:")
        logger.info(f"  - Listings found: {stats['listings_found']}")
        logger.info(f"  - Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  - Updated: {stats.get('updated', 0)}")
        logger.info(f"  - Unchanged: {stats.get('unchanged', 0)}")
        logger.info(f"  - Deactivated: {stats.get('deactivated', 0)}")
        logger.info(f"  - Errors: {stats['errors']}")
        logger.info("=" * 60)
        
        return stats
        
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        
        # Update scrape run with error
        try:
            reset_pool()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE scrape_runs
                    SET completed_at = NOW(),
                        status = 'failed',
                        error_message = %s
                    WHERE id = %s
                """, (str(e), run_id))
                conn.commit()
        except Exception:
            pass  # Don't mask original error
        
        raise


if __name__ == "__main__":
    asyncio.run(main())
