-- Migration: Add EBITDA and reviewed fields
-- Required for Sam's criteria tracking

-- Add EBITDA field to listings
ALTER TABLE listings ADD COLUMN IF NOT EXISTS ebitda DECIMAL(15, 2);

-- Add is_reviewed field for tracking which listings have been reviewed
ALTER TABLE listings ADD COLUMN IF NOT EXISTS is_reviewed BOOLEAN DEFAULT FALSE;

-- Add reviewed_at timestamp
ALTER TABLE listings ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;

-- Add notes field for user comments on listings
ALTER TABLE listings ADD COLUMN IF NOT EXISTS notes TEXT;

-- Create index for filtering by reviewed status
CREATE INDEX IF NOT EXISTS idx_listings_reviewed ON listings (is_reviewed);

-- Create index for EBITDA filtering
CREATE INDEX IF NOT EXISTS idx_listings_ebitda ON listings (ebitda) WHERE ebitda IS NOT NULL;

