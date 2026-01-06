-- Migration: Add email alerts feature
-- Run with: python -m app.migrate

-- Email alert subscriptions
CREATE TABLE IF NOT EXISTS alert_subscriptions (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    
    -- Filters for this alert
    state VARCHAR(2),
    category VARCHAR(200),
    min_price DECIMAL(15, 2),
    max_price DECIMAL(15, 2),
    min_cash_flow DECIMAL(15, 2),
    keywords TEXT[],
    
    -- Settings
    frequency VARCHAR(20) DEFAULT 'daily',  -- daily, weekly, immediate
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sent_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT alert_subscriptions_email_unique UNIQUE (email, state, category)
);

CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_active ON alert_subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_email ON alert_subscriptions(email);

-- Alert history (what was sent)
CREATE TABLE IF NOT EXISTS alert_history (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES alert_subscriptions(id) ON DELETE CASCADE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    listings_count INTEGER,
    listing_ids INTEGER[]
);

CREATE INDEX IF NOT EXISTS idx_alert_history_subscription ON alert_history(subscription_id);












