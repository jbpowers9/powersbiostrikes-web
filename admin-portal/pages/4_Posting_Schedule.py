"""
PowersBioStrikes Admin Portal - Posting Schedule
Content calendar, posting reminders, and activity tracking.
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import os
import sys
import calendar

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import sidebar_branding, section_header, metric_card, COLORS

# Page config
try:
    st.set_page_config(page_title="Posting Schedule | PBS Admin", page_icon="📅", layout="wide")
except:
    pass

sidebar_branding()

# ===== Constants =====
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')
SCHEDULE_FILE = os.path.join(DATA_DIR, 'schedule.json')

# Recommended posting frequency
POSTING_GUIDELINES = {
    "twitter": {
        "name": "X",
        "icon": "𝕏",
        "recommended_per_week": 7,  # Daily
        "min_per_week": 3,
        "best_times": ["8:00 AM", "12:00 PM", "5:00 PM"],
        "best_days": ["Tuesday", "Wednesday", "Thursday"]
    },
    "reddit": {
        "name": "Reddit",
        "icon": "📝",
        "recommended_per_week": 2,
        "min_per_week": 1,
        "best_times": ["9:00 AM", "1:00 PM"],
        "best_days": ["Monday", "Wednesday"]
    }
}

# ===== Helper Functions =====
def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r') as f:
            return json.load(f)
    return []

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    return {"reminders": [], "content_ideas": []}

def save_schedule(schedule):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f, indent=2, default=str)

def get_posts_by_date(posts, date):
    """Get posts for a specific date."""
    date_str = date.strftime("%Y-%m-%d")
    return [p for p in posts if p.get('date', '')[:10] == date_str]

def get_posts_this_week(posts):
    """Get posts from the current week."""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    return [p for p in posts
            if p.get('date') and datetime.fromisoformat(p['date'][:19]) >= week_start]

def calculate_streak(posts, platform=None):
    """Calculate current posting streak in days."""
    if platform:
        posts = [p for p in posts if p.get('platform') == platform]

    if not posts:
        return 0

    # Sort by date descending
    sorted_posts = sorted(posts, key=lambda x: x.get('date', ''), reverse=True)

    streak = 0
    current_date = datetime.now().date()

    for post in sorted_posts:
        post_date = datetime.fromisoformat(post['date'][:10]).date()
        if post_date == current_date or post_date == current_date - timedelta(days=1):
            streak += 1
            current_date = post_date - timedelta(days=1)
        elif post_date < current_date - timedelta(days=1):
            break

    return streak


# ===== Load Data =====
posts = load_posts()
schedule = load_schedule()


# ===== Main Content =====
st.title("📅 Posting Schedule")

st.markdown(f"""
<p style="color: {COLORS['text_secondary']}; margin-bottom: 30px;">
    Track your posting consistency and plan your content calendar.
