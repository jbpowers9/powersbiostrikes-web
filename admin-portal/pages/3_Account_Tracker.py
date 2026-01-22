"""
PowersBioStrikes Admin Portal - Account Tracker
Track your social media accounts, usernames, and follower growth.
NOTE: Does NOT store passwords - use a password manager for that!
"""

import streamlit as st
from datetime import datetime
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import sidebar_branding, section_header, metric_card, COLORS

# Page config
try:
    st.set_page_config(page_title="Account Tracker | PBS Admin", page_icon="👤", layout="wide")
except:
    pass

sidebar_branding()

# ===== Constants =====
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
ACCOUNTS_FILE = os.path.join(DATA_DIR, 'accounts.json')

# Platform configurations
PLATFORMS = {
    "twitter": {
        "name": "Twitter / X",
        "icon": "🐦",
        "color": "#1DA1F2",
        "login_url": "https://twitter.com/login",
        "profile_url_template": "https://twitter.com/{username}"
    },
    "reddit": {
        "name": "Reddit",
        "icon": "📝",
        "color": "#FF4500",
        "login_url": "https://www.reddit.com/login",
        "profile_url_template": "https://reddit.com/user/{username}"
    },
    "linkedin": {
        "name": "LinkedIn",
        "icon": "💼",
        "color": "#0A66C2",
        "login_url": "https://www.linkedin.com/login",
        "profile_url_template": "https://linkedin.com/in/{username}"
    },
    "stocktwits": {
        "name": "StockTwits",
        "icon": "📊",
        "color": "#40576E",
        "login_url": "https://stocktwits.com/signin",
        "profile_url_template": "https://stocktwits.com/{username}"
    },
    "discord": {
        "name": "Discord",
        "icon": "💬",
        "color": "#5865F2",
        "login_url": "https://discord.com/login",
        "profile_url_template": None  # Discord doesn't have public profiles
    },
    "substack": {
        "name": "Substack",
        "icon": "📰",
        "color": "#FF6719",
        "login_url": "https://substack.com/sign-in",
        "profile_url_template": "https://{username}.substack.com"
    }
}

# ===== Helper Functions =====
def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_accounts(accounts):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=2, default=str)

def get_profile_url(platform_key, username):
    platform = PLATFORMS.get(platform_key, {})
    template = platform.get('profile_url_template')
    if template and username:
        return template.format(username=username)
    return None


# ===== Load Data =====
if 'accounts' not in st.session_state:
    st.session_state.accounts = load_accounts()

accounts = st.session_state.accounts


# ===== Main Content =====
st.title("👤 Account Tracker")

st.markdown(f"""
<p style="color: {COLORS['text_secondary']}; margin-bottom: 10px;">
    Track your social media presence across platforms.
</p>
<p style="color: {COLORS['warning']}; font-size: 0.9rem; margin-bottom: 30px;">
    ⚠️ <strong>Security Note:</strong> This tool stores usernames only.
    Use a password manager (1Password, Bitwarden) for credentials.
</p>
""", unsafe_allow_html=True)

# ===== Quick Stats =====
active_accounts = [a for a in accounts if a.get('active', True)]
total_followers = sum(a.get('followers', 0) for a in active_accounts)

col1, col2, col3 = st.columns(3)
with col1:
    metric_card("Active Accounts", str(len(active_accounts)))
with col2:
    metric_card("Total Followers", f"{total_followers:,}")
with col3:
    metric_card("Platforms", str(len(set(a.get('platform') for a in active_accounts))))

st.markdown("<br>", unsafe_allow_html=True)

# ===== Add New Account =====
section_header("Add New Account")

