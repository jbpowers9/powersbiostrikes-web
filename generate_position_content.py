#!/usr/bin/env python3
"""
Position Content Generator
===========================
Generates website announcements and Twitter/X posts for new positions.

Usage:
    python generate_position_content.py CRMD
    python generate_position_content.py CRMD --type leap
    python generate_position_content.py CRMD --output json

Output:
    - Website announcement HTML
    - Twitter/X post text
    - Prompt for Claude to enhance content
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

# Add biotech-options-v2 to path for imports
BIOTECH_DIR = os.environ.get('BIOTECH_OPTIONS_DIR', '/mnt/c/biotech-options-v2')
if os.path.exists(BIOTECH_DIR):
    sys.path.insert(0, BIOTECH_DIR)

DB_PATH = os.path.join(BIOTECH_DIR, 'biotech_options.db')


# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_position_data(ticker: str) -> Optional[Dict]:
    """Get position data from database."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get position
    cursor.execute("""
        SELECT * FROM positions
        WHERE ticker = ? AND status = 'OPEN'
        ORDER BY entry_date DESC LIMIT 1
    """, (ticker,))
    position = cursor.fetchone()

    if not position:
        conn.close()
        return None

    position_dict = dict(position)

    # Get research data
    cursor.execute("""
        SELECT * FROM catalyst_research
        WHERE ticker = ?
        ORDER BY updated_at DESC LIMIT 1
    """, (ticker,))
    research = cursor.fetchone()

    if research:
        research_dict = dict(research)
        # Parse trade analysis JSON
        if research_dict.get('trade_analysis_json'):
            try:
                research_dict['trade_analysis'] = json.loads(research_dict['trade_analysis_json'])
            except:
                research_dict['trade_analysis'] = {}
        position_dict['research'] = research_dict

    conn.close()
    return position_dict


def get_play_type(position: Dict) -> str:
    """Determine if this is a LEAP or Standard play."""
    expiration = position.get('expiration', '')
    if not expiration:
        return 'Standard'

    try:
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        days_out = (exp_date - datetime.now()).days
        return 'LEAP' if days_out >= 180 else 'Standard'
    except:
        return 'Standard'


# =============================================================================
# CONTENT GENERATORS
# =============================================================================

def generate_twitter_post(position: Dict, short: bool = True) -> str:
    """Generate a Twitter/X post for a new position."""
    ticker = position['ticker']
    strike = position.get('strike', 0)
    expiration = position.get('expiration', '')
    entry_price = position.get('entry_price') or position.get('avg_cost', 0)
    cont_score = position.get('cont_score', 0)
    play_type = get_play_type(position)

    research = position.get('research', {})
    drug_name = research.get('drug_name', '')
    indication = research.get('indication', '')
    catalyst_event = position.get('catalyst_event', '')
    catalyst_date = position.get('catalyst_date', '')

    # Format expiration for display
    try:
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        exp_display = exp_date.strftime('%b\'%y')
    except:
        exp_display = expiration

    # Format catalyst date
    try:
        cat_date = datetime.strptime(catalyst_date, '%Y-%m-%d')
        cat_display = cat_date.strftime('%b\'%y')
    except:
        cat_display = catalyst_date

    # Get key factors
    factors = []
    if research.get('is_orphan'):
        factors.append("Orphan")
    if research.get('is_fast_track'):
        factors.append("FastTrack")
    if research.get('is_breakthrough'):
        factors.append("BTD")
    if research.get('is_first_in_class'):
        factors.append("FiC")
    if research.get('critical_unmet_need'):
        factors.append("UnmetNeed")

    if short:
        # Compact version for Twitter (< 280 chars)
        lines = []

        # Header
        emoji = "LEAP" if play_type == 'LEAP' else "New"
        lines.append(f"{emoji}: ${ticker} ${strike:.0f}c {exp_display}")

        # Entry and CONT
        cont_label = "HIGH" if cont_score >= 80 else "GOOD" if cont_score >= 60 else ""
        lines.append(f"Entry ${entry_price:.2f} | CONT {cont_score} {cont_label}".strip())

        # Catalyst
        cat_short = catalyst_event.replace('Phase 3 ', 'Ph3 ').replace('Data readout', 'data')
        lines.append(f"{cat_short} {cat_display}")

        # One-liner thesis or drug
        if drug_name:
            drug_short = drug_name.split('(')[0].strip()[:20]
            lines.append(drug_short)

        # Factors (limit to 3)
        if factors:
            lines.append(" ".join(factors[:3]))

        lines.append("")
        lines.append("powersbiostrikes.com")
        lines.append("#biotech #options")

        return "\n".join(lines)
    else:
        # Full version
        lines = []

        # Main position line
        if play_type == 'LEAP':
            lines.append(f"New LEAP Position: ${ticker}")
        else:
            lines.append(f"New Position: ${ticker}")

        lines.append("")

        # Option details
        lines.append(f"${strike} Calls | {exp_display}")
        lines.append(f"Entry: ${entry_price:.2f}")

        # CONT score
        if cont_score >= 80:
            lines.append(f"CONT: {cont_score} (HIGH)")
        elif cont_score >= 60:
            lines.append(f"CONT: {cont_score} (GOOD)")
        else:
            lines.append(f"CONT: {cont_score}")

        lines.append("")

        # Catalyst
        if catalyst_event:
            lines.append(f"Catalyst: {catalyst_event}")
        lines.append(f"Date: {cat_display}")

        lines.append("")

        # Drug info
        if drug_name:
            lines.append(f"Drug: {drug_name}")
        if indication:
            lines.append(f"Indication: {indication[:50]}{'...' if len(indication) > 50 else ''}")

        lines.append("")

        if factors:
            lines.append(" | ".join(factors))

        lines.append("")
        lines.append("Full analysis: powersbiostrikes.com")
        lines.append("")
        lines.append("#biotech #options #trading")

        return "\n".join(lines)


