-- PowersBioStrikes Catalyst Calendar - Supabase Table
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor)

-- Create the catalysts table
CREATE TABLE IF NOT EXISTS catalysts (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    catalyst_date DATE NOT NULL,
    catalyst_event TEXT NOT NULL,

    -- Event details
    drug_name TEXT,
    indication TEXT,
    company_name TEXT,
    event_type VARCHAR(50),
    stage VARCHAR(50),

    -- Classification flags
    is_binary BOOLEAN DEFAULT true,
    is_milestone BOOLEAN DEFAULT false,
    is_phase1 BOOLEAN DEFAULT false,
    is_initiation BOOLEAN DEFAULT false,
    is_submission BOOLEAN DEFAULT false,
    is_big_mover BOOLEAN DEFAULT false,

    -- Risk assessment
    mover_score DECIMAL(5,2),
    success_prob DECIMAL(5,2),
    upside_pct DECIMAL(5,2),
    downside_pct DECIMAL(5,2),

    -- Designations
    is_orphan BOOLEAN DEFAULT false,
    is_fast_track BOOLEAN DEFAULT false,
    is_breakthrough BOOLEAN DEFAULT false,
    is_priority_review BOOLEAN DEFAULT false,
    is_accelerated BOOLEAN DEFAULT false,
    is_rmat BOOLEAN DEFAULT false,
    is_first_in_class BOOLEAN DEFAULT false,
    is_best_in_class BOOLEAN DEFAULT false,
    critical_unmet_need BOOLEAN DEFAULT false,

    -- CONT analysis
    cont_score DECIMAL(5,2),
    cont_rating VARCHAR(20),

    -- CRL history
    has_crl_history BOOLEAN DEFAULT false,
    crl_count INTEGER DEFAULT 0,

    -- Company info
    mcap_millions DECIMAL(12,2),
    short_interest_pct DECIMAL(5,2),

    -- Metadata
    source VARCHAR(50) DEFAULT 'BPIQ',
    confidence VARCHAR(20) DEFAULT 'high',
    is_public BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint to prevent duplicates
    UNIQUE(ticker, catalyst_date, catalyst_event)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_catalysts_date ON catalysts(catalyst_date);
CREATE INDEX IF NOT EXISTS idx_catalysts_ticker ON catalysts(ticker);
CREATE INDEX IF NOT EXISTS idx_catalysts_event_type ON catalysts(event_type);
CREATE INDEX IF NOT EXISTS idx_catalysts_is_public ON catalysts(is_public);
CREATE INDEX IF NOT EXISTS idx_catalysts_is_big_mover ON catalysts(is_big_mover);

-- Enable Row Level Security
ALTER TABLE catalysts ENABLE ROW LEVEL SECURITY;

-- Policy: Public catalysts (next 7 days) readable by anyone
CREATE POLICY "Public catalysts are viewable by everyone"
ON catalysts FOR SELECT
USING (is_public = true);

-- Policy: All catalysts readable by authenticated users
CREATE POLICY "Authenticated users can view all catalysts"
ON catalysts FOR SELECT
TO authenticated
USING (true);

-- Policy: Only service role can insert/update/delete
-- (You'll use the service role key in your sync script)
CREATE POLICY "Service role can manage catalysts"
ON catalysts FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_catalysts_updated_at ON catalysts;
CREATE TRIGGER update_catalysts_updated_at
    BEFORE UPDATE ON catalysts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for the calendar API
CREATE OR REPLACE VIEW calendar_catalysts AS
SELECT
    id,
    ticker,
    catalyst_date,
    catalyst_event,
    drug_name,
    indication,
    company_name,
    event_type,
    stage,
    is_binary,
    is_milestone,
    is_phase1,
    is_initiation,
    is_submission,
    is_big_mover,
    mover_score,
    success_prob,
    upside_pct,
    downside_pct,
    is_orphan,
    is_fast_track,
    is_breakthrough,
    is_priority_review,
    is_accelerated,
    is_rmat,
    is_first_in_class,
    is_best_in_class,
    critical_unmet_need,
    cont_score,
    cont_rating,
    has_crl_history,
    crl_count,
    mcap_millions,
    short_interest_pct,
    is_public,
    -- Computed fields
    (catalyst_date - CURRENT_DATE) as days_until,
    TO_CHAR(catalyst_date, 'Mon DD, YYYY') as date_display,
    TO_CHAR(catalyst_date, 'Day') as weekday
FROM catalysts
WHERE catalyst_date >= CURRENT_DATE
ORDER BY catalyst_date ASC;

-- Grant access to the view
GRANT SELECT ON calendar_catalysts TO anon;
GRANT SELECT ON calendar_catalysts TO authenticated;

COMMENT ON TABLE catalysts IS 'Biotech catalyst calendar data for PowersBioStrikes.com';
