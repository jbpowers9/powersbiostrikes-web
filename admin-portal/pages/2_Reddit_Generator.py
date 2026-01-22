"""
PowersBioStrikes Admin Portal - Reddit Post Generator
Create longer-form thesis posts for r/options, r/wallstreetbets, r/biotechplays, etc.
"""

import streamlit as st
from datetime import datetime
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import sidebar_branding, section_header, COLORS

# Page config
try:
    st.set_page_config(page_title="Reddit Generator | PBS Admin", page_icon="📝", layout="wide")
except:
    pass

sidebar_branding()

# ===== Constants =====
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')

# Subreddit options
SUBREDDITS = {
    "r/options": {
        "name": "r/options",
        "description": "Options trading strategies and education",
        "rules": "Educational focus, no pump-and-dump, include position details",
        "best_for": "Strategy posts, educational content"
    },
    "r/biotechplays": {
        "name": "r/biotechplays",
        "description": "Biotech-focused trading discussion",
        "rules": "Include DD, catalyst dates, be transparent about positions",
        "best_for": "Biotech thesis, catalyst plays"
    },
    "r/wallstreetbets": {
        "name": "r/wallstreetbets",
        "description": "High-risk trading, memes, YOLO plays",
        "rules": "Min position size requirements, entertaining format",
        "best_for": "Big wins/losses, bold plays"
    },
    "r/stocks": {
        "name": "r/stocks",
        "description": "General stock discussion",
        "rules": "Substantive content, no low-effort posts",
        "best_for": "Company analysis, sector discussion"
    }
}

# ===== Helper Functions =====
def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_post(post_data):
    posts = load_posts()
    posts.append(post_data)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=2, default=str)

# ===== Post Templates =====
TEMPLATES = {
    "dd_thesis": {
        "name": "DD / Thesis Post",
        "icon": "🔬",
        "description": "In-depth analysis of a biotech opportunity",
        "template": """# {TICKER}: {TITLE}

## TL;DR
{TLDR}

---

## The Setup

**Company:** {COMPANY_NAME}
**Market Cap:** {MARKET_CAP}
**Current Price:** {CURRENT_PRICE}

---

## The Catalyst

**Event:** {CATALYST_TYPE}
**Expected Date:** {CATALYST_DATE}

{CATALYST_DETAILS}

---

## The Trade

**Position:** {POSITION_DETAILS}
**Risk/Reward:** {RISK_REWARD}

---

## Bull Case
{BULL_CASE}

## Bear Case
{BEAR_CASE}

---

## My Position
{MY_POSITION}

---

*Disclaimer: This is not financial advice. I am sharing my research and current positions for educational purposes. Do your own due diligence.*
""",
        "fields": ["TICKER", "TITLE", "TLDR", "COMPANY_NAME", "MARKET_CAP", "CURRENT_PRICE",
                   "CATALYST_TYPE", "CATALYST_DATE", "CATALYST_DETAILS", "POSITION_DETAILS",
                   "RISK_REWARD", "BULL_CASE", "BEAR_CASE", "MY_POSITION"]
    },
    "trade_recap": {
        "name": "Trade Recap",
        "icon": "📊",
        "description": "Share results of a closed trade",
        "template": """# {RESULT_EMOJI} {TICKER} Trade Recap: {RETURN_PCT}% {RESULT_TYPE}

## Summary
{SUMMARY}

---

## The Trade

| | |
|---|---|
| **Ticker** | {TICKER} |
| **Entry** | {ENTRY_DETAILS} |
| **Exit** | {EXIT_DETAILS} |
| **Return** | {RETURN_PCT}% |

---

## What Went {RESULT_WORD}

{WHAT_HAPPENED}

---

## Lessons Learned

{LESSONS}

---

## Track Record Update

This brings my YTD record to: {YTD_RECORD}

Full transparency - I post wins AND losses.

---

*Not financial advice. Past performance doesn't guarantee future results.*
""",
        "fields": ["TICKER", "RESULT_TYPE", "RETURN_PCT", "SUMMARY", "ENTRY_DETAILS",
                   "EXIT_DETAILS", "WHAT_HAPPENED", "LESSONS", "YTD_RECORD"]
    },
    "educational": {
        "name": "Educational Post",
        "icon": "📚",
        "description": "Teach a concept or methodology",
        "template": """# {TITLE}

## Introduction

{INTRO}

---

## The Concept

{MAIN_CONTENT}

---

## Example

{EXAMPLE}

---

## Key Takeaways

{TAKEAWAYS}

---

## Conclusion

{CONCLUSION}

---

*Questions? Drop them in the comments. Happy to discuss.*
""",
        "fields": ["TITLE", "INTRO", "MAIN_CONTENT", "EXAMPLE", "TAKEAWAYS", "CONCLUSION"]
    },
    "catalyst_watch": {
        "name": "Catalyst Watch",
        "icon": "📅",
        "description": "Alert about upcoming FDA catalysts",
        "template": """# Biotech Catalyst Watch: {DATE_RANGE}

Here are some notable FDA catalysts coming up:

---

## {TICKER_1}: {EVENT_1}

**Date:** {DATE_1}
**Notes:** {NOTES_1}

---

## {TICKER_2}: {EVENT_2}

**Date:** {DATE_2}
**Notes:** {NOTES_2}

---

## {TICKER_3}: {EVENT_3}

**Date:** {DATE_3}
**Notes:** {NOTES_3}

---

*These are just calendar events I'm watching. Not recommendations. Always do your own DD.*
""",
        "fields": ["DATE_RANGE", "TICKER_1", "EVENT_1", "DATE_1", "NOTES_1",
                   "TICKER_2", "EVENT_2", "DATE_2", "NOTES_2",
                   "TICKER_3", "EVENT_3", "DATE_3", "NOTES_3"]
    },
    "custom": {
        "name": "Custom Post",
        "icon": "✏️",
        "description": "Write from scratch",
        "template": "",
        "fields": []
    }
}


