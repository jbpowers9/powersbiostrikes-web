"""
PowersBioStrikes Admin Portal Theme
Matching the biotech dashboard's premium Mahogany & Steel aesthetic
"""

import streamlit as st

# ===== Color Palette =====
COLORS = {
    # Mahogany Tones
    'mahogany_dark': '#4A0E0E',
    'mahogany': '#6B1414',
    'mahogany_light': '#8B2323',

    # Steel Tones
    'steel_dark': '#2C3E50',
    'steel': '#34495E',
    'steel_light': '#5D6D7E',

    # Accent Colors
    'gold': '#D4AF37',
    'gold_dark': '#8B6914',
    'gold_light': '#E8C547',
    'silver': '#BDC3C7',

    # Status Colors
    'positive': '#00FF88',
    'negative': '#FF6B6B',
    'warning': '#FFA500',

    # Backgrounds
    'bg_dark': '#1C1C1C',
    'bg_card': '#2D2D2D',

    # Text
    'text_primary': '#FFFFFF',
    'text_secondary': '#E8E8E8',
    'text_muted': '#95A5A6',
}


def apply_theme():
    """Apply the premium PowersBioStrikes theme to the Streamlit app."""

    st.set_page_config(
        page_title="PowersBioStrikes Admin",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown(f"""
    <style>
        /* ===== Main App Background ===== */
        .stApp {{
            background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_card']} 100%);
        }}

        /* ===== Sidebar Styling ===== */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #3D1010 0%, {COLORS['mahogany_dark']} 50%, #2D0A0A 100%);
        }}

        [data-testid="stSidebar"] .stMarkdown {{
            color: {COLORS['text_secondary']};
        }}

        /* ===== Headers ===== */
        h1, h2, h3 {{
            color: {COLORS['gold']} !important;
            font-weight: 600 !important;
            letter-spacing: 1px !important;
        }}

        h1 {{
            border-bottom: 2px solid {COLORS['gold']};
            padding-bottom: 10px;
        }}

        /* ===== Text Colors ===== */
        p, span, label, .stMarkdown {{
            color: {COLORS['text_secondary']} !important;
        }}

        /* ===== Input Fields ===== */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {{
            background-color: {COLORS['bg_card']} !important;
            color: {COLORS['text_primary']} !important;
            border: 1px solid {COLORS['steel']} !important;
            border-radius: 8px !important;
        }}

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {COLORS['gold']} !important;
            box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2) !important;
        }}

        /* ===== Buttons ===== */
        .stButton > button {{
            background: linear-gradient(135deg, {COLORS['gold_dark']} 0%, {COLORS['gold']} 100%) !important;
            color: {COLORS['bg_dark']} !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            padding: 0.5rem 1.5rem !important;
            transition: all 0.3s ease !important;
        }}

        .stButton > button:hover {{
            background: linear-gradient(135deg, {COLORS['gold']} 0%, {COLORS['gold_light']} 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3) !important;
        }}

        /* Secondary Buttons */
        .stButton > button[kind="secondary"] {{
            background: transparent !important;
            border: 1px solid {COLORS['gold']} !important;
            color: {COLORS['gold']} !important;
        }}

        /* ===== Cards/Containers ===== */
        .premium-card {{
            background: linear-gradient(145deg, {COLORS['steel_dark']} 0%, {COLORS['steel']} 100%);
            border: 1px solid {COLORS['steel_light']};
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
        }}

        .premium-card-mahogany {{
            background: linear-gradient(145deg, {COLORS['mahogany_dark']} 0%, #3D1010 100%);
            border: 1px solid {COLORS['mahogany']};
        }}

        /* ===== Metrics ===== */
        [data-testid="stMetricValue"] {{
            color: {COLORS['gold']} !important;
            font-weight: 700 !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: {COLORS['text_muted']} !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }}

        /* ===== Tabs ===== */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {COLORS['bg_card']};
            border-radius: 8px;
            padding: 4px;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {COLORS['text_muted']} !important;
            border-radius: 6px !important;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {COLORS['mahogany_dark']} !important;
            color: {COLORS['gold']} !important;
        }}

        /* ===== Expanders ===== */
        .streamlit-expanderHeader {{
            background-color: {COLORS['bg_card']} !important;
            border: 1px solid {COLORS['steel']} !important;
            border-radius: 8px !important;
            color: {COLORS['text_secondary']} !important;
        }}

        /* ===== DataFrames/Tables ===== */
        .stDataFrame {{
            border: 1px solid {COLORS['steel']} !important;
            border-radius: 8px !important;
        }}

        /* ===== Alerts/Messages ===== */
        .stSuccess {{
            background-color: rgba(0, 255, 136, 0.1) !important;
            border: 1px solid {COLORS['positive']} !important;
            color: {COLORS['positive']} !important;
        }}

        .stError {{
            background-color: rgba(255, 107, 107, 0.1) !important;
            border: 1px solid {COLORS['negative']} !important;
            color: {COLORS['negative']} !important;
        }}

        .stWarning {{
            background-color: rgba(255, 165, 0, 0.1) !important;
            border: 1px solid {COLORS['warning']} !important;
            color: {COLORS['warning']} !important;
        }}

        /* ===== Scrollbar ===== */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: {COLORS['bg_dark']};
        }}

        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, {COLORS['gold']} 0%, {COLORS['gold_dark']} 100%);
            border-radius: 5px;
            border: 2px solid {COLORS['bg_dark']};
        }}

        /* ===== Custom Classes ===== */
        .gold-text {{
            color: {COLORS['gold']} !important;
        }}

        .positive-text {{
            color: {COLORS['positive']} !important;
            text-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
        }}

        .negative-text {{
            color: {COLORS['negative']} !important;
            text-shadow: 0 0 8px rgba(255, 107, 107, 0.5);
        }}

        .char-count {{
            font-size: 0.85rem;
            color: {COLORS['text_muted']};
        }}

        .char-count.warning {{
            color: {COLORS['warning']};
        }}

        .char-count.danger {{
            color: {COLORS['negative']};
        }}

        /* ===== Copy Button ===== */
        .copy-btn {{
            background: {COLORS['steel_dark']};
            border: 1px solid {COLORS['steel']};
            color: {COLORS['text_secondary']};
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .copy-btn:hover {{
            background: {COLORS['steel']};
            border-color: {COLORS['gold']};
        }}

    </style>
    """, unsafe_allow_html=True)


def sidebar_branding():
    """Add branding to the sidebar."""
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0 30px 0;">
        <div style="font-size: 2.5rem; margin-bottom: 5px;">📊</div>
        <div style="color: {COLORS['gold']}; font-size: 1.1rem; font-weight: 700;
                    letter-spacing: 2px; text-transform: uppercase;">
            PowersBioStrikes
        </div>
        <div style="color: {COLORS['silver']}; font-size: 0.75rem; margin-top: 5px;
                    letter-spacing: 1px;">
            Admin Portal
        </div>
    </div>
    <hr style="border: none; border-top: 1px solid {COLORS['mahogany']}; margin: 0 0 20px 0;">
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Create a styled metric card."""
    delta_html = ""
    if delta:
        color = COLORS['positive'] if delta_color == "positive" else COLORS['negative'] if delta_color == "negative" else COLORS['text_muted']
        delta_html = f'<div style="color: {color}; font-size: 0.9rem;">{delta}</div>'

    st.markdown(f"""
    <div class="premium-card" style="text-align: center; padding: 15px;">
        <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; text-transform: uppercase;
                    letter-spacing: 1px; margin-bottom: 5px;">
            {label}
        </div>
        <div style="color: {COLORS['gold']}; font-size: 1.8rem; font-weight: 700;">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = None):
    """Create a styled section header."""
    subtitle_html = f'<div style="color: {COLORS["text_muted"]}; font-size: 0.9rem; margin-top: 5px;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="margin-bottom: 20px;">
        <h2 style="color: {COLORS['gold']}; margin-bottom: 0;">{title}</h2>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def char_counter(current: int, max_chars: int) -> str:
    """Return HTML for character counter with color coding."""
    remaining = max_chars - current
    if remaining < 0:
        css_class = "danger"
    elif remaining < 20:
        css_class = "warning"
    else:
        css_class = ""

    return f'<span class="char-count {css_class}">{current}/{max_chars} characters</span>'
