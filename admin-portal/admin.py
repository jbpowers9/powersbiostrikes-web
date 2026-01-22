"""
PowersBioStrikes Admin Portal - Home Page
Your private marketing hub for content generation and social media management.

Run with: streamlit run admin.py
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import os

# Import theme
from theme import apply_theme, sidebar_branding, metric_card, section_header, COLORS

# Apply theme
apply_theme()

# Sidebar branding
sidebar_branding()

# ===== Data Directory Setup =====
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')
ACCOUNTS_FILE = os.path.join(DATA_DIR, 'accounts.json')
MEMBERS_FILE = os.path.join(DATA_DIR, 'founding_members.json')


def load_json(filepath, default=None):
    """Load JSON data from file."""
    if default is None:
        default = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return default


def save_json(filepath, data):
    """Save JSON data to file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# ===== Load Data =====
posts = load_json(POSTS_FILE, [])
accounts = load_json(ACCOUNTS_FILE, [])
founding_members = load_json(MEMBERS_FILE, [])


# ===== Main Content =====
st.title("Admin Dashboard")

st.markdown(f"""
<p style="color: {COLORS['text_secondary']}; font-size: 1.1rem; margin-bottom: 30px;">
    Welcome back! Here's your marketing command center.
</p>
""", unsafe_allow_html=True)

# ===== Quick Stats =====
col1, col2, col3, col4 = st.columns(4)

# Calculate stats
posts_this_week = len([p for p in posts if datetime.fromisoformat(p.get('date', '2000-01-01')) > datetime.now() - timedelta(days=7)])
total_posts = len(posts)
active_accounts = len([a for a in accounts if a.get('active', True)])

with col1:
    metric_card("Posts This Week", str(posts_this_week))

with col2:
    metric_card("Total Posts", str(total_posts))

with col3:
    metric_card("Active Accounts", str(active_accounts))

with col4:
    active_founding = len([m for m in founding_members if m.get('status', 'active') == 'active'])
    metric_card("Founding Members", str(active_founding), f"of 100 spots")

st.markdown("<br>", unsafe_allow_html=True)

# ===== Quick Actions =====
section_header("Quick Actions", "Jump to common tasks")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="premium-card" style="text-align: center; padding: 25px;">
        <div style="font-size: 2rem; margin-bottom: 10px;">🐦</div>
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 5px;">
            Create Twitter Post
        </div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
            Generate trade alerts, educational content, or track record updates
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Twitter", key="twitter_btn", use_container_width=True):
        st.switch_page("pages/1_Twitter_Generator.py")

