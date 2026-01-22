#!/usr/bin/env python3
"""
Live Positions Data Generator
==============================
Generates positions.json with live data for the landing page.

Designed to run via GitHub Actions on a schedule (every 30-60 min during market hours).
Can also be run locally for testing.

Data includes:
- Current stock and option prices
- Live ENR calculation
- Break even price
- Entry zone (green/yellow/red)
- OI trends
- CONT score
- Days to catalyst

Usage:
    python generate_live_positions.py

Output:
    data/positions.json
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# =============================================================================
# SUPABASE CONFIGURATION (for GitHub Actions)
# =============================================================================

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

supabase_client = None
if USE_SUPABASE:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"Using Supabase: {SUPABASE_URL}")
    except ImportError:
        print("Warning: supabase package not installed, falling back to local DB")
        USE_SUPABASE = False

# =============================================================================
# SCHWAB API (works in both local and cloud mode)
# =============================================================================

# Try to import local schwab_api (for cloud mode via GitHub Actions)
try:
    from schwab_api import SchwabAPI
    SCHWAB_AVAILABLE = True
    print("Schwab API module loaded")
    # Create a single shared API instance to avoid token refresh issues
    _schwab_api_instance = None
    def get_schwab_api():
        global _schwab_api_instance
        if _schwab_api_instance is None:
            _schwab_api_instance = SchwabAPI()
        return _schwab_api_instance
except ImportError as e:
    print(f"Warning: Could not import schwab_api: {e}")
    SCHWAB_AVAILABLE = False
    def get_schwab_api():
        return None

# Add biotech-options-v2 to path for imports (local mode only)
BIOTECH_DIR = os.environ.get('BIOTECH_OPTIONS_DIR', '/mnt/c/biotech-options-v2')
if os.path.exists(BIOTECH_DIR):
    sys.path.insert(0, BIOTECH_DIR)

# Try to import additional modules from biotech-options-v2 (local mode)
try:
    from enr_calculator import calculate_enr, calculate_cont_score
    from database import get_database
    LOCAL_IMPORTS_AVAILABLE = True
    # Initialize database connection (for local mode)
    if not USE_SUPABASE:
        db = get_database()
    else:
        db = None
except ImportError as e:
    print(f"Note: Local biotech modules not available (expected in cloud mode): {e}")
    LOCAL_IMPORTS_AVAILABLE = False
    db = None

# For backward compatibility
IMPORTS_AVAILABLE = LOCAL_IMPORTS_AVAILABLE


# =============================================================================
# CONFIGURATION
# =============================================================================

DB_PATH = os.path.join(BIOTECH_DIR, 'biotech_options.db')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'positions.json')

# Entry zone thresholds (relative to entry price)
ZONE_GREEN_MAX = 1.10   # Up to 10% above entry = still good
ZONE_YELLOW_MAX = 1.25  # 10-25% above entry = caution
# Above 25% = red (missed the entry)

# ENR thresholds
ENR_GOOD = 140
ENR_CAUTION = 100
ENR_AVOID = 50


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_entry_zone(current_price: float, entry_price: float) -> Dict[str, Any]:
    """Determine entry zone based on current vs entry price."""
    if not entry_price or entry_price <= 0:
        return {'zone': 'unknown', 'color': 'gray', 'message': 'No entry price', 'pct_from_entry': 0}
    if not current_price or current_price <= 0:
        return {'zone': 'unknown', 'color': 'gray', 'message': 'No current price', 'pct_from_entry': 0}

    ratio = current_price / entry_price
    pct_change = (ratio - 1) * 100

    if ratio <= 0.90:
        # Price dropped - even better entry
        return {
            'zone': 'excellent',
            'color': 'green',
            'message': f'Down {abs(pct_change):.1f}% from entry - better value',
            'pct_from_entry': pct_change
        }
    elif ratio <= ZONE_GREEN_MAX:
        return {
            'zone': 'good',
            'color': 'green',
            'message': f'Within {pct_change:.1f}% of entry - still good',
            'pct_from_entry': pct_change
        }
    elif ratio <= ZONE_YELLOW_MAX:
        return {
            'zone': 'caution',
            'color': 'yellow',
            'message': f'Up {pct_change:.1f}% - consider smaller size',
            'pct_from_entry': pct_change
        }
    else:
        return {
            'zone': 'passed',
            'color': 'red',
            'message': f'Up {pct_change:.1f}% - wait for pullback',
            'pct_from_entry': pct_change
        }


def get_enr_zone(enr: float) -> Dict[str, str]:
    """Categorize ENR score."""
    if enr >= ENR_GOOD:
        return {'zone': 'good', 'color': 'green', 'message': 'Strong expected return'}
    elif enr >= ENR_CAUTION:
        return {'zone': 'fair', 'color': 'yellow', 'message': 'Moderate expected return'}
    elif enr >= ENR_AVOID:
        return {'zone': 'weak', 'color': 'orange', 'message': 'Below target threshold'}
    else:
        return {'zone': 'avoid', 'color': 'red', 'message': 'Negative expected return'}


def calculate_cloud_enr(
    stock_price: float,
    strike: float,
    premium: float,
    days_to_expiry: int,
    catalyst_event: str,
    research_data: Dict
) -> Dict[str, Any]:
    """
    Calculate ENR in cloud mode using research data and live stock price.

    This is a simplified calculation when we don't have live option prices.
    Uses historical biotech approval rates and expected moves.
    """

    # Default values based on catalyst type
    event_lower = (catalyst_event or '').lower()

    # Determine win probability based on event type
    if 'pdufa' in event_lower or 'approval' in event_lower:
        base_win_prob = 0.85  # FDA approval success rate ~85%
    elif 'phase 3' in event_lower:
        base_win_prob = 0.60  # Phase 3 success rate ~60%
    elif 'phase 2' in event_lower:
        base_win_prob = 0.40  # Phase 2 success rate ~40%
    else:
        base_win_prob = 0.50  # Default

    # Adjust for research factors
    if research_data.get('is_first_in_class'):
        base_win_prob += 0.05
    if research_data.get('is_orphan'):
        base_win_prob += 0.05
    if research_data.get('is_fast_track'):
        base_win_prob += 0.03
    if research_data.get('is_breakthrough'):
        base_win_prob += 0.05

    # Cap win probability
    win_prob = min(0.95, base_win_prob)

    # Expected move on win (typical biotech approval move)
    if 'pdufa' in event_lower:
        expected_gain_pct = 0.80  # 80% stock move on approval
    elif 'phase 3' in event_lower:
        expected_gain_pct = 1.20  # 120% on positive Phase 3
    else:
        expected_gain_pct = 0.60  # 60% default

    # Calculate option payoff on win
    if stock_price > 0 and premium > 0:
        stock_on_win = stock_price * (1 + expected_gain_pct)
        intrinsic_on_win = max(0, stock_on_win - strike)
        option_return_on_win = (intrinsic_on_win / premium - 1) * 100 if intrinsic_on_win > premium else -50
    else:
        option_return_on_win = 200  # Default assumption

    # Loss on lose (options typically lose 80-100%)
    option_return_on_lose = -90

    # Calculate ENR
    enr = (win_prob * option_return_on_win) + ((1 - win_prob) * option_return_on_lose)

    return {
        'enr': max(0, round(enr, 1)),
        'win_prob': round(win_prob * 100, 1),
        'is_live': True,
        'calculation_method': 'cloud'
    }


def calculate_break_even(strike: float, premium: float, option_type: str = 'CALL') -> float:
    """Calculate break even price at expiration."""
    if option_type.upper() == 'CALL':
        return strike + premium
    else:
        return strike - premium


def calculate_days_to_date(target_date_str: str) -> int:
    """Calculate days until a target date."""
    try:
        target = datetime.strptime(target_date_str, '%Y-%m-%d')
        today = datetime.now()
        delta = target - today
        return max(0, delta.days)
    except:
        return -1


def get_max_buy_price(entry_price: float) -> float:
    """Calculate maximum recommended buy price (10% above entry)."""
    return round(entry_price * ZONE_GREEN_MAX, 2)


# =============================================================================
# DATA FETCHING
# =============================================================================

def get_positions_from_supabase() -> List[Dict]:
    """Fetch open positions from Supabase cloud database."""
    if not supabase_client:
        return []

    try:
        # Get positions
        positions_result = supabase_client.table('positions').select('*').eq('status', 'OPEN').execute()
        positions = positions_result.data or []

        # Get research data
        research_result = supabase_client.table('catalyst_research').select('*').execute()
        research_map = {}
        for r in (research_result.data or []):
            key = (r['ticker'], r['catalyst_date'])
            research_map[key] = r

        # Merge research into positions
        for pos in positions:
            key = (pos['ticker'], pos.get('catalyst_date'))
            research = research_map.get(key, {})
            pos['research_notes'] = research.get('research_notes')
            pos['mcap_millions'] = research.get('mcap_millions')
            pos['peak_revenue_millions'] = research.get('peak_revenue_millions')
            pos['is_first_in_class'] = research.get('is_first_in_class')
            pos['is_orphan'] = research.get('is_orphan')
            pos['is_fast_track'] = research.get('is_fast_track')
            pos['is_breakthrough'] = research.get('is_breakthrough')
            pos['short_interest_pct'] = research.get('short_interest_pct')
            pos['critical_unmet_need'] = research.get('critical_unmet_need')
            pos['price_change_60d_pct'] = research.get('price_change_60d_pct')
            pos['trade_analysis_json'] = research.get('trade_analysis_json')
            pos['is_me_too'] = research.get('is_me_too')
            pos['single_indication_only'] = research.get('single_indication_only')
            pos['incremental_improvement'] = research.get('incremental_improvement')
            pos['market_skepticism'] = research.get('market_skepticism')

        return positions
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return []


def get_positions_from_sqlite() -> List[Dict]:
    """Fetch open positions from local SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.*,
            cr.research_notes,
            cr.mcap_millions,
            cr.peak_revenue_millions,
            cr.is_first_in_class,
            cr.is_orphan,
            cr.is_fast_track,
            cr.is_breakthrough,
            cr.short_interest_pct,
            cr.critical_unmet_need,
            cr.price_change_60d_pct,
            cr.trade_analysis_json,
            cr.is_me_too,
            cr.single_indication_only,
            cr.incremental_improvement,
            cr.market_skepticism
        FROM positions p
        LEFT JOIN catalyst_research cr
            ON p.ticker = cr.ticker
            AND p.catalyst_date = cr.catalyst_date
        WHERE p.status = 'OPEN'
        ORDER BY p.catalyst_date ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


