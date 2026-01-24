"""
PowersBioStrikes Admin Portal - X Post Generator
Create trade alerts, educational content, and track record updates for X.
"""

import streamlit as st
from datetime import datetime
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import apply_theme, sidebar_branding, section_header, char_counter, COLORS

# Apply theme (page config already set by main app, skip here)
try:
    st.set_page_config(page_title="X Post Generator | PBS Admin", page_icon="𝕏", layout="wide")
except:
    pass

sidebar_branding()

# ===== Constants =====
TWITTER_CHAR_LIMIT = 280
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')

# ===== Helper Functions =====
def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_post(post_data):
    posts = load_posts()
    posts.append(post_data)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, default=str)

# ===== Post Templates =====
TEMPLATES = {
    "trade_alert": {
        "name": "Trade Alert",
        "icon": "🎯",
        "description": "Announce a new position or trade idea",
        "template": """🎯 NEW POSITION: ${TICKER}

${THESIS_BRIEF}

📊 Setup:
• Strike: ${STRIKE}
• Expiry: ${EXPIRY}
• Catalyst: ${CATALYST}

⚠️ This is my trade, not advice. Do your own DD.

#biotech #options #${TICKER}""",
        "fields": ["TICKER", "THESIS_BRIEF", "STRIKE", "EXPIRY", "CATALYST"]
    },
    "track_record": {
        "name": "Track Record Update",
        "icon": "📈",
        "description": "Share a win or loss transparently",
        "template": """${RESULT_EMOJI} TRADE CLOSED: ${TICKER}

${RESULT_TYPE}: ${RETURN_PCT}%

Entry: ${ENTRY_PRICE}
Exit: ${EXIT_PRICE}

${LESSON_LEARNED}

Full transparency - every trade, win or lose.

#biotech #options #trackrecord""",
        "fields": ["TICKER", "RESULT_TYPE", "RETURN_PCT", "ENTRY_PRICE", "EXIT_PRICE", "LESSON_LEARNED"]
    },
    "educational": {
        "name": "Educational",
        "icon": "📚",
        "description": "Share methodology or insights",
        "template": """💡 ${TOPIC}

${MAIN_POINT}

Key takeaway: ${TAKEAWAY}

This is what separates systematic trading from gambling.

#biotech #trading #education""",
        "fields": ["TOPIC", "MAIN_POINT", "TAKEAWAY"]
    },
    "catalyst_alert": {
        "name": "Catalyst Alert",
        "icon": "⚡",
        "description": "Alert about upcoming FDA event",
        "template": """⚡ CATALYST WATCH: ${TICKER}

${EVENT_TYPE} expected: ${EVENT_DATE}

What to know:
• ${KEY_POINT_1}
• ${KEY_POINT_2}

Not trading advice - just highlighting the calendar.

#biotech #FDA #catalyst""",
        "fields": ["TICKER", "EVENT_TYPE", "EVENT_DATE", "KEY_POINT_1", "KEY_POINT_2"]
    },
    "thread_starter": {
        "name": "Thread Starter",
        "icon": "🧵",
        "description": "Start a longer thread",
        "template": """🧵 THREAD: ${THREAD_TITLE}

${HOOK}

Let me break it down 👇

1/""",
        "fields": ["THREAD_TITLE", "HOOK"]
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
st.title("𝕏 X Post Generator")

st.markdown(f"""
<p style="color: {COLORS['text_secondary']}; margin-bottom: 30px;">
    Create engaging X posts with templates designed for biotech trading.
</p>
""", unsafe_allow_html=True)

# ===== Template Selection =====
section_header("Choose Template")

cols = st.columns(3)
template_keys = list(TEMPLATES.keys())

for i, key in enumerate(template_keys):
    template = TEMPLATES[key]
    with cols[i % 3]:
        selected = st.button(
            f"{template['icon']} {template['name']}",
            key=f"template_{key}",
            use_container_width=True,
            help=template['description']
        )
        if selected:
            st.session_state['selected_template'] = key

# Get selected template
selected_template_key = st.session_state.get('selected_template', 'custom')
selected_template = TEMPLATES[selected_template_key]

st.markdown(f"""
<div style="background: {COLORS['mahogany_dark']}; padding: 10px 20px; border-radius: 8px;
            margin: 20px 0; border-left: 3px solid {COLORS['gold']};">
    <span style="color: {COLORS['gold']}; font-weight: 600;">
        Selected: {selected_template['icon']} {selected_template['name']}
    </span>
    <span style="color: {COLORS['text_muted']}; margin-left: 15px;">
        {selected_template['description']}
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ===== Post Editor =====
section_header("Compose Post")

col1, col2 = st.columns([2, 1])

with col1:
    # If template has fields, show them
    if selected_template['fields']:
        st.markdown(f"**Fill in the template fields:**")

        field_values = {}
        for field in selected_template['fields']:
            field_label = field.replace('_', ' ').title()

            # Special handling for certain fields
            if field == "RESULT_TYPE":
                field_values[field] = st.selectbox(field_label, ["WIN", "LOSS"])
            elif field == "RESULT_EMOJI":
                # Auto-set based on result type
                field_values[field] = "✅" if field_values.get("RESULT_TYPE") == "WIN" else "❌"
            elif field in ["THESIS_BRIEF", "MAIN_POINT", "HOOK", "LESSON_LEARNED"]:
                field_values[field] = st.text_area(field_label, key=f"field_{field}", height=100)
            else:
                field_values[field] = st.text_input(field_label, key=f"field_{field}")

        # Generate post from template
        post_content = selected_template['template']
        for field, value in field_values.items():
            post_content = post_content.replace(f"${{{field}}}", value or f"[{field}]")

        # Handle RESULT_EMOJI specially
        if "RESULT_TYPE" in field_values:
            emoji = "✅" if field_values["RESULT_TYPE"] == "WIN" else "❌"
            post_content = post_content.replace("${RESULT_EMOJI}", emoji)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Preview & Edit:**")
        post_content = st.text_area(
            "Post Content",
            value=post_content,
            height=200,
            key="post_content",
            label_visibility="collapsed"
        )
    else:
        # Custom post - just show textarea
        post_content = st.text_area(
            "Post Content",
            height=250,
            key="post_content_custom",
            placeholder="Write your post here..."
        )

    # Character count
    char_count = len(post_content) if post_content else 0
    remaining = TWITTER_CHAR_LIMIT - char_count

    if remaining < 0:
        color = COLORS['negative']
        status = f"⚠️ {abs(remaining)} characters over limit!"
    elif remaining < 30:
        color = COLORS['warning']
        status = f"{remaining} characters remaining"
    else:
        color = COLORS['text_muted']
        status = f"{remaining} characters remaining"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
        <span style="color: {color}; font-size: 0.9rem;">{status}</span>
        <span style="color: {COLORS['text_muted']}; font-size: 0.9rem;">{char_count}/{TWITTER_CHAR_LIMIT}</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Preview card
    st.markdown(f"""
    <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                border-radius: 12px; padding: 20px;">
        <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; text-transform: uppercase;
                    letter-spacing: 1px; margin-bottom: 15px;">Preview</div>
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div style="width: 48px; height: 48px; background: {COLORS['gold']}; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center;
                        color: {COLORS['bg_dark']}; font-weight: 700; font-size: 1.2rem;">
                PB
            </div>
            <div style="margin-left: 12px;">
                <div style="color: {COLORS['text_primary']}; font-weight: 600;">PowersBioStrikes</div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">@PowersBioStrike</div>
            </div>
        </div>
        <div style="color: {COLORS['text_primary']}; white-space: pre-wrap; line-height: 1.5;">
            {post_content or '<span style="color: ' + COLORS['text_muted'] + ';">Your post preview will appear here...</span>'}
        </div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-top: 15px;
                    padding-top: 15px; border-top: 1px solid {COLORS['steel_dark']};">
            {datetime.now().strftime('%I:%M %p · %b %d, %Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Action buttons
    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("📋 Copy", use_container_width=True, help="Copy to clipboard"):
            st.session_state['copied'] = True
            # Note: Actual clipboard copy requires JavaScript
            st.toast("Post content ready to copy!", icon="📋")

    with col_b:
        if st.button("💾 Save Draft", use_container_width=True):
            if post_content:
                post_data = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "platform": "twitter",
                    "title": post_content[:50],
                    "content": post_content,
                    "template": selected_template_key,
                    "status": "draft",
                    "date": datetime.now().isoformat()
                }
                save_post(post_data)
                st.success("Draft saved!")
            else:
                st.warning("Nothing to save!")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("✅ Mark as Posted", use_container_width=True, type="primary"):
        if post_content:
            post_data = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "platform": "twitter",
                "title": post_content[:50],
                "content": post_content,
                "template": selected_template_key,
                "status": "posted",
                "date": datetime.now().isoformat()
            }
            save_post(post_data)
            st.success("Marked as posted! Great job staying consistent.")
            st.balloons()
        else:
            st.warning("Nothing to save!")

# ===== Tips Section =====
st.markdown("<br><br>", unsafe_allow_html=True)

with st.expander("📝 X Best Practices"):
    st.markdown(f"""
    ### Timing
    - **Best times:** 8-10 AM, 12-1 PM, 5-6 PM (your timezone)
    - **Frequency:** 1-3 posts per day for growth phase

    ### Content Mix
    - **40%** Educational content (methodology, concepts)
    - **30%** Trade ideas and alerts
    - **20%** Track record updates (wins AND losses)
    - **10%** Engagement (replies, quotes, community)

    ### Engagement Tips
    - Use relevant hashtags: #biotech #options #FDA #PDUFA
    - Tag relevant accounts sparingly
    - Reply to comments to boost engagement
    - Quote post interesting biotech news

    ### What NOT to do
    - Don't promise returns or guaranteed profits
    - Don't hide losses - transparency builds trust
    - Don't spam the same content
    - Don't buy followers or engagement
    """)

# ===== Recent X Posts =====
st.markdown("<br>", unsafe_allow_html=True)
section_header("Recent X Posts - Click to Copy")

posts = load_posts()
twitter_posts = [p for p in posts if p.get('platform') == 'twitter']
# Support both 'date' and 'created_at' fields
recent_twitter = sorted(twitter_posts, key=lambda x: x.get('date', x.get('created_at', '')), reverse=True)[:10]

if recent_twitter:
    for post in recent_twitter:
        status = post.get('status', 'draft')
        status_emoji = "✅" if status == 'posted' else "📝"
        post_date = post.get('date', post.get('created_at', ''))[:10]
        title = post.get('title', 'Untitled')
        full_content = post.get('content', '')
        char_count = len(full_content)

        with st.expander(f"{status_emoji} {title} ({char_count} chars)"):
            st.markdown("**Select all the text below and copy it (Ctrl+A, Ctrl+C):**")
            st.text_area(
                "Post content",
                value=full_content,
                height=200,
                key=f"content_{post.get('id')}",
                label_visibility="collapsed"
            )
            st.caption(f"Created: {post_date} | Status: {status.upper()} | {char_count}/280 characters")

            # Show thread parts if they exist
            if post.get('thread_parts'):
                st.markdown("---")
                st.markdown("**Thread parts (post these as replies):**")
                for i, part in enumerate(post.get('thread_parts', []), 1):
                    st.text_area(
                        f"Part {i}",
                        value=part,
                        height=100,
                        key=f"thread_{post.get('id')}_{i}",
                        label_visibility="collapsed"
                    )
                    st.caption(f"Part {i}: {len(part)}/280 characters")
else:
    st.info("No X posts yet. Create your first one above!")
