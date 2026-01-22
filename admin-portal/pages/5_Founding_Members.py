"""
PowersBioStrikes Admin Portal - Founding Members Tracker
Track and manage your founding member signups.
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import sidebar_branding, section_header, metric_card, COLORS

# Page config
try:
    st.set_page_config(page_title="Founding Members | PBS Admin", page_icon="🏆", layout="wide")
except:
    pass

sidebar_branding()

# ===== Constants =====
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
MEMBERS_FILE = os.path.join(DATA_DIR, 'founding_members.json')
MAX_FOUNDING_MEMBERS = 100

# ===== Helper Functions =====
def load_members():
    if os.path.exists(MEMBERS_FILE):
        with open(MEMBERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_members(members):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MEMBERS_FILE, 'w') as f:
        json.dump(members, f, indent=2, default=str)

def calculate_free_months_remaining(signup_date_str):
    """Calculate how many free months remain for a founding member."""
    try:
        signup_date = datetime.fromisoformat(signup_date_str[:19])
        months_elapsed = (datetime.now() - signup_date).days / 30
        remaining = max(0, 6 - int(months_elapsed))
        return remaining
    except:
        return 6


# ===== Load Data =====
if 'founding_members' not in st.session_state:
    st.session_state.founding_members = load_members()

members = st.session_state.founding_members


# ===== Main Content =====
st.title("🏆 Founding Members")

st.markdown(f"""
<p style="color: {COLORS['text_secondary']}; margin-bottom: 30px;">
    Track your Founding Member signups and manage early supporters.
</p>
""", unsafe_allow_html=True)

# ===== Stats Overview =====
total_members = len(members)
spots_remaining = max(0, MAX_FOUNDING_MEMBERS - total_members)
active_members = len([m for m in members if m.get('status', 'active') == 'active'])
in_free_period = len([m for m in members if calculate_free_months_remaining(m.get('signupDate', '')) > 0])

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_color = "positive" if total_members > 0 else "neutral"
    metric_card("Total Signups", str(total_members), f"of {MAX_FOUNDING_MEMBERS} spots", delta_color)

with col2:
    delta_color = "warning" if spots_remaining < 20 else "positive"
    metric_card("Spots Remaining", str(spots_remaining), "hurry!" if spots_remaining < 20 else "available", delta_color)

with col3:
    metric_card("Active Members", str(active_members))

with col4:
    metric_card("In Free Period", str(in_free_period), "6 months free")

st.markdown("<br>", unsafe_allow_html=True)

# ===== Progress Bar =====
progress_pct = (total_members / MAX_FOUNDING_MEMBERS) * 100
progress_color = COLORS['positive'] if progress_pct < 50 else COLORS['warning'] if progress_pct < 80 else COLORS['negative']

st.markdown(f"""
<div style="margin-bottom: 30px;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
        <span style="color: {COLORS['text_muted']}; font-size: 0.9rem;">Founding Member Spots Filled</span>
        <span style="color: {COLORS['gold']}; font-weight: 600;">{total_members}/{MAX_FOUNDING_MEMBERS}</span>
    </div>
    <div style="background: {COLORS['bg_dark']}; border-radius: 10px; height: 12px; overflow: hidden;">
        <div style="background: linear-gradient(90deg, {COLORS['gold']}, {progress_color});
                    width: {progress_pct}%; height: 100%; border-radius: 10px;
                    transition: width 0.3s ease;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ===== Add New Member Manually =====
section_header("Add Founding Member", "Manually add a new founding member")