with col2:
    st.markdown(f"""
    <div class="premium-card" style="text-align: center; padding: 25px;">
        <div style="font-size: 2rem; margin-bottom: 10px;">📝</div>
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 5px;">
            Create Reddit Post
        </div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
            Longer-form thesis posts for r/options, r/biotechplays
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Reddit", key="reddit_btn", use_container_width=True):
        st.switch_page("pages/2_Reddit_Generator.py")

with col3:
    st.markdown(f"""
    <div class="premium-card" style="text-align: center; padding: 25px;">
        <div style="font-size: 2rem; margin-bottom: 10px;">📅</div>
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 5px;">
            View Schedule
        </div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
            Check your posting calendar and upcoming reminders
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Schedule", key="schedule_btn", use_container_width=True):
        st.switch_page("pages/4_Posting_Schedule.py")

with col4:
    spots_remaining = 100 - active_founding
    st.markdown(f"""
    <div class="premium-card" style="text-align: center; padding: 25px; border: 1px solid {COLORS['gold']}40;">
        <div style="font-size: 2rem; margin-bottom: 10px;">🏆</div>
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 5px;">
            Founding Members
        </div>
        <div style="color: {COLORS['gold']}; font-size: 0.85rem;">
            {spots_remaining} spots remaining
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Members", key="members_btn", use_container_width=True):
        st.switch_page("pages/5_Founding_Members.py")

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Recent Activity =====
section_header("Recent Activity", "Your latest posts and actions")

if posts:
    recent_posts = sorted(posts, key=lambda x: x.get('date', ''), reverse=True)[:5]

    for post in recent_posts:
        platform_emoji = "🐦" if post.get('platform') == 'twitter' else "📝"
        status_color = COLORS['positive'] if post.get('status') == 'posted' else COLORS['warning']

        st.markdown(f"""
        <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                    border-radius: 8px; padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.2rem; margin-right: 10px;">{platform_emoji}</span>
                    <span style="color: {COLORS['text_primary']};">
                        {post.get('title', 'Untitled Post')[:50]}...
                    </span>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
                        {post.get('date', 'Unknown date')}
                    </span>
                    <span style="background: {status_color}20; color: {status_color};
                                padding: 3px 10px; border-radius: 12px; font-size: 0.75rem;
                                text-transform: uppercase;">
                        {post.get('status', 'draft')}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                border-radius: 8px; padding: 30px; text-align: center;">
        <div style="color: {COLORS['text_muted']}; font-size: 1.1rem;">
            No posts yet. Create your first post to get started!
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Posting Reminders =====
section_header("Posting Reminders", "Stay consistent with your content")

# Calculate days since last post per platform
twitter_posts = [p for p in posts if p.get('platform') == 'twitter']
reddit_posts = [p for p in posts if p.get('platform') == 'reddit']

col1, col2 = st.columns(2)

with col1:
    if twitter_posts:
        last_twitter = max(twitter_posts, key=lambda x: x.get('date', ''))
        last_date = datetime.fromisoformat(last_twitter.get('date', '2000-01-01'))
        days_ago = (datetime.now() - last_date).days
        status = "good" if days_ago <= 2 else "warning" if days_ago <= 5 else "danger"
    else:
        days_ago = "Never"
        status = "danger"

    status_color = COLORS['positive'] if status == "good" else COLORS['warning'] if status == "warning" else COLORS['negative']

    st.markdown(f"""
    <div class="premium-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; text-transform: uppercase;
                            letter-spacing: 1px;">Twitter</div>
                <div style="color: {COLORS['text_primary']}; font-size: 1.1rem; margin-top: 5px;">
                    Last post: <strong>{days_ago}</strong> {"days ago" if isinstance(days_ago, int) else ""}
                </div>
            </div>
            <div style="width: 12px; height: 12px; background: {status_color}; border-radius: 50%;
                        box-shadow: 0 0 10px {status_color};"></div>
        </div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.85rem; margin-top: 10px;">
            {"Great job staying active!" if status == "good" else "Consider posting soon!" if status == "warning" else "Time to post!"}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if reddit_posts:
        last_reddit = max(reddit_posts, key=lambda x: x.get('date', ''))
        last_date = datetime.fromisoformat(last_reddit.get('date', '2000-01-01'))
        days_ago = (datetime.now() - last_date).days
        status = "good" if days_ago <= 7 else "warning" if days_ago <= 14 else "danger"
    else:
        days_ago = "Never"
        status = "danger"

    status_color = COLORS['positive'] if status == "good" else COLORS['warning'] if status == "warning" else COLORS['negative']

    st.markdown(f"""
    <div class="premium-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; text-transform: uppercase;
                            letter-spacing: 1px;">Reddit</div>
                <div style="color: {COLORS['text_primary']}; font-size: 1.1rem; margin-top: 5px;">
                    Last post: <strong>{days_ago}</strong> {"days ago" if isinstance(days_ago, int) else ""}
                </div>
            </div>
            <div style="width: 12px; height: 12px; background: {status_color}; border-radius: 50%;
                        box-shadow: 0 0 10px {status_color};"></div>
        </div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.85rem; margin-top: 10px;">
            {"Great job staying active!" if status == "good" else "Consider posting soon!" if status == "warning" else "Time to post!"}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== Footer =====
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align: center; color: {COLORS['text_muted']}; font-size: 0.8rem; padding: 20px 0;
            border-top: 1px solid {COLORS['steel_dark']};">
    PowersBioStrikes Admin Portal | Built for systematic content creation
</div>
""", unsafe_allow_html=True)
