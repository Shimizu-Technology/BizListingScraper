"""Database upsert logic for listings."""
import json
import sys
import os
import logging
from typing import Callable

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_connection, reset_pool
from .deduplication import compute_content_hash, find_changed_fields

logger = logging.getLogger(__name__)


def upsert_listing(listing: dict) -> str:
    """
    Insert or update a listing with change tracking.
    
    Args:
        listing: Dict with listing data (must have 'external_id')
    
    Returns:
        'inserted', 'updated', or 'unchanged'
    """
    external_id = listing['external_id']
    source = listing.get('source', 'bizbuysell')
    new_hash = compute_content_hash(listing)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if listing exists
            cur.execute("""
                SELECT id, content_hash, raw_data::text
                FROM listings
                WHERE external_id = %s AND source = %s
            """, (external_id, source))
            
            existing = cur.fetchone()
            
            if existing is None:
                # NEW LISTING - Insert
                cur.execute("""
                    INSERT INTO listings (
                        external_id, source, url, title, asking_price, cash_flow,
                        gross_revenue, ebitda, city, state, county, zip_code,
                        category, subcategory, description, highlights,
                        broker_name, broker_company, broker_phone, broker_email,
                        raw_data, content_hash, first_seen_at, last_seen_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    ) RETURNING id
                """, (
                    external_id, source, listing.get('url'),
                    listing.get('title'), listing.get('asking_price'),
                    listing.get('cash_flow'), listing.get('gross_revenue'),
                    listing.get('ebitda'),
                    listing.get('city'), listing.get('state'),
                    listing.get('county'), listing.get('zip_code'),
                    listing.get('category'), listing.get('subcategory'),
                    listing.get('description'), listing.get('highlights'),
                    listing.get('broker_name'), listing.get('broker_company'),
                    listing.get('broker_phone'), listing.get('broker_email'),
                    json.dumps(listing), new_hash
                ))
                
                new_id = cur.fetchone()[0]
                
                # Log creation in history
                cur.execute("""
                    INSERT INTO listing_history (listing_id, change_type, new_values)
                    VALUES (%s, 'created', %s)
                """, (new_id, json.dumps(listing)))
                
                conn.commit()
                return 'inserted'
            
            else:
                existing_id, existing_hash, existing_raw = existing
                
                if existing_hash == new_hash:
                    # NO CHANGES - Just update last_seen
                    cur.execute("""
                        UPDATE listings
                        SET last_seen_at = NOW(), is_active = TRUE
                        WHERE id = %s
                    """, (existing_id,))
                    
                    conn.commit()
                    return 'unchanged'
                
                else:
                    # CONTENT CHANGED - Update and log
                    old_data = json.loads(existing_raw) if existing_raw else {}
                    changed_fields = find_changed_fields(old_data, listing)
                    
                    cur.execute("""
                        UPDATE listings
                        SET title = %s, asking_price = %s, cash_flow = %s,
                            gross_revenue = %s, ebitda = %s, city = %s, state = %s,
                            county = %s, zip_code = %s,
                            category = %s, subcategory = %s,
                            description = %s, highlights = %s,
                            broker_name = %s, broker_company = %s,
                            broker_phone = %s, broker_email = %s,
                            raw_data = %s, content_hash = %s,
                            last_seen_at = NOW(), last_updated_at = NOW(),
                            is_active = TRUE
                        WHERE id = %s
                    """, (
                        listing.get('title'), listing.get('asking_price'),
                        listing.get('cash_flow'), listing.get('gross_revenue'),
                        listing.get('ebitda'),
                        listing.get('city'), listing.get('state'),
                        listing.get('county'), listing.get('zip_code'),
                        listing.get('category'), listing.get('subcategory'),
                        listing.get('description'), listing.get('highlights'),
                        listing.get('broker_name'), listing.get('broker_company'),
                        listing.get('broker_phone'), listing.get('broker_email'),
                        json.dumps(listing), new_hash, existing_id
                    ))
                    
                    # Log changes in history
                    cur.execute("""
                        INSERT INTO listing_history (
                            listing_id, change_type, old_values, new_values, changed_fields
                        ) VALUES (%s, 'updated', %s, %s, %s)
                    """, (
                        existing_id,
                        existing_raw,
                        json.dumps(listing),
                        changed_fields
                    ))
                    
                    conn.commit()
                    return 'updated'