with st.expander("➕ Add Member Manually", expanded=len(members) == 0):
    col1, col2 = st.columns(2)

    with col1:
        new_name = st.text_input("Full Name", placeholder="John Smith")
        new_email = st.text_input("Email Address", placeholder="john@example.com")

    with col2:
        new_source = st.selectbox(
            "Signup Source",
            options=["landing_page", "twitter", "reddit", "referral", "direct", "other"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        new_notes = st.text_area("Notes", placeholder="Any notes about this member...", height=68)

    if st.button("Add Founding Member", type="primary"):
        if new_name and new_email:
            # Check for duplicates
            existing = [m for m in st.session_state.founding_members if m.get('email') == new_email]
            if existing:
                st.warning("A member with this email already exists!")
            else:
                new_member = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "name": new_name,
                    "email": new_email,
                    "source": new_source,
                    "notes": new_notes,
                    "signupDate": datetime.now().isoformat(),
                    "tier": "founding_member",
                    "freeMonthsRemaining": 6,
                    "status": "active"
                }
                st.session_state.founding_members.append(new_member)
                save_members(st.session_state.founding_members)
                st.success(f"Added {new_name} as a Founding Member!")
                st.rerun()
        else:
            st.warning("Please enter both name and email!")

st.markdown("<br>", unsafe_allow_html=True)

# ===== Member List =====
section_header("Founding Member List", "All signed up founding members")

if members:
    # Filter options
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        search_query = st.text_input("Search", placeholder="Search by name or email...", label_visibility="collapsed")

    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["all", "active", "churned", "converted"],
            format_func=lambda x: x.title() if x != "all" else "All Members",
            label_visibility="collapsed"
        )

    with col3:
        sort_order = st.selectbox(
            "Sort",
            options=["newest", "oldest", "name"],
            format_func=lambda x: x.title(),
            label_visibility="collapsed"
        )

    # Apply filters
    filtered_members = members

    if search_query:
        search_lower = search_query.lower()
        filtered_members = [m for m in filtered_members
                          if search_lower in m.get('name', '').lower()
                          or search_lower in m.get('email', '').lower()]

    if status_filter != "all":
        filtered_members = [m for m in filtered_members if m.get('status', 'active') == status_filter]

    # Apply sorting
    if sort_order == "newest":
        filtered_members = sorted(filtered_members, key=lambda x: x.get('signupDate', ''), reverse=True)
    elif sort_order == "oldest":
        filtered_members = sorted(filtered_members, key=lambda x: x.get('signupDate', ''))
    else:
        filtered_members = sorted(filtered_members, key=lambda x: x.get('name', '').lower())

    st.markdown(f"<p style='color: {COLORS['text_muted']}; margin-bottom: 15px;'>Showing {len(filtered_members)} of {len(members)} members</p>", unsafe_allow_html=True)

    # Member cards
    for member in filtered_members:
        free_remaining = calculate_free_months_remaining(member.get('signupDate', ''))
        status = member.get('status', 'active')
        status_color = COLORS['positive'] if status == 'active' else COLORS['warning'] if status == 'churned' else COLORS['gold']

        signup_date = member.get('signupDate', '')[:10]
        source_emoji = {
            "landing_page": "🌐",
            "twitter": "🐦",
            "reddit": "📝",
            "referral": "🤝",
            "direct": "📧",
            "other": "📌"
        }.get(member.get('source', 'other'), "📌")

        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"""
            <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                        border-left: 3px solid {COLORS['gold']}; border-radius: 8px;
                        padding: 15px 20px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="color: {COLORS['text_primary']}; font-size: 1.1rem; font-weight: 600;">
                            {member.get('name', 'Unknown')}
                        </div>
                        <div style="color: {COLORS['text_muted']}; font-size: 0.9rem; margin-top: 3px;">
                            {member.get('email', 'No email')}
                        </div>
                        <div style="display: flex; gap: 15px; margin-top: 10px;">
                            <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">
                                {source_emoji} {member.get('source', 'unknown').replace('_', ' ').title()}
                            </span>
                            <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">
                                📅 Joined {signup_date}
                            </span>
                            <span style="color: {COLORS['gold'] if free_remaining > 0 else COLORS['text_muted']}; font-size: 0.8rem;">
                                {'🎁 ' + str(int(free_remaining)) + ' free months left' if free_remaining > 0 else '💳 Paying member'}
                            </span>
                        </div>
                        {f'<div style="color: {COLORS[\"text_muted\"]}; font-size: 0.8rem; margin-top: 5px; font-style: italic;">{member.get(\"notes\", \"\")}</div>' if member.get('notes') else ''}
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 5px;">
                        <span style="background: {status_color}20; color: {status_color};
                                    padding: 3px 10px; border-radius: 12px; font-size: 0.75rem;
                                    text-transform: uppercase;">
                            {status}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Status toggle buttons
            if status == 'active':
                if st.button("Mark Churned", key=f"churn_{member['id']}", use_container_width=True):
                    for m in st.session_state.founding_members:
                        if m['id'] == member['id']:
                            m['status'] = 'churned'
                    save_members(st.session_state.founding_members)
                    st.rerun()
            elif status == 'churned':
                if st.button("Reactivate", key=f"reactivate_{member['id']}", use_container_width=True):
                    for m in st.session_state.founding_members:
                        if m['id'] == member['id']:
                            m['status'] = 'active'
                    save_members(st.session_state.founding_members)
                    st.rerun()

else:
    st.markdown(f"""
    <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                border-radius: 8px; padding: 40px; text-align: center;">
        <div style="font-size: 3rem; margin-bottom: 15px;">🏆</div>
        <div style="color: {COLORS['text_primary']}; font-size: 1.2rem; margin-bottom: 10px;">
            No Founding Members Yet
        </div>
        <div style="color: {COLORS['text_muted']};">
            Founding members will appear here as they sign up through the landing page.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Import from Landing Page =====
