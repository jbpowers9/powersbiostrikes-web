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

# Add biotech-options-v2 to path for imports
BIOTECH_DIR = os.environ.get('BIOTECH_OPTIONS_DIR', '/mnt/c/biotech-options-v2')
if os.path.exists(BIOTECH_DIR):
    sys.path.insert(0, BIOTECH_DIR)

# Try to import from biotech-options-v2
try:
    from schwab_api import SchwabAPI
    from enr_calculator import calculate_enr, calculate_cont_score
    from database import get_database
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    IMPORTS_AVAILABLE = False


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

def get_positions_from_db() -> List[Dict]:
    """Fetch open positions from database."""
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
            cr.trade_analysis_json
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


def get_live_prices(tickers: List[str]) -> Dict[str, Dict]:
    """Fetch live stock prices from Schwab API."""
    prices = {}

    if not IMPORTS_AVAILABLE:
        print("Schwab API not available, using cached data")
        return prices

    try:
        api = SchwabAPI()
        if not api.is_authenticated():
            print("Schwab API not authenticated")
            return prices

        quotes = api.get_quotes(tickers)
        for ticker, data in quotes.items():
            prices[ticker] = {
                'price': data.get('lastPrice', 0),
                'change': data.get('netChange', 0),
                'change_pct': data.get('netPercentChangeInDouble', 0),
                'bid': data.get('bidPrice', 0),
                'ask': data.get('askPrice', 0),
                'volume': data.get('totalVolume', 0),
            }
    except Exception as e:
        print(f"Error fetching quotes: {e}")

    return prices


def get_option_chain(ticker: str, expiration: str, strike: float) -> Dict:
    """Fetch specific option data from Schwab API."""
    if not IMPORTS_AVAILABLE:
        return {}

    try:
        api = SchwabAPI()
        if not api.is_authenticated():
            return {}

        chain = api.get_option_chain(ticker, expiration_date=expiration)
        # Find the specific strike
        for option in chain.get('callExpDateMap', {}).get(expiration, {}).get(str(strike), []):
            return {
                'bid': option.get('bid', 0),
                'ask': option.get('ask', 0),
                'last': option.get('last', 0),
                'volume': option.get('totalVolume', 0),
                'open_interest': option.get('openInterest', 0),
                'iv': option.get('volatility', 0),
            }
    except Exception as e:
        print(f"Error fetching option chain for {ticker}: {e}")

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

    # Calculate entry zone for options (compare current option price to entry)
    # current_price may be total position value, not per-contract - check if it's reasonable
    raw_current = position.get('current_price')
    quantity = position.get('quantity', 1) or 1

    # If current_price exists and seems like a total value (way higher than entry), divide by quantity*100
    if raw_current and entry_price and raw_current > entry_price * 10:
        current_option = raw_current / (quantity * 100)
    elif raw_current:
        current_option = raw_current
    else:
        current_option = entry_price  # Fall back to entry if no current price

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

    # Calculate CONT score
    cont_data = {
        'cont_score': position.get('cont_score', 0),
        'cont_rating': 'unknown'
    }

    if IMPORTS_AVAILABLE:
        try:
            cont_result = calculate_cont_score(
                is_first_in_class=position.get('is_first_in_class', False),
                critical_unmet_need=position.get('critical_unmet_need', False),
                is_orphan=position.get('is_orphan', False),
                has_multiple_catalysts=False,  # Would need pipeline data
                price_change_60d_pct=position.get('price_change_60d_pct', 0),
                mcap_millions=position.get('mcap_millions'),
                is_me_too=False,
                single_indication_only=False,
                incremental_improvement=False,
            )
            cont_data = cont_result
        except:
            pass

    # Calculate live ENR if we have current prices
    enr_data = {
        'enr': 0,
        'win_prob': 0,
        'enr_zone': get_enr_zone(0)
    }

    if IMPORTS_AVAILABLE and current_stock > 0 and current_option > 0:
        try:
            event_type = position.get('catalyst_event', 'Phase 3')
            if 'PDUFA' in event_type or 'Approval' in event_type:
                event_type = 'PDUFA'
            elif 'Phase 3' in event_type:
                event_type = 'Phase 3'
            elif 'Phase 2' in event_type:
                event_type = 'Phase 2'

            enr_result = calculate_enr(
                current_price=current_stock,
                strike=strike,
                premium=current_option,
                days_to_expiry=days_to_expiry,
                event_type=event_type,
                market_data={
                    'mcap': position.get('mcap_millions'),
                    'is_first_in_class': position.get('is_first_in_class', False),
                    'short_interest_pct': position.get('short_interest_pct', 0),
                }
            )
            enr_data = {
                'enr': round(enr_result.get('enr', 0), 1),
                'win_prob': round(enr_result.get('win_prob', 0) * 100, 1),
                'enr_zone': get_enr_zone(enr_result.get('enr', 0))
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