def mark_stale_listings(source: str = 'bizbuysell', days_threshold: int = 3) -> int:
    """
    Mark listings not seen in X days as inactive.
    
    Returns:
        Number of listings deactivated
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE listings
                SET is_active = FALSE, status = 'stale'
                WHERE source = %s
                  AND is_active = TRUE
                  AND last_seen_at < NOW() - INTERVAL '%s days'
                RETURNING id
            """, (source, days_threshold))
            
            deactivated_ids = [row[0] for row in cur.fetchall()]
            
            # Log deactivations
            for listing_id in deactivated_ids:
                cur.execute("""
                    INSERT INTO listing_history (listing_id, change_type)
                    VALUES (%s, 'deactivated')
                """, (listing_id,))
            
            conn.commit()
            return len(deactivated_ids)


def bulk_upsert_listings(listings: list[dict], source: str = 'bizbuysell') -> dict:
    """
    Bulk upsert listings using PostgreSQL's INSERT ... ON CONFLICT.
    Much faster than individual upserts for remote databases.
    
    Args:
        listings: List of listing dicts to upsert
        source: Source identifier (bizbuysell, bizquest, etc.)
    
    Returns:
        Stats dict with inserted, updated, unchanged counts
    """
    if not listings:
        return {'inserted': 0, 'updated': 0, 'unchanged': 0, 'errors': 0}
    
    stats = {'inserted': 0, 'updated': 0, 'unchanged': 0, 'errors': 0}
    
    # Compute content hashes for all listings
    listings_with_hash = []
    for listing in listings:
        if not listing.get('external_id'):
            continue
        listing['content_hash'] = compute_content_hash(listing)
        listing['source'] = listing.get('source', source)
        listings_with_hash.append(listing)
    
    if not listings_with_hash:
        return stats
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Step 1: Get existing listings with their hashes
                external_ids = [l['external_id'] for l in listings_with_hash]
                
                cur.execute("""
                    SELECT external_id, id, content_hash
                    FROM listings
                    WHERE external_id = ANY(%s) AND source = %s
                """, (external_ids, source))
                
                existing = {row[0]: {'id': row[1], 'hash': row[2]} for row in cur.fetchall()}
                
                # Categorize listings
                to_insert = []
                to_update = []
                unchanged_ids = []
                
                for listing in listings_with_hash:
                    ext_id = listing['external_id']
                    if ext_id not in existing:
                        to_insert.append(listing)
                    elif existing[ext_id]['hash'] != listing['content_hash']:
                        listing['_db_id'] = existing[ext_id]['id']
                        to_update.append(listing)
                    else:
                        unchanged_ids.append(existing[ext_id]['id'])
                
                # Step 2: Bulk INSERT new listings
                if to_insert:
                    from psycopg import sql
                    
                    insert_values = []
                    for l in to_insert:
                        insert_values.append((
                            l.get('external_id'), l.get('source', source), l.get('url'),
                            l.get('title'), l.get('asking_price'), l.get('cash_flow'),
                            l.get('gross_revenue'), l.get('ebitda'),
                            l.get('city'), l.get('state'), l.get('county'), l.get('zip_code'),
                            l.get('category'), l.get('subcategory'),
                            l.get('description'), l.get('highlights'),
                            l.get('broker_name'), l.get('broker_company'),
                            l.get('broker_phone'), l.get('broker_email'),
                            json.dumps(l), l['content_hash']
                        ))
                    
                    cur.executemany("""
                        INSERT INTO listings (
                            external_id, source, url, title, asking_price, cash_flow,
                            gross_revenue, ebitda, city, state, county, zip_code,
                            category, subcategory, description, highlights,
                            broker_name, broker_company, broker_phone, broker_email,
                            raw_data, content_hash, first_seen_at, last_seen_at, is_active
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), TRUE
                        )
                        ON CONFLICT (external_id, source) DO UPDATE SET
                            last_seen_at = NOW(),
                            is_active = TRUE
                    """, insert_values)
                    
                    stats['inserted'] = len(to_insert)
                    logger.info(f"Bulk inserted {len(to_insert)} new listings")
                
                # Step 3: Bulk UPDATE changed listings
                if to_update:
                    for l in to_update:
                        cur.execute("""
                            UPDATE listings
                            SET title = %s, asking_price = %s, cash_flow = %s,
                                gross_revenue = %s, ebitda = %s, city = %s, state = %s,
                                county = %s, zip_code = %s, category = %s, subcategory = %s,
                                description = %s, highlights = %s,
                                broker_name = %s, broker_company = %s,
                                broker_phone = %s, broker_email = %s,
                                raw_data = %s, content_hash = %s,
                                last_seen_at = NOW(), last_updated_at = NOW(), is_active = TRUE
                            WHERE id = %s
                        """, (
                            l.get('title'), l.get('asking_price'), l.get('cash_flow'),
                            l.get('gross_revenue'), l.get('ebitda'),
                            l.get('city'), l.get('state'), l.get('county'), l.get('zip_code'),
                            l.get('category'), l.get('subcategory'),
                            l.get('description'), l.get('highlights'),
                            l.get('broker_name'), l.get('broker_company'),
                            l.get('broker_phone'), l.get('broker_email'),
                            json.dumps(l), l['content_hash'], l['_db_id']
                        ))
                    
                    stats['updated'] = len(to_update)
                    logger.info(f"Updated {len(to_update)} changed listings")
                
                # Step 4: Update last_seen for unchanged listings
                if unchanged_ids:
                    cur.execute("""
                        UPDATE listings
                        SET last_seen_at = NOW(), is_active = TRUE
                        WHERE id = ANY(%s)
                    """, (unchanged_ids,))
                    
                    stats['unchanged'] = len(unchanged_ids)
                
                conn.commit()
                
    except Exception as e:
        logger.error(f"Bulk upsert error: {e}")
        stats['errors'] = len(listings_with_hash)
        raise
    
    return stats


