"""Statistics and scrape management endpoints."""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from ..models import StatsResponse, ScrapeRunResponse
from ..database import get_connection, init_pool
from ..config import TARGET_STATES

router = APIRouter()

# Track running scrape
_scrape_task = None
_scrape_status = {"running": False, "run_id": None}


class ScrapeRequest(BaseModel):
    states: Optional[list[str]] = None
    max_pages: int = 25


@router.get("", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total active
            cur.execute("SELECT COUNT(*) FROM listings WHERE is_active = TRUE")
            total_active = cur.fetchone()[0]
            
            # New today
            cur.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE DATE(first_seen_at) = CURRENT_DATE
            """)
            new_today = cur.fetchone()[0]
            
            # Updated today (price changed, etc.)
            cur.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE DATE(last_updated_at) = CURRENT_DATE
                  AND last_updated_at > first_seen_at
            """)
            updated_today = cur.fetchone()[0]
            
            # Removed this week
            cur.execute("""
                SELECT COUNT(*) FROM listings 
                WHERE is_active = FALSE
                  AND last_seen_at > NOW() - INTERVAL '7 days'
            """)
            removed_week = cur.fetchone()[0]
            
            # Average price and total value
            cur.execute("""
                SELECT COALESCE(AVG(asking_price), 0), COALESCE(SUM(asking_price), 0)
                FROM listings 
                WHERE is_active = TRUE AND asking_price > 0
            """)
            avg_price, total_value = cur.fetchone()
            
            # By category (top 10)
            cur.execute("""
                SELECT COALESCE(category, 'Uncategorized'), COUNT(*) 
                FROM listings 
                WHERE is_active = TRUE
                GROUP BY category 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            by_category = {row[0]: row[1] for row in cur.fetchall()}
            
            # By state
            cur.execute("""
                SELECT COALESCE(state, 'Unknown'), COUNT(*) 
                FROM listings 
                WHERE is_active = TRUE
                GROUP BY state 
                ORDER BY COUNT(*) DESC
            """)
            by_state = {row[0]: row[1] for row in cur.fetchall()}
    
    return StatsResponse(
        total_active_listings=total_active,
        new_today=new_today,
        updated_today=updated_today,
        removed_this_week=removed_week,
        avg_asking_price=float(avg_price) if avg_price else 0.0,
        total_value=float(total_value) if total_value else 0.0,
        listings_by_category=by_category,
        listings_by_state=by_state
    )


@router.get("/scrape-runs", response_model=list[ScrapeRunResponse])
async def get_scrape_runs(limit: int = 10):
    """Get recent scrape run history."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, source, started_at, completed_at, status,
                       pages_scraped, listings_found, listings_inserted,
                       listings_updated, listings_unchanged, listings_deactivated,
                       error_message
                FROM scrape_runs
                ORDER BY started_at DESC
                LIMIT %s
            """, (limit,))
            
            rows = cur.fetchall()
    
    return [
        ScrapeRunResponse(
            id=row[0],
            source=row[1],
            started_at=row[2],
            completed_at=row[3],
            status=row[4],
            pages_scraped=row[5] or 0,
            listings_found=row[6] or 0,
            listings_inserted=row[7] or 0,
            listings_updated=row[8] or 0,
            listings_unchanged=row[9] or 0,
            listings_deactivated=row[10] or 0,
            error_message=row[11]
        )
        for row in rows
    ]


@router.get("/scrape-status")
async def get_scrape_status():
    """Get current scrape status."""
    if _scrape_status["running"] and _scrape_status["run_id"]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status, listings_found, error_message
                    FROM scrape_runs WHERE id = %s
                """, (_scrape_status["run_id"],))
                row = cur.fetchone()
                if row:
                    return {
                        "running": row[0] == 'running',
                        "run_id": _scrape_status["run_id"],
                        "status": row[0],
                        "listings_found": row[1] or 0,
                        "error": row[2]
                    }
    
    return {"running": False, "run_id": None, "status": "idle"}


