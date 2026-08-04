"""
Dashboard page — summary KPI cards and current-month overview.
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd

from database.db import (
    get_monthly_summary,
    get_monthly_category_expenses,
    get_monthly_trends,
    get_all_income,
    get_all_expenses,
)
from utils.charts import (
    income_vs_expense_bar,
    savings_trend_line,
    expense_pie_chart,
)


def _kpi_card(label: str, value: str, icon: str, sub: str = "", card_class: str = "") -> str:
    return f"""
    <div class="kpi-card {card_class}">
      <div class="kpi-icon">{icon}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}
    </div>
    """


def render(dark: bool = True):
    st.markdown('<div class="page-title">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-subtitle">Welcome back! Here\'s your financial snapshot for {datetime.now().strftime("%B %Y")}.</div>',
        unsafe_allow_html=True,
    )

    current_month = datetime.now().strftime("%Y-%m")
    summary = get_monthly_summary(current_month)

    total_income   = summary["income"]
    total_expense  = summary["expenses"]
    savings        = summary["savings"]
    savings_rate   = summary["savings_rate"]

    # Budget remaining (compare with all budgets for month)
    from database.db import get_budgets_for_month
    budgets_df = get_budgets_for_month(current_month)
    total_budget    = budgets_df["amount"].sum() if not budgets_df.empty else 0
    remaining_budget = total_budget - total_expense

    # ── KPI Row ──────────────────────────────────────────────────────────────
    cols = st.columns(5)
    kpis = [
        ("Total Income",     f"${total_income:,.0f}",    "💰", "This month",   "green"),
        ("Total Expenses",   f"${total_expense:,.0f}",   "💸", "This month",   "red"),
        ("Net Savings",      f"${savings:,.0f}",         "🏦", "Income − Exp", "" if savings >= 0 else "red"),
        ("Savings Rate",     f"{savings_rate:.1f}%",     "📈", "of income",    "green" if savings_rate >= 20 else "amber"),
        ("Budget Remaining", f"${remaining_budget:,.0f}","🎯", "vs. budget",   "green" if remaining_budget >= 0 else "red"),
    ]
    for col, (label, val, icon, sub, cls) in zip(cols, kpis):
        with col:
            st.markdown(_kpi_card(label, val, icon, sub, cls), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Trends & Pie ─────────────────────────────────────────────────────────
    trends_df = get_monthly_trends(6)
    cat_df    = get_monthly_category_expenses(current_month)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.plotly_chart(income_vs_expense_bar(trends_df, dark), use_container_width=True)
    with col_right:
        st.plotly_chart(expense_pie_chart(cat_df, dark), use_container_width=True)

    # ── Savings trend + insights ──────────────────────────────────────────────
    col_chart, col_insights = st.columns([3, 2])
    with col_chart:
        st.plotly_chart(savings_trend_line(trends_df, dark), use_container_width=True)

    with col_insights:
        st.markdown("### 💡 Monthly Insights")
        _render_insights(summary, cat_df)

    # ── Recent transactions ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🕒 Recent Transactions")
    _render_recent(current_month)


def _render_insights(summary: dict, cat_df: pd.DataFrame):
    insights = []

    sr = summary["savings_rate"]
    if sr >= 30:
        insights.append(("🌟", "Excellent savings rate!", f"You're saving {sr:.1f}% of your income — well above the 20% benchmark."))
    elif sr >= 20:
        insights.append(("✅", "Good savings habit!", f"Savings rate of {sr:.1f}% meets the recommended 20% target."))
    elif sr > 0:
        insights.append(("⚠️", "Room to save more", f"Your savings rate is {sr:.1f}%. Aim for at least 20%."))
    elif summary["income"] > 0:
        insights.append(("🚨", "Overspending alert!", "Your expenses exceed your income this month."))

    if not cat_df.empty:
        top_cat = cat_df.iloc[0]
        pct = top_cat["total"] / summary["expenses"] * 100 if summary["expenses"] > 0 else 0
        insights.append(("📌", f"Top expense: {top_cat['category']}",
                         f"${top_cat['total']:,.0f} — {pct:.0f}% of total spending"))

    if summary["income"] == 0:
        insights.append(("💡", "No income recorded", "Add your income to get started with insights."))

    if not insights:
        insights.append(("📋", "Keep tracking!", "Add more transactions to unlock financial insights."))

    for emoji, title, body in insights:
        st.markdown(
            f'<div class="insight-card"><b>{emoji} {title}</b><br><span style="color:#94A3B8;font-size:0.85rem">{body}</span></div>',
            unsafe_allow_html=True,
        )


def _render_recent(month: str):
    income_df   = get_all_income()
    expenses_df = get_all_expenses()

    rows = []
    if not income_df.empty:
        inc = income_df[income_df["date"].str.startswith(month)].head(5)
        for _, r in inc.iterrows():
            rows.append({"Date": r["date"], "Type": "Income ↑", "Description": r["source"],
                         "Amount": f"+${r['amount']:,.2f}"})
    if not expenses_df.empty:
        exp = expenses_df[expenses_df["date"].str.startswith(month)].head(5)
        for _, r in exp.iterrows():
            rows.append({"Date": r["date"], "Type": "Expense ↓", "Description": r.get("description") or r["category"],
                         "Amount": f"-${r['amount']:,.2f}"})

    if not rows:
        st.markdown(
            '<div class="empty-state"><div class="emoji">📭</div>'
            '<h3>No transactions this month</h3>'
            '<p>Add income or expenses to see them here.</p></div>',
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(rows).sort_values("Date", ascending=False).head(10)
    st.dataframe(df, use_container_width=True, hide_index=True)
