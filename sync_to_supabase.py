#!/usr/bin/env python3
"""
Supabase Sync Script
====================
Syncs catalyst data from SQLite to Supabase.

Setup:
1. Run the SQL in supabase/create_catalysts_table.sql in your Supabase dashboard
2. Get your service role key from Supabase Dashboard > Settings > API > service_role
3. Set environment variable: export SUPABASE_SERVICE_KEY="your-key"
4. Run: python sync_to_supabase.py

Usage:
    python sync_to_supabase.py              # Full sync
    python sync_to_supabase.py --dry-run    # Preview without syncing
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Supabase config (same URL as auth, different key)
SUPABASE_URL = 'https://fnjnqtikxcspebobqdbe.supabase.co'
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

# SQLite database path
def get_db_path():
    paths = [
        r'C:\biotech-options-v2\biotech_options.db',
        '/mnt/c/biotech-options-v2/biotech_options.db',
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

DB_PATH = get_db_path()
PUBLIC_DAYS = 7  # How many days to show publicly


def get_event_type(event: str, stage: str = None) -> str:
    """Categorize catalyst event type."""
    if not event:
        return 'Other'

    event_lower = event.lower()
    stage_lower = (stage or '').lower()

    if any(x in event_lower for x in ['pdufa', 'approval', 'nda', 'bla', 'fda decision']):
        return 'PDUFA'
    elif 'adcom' in event_lower or 'advisory' in event_lower:
        return 'AdCom'
    elif 'initiat' in event_lower or 'start' in event_lower or 'begin' in event_lower:
        return 'Initiation'
    elif 'submission' in event_lower or 'submit' in event_lower:
        return 'Submission'
    elif 'phase 3' in stage_lower or 'phase3' in stage_lower or 'pivotal' in event_lower:
        return 'Phase 3'
    elif 'phase 2' in stage_lower or 'phase2' in stage_lower:
        return 'Phase 2'
    elif 'phase 1' in stage_lower or 'phase1' in stage_lower:
        return 'Phase 1'
    else:
        return 'Other'


def fetch_catalysts_from_sqlite() -> List[Dict]:
    """Fetch all upcoming catalysts from SQLite."""
    if not DB_PATH:
        print(f"[ERROR] Database not found")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ticker, catalyst_date, catalyst_event, drug_name, indication,
            mcap_millions, is_orphan, is_fast_track, is_breakthrough,
            is_first_in_class, is_best_in_class, critical_unmet_need,
            is_priority_review, is_rmat, is_accelerated,
            short_interest_pct,
            stage, is_big_mover, mover_score,
            success_prob, upside_pct, downside_pct,
            cont_score, cont_rating,
            has_crl_history, crl_count,
            is_binary, is_milestone, is_phase1, is_initiation, is_submission,
            company_name, source, confidence
        FROM catalyst_research
        WHERE catalyst_date >= date('now')
        AND (excluded != 1 OR excluded IS NULL)
        ORDER BY catalyst_date ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    today = datetime.now().date()
    public_cutoff = today + timedelta(days=PUBLIC_DAYS)

    catalysts = []
    for row in rows:
        try:
            cat_date = datetime.strptime(row['catalyst_date'], '%Y-%m-%d').date()
            is_public = cat_date <= public_cutoff
        except:
            continue

        event_type = get_event_type(row['catalyst_event'], row['stage'])

        # Override event_type for special events
        if row['is_initiation']:
            event_type = 'Initiation'
        elif row['is_submission']:
            event_type = 'Submission'

        catalyst = {
            'ticker': row['ticker'],
            'catalyst_date': row['catalyst_date'],
            'catalyst_event': row['catalyst_event'],
            'drug_name': row['drug_name'],
            'indication': row['indication'],
            'company_name': row['company_name'],
            'event_type': event_type,
            'stage': row['stage'],
            'is_binary': bool(row['is_binary']) if row['is_binary'] is not None else True,
            'is_milestone': bool(row['is_milestone']) if row['is_milestone'] else False,
            'is_phase1': bool(row['is_phase1']) if row['is_phase1'] else False,
            'is_initiation': bool(row['is_initiation']) if row['is_initiation'] else False,
            'is_submission': bool(row['is_submission']) if row['is_submission'] else False,
            'is_big_mover': bool(row['is_big_mover']) if row['is_big_mover'] else False,
            'mover_score': row['mover_score'],
            'success_prob': row['success_prob'],
            'upside_pct': row['upside_pct'],
            'downside_pct': row['downside_pct'],
            'is_orphan': bool(row['is_orphan']) if row['is_orphan'] else False,
            'is_fast_track': bool(row['is_fast_track']) if row['is_fast_track'] else False,
            'is_breakthrough': bool(row['is_breakthrough']) if row['is_breakthrough'] else False,
            'is_priority_review': bool(row['is_priority_review']) if row['is_priority_review'] else False,
            'is_accelerated': bool(row['is_accelerated']) if row['is_accelerated'] else False,
            'is_rmat': bool(row['is_rmat']) if row['is_rmat'] else False,
            'is_first_in_class': bool(row['is_first_in_class']) if row['is_first_in_class'] else False,
            'is_best_in_class': bool(row['is_best_in_class']) if row['is_best_in_class'] else False,
            'critical_unmet_need': bool(row['critical_unmet_need']) if row['critical_unmet_need'] else False,
            'cont_score': row['cont_score'],
            'cont_rating': row['cont_rating'],
            'has_crl_history': bool(row['has_crl_history']) if row['has_crl_history'] else False,
            'crl_count': row['crl_count'] or 0,
            'mcap_millions': row['mcap_millions'],
            'short_interest_pct': row['short_interest_pct'],
            'source': row['source'] or 'BPIQ',
            'confidence': row['confidence'] or 'high',
            'is_public': is_public,
        }
        catalysts.append(catalyst)

    return catalysts


def sync_to_supabase(catalysts: List[Dict], dry_run: bool = False) -> int:
    """Sync catalysts to Supabase."""
    try:
        from supabase import create_client, Client
    except ImportError:
        print("[ERROR] supabase-py not installed. Run: pip install supabase")
        return 0

    if not SUPABASE_SERVICE_KEY:
        print("[ERROR] SUPABASE_SERVICE_KEY environment variable not set")
        print("  Get your service_role key from Supabase Dashboard > Settings > API")
        print("  Then: export SUPABASE_SERVICE_KEY='your-key-here'")
        return 0

    if dry_run:
        print(f"[DRY RUN] Would sync {len(catalysts)} catalysts to Supabase")
        return len(catalysts)

    # Create Supabase client with service role key
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Clear existing future catalysts and insert fresh data
    # This ensures we don't have stale data
    print(f"[SUPABASE] Clearing existing future catalysts...")
    try:
        supabase.table('catalysts').delete().gte('catalyst_date', datetime.now().strftime('%Y-%m-%d')).execute()
    except Exception as e:
        print(f"[WARN] Could not clear existing catalysts: {e}")

    print(f"[SUPABASE] Inserting {len(catalysts)} catalysts...")

    # Insert in batches of 100
    batch_size = 100
    inserted = 0

    for i in range(0, len(catalysts), batch_size):
        batch = catalysts[i:i + batch_size]
        try:
            result = supabase.table('catalysts').upsert(
                batch,
                on_conflict='ticker,catalyst_date,catalyst_event'
            ).execute()
            inserted += len(batch)
            print(f"  Batch {i//batch_size + 1}: {len(batch)} catalysts")
        except Exception as e:
            print(f"[ERROR] Batch {i//batch_size + 1} failed: {e}")

    return inserted


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sync catalysts to Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Preview without syncing')
    args = parser.parse_args()

    print("=" * 60)
    print("PowersBioStrikes - Supabase Sync")
    print("=" * 60)

    # Fetch from SQLite
    print(f"\n[SQLITE] Fetching catalysts from {DB_PATH}...")
    catalysts = fetch_catalysts_from_sqlite()
    print(f"[SQLITE] Found {len(catalysts)} upcoming catalysts")

    if not catalysts:
        print("[ERROR] No catalysts to sync")
        return

    # Count by type
    by_type = {}
    for c in catalysts:
        t = c['event_type']
        by_type[t] = by_type.get(t, 0) + 1

    print(f"\nBy type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")

    public_count = sum(1 for c in catalysts if c['is_public'])
    print(f"\nPublic (next {PUBLIC_DAYS} days): {public_count}")
    print(f"Members only: {len(catalysts) - public_count}")

    # Sync to Supabase
    print()
    if args.dry_run:
        sync_to_supabase(catalysts, dry_run=True)
    else:
        count = sync_to_supabase(catalysts)
        print(f"\n[COMPLETE] Synced {count} catalysts to Supabase")


if __name__ == '__main__':
    main()