def batch_upsert_listings(
    listings: list[dict],
    batch_size: int = 50,
    on_progress: Callable[[int, int, dict], None] | None = None
) -> dict:
    """
    Upsert listings in batches with connection refresh to handle long operations.
    
    Args:
        listings: List of listing dicts to upsert
        batch_size: Number of listings per batch before connection refresh
        on_progress: Optional callback(processed, total, batch_stats)
    
    Returns:
        Stats dict with inserted, updated, unchanged, errors counts
    """
    stats = {'inserted': 0, 'updated': 0, 'unchanged': 0, 'errors': 0}
    total = len(listings)
    
    for i in range(0, total, batch_size):
        batch = listings[i:i + batch_size]
        batch_stats = {'inserted': 0, 'updated': 0, 'unchanged': 0, 'errors': 0}
        
        # Reset connection pool every batch to prevent timeouts
        if i > 0:
            reset_pool()
        
        for listing in batch:
            if not listing.get('external_id'):
                continue
            
            try:
                result = upsert_listing(listing)
                batch_stats[result] += 1
                stats[result] += 1
            except Exception as e:
                logger.error(f"Error upserting {listing.get('external_id')}: {e}")
                stats['errors'] += 1
                batch_stats['errors'] += 1
        
        processed = min(i + batch_size, total)
        
        if on_progress:
            on_progress(processed, total, batch_stats)
        else:
            logger.info(f"Processed {processed}/{total} listings")
    
    return stats