async def run_scrape_job(states: list[str], max_pages: int, run_id: int):
    """Background scrape job - runs ALL scrapers."""
    global _scrape_status
    
    try:
        # Import all scrapers (7 sources)
        from scraper.bizbuysell import scrape_bizbuysell
        from scraper.bizquest import scrape_bizquest
        from scraper.businessesforsale import scrape_businessesforsale
        from scraper.transworld import scrape_transworld
        from scraper.fcbb import scrape_fcbb
        from scraper.synergybb import scrape_synergybb
        from scraper.smbdealhunter import scrape_smbdealhunter
        from scraper.upsert import bulk_upsert_listings, mark_stale_listings
        from ..database import reset_pool
        
        total_stats = {
            'found': 0,
            'inserted': 0,
            'updated': 0,
            'unchanged': 0,
            'deactivated': 0,
            'sources_completed': [],
            'sources_failed': []
        }
        
        # Define all scrapers with their configs (7 sources)
        scrapers = [
            ('bizquest', scrape_bizquest, {'max_pages': 50}),
            ('bizbuysell', scrape_bizbuysell, {'max_pages': max_pages}),
            ('businessesforsale', scrape_businessesforsale, {'max_pages': 20}),
            ('transworld', scrape_transworld, {'max_pages': 20}),
            ('synergybb', scrape_synergybb, {}),
            ('smbdealhunter', scrape_smbdealhunter, {'max_clicks': 50}),
            ('fcbb', scrape_fcbb, {}),
        ]
        
        for source_name, scraper_func, kwargs in scrapers:
            try:
                print(f"[SCRAPE] Starting {source_name}...")
                source_listings = []
                
                for state in states:
                    reset_pool()
                    listings = await scraper_func(state=state, **kwargs)
                    source_listings.extend(listings)
                
                if source_listings:
                    reset_pool()
                    result = bulk_upsert_listings(source_listings, source=source_name)
                    total_stats['found'] += len(source_listings)
                    total_stats['inserted'] += result.get('inserted', 0)
                    total_stats['updated'] += result.get('updated', 0)
                    total_stats['unchanged'] += result.get('unchanged', 0)
                
                total_stats['sources_completed'].append(f"{source_name}: {len(source_listings)}")
                print(f"[SCRAPE] ✅ {source_name}: {len(source_listings)} listings")
                
                # Update progress in DB
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE scrape_runs 
                            SET listings_found = %s, listings_inserted = %s,
                                error_message = %s
                            WHERE id = %s
                        """, (total_stats['found'], total_stats['inserted'],
                              f"Completed: {', '.join(total_stats['sources_completed'])}", run_id))
                        conn.commit()
                        
            except Exception as e:
                print(f"[SCRAPE] ❌ {source_name} failed: {e}")
                total_stats['sources_failed'].append(f"{source_name}: {str(e)[:100]}")
        
        # Mark stale listings for each source
        for source_name, _, _ in scrapers:
            try:
                reset_pool()
                deactivated = mark_stale_listings(source_name, days_threshold=7)
                total_stats['deactivated'] += deactivated
            except Exception:
                pass
        
        # Build summary message
        summary = f"Completed: {', '.join(total_stats['sources_completed'])}"
        if total_stats['sources_failed']:
            summary += f" | Failed: {', '.join(total_stats['sources_failed'])}"
        
        # Final update
        status = 'completed' if not total_stats['sources_failed'] else 'partial'
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE scrape_runs 
                    SET completed_at = NOW(), status = %s,
                        listings_found = %s, listings_inserted = %s,
                        listings_updated = %s, listings_unchanged = %s,
                        listings_deactivated = %s, error_message = %s
                    WHERE id = %s
                """, (status, total_stats['found'], total_stats['inserted'], 
                      total_stats['updated'], total_stats['unchanged'],
                      total_stats['deactivated'], summary, run_id))
                conn.commit()
                
    except Exception as e:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE scrape_runs 
                    SET completed_at = NOW(), status = 'failed', error_message = %s
                    WHERE id = %s
                """, (str(e), run_id))
                conn.commit()
    finally:
        _scrape_status["running"] = False
        _scrape_status["run_id"] = None


@router.post("/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Trigger a new scrape. Runs in background."""
    global _scrape_status
    
    if _scrape_status["running"]:
        raise HTTPException(status_code=409, detail="A scrape is already running")
    
    states = request.states or TARGET_STATES
    
    # Create scrape run record
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scrape_runs (source, started_at, status)
                VALUES ('all', NOW(), 'running')
                RETURNING id
            """)
            run_id = cur.fetchone()[0]
            conn.commit()
    
    _scrape_status["running"] = True
    _scrape_status["run_id"] = run_id
    
    # Run in background
    background_tasks.add_task(run_scrape_job, states, request.max_pages, run_id)
    
    return {
        "message": "Scrape started",
        "run_id": run_id,
        "states": states,
        "max_pages": request.max_pages
    }