with st.expander("➕ Add Account", expanded=len(accounts) == 0):
    col1, col2 = st.columns(2)

    with col1:
        new_platform = st.selectbox(
            "Platform",
            options=list(PLATFORMS.keys()),
            format_func=lambda x: f"{PLATFORMS[x]['icon']} {PLATFORMS[x]['name']}"
        )
        new_username = st.text_input("Username (without @)", placeholder="PowersBioStrikes")

    with col2:
        new_display_name = st.text_input("Display Name", placeholder="PowersBioStrikes")
        new_followers = st.number_input("Current Followers", min_value=0, value=0)

    new_notes = st.text_area("Notes", placeholder="Any notes about this account...", height=80)

    if st.button("Add Account", type="primary"):
        if new_username:
            new_account = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "platform": new_platform,
                "username": new_username,
                "display_name": new_display_name or new_username,
                "followers": new_followers,
                "notes": new_notes,
                "active": True,
                "created_at": datetime.now().isoformat(),
                "follower_history": [
                    {"date": datetime.now().isoformat(), "count": new_followers}
                ]
            }
            st.session_state.accounts.append(new_account)
            save_accounts(st.session_state.accounts)
            st.success(f"Added {PLATFORMS[new_platform]['name']} account: @{new_username}")
            st.rerun()
        else:
            st.warning("Please enter a username!")

st.markdown("<br>", unsafe_allow_html=True)

# ===== Account Cards =====
section_header("Your Accounts")

if accounts:
    # Group by platform
    accounts_by_platform = {}
    for account in accounts:
        platform = account.get('platform', 'other')
        if platform not in accounts_by_platform:
            accounts_by_platform[platform] = []
        accounts_by_platform[platform].append(account)

    for platform_key, platform_accounts in accounts_by_platform.items():
        platform = PLATFORMS.get(platform_key, {"name": platform_key, "icon": "🔗", "color": COLORS['steel']})

        st.markdown(f"""
        <div style="color: {COLORS['gold']}; font-size: 1.1rem; font-weight: 600;
                    margin: 20px 0 10px 0;">
            {platform['icon']} {platform['name']}
        </div>
        """, unsafe_allow_html=True)

        for account in platform_accounts:
            status_color = COLORS['positive'] if account.get('active', True) else COLORS['text_muted']
            profile_url = get_profile_url(platform_key, account.get('username', ''))

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                            border-left: 3px solid {platform.get('color', COLORS['gold'])};
                            border-radius: 8px; padding: 20px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div style="color: {COLORS['text_primary']}; font-size: 1.2rem; font-weight: 600;">
                                {account.get('display_name', account.get('username', 'Unknown'))}
                            </div>
                            <div style="color: {COLORS['text_muted']}; font-size: 0.9rem;">
                                @{account.get('username', 'unknown')}
                            </div>
                            <div style="color: {COLORS['gold']}; font-size: 1.1rem; margin-top: 10px;">
                                {account.get('followers', 0):,} followers
                            </div>
                            {f'<div style="color: {COLORS["text_muted"]}; font-size: 0.85rem; margin-top: 5px;">{account.get("notes", "")}</div>' if account.get('notes') else ''}
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px;">
                            <span style="background: {status_color}20; color: {status_color};
                                        padding: 3px 10px; border-radius: 12px; font-size: 0.75rem;">
                                {'Active' if account.get('active', True) else 'Inactive'}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)

                # Quick action buttons
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    login_url = platform.get('login_url', '#')
                    st.markdown(f"""
                    <a href="{login_url}" target="_blank" style="
                        display: inline-block;
                        background: {COLORS['steel_dark']};
                        border: 1px solid {COLORS['steel']};
                        color: {COLORS['text_secondary']};
                        padding: 8px 12px;
                        border-radius: 6px;
                        text-decoration: none;
                        font-size: 0.85rem;
                        text-align: center;
                        width: 100%;
                    ">🔑 Login</a>
                    """, unsafe_allow_html=True)

                with btn_col2:
                    if profile_url:
                        st.markdown(f"""
                        <a href="{profile_url}" target="_blank" style="
                            display: inline-block;
                            background: {COLORS['steel_dark']};
                            border: 1px solid {COLORS['steel']};
                            color: {COLORS['text_secondary']};
                            padding: 8px 12px;
                            border-radius: 6px;
                            text-decoration: none;
                            font-size: 0.85rem;
                            text-align: center;
                            width: 100%;
                        ">👤 Profile</a>
                        """, unsafe_allow_html=True)