</p>
""", unsafe_allow_html=True)

# ===== Weekly Overview =====
section_header("This Week's Activity")

posts_this_week = get_posts_this_week(posts)
twitter_this_week = len([p for p in posts_this_week if p.get('platform') == 'twitter' and p.get('status') == 'posted'])
reddit_this_week = len([p for p in posts_this_week if p.get('platform') == 'reddit' and p.get('status') == 'posted'])

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_color = "positive" if twitter_this_week >= POSTING_GUIDELINES['twitter']['min_per_week'] else "negative"
    metric_card(
        "X Posts",
        str(twitter_this_week),
        f"Goal: {POSTING_GUIDELINES['twitter']['recommended_per_week']}/week",
        delta_color
    )

with col2:
    delta_color = "positive" if reddit_this_week >= POSTING_GUIDELINES['reddit']['min_per_week'] else "negative"
    metric_card(
        "Reddit Posts",
        str(reddit_this_week),
        f"Goal: {POSTING_GUIDELINES['reddit']['recommended_per_week']}/week",
        delta_color
    )

with col3:
    streak = calculate_streak([p for p in posts if p.get('status') == 'posted'])
    metric_card("Current Streak", f"{streak} days")

with col4:
    total_posts = len([p for p in posts if p.get('status') == 'posted'])
    metric_card("All-Time Posts", str(total_posts))

st.markdown("<br>", unsafe_allow_html=True)

# ===== Calendar View =====
section_header("Content Calendar")

# Get current month
today = datetime.now()
current_year = today.year
current_month = today.month

col1, col2 = st.columns([3, 1])

with col2:
    view_month = st.selectbox(
        "Month",
        options=list(range(1, 13)),
        index=current_month - 1,
        format_func=lambda x: calendar.month_name[x]
    )
    view_year = st.selectbox(
        "Year",
        options=[current_year - 1, current_year, current_year + 1],
        index=1
    )

with col1:
    # Generate calendar
    cal = calendar.monthcalendar(view_year, view_month)

    # Calendar header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h3 style="color: {COLORS['gold']}; margin: 0;">
            {calendar.month_name[view_month]} {view_year}
        </h3>
    </div>
    """, unsafe_allow_html=True)

    # Day headers
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, day in enumerate(days):
        with header_cols[i]:
            st.markdown(f"""
            <div style="text-align: center; color: {COLORS['text_muted']};
                        font-weight: 600; padding: 10px 0;">
                {day}
            </div>
            """, unsafe_allow_html=True)

    # Calendar weeks
    for week in cal:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            with week_cols[i]:
                if day == 0:
                    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                else:
                    date = datetime(view_year, view_month, day)
                    day_posts = get_posts_by_date(posts, date)
                    posted_count = len([p for p in day_posts if p.get('status') == 'posted'])

                    is_today = date.date() == today.date()
                    is_future = date.date() > today.date()

                    bg_color = COLORS['mahogany_dark'] if is_today else COLORS['bg_card']
                    border_color = COLORS['gold'] if is_today else COLORS['steel']

                    # Activity indicator
                    activity = ""
                    if posted_count > 0:
                        activity = f"""
                        <div style="display: flex; justify-content: center; gap: 3px; margin-top: 5px;">
                            {''.join(['<span style="color: ' + COLORS['positive'] + ';">●</span>' for _ in range(min(posted_count, 3))])}
                            {f'<span style="color: {COLORS["positive"]};">+{posted_count - 3}</span>' if posted_count > 3 else ''}
                        </div>
                        """

                    st.markdown(f"""
                    <div style="background: {bg_color}; border: 1px solid {border_color};
                                border-radius: 8px; padding: 10px; height: 80px;
                                text-align: center; opacity: {'0.5' if is_future else '1'};">
                        <div style="color: {COLORS['text_primary']}; font-weight: {'700' if is_today else '400'};">
                            {day}
                        </div>
                        {activity}
                    </div>
                    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Posting Recommendations =====
section_header("Posting Recommendations")

col1, col2 = st.columns(2)

for i, (platform_key, guidelines) in enumerate(POSTING_GUIDELINES.items()):
    col = col1 if i == 0 else col2

    with col:
        platform_posts = [p for p in posts_this_week if p.get('platform') == platform_key and p.get('status') == 'posted']
        current_count = len(platform_posts)
        goal = guidelines['recommended_per_week']
        remaining = max(0, goal - current_count)

        progress_pct = min(100, (current_count / goal) * 100)
        progress_color = COLORS['positive'] if progress_pct >= 100 else COLORS['warning'] if progress_pct >= 50 else COLORS['negative']

        st.markdown(f"""
        <div class="premium-card" style="background: linear-gradient(145deg, {COLORS['steel_dark']} 0%, {COLORS['steel']} 100%);
                    border: 1px solid {COLORS['steel_light']}; border-radius: 12px; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div style="color: {COLORS['text_primary']}; font-size: 1.1rem; font-weight: 600;">
                    {guidelines['icon']} {guidelines['name']}
                </div>
                <div style="color: {progress_color}; font-weight: 700;">
                    {current_count}/{goal} this week
                </div>
            </div>

            <!-- Progress bar -->
            <div style="background: {COLORS['bg_dark']}; border-radius: 10px; height: 10px; margin-bottom: 15px;">
                <div style="background: {progress_color}; width: {progress_pct}%;
                            height: 100%; border-radius: 10px; transition: width 0.3s;"></div>
            </div>

            <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
                <div style="margin-bottom: 8px;">
                    <strong>Best times:</strong> {', '.join(guidelines['best_times'])}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Best days:</strong> {', '.join(guidelines['best_days'])}
                </div>
                <div>
                    <strong>Remaining:</strong> {remaining} posts to hit goal
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Content Ideas Queue =====
section_header("Content Ideas Queue")

st.markdown(f"""
<p style="color: {COLORS['text_muted']}; font-size: 0.9rem; margin-bottom: 20px;">
    Save ideas for future posts. Never run out of content!
</p>
""", unsafe_allow_html=True)

# Add new idea
with st.expander("➕ Add Content Idea"):
    col1, col2 = st.columns(2)

    with col1:
        idea_platform = st.selectbox(
            "Platform",
            options=["twitter", "reddit", "both"],
            format_func=lambda x: {"twitter": "𝕏 X", "reddit": "📝 Reddit", "both": "🔄 Both"}[x]
        )

    with col2:
        idea_type = st.selectbox(
            "Content Type",
            options=["trade_alert", "educational", "track_record", "engagement", "other"],
            format_func=lambda x: x.replace("_", " ").title()
        )

    idea_title = st.text_input("Idea Title", placeholder="Brief description of the post idea")
    idea_notes = st.text_area("Notes", placeholder="Details, links, or draft content...", height=100)

    if st.button("Save Idea", type="primary"):
        if idea_title:
            new_idea = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "platform": idea_platform,
                "type": idea_type,
                "title": idea_title,
                "notes": idea_notes,
                "created_at": datetime.now().isoformat(),
                "used": False
            }
            schedule['content_ideas'].append(new_idea)
            save_schedule(schedule)
            st.success("Idea saved!")
            st.rerun()
        else:
            st.warning("Please add a title!")