def get_positions_from_db() -> List[Dict]:
    """Fetch open positions from database (Supabase or local SQLite)."""
    if USE_SUPABASE:
        print("Fetching positions from Supabase...")
        return get_positions_from_supabase()
    else:
        print("Fetching positions from local SQLite...")
        return get_positions_from_sqlite()


def get_live_prices(tickers: List[str]) -> Dict[str, Dict]:
    """Fetch live stock prices from Schwab API."""
    prices = {}

    if not SCHWAB_AVAILABLE:
        print("Schwab API not available")
        return prices

    try:
        api = get_schwab_api()
        if api and api.is_authenticated():
            print(f"Fetching live prices from Schwab API for: {tickers}")
            quotes = api.get_quotes(tickers)
            for ticker, data in quotes.items():
                # Schwab returns nested structure: data['quote']['lastPrice']
                quote_data = data.get('quote', data)  # Fall back to data if no 'quote' key
                price = quote_data.get('lastPrice', 0) or quote_data.get('mark', 0)
                prices[ticker] = {
                    'price': price,
                    'change': quote_data.get('netChange', 0),
                    'change_pct': quote_data.get('netPercentChangeInDouble', 0),
                    'bid': quote_data.get('bidPrice', 0),
                    'ask': quote_data.get('askPrice', 0),
                    'volume': quote_data.get('totalVolume', 0),
                }
                print(f"  {ticker}: ${price:.2f}")
            return prices
        else:
            print("Schwab API not authenticated")
    except Exception as e:
        print(f"Schwab API error: {e}")

    return prices


