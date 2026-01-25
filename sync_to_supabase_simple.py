#!/usr/bin/env python3
"""
Simple Supabase Sync - Uses REST API directly (no supabase-py needed)
"""

import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta

# Supabase config
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
PUBLIC_DAYS = 7


def get_event_type(event, stage=None):
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
    return 'Other'


def fetch_catalysts():
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
            short_interest_pct, stage, is_big_mover, mover_score,
            success_prob, upside_pct, downside_pct,
            cont_score, cont_rating, has_crl_history, crl_count,
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
            'mover_score': float(row['mover_score']) if row['mover_score'] else None,
            'success_prob': float(row['success_prob']) if row['success_prob'] else None,
            'upside_pct': float(row['upside_pct']) if row['upside_pct'] else None,
            'downside_pct': float(row['downside_pct']) if row['downside_pct'] else None,
            'is_orphan': bool(row['is_orphan']) if row['is_orphan'] else False,
            'is_fast_track': bool(row['is_fast_track']) if row['is_fast_track'] else False,
            'is_breakthrough': bool(row['is_breakthrough']) if row['is_breakthrough'] else False,
            'is_priority_review': bool(row['is_priority_review']) if row['is_priority_review'] else False,
            'is_accelerated': bool(row['is_accelerated']) if row['is_accelerated'] else False,
            'is_rmat': bool(row['is_rmat']) if row['is_rmat'] else False,
            'is_first_in_class': bool(row['is_first_in_class']) if row['is_first_in_class'] else False,
            'is_best_in_class': bool(row['is_best_in_class']) if row['is_best_in_class'] else False,
            'critical_unmet_need': bool(row['critical_unmet_need']) if row['critical_unmet_need'] else False,
            'cont_score': float(row['cont_score']) if row['cont_score'] else None,
            'cont_rating': row['cont_rating'],
            'has_crl_history': bool(row['has_crl_history']) if row['has_crl_history'] else False,
            'crl_count': row['crl_count'] or 0,
            'mcap_millions': float(row['mcap_millions']) if row['mcap_millions'] else None,
            'short_interest_pct': float(row['short_interest_pct']) if row['short_interest_pct'] else None,
            'source': row['source'] or 'BPIQ',
            'confidence': row['confidence'] or 'high',
            'is_public': is_public,
        }
        catalysts.append(catalyst)

    return catalysts


def sync_to_supabase(catalysts):
    if not SUPABASE_SERVICE_KEY:
        print("[ERROR] SUPABASE_SERVICE_KEY not set")
        return 0

    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }

    # Clear existing future catalysts
    print("[SUPABASE] Clearing existing future catalysts...")
    today = datetime.now().strftime('%Y-%m-%d')
    delete_url = f"{SUPABASE_URL}/rest/v1/catalysts?catalyst_date=gte.{today}"
    resp = requests.delete(delete_url, headers=headers)
    if resp.status_code not in [200, 204]:
        print(f"[WARN] Delete failed: {resp.status_code} {resp.text}")

    # Insert in batches
    print(f"[SUPABASE] Inserting {len(catalysts)} catalysts...")
    batch_size = 100
    inserted = 0

    for i in range(0, len(catalysts), batch_size):
        batch = catalysts[i:i + batch_size]
        url = f"{SUPABASE_URL}/rest/v1/catalysts"
        resp = requests.post(url, headers=headers, json=batch)

        if resp.status_code in [200, 201]:
            inserted += len(batch)
            print(f"  Batch {i//batch_size + 1}: {len(batch)} catalysts")
        else:
            print(f"[ERROR] Batch {i//batch_size + 1} failed: {resp.status_code} {resp.text[:200]}")

    return inserted


def main():
    print("=" * 60)
    print("PowersBioStrikes - Supabase Sync")
    print("=" * 60)

    print(f"\n[SQLITE] Fetching catalysts from {DB_PATH}...")
    catalysts = fetch_catalysts()
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

    count = sync_to_supabase(catalysts)
    print(f"\n[COMPLETE] Synced {count} catalysts to Supabase")


if __name__ == '__main__':
    main()
