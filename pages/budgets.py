"""
Budget management page.
Create monthly budgets, compare with actual spending, show progress bars.
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd

from database.db import (
    set_budget, get_budgets_for_month, get_all_budgets,
    get_monthly_category_expenses, delete_budget,
)
from utils.charts import budget_vs_actual_bar


CATEGORIES = [
    "Food", "Transport", "Shopping", "Entertainment",
    "Bills", "Education", "Health", "Other",
]

CATEGORY_ICONS = {
    "Food": "🍔", "Transport": "🚗", "Shopping": "🛍️",
    "Entertainment": "🎬", "Bills": "📄", "Education": "📚",
    "Health": "🏥", "Other": "📦",
}


def render(dark: bool = True):
    st.markdown('<div class="page-title">🎯 Budgets</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Set monthly spending limits and track your progress in real time.</div>',
        unsafe_allow_html=True,
    )

    tab_set, tab_track, tab_history = st.tabs(["⚙️ Set Budgets", "📊 Track Progress", "📋 All Budgets"])

    with tab_set:
        _render_set_budgets()

    with tab_track:
        _render_track_progress(dark)

    with tab_history:
        _render_all_budgets()


def _render_set_budgets():
    st.markdown("### Set Monthly Budget")
    st.caption("Create or update spending limits per category for any month.")

    col1, col2 = st.columns([1, 2])
    with col1:
        budget_month = st.date_input(
            "Month",
            value=date.today().replace(day=1),
            format="YYYY-MM-DD",
        )
        month_str = budget_month.strftime("%Y-%m")

    # Load existing budgets for that month
    existing = get_budgets_for_month(month_str)
    existing_map = dict(zip(existing["category"], existing["amount"])) if not existing.empty else {}

    st.markdown(f"**Setting budgets for: `{month_str}`**")
    st.markdown("Enter $0 to skip a category.")

    with st.form("budget_form"):
        budget_inputs = {}
        cols = st.columns(2)
        for i, cat in enumerate(CATEGORIES):
            icon = CATEGORY_ICONS.get(cat, "📦")
            current_val = existing_map.get(cat, 0.0)
            with cols[i % 2]:
                budget_inputs[cat] = st.number_input(
                    f"{icon} {cat}",
                    min_value=0.0, max_value=1_000_000.0,
                    value=float(current_val), step=10.0, format="%.2f",
                    key=f"budget_{cat}",
                )

        submitted = st.form_submit_button("💾 Save Budgets", use_container_width=True)

    if submitted:
        saved = 0
        for cat, amt in budget_inputs.items():
            if amt > 0:
                if set_budget(month_str, cat, round(amt, 2)):
                    saved += 1
        if saved > 0:
            st.success(f"✅ Saved budgets for {saved} categories in {month_str}!")
            st.rerun()
        else:
            st.warning("No budgets saved. Enter amounts greater than $0.")


def _render_track_progress(dark: bool):
    st.markdown("### Budget Progress Tracker")

    # Month selector
    col_select, _ = st.columns([1, 2])
    with col_select:
        track_month = st.selectbox(
            "Select Month",
            _available_months(),
            index=0,
        )

    budgets_df  = get_budgets_for_month(track_month)
    expenses_df = get_monthly_category_expenses(track_month)

    if budgets_df.empty:
        st.markdown(
            '<div class="empty-state"><div class="emoji">🎯</div>'
            '<h3>No budgets set for this month</h3>'
            '<p>Go to "Set Budgets" to create spending limits.</p></div>',
            unsafe_allow_html=True,
        )
        return

    # Merge actual
    actual_map = dict(zip(expenses_df["category"], expenses_df["total"])) if not expenses_df.empty else {}

    total_budget = budgets_df["amount"].sum()
    total_actual = sum(actual_map.values())
    total_remaining = total_budget - total_actual

    # ── Summary KPIs ─────────────────────────────────────────────────────────
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Budget",    f"${total_budget:,.0f}")
    k2.metric("Total Spent",     f"${total_actual:,.0f}")
    k3.metric("Remaining",       f"${total_remaining:,.0f}",
              delta=f"{(total_remaining/total_budget*100):.1f}% left" if total_budget > 0 else "N/A",
              delta_color="normal" if total_remaining >= 0 else "inverse")

    st.markdown("---")

    # ── Per-category progress bars ────────────────────────────────────────────
    for _, row in budgets_df.iterrows():
        cat    = row["category"]
        budget = row["amount"]
        actual = actual_map.get(cat, 0.0)
        pct    = min(actual / budget, 1.0) if budget > 0 else 0.0
        icon   = CATEGORY_ICONS.get(cat, "📦")
        remaining = budget - actual
        over = actual > budget

        col_label, col_bar = st.columns([1, 3])
        with col_label:
            st.markdown(
                f"**{icon} {cat}**<br>"
                f"<span style='font-size:0.78rem;color:#94A3B8'>"
                f"${actual:,.0f} / ${budget:,.0f}</span>",
                unsafe_allow_html=True,
            )
        with col_bar:
            if over:
                bar_val = 1.0
                st.progress(bar_val)
                over_by = actual - budget
                st.markdown(
                    f'<span class="budget-warn">⚠️ Over budget by ${over_by:,.2f}!</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.progress(pct)
                left_pct = (1 - pct) * 100
                status_color = "#EF4444" if pct > 0.9 else "#F59E0B" if pct > 0.75 else "#10B981"
                st.markdown(
                    f'<span style="font-size:0.78rem;color:{status_color}">'
                    f"${remaining:,.2f} remaining ({left_pct:.0f}%)</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    st.markdown("---")
    # Budget vs actual chart
    st.plotly_chart(budget_vs_actual_bar(budgets_df, expenses_df, dark), use_container_width=True)


def _render_all_budgets():
    st.markdown("### All Budget Records")

    df = get_all_budgets()
    if df.empty:
        st.markdown(
            '<div class="empty-state"><div class="emoji">📋</div>'
            '<h3>No budgets created yet</h3>'
            '<p>Set up your first budget to get started.</p></div>',
            unsafe_allow_html=True,
        )
        return

    display = df[["id","month","category","amount"]].copy()
    display["category"] = display["category"].apply(
        lambda c: f"{CATEGORY_ICONS.get(c,'📦')} {c}"
    )
    display["amount"] = display["amount"].apply(lambda x: f"${x:,.2f}")
    display.columns = ["ID","Month","Category","Budget ($)"]
    st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander("🗑️ Delete a Budget"):
        del_id = st.number_input("Enter Budget ID to delete", min_value=1, step=1, key="del_bud_id")
        if st.button("Delete", key="del_bud_btn"):
            if delete_budget(int(del_id)):
                st.success(f"Budget #{int(del_id)} deleted.")
                st.rerun()
            else:
                st.error("Could not delete.")


def _available_months() -> list:
    """Return last 12 months as YYYY-MM strings, most recent first."""
    now = datetime.now()
    months = []
    for i in range(12):
        month_dt = date(now.year - (1 if now.month - i <= 0 else 0),
                        (now.month - i - 1) % 12 + 1, 1)
        months.append(month_dt.strftime("%Y-%m"))
    return months
