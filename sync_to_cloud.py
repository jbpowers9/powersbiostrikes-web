#!/usr/bin/env python3
"""
Sync to Cloud (Supabase)
========================
Syncs local SQLite data to Supabase cloud database.

Run this whenever you update positions or research locally.
Can be run manually or triggered from admin portal.

Usage:
    python sync_to_cloud.py

Environment variables required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_KEY - Your Supabase secret key (sb_secret_...)
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("Installing supabase-py...")
    os.system(f"{sys.executable} -m pip install supabase")
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load .env file first
def load_env_file():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

# Local database path - handle both Windows and WSL paths
def get_biotech_dir():
    env_dir = os.environ.get('BIOTECH_OPTIONS_DIR')
    if env_dir and os.path.exists(env_dir):
        return env_dir
    win_path = r'C:\biotech-options-v2'
    if os.path.exists(win_path):
        return win_path
    wsl_path = '/mnt/c/biotech-options-v2'
    if os.path.exists(wsl_path):
        return wsl_path
    return None

BIOTECH_DIR = get_biotech_dir()
DB_PATH = os.path.join(BIOTECH_DIR, 'biotech_options.db') if BIOTECH_DIR else None

# Supabase credentials - from environment or .env file
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://fnjnqtikxcspebobqdbe.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_local_positions():
    """Fetch open positions from local SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ticker, strike, expiration, option_type, account,
            quantity, avg_cost, entry_date, entry_price, entry_stock_price,
            stock_price, catalyst_date, catalyst_event, catalyst_drug,
            enr, win_prob, cont_score, status, notes,
            created_at, updated_at
        FROM positions
        WHERE status = 'OPEN'
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


def get_local_research():
    """Fetch catalyst research from local SQLite database."""
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get research for open positions only
    cursor.execute("""
        SELECT DISTINCT
            cr.ticker, cr.catalyst_date, cr.catalyst_event,
            cr.drug_name, cr.indication, cr.mcap_millions,
            cr.peak_revenue_millions, cr.short_interest_pct,
            cr.is_breakthrough, cr.is_fast_track, cr.is_orphan,
            cr.is_first_in_class, cr.is_me_too, cr.critical_unmet_need,
            cr.single_indication_only, cr.incremental_improvement,
            cr.market_skepticism, cr.price_change_60d_pct,
            cr.research_notes, cr.trade_analysis_json,
            cr.created_at, cr.updated_at
        FROM catalyst_research cr
        INNER JOIN positions p
            ON cr.ticker = p.ticker
            AND cr.catalyst_date = p.catalyst_date
        WHERE p.status = 'OPEN'
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


def sync_to_supabase(supabase: Client, positions: list, research: list):
    """Sync data to Supabase, replacing existing records."""

    print(f"\nSyncing {len(positions)} positions...")

    # Clear existing open positions and re-insert
    # (This ensures we don't have stale data)
    try:
        # Delete existing OPEN positions
        supabase.table('positions').delete().eq('status', 'OPEN').execute()

        # Insert new positions
        if positions:
            result = supabase.table('positions').insert(positions).execute()
            print(f"  Inserted {len(result.data)} positions")
    except Exception as e:
        print(f"  Error syncing positions: {e}")
        return False

    print(f"\nSyncing {len(research)} research records...")

    try:
        # For research, upsert based on unique key (ticker, catalyst_date, catalyst_event)
        for r in research:
            try:
                # Try to upsert
                supabase.table('catalyst_research').upsert(
                    r,
                    on_conflict='ticker,catalyst_date,catalyst_event'
                ).execute()
            except Exception as e:
                print(f"  Warning: Could not upsert research for {r['ticker']}: {e}")

        print(f"  Synced {len(research)} research records")
    except Exception as e:
        print(f"  Error syncing research: {e}")
        return False

    return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("PowersBioStrikes - Sync to Cloud")
    print("=" * 60)
    print(f"\nLocal database: {DB_PATH}")
    print(f"Supabase URL: {SUPABASE_URL}")

    # Check for secret key
    if not SUPABASE_KEY:
        print("\nError: SUPABASE_KEY not found!")
        print("\nMake sure your .env file contains:")
        print("  SUPABASE_KEY=sb_secret_your_key_here")
        return 1

    # Connect to Supabase
    print("\nConnecting to Supabase...")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("  Connected!")
    except Exception as e:
        print(f"  Error connecting: {e}")
        return 1

    # Get local data
    print("\nReading local database...")
    positions = get_local_positions()
    print(f"  Found {len(positions)} open positions")

    research = get_local_research()
    print(f"  Found {len(research)} research records")

    if not positions:
        print("\nNo open positions to sync.")
        return 0

    # Sync to cloud
    success = sync_to_supabase(supabase, positions, research)

    if success:
        print("\n" + "=" * 60)
        print("Sync completed successfully!")
        print("=" * 60)
        print(f"\nYour data is now live at:")
        print(f"  {SUPABASE_URL}")
        return 0
    else:
        print("\nSync failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
