"""
Income management page.
Add, view, filter and delete income records.
"""

import streamlit as st
from datetime import date, datetime
import pandas as pd

from database.db import add_income, get_all_income, get_income_by_date_range, delete_income
from utils.charts import income_sources_pie


COMMON_SOURCES = [
    "Salary", "Freelance", "Business", "Investment Returns",
    "Rental Income", "Dividends", "Bonus", "Gift", "Other",
]


def render(dark: bool = True):
    st.markdown('<div class="page-title">💰 Income</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Track all your income sources and stay on top of your earnings.</div>',
        unsafe_allow_html=True,
    )

    tab_add, tab_view, tab_chart = st.tabs(["➕ Add Income", "📋 Transaction History", "📊 Analytics"])

    with tab_add:
        _render_add_form()

    with tab_view:
        _render_history(dark)

    with tab_chart:
        _render_charts(dark)


def _render_add_form():
    st.markdown("### Add New Income")

    with st.form("add_income_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            income_date = st.date_input("Date *", value=date.today(), max_value=date.today())
            amount = st.number_input(
                "Amount ($) *",
                min_value=0.01, max_value=10_000_000.0,
                step=0.01, format="%.2f",
                help="Enter the income amount in dollars.",
            )

        with col2:
            source_option = st.selectbox("Source *", COMMON_SOURCES + ["Custom..."])
            if source_option == "Custom...":
                source = st.text_input("Custom Source *", placeholder="e.g. Consulting Project")
            else:
                source = source_option

        notes = st.text_area("Notes (optional)", placeholder="Any additional details...", max_chars=300)

        submitted = st.form_submit_button("💾 Save Income", use_container_width=True)

    if submitted:
        # Validation
        errors = []
        if amount <= 0:
            errors.append("Amount must be greater than 0.")
        if not source.strip():
            errors.append("Source cannot be empty.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            success = add_income(
                date=income_date.strftime("%Y-%m-%d"),
                amount=round(amount, 2),
                source=source.strip(),
                notes=notes.strip(),
            )
            if success:
                st.success(f"✅ Income of **${amount:,.2f}** from **{source}** added successfully!")
                st.balloons()
            else:
                st.error("❌ Failed to save income. Please try again.")


def _render_history(dark: bool):
    st.markdown("### Transaction History")

    df = get_all_income()

    if df.empty:
        st.markdown(
            '<div class="empty-state"><div class="emoji">💸</div>'
            '<h3>No income records found</h3>'
            '<p>Use the "Add Income" tab to record your first income entry.</p></div>',
            unsafe_allow_html=True,
        )
        return

    # ── Filters ──────────────────────────────────────────────────────────────
    with st.expander("🔍 Filter & Search", expanded=False):
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            search = st.text_input("Search source / notes", placeholder="Type to search...")
        with fcol2:
            min_date = pd.to_datetime(df["date"]).min().date()
            max_date = pd.to_datetime(df["date"]).max().date()
            date_range = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        with fcol3:
            all_sources = ["All"] + sorted(df["source"].unique().tolist())
            source_filter = st.selectbox("Source", all_sources)

    # Apply filters
    filtered = df.copy()
    if search:
        mask = (
            filtered["source"].str.contains(search, case=False, na=False)
            | filtered["notes"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["date"] >= str(start)) & (filtered["date"] <= str(end))
        ]
    if source_filter != "All":
        filtered = filtered[filtered["source"] == source_filter]

    # ── Summary row ──────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Records", len(filtered))
    col2.metric("Total Amount", f"${filtered['amount'].sum():,.2f}")
    col3.metric("Average",      f"${filtered['amount'].mean():,.2f}" if not filtered.empty else "$0.00")

    st.markdown("---")

    if filtered.empty:
        st.info("No records match your filters.")
        return

    # Display table
    display_df = filtered[["id","date","source","amount","notes"]].copy()
    display_df.columns = ["ID","Date","Source","Amount ($)","Notes"]
    display_df["Amount ($)"] = display_df["Amount ($)"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ── Delete ────────────────────────────────────────────────────────────────
    with st.expander("🗑️ Delete a Record"):
        del_id = st.number_input("Enter Record ID to delete", min_value=1, step=1, key="del_income_id")
        if st.button("Delete", key="del_income_btn"):
            if int(del_id) in filtered["id"].values:
                if delete_income(int(del_id)):
                    st.success(f"Record #{int(del_id)} deleted.")
                    st.rerun()
                else:
                    st.error("Could not delete record.")
            else:
                st.warning("ID not found in current filtered view.")

    # ── Download ──────────────────────────────────────────────────────────────
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="📥 Export as CSV",
        data=csv,
        file_name=f"income_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


def _render_charts(dark: bool):
    df = get_all_income()
    if df.empty:
        st.markdown(
            '<div class="empty-state"><div class="emoji">📊</div>'
            '<h3>No data to visualise yet</h3>'
            '<p>Add income records first.</p></div>',
            unsafe_allow_html=True,
        )
        return

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(income_sources_pie(df, dark), use_container_width=True)
    with col2:
        # Monthly income trend
        df["month"] = df["date"].str[:7]
        monthly = df.groupby("month")["amount"].sum().reset_index()
        monthly.columns = ["month","income"]
        monthly["expenses"] = 0
        monthly["savings"] = monthly["income"]
        from utils.charts import income_vs_expense_bar
        st.plotly_chart(income_vs_expense_bar(monthly, dark), use_container_width=True)

    # Top sources table
    st.markdown("### Top Income Sources (All Time)")
    top = df.groupby("source")["amount"].agg(["sum","count"]).reset_index()
    top.columns = ["Source","Total ($)","# Records"]
    top = top.sort_values("Total ($)", ascending=False)
    top["Total ($)"] = top["Total ($)"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(top, use_container_width=True, hide_index=True)
