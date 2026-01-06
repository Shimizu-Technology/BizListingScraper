-- BizListingScraper Initial Schema
-- Run with: python -m app.migrate

-- ============================================================
-- Migration Tracking Table (run this first, only once)
-- ============================================================
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

-- Enable UUID extension (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main listings table
CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'bizbuysell',
    url TEXT NOT NULL,
    
    -- Core listing data
    title TEXT NOT NULL,
    asking_price DECIMAL(15, 2),
    cash_flow DECIMAL(15, 2),
    gross_revenue DECIMAL(15, 2),
    ebitda DECIMAL(15, 2),
    
    -- Location
    city VARCHAR(100),
    state VARCHAR(2),
    county VARCHAR(100),
    zip_code VARCHAR(10),
    
    -- Category
    category VARCHAR(200),
    subcategory VARCHAR(200),
    
    -- Description
    description TEXT,
    highlights TEXT,
    
    -- Seller info
    broker_name VARCHAR(200),
    broker_company VARCHAR(200),
    broker_phone VARCHAR(50),
    broker_email VARCHAR(200),
    
    -- Raw data (for debugging/future use)
    raw_data JSONB,
    
    -- Change tracking
    content_hash VARCHAR(64) NOT NULL,
    
    -- Timestamps
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    
    -- Unique constraint
    CONSTRAINT listings_external_source_unique UNIQUE (external_id, source)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_listings_state ON listings(state);
CREATE INDEX IF NOT EXISTS idx_listings_asking_price ON listings(asking_price);
CREATE INDEX IF NOT EXISTS idx_listings_category ON listings(category);
CREATE INDEX IF NOT EXISTS idx_listings_first_seen ON listings(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_listings_is_active ON listings(is_active);
CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source);

-- Change history table
CREATE TABLE IF NOT EXISTS listing_history (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_type VARCHAR(20) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[]
);

CREATE INDEX IF NOT EXISTS idx_listing_history_listing_id ON listing_history(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_history_changed_at ON listing_history(changed_at);

-- Scrape runs table
CREATE TABLE IF NOT EXISTS scrape_runs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running',
    
    -- Statistics
    pages_scraped INTEGER DEFAULT 0,
    listings_found INTEGER DEFAULT 0,
    listings_inserted INTEGER DEFAULT 0,
    listings_updated INTEGER DEFAULT 0,
    listings_unchanged INTEGER DEFAULT 0,
    listings_deactivated INTEGER DEFAULT 0,
    
    -- Errors
    error_message TEXT,
    error_details JSONB
);

CREATE INDEX IF NOT EXISTS idx_scrape_runs_started_at ON scrape_runs(started_at);

-- Daily statistics
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    source VARCHAR(50) NOT NULL,
    
    total_active_listings INTEGER DEFAULT 0,
    new_listings INTEGER DEFAULT 0,
    updated_listings INTEGER DEFAULT 0,
    removed_listings INTEGER DEFAULT 0,
    
    avg_asking_price DECIMAL(15, 2),
    median_asking_price DECIMAL(15, 2),
    total_listings_value DECIMAL(20, 2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT daily_stats_date_source_unique UNIQUE (date, source)
);

CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_user;