# ===== Main Content =====
st.title("📝 Reddit Post Generator")

st.markdown(f"""
<p style="color: {COLORS['text_secondary']}; margin-bottom: 30px;">
    Create longer-form content for Reddit's trading communities.
</p>
""", unsafe_allow_html=True)

# ===== Subreddit Selection =====
section_header("Target Subreddit")

selected_sub = st.selectbox(
    "Choose subreddit",
    options=list(SUBREDDITS.keys()),
    format_func=lambda x: f"{x} - {SUBREDDITS[x]['description']}"
)

sub_info = SUBREDDITS[selected_sub]
st.markdown(f"""
<div style="background: {COLORS['mahogany_dark']}; padding: 15px 20px; border-radius: 8px;
            margin: 10px 0 30px 0; border-left: 3px solid {COLORS['gold']};">
    <div style="color: {COLORS['gold']}; font-weight: 600; margin-bottom: 5px;">
        {sub_info['name']} Guidelines
    </div>
    <div style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
        <strong>Rules:</strong> {sub_info['rules']}<br>
        <strong>Best for:</strong> {sub_info['best_for']}
    </div>
</div>
""", unsafe_allow_html=True)

# ===== Template Selection =====
section_header("Choose Template")

cols = st.columns(5)
template_keys = list(TEMPLATES.keys())

for i, key in enumerate(template_keys):
    template = TEMPLATES[key]
    with cols[i % 5]:
        if st.button(
            f"{template['icon']}\n{template['name']}",
            key=f"template_{key}",
            use_container_width=True
        ):
            st.session_state['reddit_template'] = key

# Get selected template
selected_template_key = st.session_state.get('reddit_template', 'custom')
selected_template = TEMPLATES[selected_template_key]

st.markdown(f"""
<div style="color: {COLORS['text_muted']}; margin: 15px 0 30px 0;">
    Selected: <span style="color: {COLORS['gold']};">{selected_template['icon']} {selected_template['name']}</span>
    - {selected_template['description']}
</div>
""", unsafe_allow_html=True)

# ===== Post Editor =====
section_header("Compose Post")

# Title input
post_title = st.text_input("Post Title", placeholder="Your attention-grabbing title here...")

st.markdown("<br>", unsafe_allow_html=True)

# Template fields or custom editor
if selected_template['fields']:
    st.markdown("**Fill in the template fields:**")

    field_values = {}
    cols = st.columns(2)

    for i, field in enumerate(selected_template['fields']):
        field_label = field.replace('_', ' ').title()
        col = cols[i % 2]

        with col:
            # Determine input type based on field name
            if field in ["TLDR", "SUMMARY", "INTRO", "CONCLUSION", "BULL_CASE", "BEAR_CASE",
                        "MAIN_CONTENT", "CATALYST_DETAILS", "WHAT_HAPPENED", "LESSONS",
                        "TAKEAWAYS", "EXAMPLE", "MY_POSITION"]:
                field_values[field] = st.text_area(field_label, key=f"reddit_field_{field}", height=120)
            elif field == "RESULT_TYPE":
                field_values[field] = st.selectbox(field_label, ["WIN", "LOSS"], key=f"reddit_field_{field}")
            elif field == "RESULT_EMOJI":
                # Auto-set
                pass
            elif field == "RESULT_WORD":
                # Auto-set
                pass
            else:
                field_values[field] = st.text_input(field_label, key=f"reddit_field_{field}")

    # Generate post content
    post_content = selected_template['template']
    for field, value in field_values.items():
        post_content = post_content.replace("{" + field + "}", value or f"[{field}]")

    # Handle auto-set fields
    if "RESULT_TYPE" in field_values:
        result_type = field_values["RESULT_TYPE"]
        post_content = post_content.replace("{RESULT_EMOJI}", "✅" if result_type == "WIN" else "❌")
        post_content = post_content.replace("{RESULT_WORD}", "Right" if result_type == "WIN" else "Wrong")

    st.markdown("<br>**Preview & Edit:**", unsafe_allow_html=True)
    post_content = st.text_area(
        "Post Content",
        value=post_content,
        height=400,
        key="reddit_post_content",
        label_visibility="collapsed"
    )