# Display existing ideas
ideas = [i for i in schedule.get('content_ideas', []) if not i.get('used', False)]

if ideas:
    for idea in sorted(ideas, key=lambda x: x.get('created_at', ''), reverse=True):
        platform_emoji = {"twitter": "🐦", "reddit": "📝", "both": "🔄"}.get(idea.get('platform', ''), "📄")

        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"""
            <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                        border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                    <span>{platform_emoji}</span>
                    <span style="color: {COLORS['text_primary']}; font-weight: 600;">
                        {idea.get('title', 'Untitled')}
                    </span>
                    <span style="background: {COLORS['steel_dark']}; color: {COLORS['text_muted']};
                                padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">
                        {idea.get('type', 'other').replace('_', ' ').title()}
                    </span>
                </div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.9rem;">
                    {idea.get('notes', '')[:100]}{'...' if len(idea.get('notes', '')) > 100 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("✅ Used", key=f"used_{idea['id']}"):
                for i in schedule['content_ideas']:
                    if i['id'] == idea['id']:
                        i['used'] = True
                save_schedule(schedule)
                st.rerun()
else:
    st.info("No content ideas saved yet. Add some above to never run out of post topics!")

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Recent Activity Log =====
section_header("Recent Activity")

recent_posts = sorted(
    [p for p in posts if p.get('status') == 'posted'],
    key=lambda x: x.get('date', ''),
    reverse=True
)[:10]

if recent_posts:
    for post in recent_posts:
        platform_emoji = "🐦" if post.get('platform') == 'twitter' else "📝"
        post_date = post.get('date', '')[:10]

        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 15px; padding: 10px 0;
                    border-bottom: 1px solid {COLORS['steel_dark']};">
            <span style="font-size: 1.2rem;">{platform_emoji}</span>
            <div style="flex: 1;">
                <div style="color: {COLORS['text_primary']};">
                    {post.get('title', post.get('content', '')[:50])}...
                </div>
            </div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
                {post_date}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No posts yet. Start creating content to build your track record!")

# ===== Footer Tips =====
st.markdown("<br><br>", unsafe_allow_html=True)

with st.expander("📊 Consistency Tips"):
    st.markdown(f"""
    ### Why Consistency Matters

    - **Algorithm favor**: Social platforms reward consistent posters
    - **Audience expectations**: Followers expect regular content
    - **Compounding growth**: Daily posts compound to massive reach over time

    ### Building the Habit

    1. **Batch create**: Write multiple posts in one session
    2. **Use templates**: Reuse formats that work
    3. **Set reminders**: Schedule specific posting times
    4. **Track metrics**: Monitor what content performs best

    ### Content Pillars

    Rotate between these content types:
    - **Educational** (40%): Teach concepts, explain methodology
    - **Trade Ideas** (30%): Share opportunities with reasoning
    - **Track Record** (20%): Transparency on results
    - **Engagement** (10%): Replies, quotes, community building
    """)