section_header("Import Data", "Sync with landing page localStorage data")

st.markdown(f"""
<div style="background: {COLORS['mahogany_dark']}; border: 1px solid {COLORS['steel']};
            border-radius: 8px; padding: 20px; margin-bottom: 20px;">
    <div style="color: {COLORS['gold']}; font-weight: 600; margin-bottom: 10px;">
        📥 Import from Landing Page
    </div>
    <div style="color: {COLORS['text_muted']}; font-size: 0.9rem; margin-bottom: 15px;">
        To import founding members from your landing page, open your browser's Developer Tools (F12) on the landing page,
        go to Console, and run: <code style="background: {COLORS['bg_dark']}; padding: 2px 6px; border-radius: 4px;">
        copy(localStorage.getItem('pbs_founding_members'))</code>
        <br><br>
        Then paste the JSON data below:
    </div>
</div>
""", unsafe_allow_html=True)

import_data = st.text_area("Paste JSON data here", placeholder='[{"name": "...", "email": "..."}, ...]', height=100)

if st.button("Import Members"):
    if import_data:
        try:
            imported = json.loads(import_data)
            if isinstance(imported, list):
                new_count = 0
                for member in imported:
                    # Check for duplicates
                    existing = [m for m in st.session_state.founding_members if m.get('email') == member.get('email')]
                    if not existing and member.get('email'):
                        # Ensure required fields
                        member['id'] = member.get('id', datetime.now().strftime("%Y%m%d%H%M%S"))
                        member['source'] = member.get('source', 'landing_page')
                        member['status'] = member.get('status', 'active')
                        st.session_state.founding_members.append(member)
                        new_count += 1

                save_members(st.session_state.founding_members)
                st.success(f"Imported {new_count} new founding members!")
                st.rerun()
            else:
                st.error("Invalid format. Expected a JSON array.")
        except json.JSONDecodeError:
            st.error("Invalid JSON. Please check the format.")
    else:
        st.warning("Please paste some data to import.")

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Export =====
with st.expander("📤 Export Members"):
    if members:
        export_data = json.dumps(members, indent=2, default=str)
        st.code(export_data, language="json")
        st.download_button(
            label="Download JSON",
            data=export_data,
            file_name="founding_members.json",
            mime="application/json"
        )
    else:
        st.info("No members to export yet.")

# ===== Founding Member Benefits Reminder =====
with st.expander("🎁 Founding Member Benefits"):
    st.markdown(f"""
    ### What Founding Members Get

    - **6 Months Free Access** - Full premium content at no cost
    - **50% Off Forever** - After free period, locked in at half price
    - **Priority Support** - Direct access and faster responses
    - **Early Feature Access** - First to try new tools and analysis

    ### Pricing After Free Period

    | Plan | Regular Price | Founding Member Price |
    |------|---------------|----------------------|
    | Monthly | $49/mo | $24.50/mo |
    | Annual | $399/yr | $199.50/yr |

    ### Timeline

    1. **Month 1-6**: Full free access
    2. **Month 7**: Payment begins at 50% discount
    3. **Forever**: Locked in at founding rate
    """)