def get_option_price(ticker: str, expiration: str, strike: float, option_type: str = 'CALL') -> Dict:
    """Fetch specific option price from Schwab API."""
    if not SCHWAB_AVAILABLE:
        return {}

    try:
        api = get_schwab_api()
        if not api or not api.is_authenticated():
            print(f"Cannot get option price - not authenticated")
            return {}

        # Get option chain for this ticker and expiration
        print(f"  Fetching option chain for {ticker} {expiration} ${strike} {option_type}")
        chain = api.get_option_chain(ticker, expiration_date=expiration)

        if not chain:
            print(f"  No option chain returned for {ticker}")
            return {}

        # Navigate to the correct expiration and strike
        exp_map_key = 'callExpDateMap' if option_type.upper() == 'CALL' else 'putExpDateMap'
        exp_map = chain.get(exp_map_key, {})

        # Schwab uses format like "2026-07-17:500" for the key
        for exp_key, strikes in exp_map.items():
            if expiration in exp_key:
                # Look for the strike
                strike_str = str(float(strike))
                if strike_str in strikes:
                    options = strikes[strike_str]
                    if options and len(options) > 0:
                        opt = options[0]
                        bid = opt.get('bid', 0)
                        ask = opt.get('ask', 0)
                        last = opt.get('last', 0)
                        mid = (bid + ask) / 2 if bid and ask else last
                        print(f"  Found option: bid=${bid:.2f}, ask=${ask:.2f}, mid=${mid:.2f}")
                        return {
                            'bid': bid,
                            'ask': ask,
                            'last': last,
                            'mid': mid,
                            'volume': opt.get('totalVolume', 0),
                            'open_interest': opt.get('openInterest', 0),
                            'iv': opt.get('volatility', 0),
                        }

        print(f"  Strike ${strike} not found in option chain")
    except Exception as e:
        print(f"Error fetching option price for {ticker}: {e}")

    return {}