def generate_website_announcement(position: Dict) -> str:
    """Generate a website announcement section for a new position."""
    ticker = position['ticker']
    strike = position.get('strike', 0)
    expiration = position.get('expiration', '')
    entry_price = position.get('entry_price') or position.get('avg_cost', 0)
    cont_score = position.get('cont_score', 0)
    play_type = get_play_type(position)

    research = position.get('research', {})
    drug_name = research.get('drug_name', '')
    indication = research.get('indication', '')
    catalyst_event = position.get('catalyst_event', '')
    catalyst_date = position.get('catalyst_date', '')

    # Get thesis from trade analysis
    trade_analysis = research.get('trade_analysis', {})
    leap_analysis = trade_analysis.get('leap', {})
    standard_analysis = trade_analysis.get('standard', {})

    # Use the appropriate analysis
    analysis = leap_analysis if play_type == 'LEAP' and leap_analysis else standard_analysis

    thesis_summary = analysis.get('executive_summary', '') or analysis.get('one_line_summary', '')
    key_risks = analysis.get('key_risks', [])

    # Format dates
    try:
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        exp_display = exp_date.strftime('%B %d, %Y')
    except:
        exp_display = expiration

    try:
        cat_date = datetime.strptime(catalyst_date, '%Y-%m-%d')
        cat_display = cat_date.strftime('%B %Y')
    except:
        cat_display = catalyst_date

    # CONT badge
    if cont_score >= 80:
        cont_badge = f'<span class="cont-high">CONT {cont_score} - HIGH</span>'
        cont_color = '#00C853'
    elif cont_score >= 60:
        cont_badge = f'<span class="cont-good">CONT {cont_score} - GOOD</span>'
        cont_color = '#8BC34A'
    else:
        cont_badge = f'<span class="cont-moderate">CONT {cont_score}</span>'
        cont_color = '#FFB300'

    # Designation badges
    designation_badges = []
    if research.get('is_orphan'):
        designation_badges.append('<span class="badge badge-orphan">Orphan</span>')
    if research.get('is_fast_track'):
        designation_badges.append('<span class="badge badge-fasttrack">Fast Track</span>')
    if research.get('is_breakthrough'):
        designation_badges.append('<span class="badge badge-btd">BTD</span>')
    if research.get('is_first_in_class'):
        designation_badges.append('<span class="badge badge-fic">First-in-Class</span>')
    if research.get('critical_unmet_need'):
        designation_badges.append('<span class="badge badge-unmet">Unmet Need</span>')

    badges_html = ' '.join(designation_badges)

    # Play type badge
    play_badge = '<span class="badge badge-leap">LEAP</span>' if play_type == 'LEAP' else '<span class="badge badge-standard">Standard</span>'

    # Build HTML
    html = f"""
<!-- New Position: {ticker} - {datetime.now().strftime('%Y-%m-%d')} -->
<div class="position-announcement" id="position-{ticker.lower()}">
    <div class="announcement-header">
        <div class="position-title">
            <h3>{ticker}</h3>
            {play_badge}
            <span class="cont-badge" style="background: {cont_color};">CONT {cont_score}</span>
        </div>
        <div class="position-date">{datetime.now().strftime('%b %d, %Y')}</div>
    </div>

    <div class="position-details">
        <div class="detail-row">
            <span class="label">Option:</span>
            <span class="value">${strike:.0f} Calls</span>
        </div>
        <div class="detail-row">
            <span class="label">Expiration:</span>
            <span class="value">{exp_display}</span>
        </div>
        <div class="detail-row">
            <span class="label">Entry:</span>
            <span class="value">${entry_price:.2f}</span>
        </div>
    </div>

    <div class="catalyst-info">
        <div class="catalyst-type">{catalyst_event}</div>
        <div class="catalyst-date">{cat_display}</div>
        {f'<div class="drug-name">{drug_name}</div>' if drug_name else ''}
        {f'<div class="indication">{indication}</div>' if indication else ''}
    </div>

    <div class="designations">
        {badges_html}
    </div>

    {f'''<div class="thesis-summary">
        <h4>Investment Thesis</h4>
        <p>{thesis_summary[:500]}{"..." if len(thesis_summary) > 500 else ""}</p>
    </div>''' if thesis_summary else ''}

    {f'''<div class="key-risks">
        <h4>Key Risks</h4>
        <ul>
            {"".join(f"<li>{risk}</li>" for risk in key_risks[:3])}
        </ul>
    </div>''' if key_risks else ''}
</div>
"""
    return html


