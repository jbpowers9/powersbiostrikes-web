-- PowersBioStrikes Supabase Setup
-- Run this in Supabase SQL Editor

-- =============================================================================
-- POSITIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    strike REAL NOT NULL,
    expiration TEXT NOT NULL,
    option_type TEXT NOT NULL DEFAULT 'CALL',
    account TEXT NOT NULL DEFAULT 'default',
    quantity INTEGER DEFAULT 0,
    avg_cost REAL,
    market_value REAL,
    cost_basis REAL,
    current_price REAL,
    day_pnl REAL,
    total_pnl REAL,
    total_pnl_pct REAL,
    days_to_exp INTEGER,
    stock_price REAL,
    market_cap REAL,
    entry_date TEXT,
    entry_price REAL,
    entry_stock_price REAL,
    catalyst_date TEXT,
    catalyst_event TEXT,
    catalyst_drug TEXT,
    enr REAL,
    win_prob REAL,
    max_buy REAL,
    cont_score INTEGER,
    success_prob REAL,
    status TEXT DEFAULT 'OPEN',
    last_updated TEXT,
    catalyst_type TEXT,
    notes TEXT,
    schwab_cost_basis REAL,
    thesis_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- CATALYST RESEARCH TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS catalyst_research (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    catalyst_date TEXT NOT NULL,
    catalyst_event TEXT NOT NULL,
    drug_name TEXT,
    indication TEXT,
    mcap_millions REAL,
    peak_revenue_millions REAL,
    cash_runway_months INTEGER,
    has_revenue INTEGER DEFAULT 0,
    active_atm INTEGER DEFAULT 0,
    recent_shelf INTEGER DEFAULT 0,
    short_interest_pct REAL,
    days_to_cover REAL,
    is_breakthrough INTEGER DEFAULT 0,
    is_accelerated INTEGER DEFAULT 0,
    is_rmat INTEGER DEFAULT 0,
    is_fast_track INTEGER DEFAULT 0,
    is_priority_review INTEGER DEFAULT 0,
    is_orphan INTEGER DEFAULT 0,
    is_first_in_class INTEGER DEFAULT 0,
    is_best_in_class INTEGER DEFAULT 0,
    is_me_too INTEGER DEFAULT 0,
    competitors_approved INTEGER,
    insider_signal TEXT,
    management_record TEXT,
    prior_results TEXT,
    biomarker_selected INTEGER DEFAULT 0,
    critical_unmet_need INTEGER DEFAULT 0,
    single_indication_only INTEGER DEFAULT 0,
    incremental_improvement INTEGER DEFAULT 0,
    market_skepticism INTEGER DEFAULT 0,
    options_activity TEXT,
    price_change_60d_pct REAL,
    data_completeness_pct REAL,
    research_notes TEXT,
    trade_analysis_json TEXT,
    trade_analysis_date TEXT,
    is_leap_play INTEGER DEFAULT 0,
    drug_type TEXT,
    submission_type TEXT,
    has_priority_review_potential INTEGER DEFAULT 0,
    estimated_nda_filing_months INTEGER,
    estimated_pdufa_date TEXT,
    leap_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, catalyst_date, catalyst_event)
);

-- =============================================================================
-- ROW LEVEL SECURITY
-- =============================================================================
-- Enable RLS
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalyst_research ENABLE ROW LEVEL SECURITY;

-- Allow public read access (for landing page)
CREATE POLICY "Public read access for positions" ON positions
    FOR SELECT USING (true);

CREATE POLICY "Public read access for catalyst_research" ON catalyst_research
    FOR SELECT USING (true);

-- Allow authenticated write access (for sync script)
CREATE POLICY "Service role write access for positions" ON positions
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role write access for catalyst_research" ON catalyst_research
    FOR ALL USING (true) WITH CHECK (true);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_research_ticker ON catalyst_research(ticker);
CREATE INDEX IF NOT EXISTS idx_research_catalyst_date ON catalyst_research(catalyst_date);

-- Done!
SELECT 'Tables created successfully!' as result;
