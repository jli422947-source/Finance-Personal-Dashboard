"""
Reports page — export data, download reports, view transaction history.
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd

from database.db import get_all_income, get_all_expenses, get_all_budgets, get_monthly_trends
from utils.reports import generate_excel_report, generate_monthly_summary_csv


def render(dark: bool = True):
    st.markdown('<div class="page-title">📄 Reports</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Export your financial data and generate detailed reports.</div>',
        unsafe_allow_html=True,
    )

    tab_export, tab_history = st.tabs(["📥 Export Reports", "🔍 Full Transaction History"])

    with tab_export:
        _render_exports()

    with tab_history:
        _render_full_history(dark)


def _render_exports():
    st.markdown("### Download Reports")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="kpi-card">
              <div class="kpi-icon">📊</div>
              <div class="kpi-label">Full Excel Report</div>
              <div class="kpi-sub">All data — income, expenses, budgets &amp; trends</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            excel_bytes = generate_excel_report()
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_bytes,
                file_name=f"finance_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error generating Excel report: {e}")

    with col2:
        st.markdown(
            """
            <div class="kpi-card amber">
              <div class="kpi-icon">📅</div>
              <div class="kpi-label">Monthly CSV Export</div>
              <div class="kpi-sub">Income + expenses for a specific month</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        export_month = st.selectbox("Select month", _available_months(), key="csv_month")
        csv_data = generate_monthly_summary_csv(export_month)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"transactions_{export_month}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### Report Summary")
    _render_report_summary()


def _render_report_summary():
    income_df   = get_all_income()
    expenses_df = get_all_expenses()
    budgets_df  = get_all_budgets()

    total_income   = income_df["amount"].sum()   if not income_df.empty   else 0
    total_expenses = expenses_df["amount"].sum() if not expenses_df.empty else 0
    savings        = total_income - total_expenses
    savings_rate   = (savings / total_income * 100) if total_income > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Income Records",   len(income_df))
    c2.metric("Expense Records",  len(expenses_df))
    c3.metric("Budget Entries",   len(budgets_df))
    c4.metric("Net Savings",      f"${savings:,.2f}")

    st.markdown("---")

    # Trends table
    trends = get_monthly_trends(12)
    if not trends.empty:
        st.markdown("### 12-Month Summary Table")
        t = trends.copy().sort_values("month", ascending=False)
        t["savings_rate"] = t.apply(
            lambda r: f"{r['savings']/r['income']*100:.1f}%" if r["income"] > 0 else "N/A",
            axis=1,
        )
        for col in ["income","expenses","savings"]:
            t[col] = t[col].apply(lambda x: f"${x:,.2f}")
        t.columns = ["Month","Income","Expenses","Savings","Savings Rate"]
        st.dataframe(t, use_container_width=True, hide_index=True)


def _render_full_history(dark: bool):
    st.markdown("### Complete Transaction History")

    income_df   = get_all_income()
    expenses_df = get_all_expenses()

    if income_df.empty and expenses_df.empty:
        st.markdown(
            '<div class="empty-state"><div class="emoji">📭</div>'
            '<h3>No transactions yet</h3>'
            '<p>Start recording income and expenses to see them here.</p></div>',
            unsafe_allow_html=True,
        )
        return

    # Combine all transactions
    rows = []
    if not income_df.empty:
        for _, r in income_df.iterrows():
            rows.append({
                "Date": r["date"], "Type": "Income",
                "Category/Source": r["source"],
                "Description": r.get("notes","") or "",
                "Amount": r["amount"], "Sign": "+"
            })
    if not expenses_df.empty:
        for _, r in expenses_df.iterrows():
            rows.append({
                "Date": r["date"], "Type": "Expense",
                "Category/Source": r["category"],
                "Description": r.get("description","") or "",
                "Amount": r["amount"], "Sign": "-"
            })

    combined = pd.DataFrame(rows).sort_values("Date", ascending=False)

    # ── Filters ──────────────────────────────────────────────────────────────
    with st.expander("🔍 Filter Transactions", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            type_filter = st.selectbox("Type", ["All", "Income", "Expense"])
        with fc2:
            search = st.text_input("Search", placeholder="keyword...")
        with fc3:
            min_d = pd.to_datetime(combined["Date"]).min().date()
            max_d = pd.to_datetime(combined["Date"]).max().date()
            date_range = st.date_input("Date range", value=(min_d, max_d),
                                       min_value=min_d, max_value=max_d)
        with fc4:
            min_amt = st.number_input("Min Amount ($)", min_value=0.0, value=0.0, step=1.0)

    filtered = combined.copy()
    if type_filter != "All":
        filtered = filtered[filtered["Type"] == type_filter]
    if search:
        mask = (
            filtered["Category/Source"].str.contains(search, case=False, na=False)
            | filtered["Description"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        s, e = date_range
        filtered = filtered[
            (filtered["Date"] >= str(s)) & (filtered["Date"] <= str(e))
        ]
    filtered = filtered[filtered["Amount"] >= min_amt]

    # Summary
    inc_total = filtered[filtered["Type"]=="Income"]["Amount"].sum()
    exp_total = filtered[filtered["Type"]=="Expense"]["Amount"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Filtered Records", len(filtered))
    c2.metric("Income",  f"${inc_total:,.2f}")
    c3.metric("Expenses",f"${exp_total:,.2f}")

    # Display
    display = filtered.drop(columns=["Sign"]).copy()
    display["Amount"] = display.apply(
        lambda r: f"+${r['Amount']:,.2f}" if r["Type"]=="Income" else f"-${r['Amount']:,.2f}",
        axis=1,
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    csv = filtered.drop(columns=["Sign"]).to_csv(index=False)
    st.download_button("📥 Export filtered as CSV", csv,
                       f"transactions_filtered_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")


def _available_months() -> list:
    now = datetime.now()
    months = []
    for i in range(24):
        y = now.year - (1 if now.month - i <= 0 else 0)
        m = (now.month - i - 1) % 12 + 1
        months.append(date(y, m, 1).strftime("%Y-%m"))
    return months
