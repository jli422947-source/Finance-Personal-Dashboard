"""
Personal Finance Dashboard
==========================
Main entry point. Handles page routing, sidebar navigation,
theme toggle, and CSS injection.

Run with:
    streamlit run app.py --server.port 5000
"""

import streamlit as st
import os
import sys

# ── Path setup ───────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── DB init ───────────────────────────────────────────────────────────────────
from database.db import initialize_database
initialize_database()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinanceFlow — Personal Finance Dashboard",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS loader ────────────────────────────────────────────────────────────────
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()
def _render_sidebar_stats():
    """Show quick summary stats at the bottom of the sidebar."""
    from datetime import datetime
    from database.db import get_monthly_summary

    current_month = datetime.now().strftime("%Y-%m")
    try:
        summary = get_monthly_summary(current_month)
        st.markdown(
            '<div style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;'
            'color:#64748B;font-weight:600;margin-bottom:8px">This Month</div>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Income",  f"${summary['income']:,.0f}")
            st.metric("Savings", f"${summary['savings']:,.0f}")
        with col2:
            st.metric("Spent",   f"${summary['expenses']:,.0f}")
            st.metric("Rate",    f"{summary['savings_rate']:.0f}%")
    except Exception:
        pass

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.7rem;color:#4B5563;text-align:center">'
        "FinanceFlow v1.0<br>Built with ❤️ &amp; Streamlit</div>",
        unsafe_allow_html=True,
    )

# ── Session state defaults ────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"


# ── Sidebar ───────────────────────────────────────────────────────────────────
PAGES = {
    "Dashboard":  {"icon": "🏠", "description": "Overview & KPIs"},
    "Income":     {"icon": "💰", "description": "Track earnings"},
    "Expenses":   {"icon": "💸", "description": "Log spending"},
    "Budgets":    {"icon": "🎯", "description": "Set limits"},
    "Analytics":  {"icon": "📈", "description": "Charts & insights"},
    "Reports":    {"icon": "📄", "description": "Export & download"},
    "Import CSV": {"icon": "📥", "description": "批量导入交易记录"},
}

with st.sidebar:
    # Logo & branding
    st.markdown(
        """
        <div style="text-align:center;padding:20px 0 16px 0">
          <div style="font-size:2.5rem">💜</div>
          <div style="font-size:1.4rem;font-weight:800;
                      background:linear-gradient(135deg,#8B5CF6,#EC4899);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      background-clip:text">FinanceFlow</div>
          <div style="font-size:0.72rem;color:#64748B;letter-spacing:0.12em;
                      text-transform:uppercase;margin-top:2px">Personal Finance</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation
    st.markdown(
        '<div style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;'
        'color:#64748B;font-weight:600;margin-bottom:8px">Navigation</div>',
        unsafe_allow_html=True,
    )

    for page_name, meta in PAGES.items():
        is_active = st.session_state["current_page"] == page_name
        btn_style = (
            "background:linear-gradient(135deg,#8B5CF6,#EC4899);color:#fff;"
            if is_active
            else "background:transparent;"
        )
        if st.sidebar.button(
            f"{meta['icon']}  {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            help=meta["description"],
        ):
            st.session_state["current_page"] = page_name
            st.rerun()

    st.markdown("---")

    # Dark / Light mode toggle
    dark_label = "🌙 Dark Mode" if st.session_state["dark_mode"] else "☀️ Light Mode"
    if st.button(dark_label, key="theme_toggle", use_container_width=True):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick stats in sidebar
    _render_sidebar_stats()





# ── Page routing ──────────────────────────────────────────────────────────────
dark = st.session_state["dark_mode"]
page = st.session_state["current_page"]

# Inject dark/light body class
body_bg = "#0F0C29" if dark else "#F0EEFF"
text_color = "#E2E8F0" if dark else "#1E1B4B"
st.markdown(
    f"""
    <style>
      .stApp {{
        background: {"linear-gradient(135deg, #0F0C29 0%, #1A1645 50%, #1E1B4B 100%)" if dark
                     else "linear-gradient(135deg, #F0EEFF 0%, #F8F7FF 100%)"} !important;
        color: {text_color} !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Always-visible navigation fallback ───────────────────────────────────────
# Keep page switching available even when the Streamlit sidebar is collapsed.
st.markdown("**栏目导航 / Navigation**")
nav_columns = st.columns(len(PAGES))
for nav_column, (page_name, meta) in zip(nav_columns, PAGES.items()):
    with nav_column:
        if st.button(
            f"{meta['icon']} {page_name}",
            key=f"main_nav_{page_name}",
            use_container_width=True,
            type="primary" if page == page_name else "secondary",
        ):
            st.session_state["current_page"] = page_name
            st.rerun()

# Import and render the selected page
if page == "Dashboard":
    from pages.dashboard import render
    render(dark)
elif page == "Income":
    from pages.income import render
    render(dark)
elif page == "Expenses":
    from pages.expenses import render
    render(dark)
elif page == "Budgets":
    from pages.budgets import render
    render(dark)
elif page == "Analytics":
    from pages.analytics import render
    render(dark)
elif page == "Reports":
    from pages.reports import render
    render(dark)
elif page == "Import CSV":
    from pages.import_data import render
    render(dark)
