"""
Simple database migration runner.

Tracks applied migrations in a schema_migrations table.
No external dependencies - just raw SQL files.

Usage:
    python -m app.migrate           # Run pending migrations
    python -m app.migrate --status  # Show migration status
    python -m app.migrate --reset   # Drop all tables and re-run (DANGER!)
"""

import os
import sys
import glob
import argparse
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_connection, init_pool
from app.config import DATABASE_URL


def get_applied_migrations(conn) -> set[str]:
    """Get set of already-applied migration versions."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT version FROM schema_migrations ORDER BY version
            """)
            return {row[0] for row in cur.fetchall()}
    except Exception:
        # Table doesn't exist yet
        return set()


def ensure_migrations_table(conn):
    """Create the migrations tracking table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(50) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                description TEXT
            )
        """)
    conn.commit()


def get_migration_files() -> list[tuple[str, str]]:
    """Get all migration files sorted by version."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    files = glob.glob(str(migrations_dir / "*.sql"))
    
    migrations = []
    for f in sorted(files):
        filename = os.path.basename(f)
        # Extract version (e.g., "001" from "001_initial.sql")
        version = filename.split("_")[0]
        migrations.append((version, f))
    
    return migrations


def run_migration(conn, version: str, filepath: str):
    """Run a single migration file."""
    print(f"  Applying {os.path.basename(filepath)}...")
    
    with open(filepath, 'r') as f:
        sql = f.read()
    
    # Execute the migration
    with conn.cursor() as cur:
        cur.execute(sql)
        
        # Record the migration
        cur.execute("""
            INSERT INTO schema_migrations (version, description)
            VALUES (%s, %s)
            ON CONFLICT (version) DO NOTHING
        """, (version, os.path.basename(filepath)))
    
    conn.commit()
    print(f"  ✅ Applied {version}")


def migrate():
    """Run all pending migrations."""
    print("\n🔄 Running database migrations...")
    print(f"   Database: {DATABASE_URL[:50]}...")
    
    init_pool()
    
    with get_connection() as conn:
        # Ensure migrations table exists
        ensure_migrations_table(conn)
        
        # Get applied migrations
        applied = get_applied_migrations(conn)
        print(f"   Already applied: {len(applied)} migrations")
        
        # Get all migration files
        migrations = get_migration_files()
        print(f"   Available: {len(migrations)} migrations")
        
        # Run pending migrations
        pending = [(v, f) for v, f in migrations if v not in applied]
        
        if not pending:
            print("\n✅ Database is up to date!")
            return
        
        print(f"\n   Pending: {len(pending)} migrations")
        
        for version, filepath in pending:
            run_migration(conn, version, filepath)
        
        print(f"\n✅ Applied {len(pending)} migrations successfully!")


def status():
    """Show migration status."""
    print("\n📊 Migration Status")
    print("=" * 60)
    
    init_pool()
    
    with get_connection() as conn:
        ensure_migrations_table(conn)
        applied = get_applied_migrations(conn)
        migrations = get_migration_files()
        
        for version, filepath in migrations:
            filename = os.path.basename(filepath)
            if version in applied:
                print(f"  ✅ {filename}")
            else:
                print(f"  ⏳ {filename} (pending)")
        
        print("=" * 60)
        print(f"Applied: {len(applied)} | Pending: {len(migrations) - len(applied)}")


def reset():
    """Drop all tables and re-run migrations. DANGER!"""
    print("\n⚠️  WARNING: This will DROP ALL TABLES!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("\n🗑️  Dropping all tables...")
    
    init_pool()
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get all tables
            cur.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            # Drop each table
            for table in tables:
                print(f"   Dropping {table}...")
                cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
        
        conn.commit()
    
    print("\n🔄 Re-running migrations...")
    migrate()


def main():
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--reset", action="store_true", help="Drop all tables and re-run (DANGER!)")
    
    args = parser.parse_args()
    
    if args.status:
        status()
    elif args.reset:
        reset()
    else:
        migrate()


if __name__ == "__main__":
    main()