def generate_claude_prompt(position: Dict) -> str:
    """Generate a prompt for Claude to create enhanced content."""
    ticker = position['ticker']
    strike = position.get('strike', 0)
    expiration = position.get('expiration', '')
    entry_price = position.get('entry_price') or position.get('avg_cost', 0)
    cont_score = position.get('cont_score', 0)
    play_type = get_play_type(position)

    research = position.get('research', {})
    drug_name = research.get('drug_name', '')
    indication = research.get('indication', '')
    catalyst_event = position.get('catalyst_event', '')
    catalyst_date = position.get('catalyst_date', '')
    research_notes = research.get('research_notes', '')

    trade_analysis = research.get('trade_analysis', {})
    leap_analysis = trade_analysis.get('leap', {})
    standard_analysis = trade_analysis.get('standard', {})
    analysis = leap_analysis if play_type == 'LEAP' and leap_analysis else standard_analysis

    prompt = f"""Please help me create content for a new biotech options position announcement.

## Position Details
- **Ticker:** {ticker}
- **Play Type:** {play_type}
- **Strike:** ${strike}
- **Expiration:** {expiration}
- **Entry Price:** ${entry_price:.2f}
- **CONT Score:** {cont_score}

## Catalyst Information
- **Event:** {catalyst_event}
- **Date:** {catalyst_date}
- **Drug:** {drug_name}
- **Indication:** {indication}

## Research Background
{research_notes}

## Existing Analysis
{json.dumps(analysis, indent=2, default=str) if analysis else 'None available'}

## Request
Please generate:

1. **Twitter Post (280 chars max):** A punchy announcement highlighting:
   - The ticker and play type
   - Key catalyst
   - One compelling factor (CONT score, designation, or thesis highlight)
   - Include relevant hashtags

2. **Blog Post Intro (2-3 paragraphs):** An engaging introduction for our website that:
   - Introduces the position and rationale
   - Highlights the key catalyst and timeline
   - Mentions why we chose {play_type} structure
   - Notes the CONT score and what it means

3. **Key Bullet Points (3-5):** The most important factors for subscribers to understand.

Format your response with clear headers for each section.
"""
    return prompt


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Generate position content for website and Twitter')
    parser.add_argument('ticker', type=str, help='Stock ticker')
    parser.add_argument('--type', choices=['all', 'twitter', 'website', 'prompt'], default='all',
                        help='Type of content to generate')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                        help='Output format')

    args = parser.parse_args()
    ticker = args.ticker.upper()

    # Get position data
    position = get_position_data(ticker)

    if not position:
        print(f"No open position found for {ticker}")
        sys.exit(1)

    play_type = get_play_type(position)

    # Generate content
    results = {}

    if args.type in ['all', 'twitter']:
        results['twitter_short'] = generate_twitter_post(position, short=True)
        results['twitter_full'] = generate_twitter_post(position, short=False)

    if args.type in ['all', 'website']:
        results['website'] = generate_website_announcement(position)

    if args.type in ['all', 'prompt']:
        results['claude_prompt'] = generate_claude_prompt(position)

    # Output
    if args.output == 'json':
        print(json.dumps({
            'ticker': ticker,
            'play_type': play_type,
            'content': results
        }, indent=2))
    else:
        print("=" * 70)
        print(f"POSITION CONTENT: {ticker} ({play_type})")
        print("=" * 70)

        if 'twitter_short' in results:
            print("\n" + "-" * 40)
            print("TWITTER POST (Short - < 280 chars):")
            print("-" * 40)
            print(results['twitter_short'])
            print(f"\n[{len(results['twitter_short'])} characters]")

        if 'twitter_full' in results:
            print("\n" + "-" * 40)
            print("TWITTER POST (Full version):")
            print("-" * 40)
            print(results['twitter_full'])
            print(f"\n[{len(results['twitter_full'])} characters]")

        if 'website' in results:
            print("\n" + "-" * 40)
            print("WEBSITE ANNOUNCEMENT:")
            print("-" * 40)
            print(results['website'])

        if 'claude_prompt' in results:
            print("\n" + "-" * 40)
            print("CLAUDE ENHANCEMENT PROMPT:")
            print("-" * 40)
            print(results['claude_prompt'])


if __name__ == '__main__':
    main()
