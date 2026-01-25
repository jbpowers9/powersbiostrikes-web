#!/usr/bin/env python3
"""
Catalyst Calendar Generator
============================
Generates calendar.json for the PowersBioStrikes website.

Public (next 7 days): Basic info to hook them
Members-only (beyond 7 days): Full details + your analysis

Usage:
    python generate_catalyst_calendar.py
    python generate_catalyst_calendar.py --days 14  # Show 14 days public
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Database path - handle both Windows and WSL paths
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

# Output path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'data', 'calendar.json')


def get_catalyst_type(event: str) -> str:
    """Categorize catalyst event type."""
    if not event:
        return 'Other'

    event_lower = event.lower()

    if any(x in event_lower for x in ['pdufa', 'approval', 'nda', 'bla', 'fda decision']):
        return 'PDUFA'
    elif 'adcom' in event_lower or 'advisory' in event_lower:
        return 'AdCom'
    elif 'phase 3' in event_lower or 'phase3' in event_lower or 'pivotal' in event_lower:
        return 'Phase 3'
    elif 'phase 2' in event_lower or 'phase2' in event_lower:
        return 'Phase 2'
    elif 'phase 1' in event_lower or 'phase1' in event_lower:
        return 'Phase 1'
    else:
        return 'Other'


def get_binary_risk(catalyst_type: str, is_binary: int = None) -> Dict:
    """Assess binary risk level."""
    if is_binary:
        return {'level': 'HIGH', 'color': 'red', 'note': 'Binary event - expect 30-70% move'}

    if catalyst_type == 'PDUFA':
        return {'level': 'HIGH', 'color': 'red', 'note': 'FDA decision - binary outcome'}
    elif catalyst_type == 'AdCom':
        return {'level': 'HIGH', 'color': 'red', 'note': 'Advisory committee - high volatility expected'}
    elif catalyst_type == 'Phase 3':
        return {'level': 'MEDIUM-HIGH', 'color': 'orange', 'note': 'Pivotal data - significant move likely'}
    elif catalyst_type == 'Phase 2':
        return {'level': 'MEDIUM', 'color': 'yellow', 'note': 'Early efficacy data'}
    else:
        return {'level': 'LOW', 'color': 'gray', 'note': 'Non-binary catalyst'}


def generate_calendar(public_days: int = 7) -> Dict:
    """Generate the catalyst calendar JSON."""

    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all upcoming catalysts
    cursor.execute("""
        SELECT
            ticker, catalyst_date, catalyst_event, drug_name, indication,
            mcap_millions, is_orphan, is_fast_track, is_breakthrough,
            is_first_in_class, is_best_in_class, critical_unmet_need,
            is_leap_play, estimated_pdufa_date, data_completeness_pct,
            research_notes, is_priority_review, is_rmat, is_accelerated,
            short_interest_pct
        FROM catalyst_research
        WHERE catalyst_date >= date('now')
        AND (excluded != 1 OR excluded IS NULL)
        ORDER BY catalyst_date ASC
    """)

    rows = cursor.fetchall()

    # Also get any positions we have for these tickers (for CONT scores)
    cursor.execute("""
        SELECT ticker, cont_score, play_type
        FROM positions
        WHERE status = 'OPEN'
    """)
    position_data = {row['ticker']: dict(row) for row in cursor.fetchall()}

    conn.close()

    today = datetime.now().date()
    public_cutoff = today + timedelta(days=public_days)

    catalysts = []

    for row in rows:
        ticker = row['ticker']
        catalyst_date = row['catalyst_date']

        # Parse date
        try:
            cat_dt = datetime.strptime(catalyst_date, '%Y-%m-%d').date()
            days_until = (cat_dt - today).days
        except:
            continue

        # Determine if public or members-only
        is_public = cat_dt <= public_cutoff

        # Get catalyst type
        catalyst_type = get_catalyst_type(row['catalyst_event'])

        # Get binary risk
        binary_risk = get_binary_risk(catalyst_type)

        # Build designation flags
        designations = []
        if row['is_orphan']:
            designations.append({'code': 'ORPHAN', 'label': 'Orphan Drug', 'color': 'purple'})
        if row['is_fast_track']:
            designations.append({'code': 'FT', 'label': 'Fast Track', 'color': 'blue'})
        if row['is_breakthrough']:
            designations.append({'code': 'BTD', 'label': 'Breakthrough Therapy', 'color': 'green'})
        if row['is_priority_review']:
            designations.append({'code': 'PR', 'label': 'Priority Review', 'color': 'orange'})
        if row['is_accelerated']:
            designations.append({'code': 'AA', 'label': 'Accelerated Approval', 'color': 'yellow'})
        if row['is_rmat']:
            designations.append({'code': 'RMAT', 'label': 'RMAT', 'color': 'teal'})
        if row['is_first_in_class']:
            designations.append({'code': 'FIC', 'label': 'First-in-Class', 'color': 'gold'})
        if row['is_best_in_class']:
            designations.append({'code': 'BIC', 'label': 'Best-in-Class', 'color': 'gold'})
        if row['critical_unmet_need']:
            designations.append({'code': 'UMN', 'label': 'Unmet Medical Need', 'color': 'red'})

        # Get CONT score from position if we have one
        cont_score = None
        play_type = None
        if ticker in position_data:
            cont_score = position_data[ticker].get('cont_score')
            play_type = position_data[ticker].get('play_type')

        # Format date for display
        cat_display = cat_dt.strftime('%b %d, %Y')
        weekday = cat_dt.strftime('%A')

        catalyst = {
            'ticker': ticker,
            'date': catalyst_date,
            'date_display': cat_display,
            'weekday': weekday,
            'days_until': days_until,
            'is_public': is_public,

            'event': {
                'type': catalyst_type,
                'description': row['catalyst_event'],
                'drug_name': row['drug_name'],
                'indication': row['indication'],
            },

            'risk': binary_risk,
            'designations': designations,

            'company': {
                'mcap_millions': row['mcap_millions'],
                'short_interest_pct': row['short_interest_pct'],
            },

            # Members-only details
            'analysis': {
                'cont_score': cont_score,
                'play_type': play_type,
                'is_leap_play': bool(row['is_leap_play']),
                'estimated_pdufa': row['estimated_pdufa_date'],
                'data_completeness': row['data_completeness_pct'],
            },

            'meta': {
                'has_position': ticker in position_data,
                'research_available': bool(row['research_notes']),
            }
        }

        catalysts.append(catalyst)

    # Build summary stats
    this_week = [c for c in catalysts if c['days_until'] <= 7]
    next_week = [c for c in catalysts if 7 < c['days_until'] <= 14]
    this_month = [c for c in catalysts if c['days_until'] <= 30]

    pdufa_count = len([c for c in catalysts if c['event']['type'] == 'PDUFA'])
    phase3_count = len([c for c in catalysts if c['event']['type'] == 'Phase 3'])
    phase2_count = len([c for c in catalysts if c['event']['type'] == 'Phase 2'])
    phase1_count = len([c for c in catalysts if c['event']['type'] == 'Phase 1'])

    calendar_data = {
        'generated_at': datetime.now().isoformat(),
        'public_days': public_days,

        'summary': {
            'total_catalysts': len(catalysts),
            'this_week': len(this_week),
            'next_week': len(next_week),
            'this_month': len(this_month),
            'by_type': {
                'PDUFA': pdufa_count,
                'Phase 3': phase3_count,
                'Phase 2': phase2_count,
                'Phase 1': phase1_count,
                'AdCom': len([c for c in catalysts if c['event']['type'] == 'AdCom']),
                'Other': len([c for c in catalysts if c['event']['type'] == 'Other']),
            }
        },

        'catalysts': catalysts
    }

    return calendar_data


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate catalyst calendar')
    parser.add_argument('--days', type=int, default=7, help='Days to show publicly (default: 7)')
    parser.add_argument('--output', type=str, default=OUTPUT_PATH, help='Output file path')

    args = parser.parse_args()

    print(f"Generating catalyst calendar...")
    print(f"  Public window: {args.days} days")
    print(f"  Output: {args.output}")

    calendar = generate_calendar(public_days=args.days)

    if not calendar:
        print("Failed to generate calendar")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Write JSON
    with open(args.output, 'w') as f:
        json.dump(calendar, f, indent=2)

    print(f"\nCalendar generated successfully!")
    print(f"  Total catalysts: {calendar['summary']['total_catalysts']}")
    print(f"  This week (public): {calendar['summary']['this_week']}")
    print(f"  This month: {calendar['summary']['this_month']}")
    print(f"\nBy type:")
    for cat_type, count in calendar['summary']['by_type'].items():
        print(f"  {cat_type}: {count}")

    print(f"\nNext 5 catalysts:")
    for cat in calendar['catalysts'][:5]:
        status = "PUBLIC" if cat['is_public'] else "MEMBERS"
        print(f"  [{status}] {cat['ticker']} - {cat['date_display']} - {cat['event']['type']}")


if __name__ == '__main__':
    main()