else:
    post_content = st.text_area(
        "Post Content",
        height=400,
        key="reddit_post_content_custom",
        placeholder="Write your post content here using Markdown formatting..."
    )

# Word count
word_count = len(post_content.split()) if post_content else 0
st.markdown(f"""
<div style="color: {COLORS['text_muted']}; font-size: 0.9rem; margin-top: 10px;">
    Word count: {word_count} | Estimated read time: {max(1, word_count // 200)} min
</div>
""", unsafe_allow_html=True)

# ===== Action Buttons =====
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📋 Copy Title + Content", use_container_width=True):
        st.toast("Ready to copy!", icon="📋")

with col2:
    if st.button("👁️ Preview Markdown", use_container_width=True):
        st.session_state['show_preview'] = not st.session_state.get('show_preview', False)

with col3:
    if st.button("💾 Save Draft", use_container_width=True):
        if post_title and post_content:
            post_data = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "platform": "reddit",
                "subreddit": selected_sub,
                "title": post_title,
                "content": post_content,
                "template": selected_template_key,
                "status": "draft",
                "date": datetime.now().isoformat()
            }
            save_post(post_data)
            st.success("Draft saved!")
        else:
            st.warning("Please add a title and content!")

with col4:
    if st.button("✅ Mark as Posted", use_container_width=True, type="primary"):
        if post_title and post_content:
            post_data = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "platform": "reddit",
                "subreddit": selected_sub,
                "title": post_title,
                "content": post_content,
                "template": selected_template_key,
                "status": "posted",
                "date": datetime.now().isoformat()
            }
            save_post(post_data)
            st.success("Marked as posted!")
            st.balloons()
        else:
            st.warning("Please add a title and content!")

# ===== Markdown Preview =====
if st.session_state.get('show_preview', False):
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Markdown Preview")

    with st.container():
        st.markdown(f"""
        <div style="background: white; color: black; padding: 30px; border-radius: 8px;
                    max-width: 800px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <h1 style="color: black; border-bottom: none;">{post_title or 'Untitled Post'}</h1>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(post_content)

# ===== Tips Section =====
st.markdown("<br><br>", unsafe_allow_html=True)

with st.expander("📝 Reddit Best Practices"):
    st.markdown(f"""
    ### Formatting Tips
    - Use **headers** (##) to break up long posts
    - Include a **TL;DR** at the top for skimmers
    - Use **tables** for position details
    - Add **horizontal rules** (---) between sections

    ### Content Tips
    - Be substantive - Reddit rewards quality DD
    - Include both bull and bear cases
    - Be transparent about your position
    - Cite sources where possible

    ### Engagement
    - Respond to comments within the first hour
    - Be open to criticism - it builds credibility
    - Cross-post to relevant subreddits (with different titles)
    - Time your posts: 8-10 AM EST weekdays is optimal

    ### Subreddit-Specific
    - **r/options**: Focus on the strategy, explain your reasoning
    - **r/biotechplays**: Include catalyst dates and clinical details
    - **r/wallstreetbets**: Be entertaining, include position screenshots
    - **r/stocks**: More conservative tone, fundamental focus
    """)

# ===== Recent Reddit Posts =====
st.markdown("<br>", unsafe_allow_html=True)
section_header("Recent Reddit Posts")

posts = load_posts()
reddit_posts = [p for p in posts if p.get('platform') == 'reddit']
recent_reddit = sorted(reddit_posts, key=lambda x: x.get('date', ''), reverse=True)[:5]

if recent_reddit:
    for post in recent_reddit:
        status_color = COLORS['positive'] if post.get('status') == 'posted' else COLORS['warning']
        st.markdown(f"""
        <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                    border-radius: 8px; padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="color: {COLORS['gold']}; font-size: 0.8rem; margin-bottom: 5px;">
                        {post.get('subreddit', 'r/unknown')}
                    </div>
                    <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 5px;">
                        {post.get('title', 'Untitled')[:60]}...
                    </div>
                    <div style="color: {COLORS['text_muted']}; font-size: 0.8rem;">
                        {post.get('date', '')[:10]}
                    </div>
                </div>
                <span style="background: {status_color}20; color: {status_color};
                            padding: 3px 10px; border-radius: 12px; font-size: 0.75rem;
                            text-transform: uppercase; margin-left: 15px;">
                    {post.get('status', 'draft')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No Reddit posts yet. Create your first one above!")