else:
    st.markdown(f"""
    <div style="background: {COLORS['bg_card']}; border: 1px solid {COLORS['steel']};
                border-radius: 8px; padding: 40px; text-align: center;">
        <div style="font-size: 3rem; margin-bottom: 15px;">👤</div>
        <div style="color: {COLORS['text_primary']}; font-size: 1.2rem; margin-bottom: 10px;">
            No accounts added yet
        </div>
        <div style="color: {COLORS['text_muted']};">
            Add your first social media account above to get started.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Update Followers Section =====
if accounts:
    section_header("Update Follower Counts")

    st.markdown(f"""
    <p style="color: {COLORS['text_muted']}; font-size: 0.9rem; margin-bottom: 20px;">
        Periodically update your follower counts to track growth.
    </p>
    """, unsafe_allow_html=True)

    with st.form("update_followers"):
        updates = {}
        cols = st.columns(min(3, len(accounts)))

        for i, account in enumerate(accounts):
            platform = PLATFORMS.get(account.get('platform', ''), {})
            col = cols[i % len(cols)]

            with col:
                updates[account['id']] = st.number_input(
                    f"{platform.get('icon', '🔗')} @{account.get('username', 'unknown')}",
                    min_value=0,
                    value=account.get('followers', 0),
                    key=f"followers_{account['id']}"
                )

        if st.form_submit_button("Update All", type="primary"):
            for account in st.session_state.accounts:
                if account['id'] in updates:
                    new_count = updates[account['id']]
                    if new_count != account.get('followers', 0):
                        account['followers'] = new_count
                        if 'follower_history' not in account:
                            account['follower_history'] = []
                        account['follower_history'].append({
                            "date": datetime.now().isoformat(),
                            "count": new_count
                        })

            save_accounts(st.session_state.accounts)
            st.success("Follower counts updated!")
            st.rerun()

st.markdown("<br><br>", unsafe_allow_html=True)

# ===== Password Manager Recommendations =====
with st.expander("🔐 Recommended Password Managers"):
    st.markdown(f"""
    **Why use a password manager?**

    Storing passwords in files or spreadsheets is a security risk. Use a dedicated password manager:

    ### Free Options
    - **[Bitwarden](https://bitwarden.com)** - Open source, free tier is excellent
    - **[KeePassXC](https://keepassxc.org)** - Local-only, highly secure

    ### Paid Options (with extra features)
    - **[1Password](https://1password.com)** - Great UX, family sharing
    - **[Dashlane](https://dashlane.com)** - VPN included
    - **[LastPass](https://lastpass.com)** - Popular, easy to use

    ### Best Practices
    - Use a unique password for each account
    - Enable 2FA (two-factor authentication) on all accounts
    - Use your password manager to generate random passwords
    - Back up your password manager vault securely
    """)

# ===== Manage Accounts =====
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("⚙️ Manage Accounts"):
    if accounts:
        account_to_delete = st.selectbox(
            "Select account to manage",
            options=[a['id'] for a in accounts],
            format_func=lambda x: next(
                f"{PLATFORMS.get(a['platform'], {}).get('icon', '🔗')} @{a['username']}"
                for a in accounts if a['id'] == x
            )
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Toggle Active/Inactive", use_container_width=True):
                for account in st.session_state.accounts:
                    if account['id'] == account_to_delete:
                        account['active'] = not account.get('active', True)
                save_accounts(st.session_state.accounts)
                st.rerun()

        with col2:
            if st.button("🗑️ Delete Account", use_container_width=True, type="secondary"):
                st.session_state.accounts = [a for a in st.session_state.accounts if a['id'] != account_to_delete]
                save_accounts(st.session_state.accounts)
                st.success("Account deleted!")
                st.rerun()
    else:
        st.info("No accounts to manage yet.")