# =============================================================================
# MAIN GENERATION
# =============================================================================

def generate_position_data(position: Dict, stock_price: Optional[float] = None) -> Dict:
    """Generate full position data with live calculations."""

    ticker = position['ticker']
    strike = position.get('strike', 0) or 0
    expiration = position.get('expiration', '')
    entry_price = position.get('entry_price') or position.get('avg_cost') or 0
    catalyst_date = position.get('catalyst_date', '')

    # Use provided stock price or fall back to stored
    current_stock = stock_price or position.get('stock_price') or 0

    # Calculate days to expiry and catalyst
    days_to_expiry = calculate_days_to_date(expiration)
    days_to_catalyst = calculate_days_to_date(catalyst_date)

    # Calculate break even
    break_even = calculate_break_even(strike, entry_price)

    # Get current option price from Schwab API
    quantity = position.get('quantity', 1) or 1
    option_type = position.get('option_type', 'CALL')

    # Try to get live option price from Schwab
    current_option = entry_price  # Default to entry price
    option_data = get_option_price(ticker, expiration, strike, option_type)
    if option_data and option_data.get('mid', 0) > 0:
        current_option = option_data['mid']
        print(f"  {ticker}: Live option price = ${current_option:.2f}")
    else:
        # Fall back to stored current_price or entry_price
        raw_current = position.get('current_price')
        if raw_current and entry_price and raw_current > entry_price * 10:
            current_option = raw_current / (quantity * 100)
        elif raw_current:
            current_option = raw_current
        print(f"  {ticker}: Using stored option price = ${current_option:.2f}")

    entry_zone = get_entry_zone(current_option, entry_price)

    # Max buy price
    max_buy = get_max_buy_price(entry_price)

    # Parse trade analysis for thesis highlights
    thesis_highlights = []
    risks = []
    try:
        if position.get('trade_analysis_json'):
            analysis = json.loads(position['trade_analysis_json'])
            # Extract key info
            if analysis.get('executive_summary'):
                thesis_highlights.append(analysis['executive_summary'][:300] + '...')
            risks = analysis.get('key_risks', [])[:3]
    except:
        pass

    # Calculate CONT score using research data
    # In Supabase mode: use synced cont_score OR calculate from merged research data
    # In local mode: use database single source of truth
    cont_data = {
        'cont_score': position.get('cont_score', 0),
        'cont_rating': get_cont_rating(position.get('cont_score', 0))
    }

    # If we have local database access, recalculate for accuracy
    if IMPORTS_AVAILABLE and db and not USE_SUPABASE:
        try:
            research = db.get_catalyst_research(ticker, catalyst_date, position.get('catalyst_event'))
            if research:
                cont_result = calculate_cont_score(
                    is_first_in_class=bool(research.get('is_first_in_class')),
                    critical_unmet_need=bool(research.get('critical_unmet_need')),
                    is_orphan=bool(research.get('is_orphan')),
                    is_breakthrough=bool(research.get('is_breakthrough')),
                    is_fast_track=bool(research.get('is_fast_track')),
                    multiple_catalysts=1,
                    price_change_60d_pct=research.get('price_change_60d_pct') or 0,
                    mcap_millions=research.get('mcap_millions'),
                    is_me_too=bool(research.get('is_me_too')),
                    single_indication_only=bool(research.get('single_indication_only')),
                    incremental_improvement=bool(research.get('incremental_improvement')),
                    market_skepticism=bool(research.get('market_skepticism')),
                )
                cont_data = cont_result
        except Exception as e:
            print(f"Error calculating CONT for {ticker}: {e}")
    elif USE_SUPABASE and IMPORTS_AVAILABLE:
        # In Supabase mode with enr_calculator available, calculate from merged research
        try:
            cont_result = calculate_cont_score(
                is_first_in_class=bool(position.get('is_first_in_class')),
                critical_unmet_need=bool(position.get('critical_unmet_need')),
                is_orphan=bool(position.get('is_orphan')),
                is_breakthrough=bool(position.get('is_breakthrough')),
                is_fast_track=bool(position.get('is_fast_track')),
                multiple_catalysts=1,
                price_change_60d_pct=position.get('price_change_60d_pct') or 0,
                mcap_millions=position.get('mcap_millions'),
                is_me_too=bool(position.get('is_me_too')),
                single_indication_only=bool(position.get('single_indication_only')),
                incremental_improvement=bool(position.get('incremental_improvement')),
                market_skepticism=bool(position.get('market_skepticism')),
            )
            cont_data = cont_result
        except Exception as e:
            print(f"Error calculating CONT for {ticker} in Supabase mode: {e}")

    # Calculate live ENR if we have current prices
    # In local mode: use database single source of truth for live calculation
    # In Supabase/cloud mode: calculate ENR using research data + live stock prices
    synced_enr = position.get('enr') or 0
    synced_win_prob = position.get('win_prob') or 0

    enr_data = {
        'enr': round(synced_enr, 1),
        'win_prob': round(synced_win_prob * 100, 1) if synced_win_prob < 1 else round(synced_win_prob, 1),
        'enr_zone': get_enr_zone(synced_enr),
        'is_live': False
    }

    # Cloud mode: calculate ENR using research data + live stock/option prices
    if SCHWAB_AVAILABLE and current_stock > 0 and current_option > 0:
        try:
            research_data = {
                'is_first_in_class': position.get('is_first_in_class'),
                'is_orphan': position.get('is_orphan'),
                'is_fast_track': position.get('is_fast_track'),
                'is_breakthrough': position.get('is_breakthrough'),
            }
            cloud_enr = calculate_cloud_enr(
                stock_price=current_stock,
                strike=strike,
                premium=current_option,  # Use live option price
                days_to_expiry=days_to_expiry,
                catalyst_event=position.get('catalyst_event', ''),
                research_data=research_data
            )
            enr_data = {
                'enr': cloud_enr['enr'],
                'win_prob': cloud_enr['win_prob'],
                'enr_zone': get_enr_zone(cloud_enr['enr']),
                'is_live': True
            }
            print(f"  {ticker}: Live ENR = {cloud_enr['enr']:.1f}%, Win Prob = {cloud_enr['win_prob']:.1f}%")
        except Exception as e:
            print(f"  Error calculating live ENR for {ticker}: {e}")

    # If we have local database, calculate live ENR (more accurate)
    elif IMPORTS_AVAILABLE and db and not USE_SUPABASE and current_stock > 0 and current_option > 0:
        try:
            enr_inputs = db.get_enr_inputs_for_catalyst(
                ticker=ticker,
                catalyst_date=catalyst_date,
                catalyst_event=position.get('catalyst_event')
            )

            enr_result = calculate_enr(
                current_price=current_stock,
                strike=strike,
                premium=current_option,
                days_to_expiry=days_to_expiry,
                event_type=enr_inputs['event_type'],
                indication=enr_inputs['indication'],
                market_data=enr_inputs['market_data'],
                adjustments=enr_inputs['adjustments'],
            )
            enr_data = {
                'enr': round(enr_result.get('enr', 0), 1),
                'win_prob': round(enr_result.get('win_prob', 0) * 100, 1),
                'enr_zone': get_enr_zone(enr_result.get('enr', 0)),
                'research_found': enr_inputs.get('research_found', False),
                'is_live': True
            }
        except Exception as e:
            print(f"Error calculating ENR for {ticker}: {e}")

    # Build position object
    return {
        'ticker': ticker,
        'status': position.get('status', 'OPEN'),
        'category': get_category_from_indication(position.get('catalyst_event', '')),

        # Position details
        'position': {
            'strike': strike,
            'expiration': expiration,
            'expiration_display': format_date(expiration),
            'option_type': position.get('option_type', 'CALL'),
            'quantity': position.get('quantity', 0),
        },

        # Prices
        'prices': {
            'entry': entry_price,
            'current': current_option,
            'stock_price': current_stock,
            'break_even': break_even,
            'max_buy': max_buy,
            'pnl_pct': round((current_option - entry_price) / entry_price * 100, 1) if entry_price > 0 else 0,
        },

        # Entry zone
        'entry_zone': entry_zone,

        # ENR data
        'enr': enr_data,

        # CONT score
        'cont': {
            'score': cont_data.get('cont_score', 0),
            'rating': cont_data.get('cont_rating', 'unknown'),
            'display': get_cont_display(cont_data.get('cont_score', 0)),
        },

        # Catalyst info
        'catalyst': {
            'date': catalyst_date,
            'date_display': format_date(catalyst_date),
            'event': position.get('catalyst_event', ''),
            'drug': position.get('catalyst_drug', ''),
            'days_to_catalyst': days_to_catalyst,
        },

        # Timing
        'timing': {
            'days_to_expiry': days_to_expiry,
            'entry_date': position.get('entry_date', ''),
        },

        # Thesis
        'thesis': {
            'drug_name': position.get('catalyst_drug', ''),
            'indication': extract_indication(position.get('catalyst_event', '')),
            'highlights': thesis_highlights,
            'risks': risks,
            'is_first_in_class': position.get('is_first_in_class', False),
            'is_orphan': position.get('is_orphan', False),
            'is_fast_track': position.get('is_fast_track', False),
            'short_interest': position.get('short_interest_pct', 0),
        },

        # OI tracking (placeholder - would need historical data)
        'oi': {
            'current': 0,
            'change_1d': 0,
            'change_5d': 0,
            'trend': 'unknown',
        },

        # Metadata
        'last_updated': datetime.now().isoformat(),
    }


