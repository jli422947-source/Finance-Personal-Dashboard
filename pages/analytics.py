"""
Analytics page with interactive Plotly charts.
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd

from database.db import (
    get_all_expenses, get_all_income,
    get_monthly_category_expenses, get_monthly_trends,
    get_monthly_summary,
)
from utils.charts import (
    expense_pie_chart, income_vs_expense_bar,
    savings_trend_line, category_spending_bar,
    top_spending_categories, income_sources_pie,
)


def render(dark: bool = True):
    st.markdown('<div class="page-title">📈 Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Deep-dive into your financial patterns with interactive charts.</div>',
        unsafe_allow_html=True,
    )

    # ── Global filters ────────────────────────────────────────────────────────
    with st.expander("🔧 Chart Settings", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            months_back = st.slider("Months of history", 2, 24, 6)
        with col2:
            selected_month = st.selectbox(
                "Month for category breakdown",
                _available_months(),
                index=0,
            )

    income_df   = get_all_income()
    expenses_df = get_all_expenses()
    trends_df   = get_monthly_trends(months_back)
    cat_df      = get_monthly_category_expenses(selected_month)
    all_cat_df  = (
        expenses_df.groupby("category")["amount"].sum().reset_index().rename(
            columns={"amount": "total"}
        )
        if not expenses_df.empty else pd.DataFrame(columns=["category","total"])
    )

    # ── Row 1: Pie + Bar ──────────────────────────────────────────────────────
    st.markdown("### Spending Breakdown")
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"Expense distribution — {selected_month}")
        st.plotly_chart(expense_pie_chart(cat_df, dark), use_container_width=True)
    with c2:
        st.caption(f"Monthly income vs expenses — last {months_back} months")
        st.plotly_chart(income_vs_expense_bar(trends_df, dark), use_container_width=True)

    # ── Row 2: Savings + Category bar ────────────────────────────────────────
    st.markdown("### Trends & Category Analysis")
    c3, c4 = st.columns(2)
    with c3:
        st.caption(f"Savings trend — last {months_back} months")
        st.plotly_chart(savings_trend_line(trends_df, dark), use_container_width=True)
    with c4:
        st.caption("Category-wise spending (all time)")
        st.plotly_chart(category_spending_bar(all_cat_df, dark), use_container_width=True)

    # ── Row 3: Top categories + Income sources ────────────────────────────────
    st.markdown("### Top Spenders & Income Sources")
    c5, c6 = st.columns(2)
    with c5:
        top_n = st.slider("Show top N categories", 3, 8, 5, key="top_n_slider")
        st.plotly_chart(top_spending_categories(all_cat_df, top_n, dark), use_container_width=True)
    with c6:
        st.plotly_chart(income_sources_pie(income_df, dark), use_container_width=True)

    # ── Monthly stats table ────────────────────────────────────────────────────
    st.markdown("### Monthly Performance Summary")
    if not trends_df.empty:
        display = trends_df.copy().sort_values("month", ascending=False)
        display["savings_rate"] = display.apply(
            lambda r: f"{(r['savings']/r['income']*100):.1f}%" if r["income"] > 0 else "N/A",
            axis=1,
        )
        display["income"]   = display["income"].apply(lambda x: f"${x:,.2f}")
        display["expenses"] = display["expenses"].apply(lambda x: f"${x:,.2f}")
        display["savings"]  = display["savings"].apply(lambda x: f"${x:,.2f}")
        display.columns = ["Month","Income","Expenses","Savings","Savings Rate"]
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("Not enough data for a monthly summary. Add income and expense records to get started.")

    # ── Financial health score ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏆 Financial Health Score")
    _render_health_score(trends_df, all_cat_df, income_df)


def _render_health_score(trends_df, cat_df, income_df):
    """Simple rule-based financial health score (0–100)."""
    score = 0
    notes = []

    if trends_df.empty or income_df.empty:
        st.info("Add at least one month of data to calculate your financial health score.")
        return

    latest = trends_df.iloc[-1] if not trends_df.empty else None

    # Savings rate (max 40 pts)
    if latest is not None and latest["income"] > 0:
        sr = latest["savings"] / latest["income"] * 100
        if sr >= 30:
            score += 40; notes.append(("✅", f"Excellent savings rate: {sr:.1f}%", 40))
        elif sr >= 20:
            score += 30; notes.append(("✅", f"Good savings rate: {sr:.1f}%", 30))
        elif sr >= 10:
            score += 20; notes.append(("⚠️", f"Moderate savings rate: {sr:.1f}% (target 20%+)", 20))
        elif sr >= 0:
            score += 10; notes.append(("⚠️", f"Low savings rate: {sr:.1f}%", 10))
        else:
            notes.append(("🚨", "Spending exceeds income!", 0))

    # Expense diversity (max 20 pts — diversified spending = better planning)
    if not cat_df.empty:
        n_cats = len(cat_df)
        if n_cats >= 4:
            score += 20; notes.append(("✅", f"Good expense diversity ({n_cats} categories tracked)", 20))
        elif n_cats >= 2:
            score += 10; notes.append(("⚠️", f"Some expense diversity ({n_cats} categories)", 10))
        else:
            notes.append(("💡", "Track more expense categories for better insights", 0))

    # Income consistency (max 20 pts)
    if len(trends_df) >= 3:
        score += 20; notes.append(("✅", "3+ months of data — good tracking consistency", 20))
    elif len(trends_df) >= 1:
        score += 10; notes.append(("💡", "Keep recording — more data = better insights", 10))

    # Multiple income sources (max 20 pts)
    if not income_df.empty:
        n_sources = income_df["source"].nunique()
        if n_sources >= 3:
            score += 20; notes.append(("✅", f"{n_sources} income sources — well diversified", 20))
        elif n_sources >= 2:
            score += 10; notes.append(("💡", f"{n_sources} income sources", 10))
        else:
            notes.append(("💡", "Consider diversifying your income sources", 0))

    # Display score
    col_score, col_notes = st.columns([1, 3])
    with col_score:
        color = "#10B981" if score >= 70 else "#F59E0B" if score >= 40 else "#EF4444"
        grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
        st.markdown(
            f"""
            <div style="text-align:center;padding:24px;background:rgba(139,92,246,0.1);
                        border-radius:16px;border:1px solid rgba(139,92,246,0.3)">
              <div style="font-size:3.5rem;font-weight:900;color:{color}">{score}</div>
              <div style="font-size:1.2rem;font-weight:700;color:{color}">Grade: {grade}</div>
              <div style="font-size:0.78rem;color:#94A3B8;margin-top:6px">out of 100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(score / 100)

    with col_notes:
        for emoji, text, pts in notes:
            pts_str = f"+{pts}" if pts > 0 else "±0"
            st.markdown(
                f'<div class="insight-card">{emoji} {text} <span style="float:right;color:#8B5CF6;font-weight:700">{pts_str} pts</span></div>',
                unsafe_allow_html=True,
            )


def _available_months() -> list:
    now = datetime.now()
    months = []
    for i in range(12):
        y = now.year - (1 if now.month - i <= 0 else 0)
        m = (now.month - i - 1) % 12 + 1
        months.append(date(y, m, 1).strftime("%Y-%m"))
    return months