def get_category_from_indication(event: str) -> str:
    """Extract category from catalyst event."""
    event_lower = event.lower()
    if 'lung' in event_lower or 'nsclc' in event_lower or 'cancer' in event_lower or 'oncolog' in event_lower:
        return 'Oncology'
    elif 'fung' in event_lower or 'infect' in event_lower:
        return 'Infectious Disease'
    elif 'neuro' in event_lower or 'cns' in event_lower:
        return 'CNS/Neurology'
    elif 'cardio' in event_lower or 'heart' in event_lower:
        return 'Cardiovascular'
    elif 'autoimmune' in event_lower or 'inflam' in event_lower:
        return 'Autoimmune'
    return 'Biotech'


def extract_indication(event: str) -> str:
    """Extract indication from event string."""
    # Simple extraction - would be better from database
    return event


def format_date(date_str: str) -> str:
    """Format date for display."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except:
        return date_str


def get_cont_display(score: int) -> str:
    """Get CONT score display text."""
    if score is None:
        return 'Unknown'
    if score >= 80:
        return 'High (Hold Through)'
    elif score >= 50:
        return 'Moderate'
    else:
        return 'Low (Exit Early)'


def get_cont_rating(score: int) -> str:
    """Get CONT score rating category."""
    if score is None:
        return 'unknown'
    if score >= 80:
        return 'HIGH'
    elif score >= 50:
        return 'MODERATE'
    else:
        return 'LOW'


def generate_all_positions() -> Dict:
    """Generate data for all open positions."""

    # Get positions from database
    positions = get_positions_from_db()

    if not positions:
        print("No open positions found")
        return {'positions': [], 'last_updated': datetime.now().isoformat()}

    # Get unique tickers
    tickers = list(set(p['ticker'] for p in positions))

    # Fetch live stock prices
    live_prices = get_live_prices(tickers)

    # Process each position
    processed = []
    for pos in positions:
        ticker = pos['ticker']
        stock_price = live_prices.get(ticker, {}).get('price')

        position_data = generate_position_data(pos, stock_price)
        processed.append(position_data)

    # Generate summary stats
    total_positions = len(processed)
    total_value = sum(p['prices']['current'] * p['position']['quantity'] * 100 for p in processed)

    return {
        'positions': processed,
        'summary': {
            'total_positions': total_positions,
            'total_value': round(total_value, 2),
            'avg_days_to_catalyst': round(sum(p['catalyst']['days_to_catalyst'] for p in processed) / total_positions, 0) if total_positions > 0 else 0,
        },
        'market_status': {
            'is_open': is_market_open(),
            'last_updated': datetime.now().isoformat(),
        },
        'last_updated': datetime.now().isoformat(),
    }


def is_market_open() -> bool:
    """Check if market is currently open."""
    now = datetime.now()
    # Simple check - weekday and between 9:30 AM and 4 PM ET
    if now.weekday() >= 5:  # Weekend
        return False
    # Would need proper timezone handling for production
    return True


def main():
    """Main entry point."""
    print(f"Generating live positions data...")
    print(f"Database: {DB_PATH}")
    print(f"Output: {OUTPUT_FILE}")

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate data
    data = generate_all_positions()

    # Write to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Generated data for {len(data.get('positions', []))} positions")
    print(f"Output written to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
