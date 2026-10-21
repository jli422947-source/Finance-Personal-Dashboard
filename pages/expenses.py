"""
Expense management page.
Add, view, filter and delete expense records.
"""

import streamlit as st
from datetime import date, datetime
import pandas as pd

from database.db import (
    add_expense, get_all_expenses,
    get_expenses_by_date_range, delete_expense,
)
from utils.charts import expense_pie_chart, category_spending_bar


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
    st.markdown('<div class="page-title">💸 Expenses</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Monitor where your money goes and stay within budget.</div>',
        unsafe_allow_html=True,
    )

    tab_add, tab_view, tab_chart = st.tabs(["➕ Add Expense", "📋 Transaction History", "📊 Analytics"])

    with tab_add:
        _render_add_form()

    with tab_view:
        _render_history(dark)

    with tab_chart:
        _render_charts(dark)


def _render_add_form():
    st.markdown("### Record a New Expense")

    # Category quick-select buttons
    st.markdown("**Select Category:**")
    btn_cols = st.columns(len(CATEGORIES))
    selected_cat = st.session_state.get("selected_expense_cat", CATEGORIES[0])

    for i, cat in enumerate(CATEGORIES):
        with btn_cols[i]:
            icon = CATEGORY_ICONS.get(cat, "📦")
            is_active = selected_cat == cat
            label = f"{icon} {cat}" if not is_active else f"✅ {cat}"
            if st.button(label, key=f"cat_btn_{cat}", use_container_width=True):
                st.session_state["selected_expense_cat"] = cat
                st.rerun()

    selected_cat = st.session_state.get("selected_expense_cat", CATEGORIES[0])
    st.markdown("---")

    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            expense_date = st.date_input("Date *", value=date.today(), max_value=date.today())
            amount = st.number_input(
                "Amount ($) *",
                min_value=0.01, max_value=1_000_000.0,
                step=0.01, format="%.2f",
            )

        with col2:
            category = st.selectbox(
                "Category *", CATEGORIES,
                index=CATEGORIES.index(selected_cat),
            )
            description = st.text_input(
                "Description (optional)",
                placeholder="e.g. Grocery run at Whole Foods",
            )

        submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)

    if submitted:
        errors = []
        if amount <= 0:
            errors.append("Amount must be greater than 0.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            success = add_expense(
                date=expense_date.strftime("%Y-%m-%d"),
                amount=round(amount, 2),
                category=category,
                description=description.strip(),
            )
            if success:
                icon = CATEGORY_ICONS.get(category, "📦")
                st.success(f"✅ Expense of **${amount:,.2f}** in **{icon} {category}** saved!")
            else:
                st.error("❌ Failed to save expense. Please try again.")


def _render_history(dark: bool):
    st.markdown("### Transaction History")

    df = get_all_expenses()

    if df.empty:
        st.markdown(
            '<div class="empty-state"><div class="emoji">🧾</div>'
            '<h3>No expense records yet</h3>'
            '<p>Use the "Add Expense" tab to log your first expense.</p></div>',
            unsafe_allow_html=True,
        )
        return

    # ── Filters ──────────────────────────────────────────────────────────────
    with st.expander("🔍 Filter & Search", expanded=False):
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            search = st.text_input("Search description", placeholder="Search...")
        with fcol2:
            min_d = pd.to_datetime(df["date"]).min().date()
            latest_record_date = pd.to_datetime(df["date"]).max().date()
            # Allow reviewing calendar dates after the latest transaction.
            max_d = max(latest_record_date, date.today())
            date_range = st.date_input(
                "Date range",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d,
                help="The end date can extend beyond the latest transaction up to today.",
            )
        with fcol3:
            cat_options = ["All"] + CATEGORIES
            cat_filter = st.selectbox("Category", cat_options)

    filtered = df.copy()
    if search:
        filtered = filtered[
            filtered["description"].str.contains(search, case=False, na=False)
        ]
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        s, e = date_range
        filtered = filtered[
            (filtered["date"] >= str(s)) & (filtered["date"] <= str(e))
        ]
    if cat_filter != "All":
        filtered = filtered[filtered["category"] == cat_filter]

    # ── Summary ───────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Records", len(filtered))
    col2.metric("Total Spent", f"${filtered['amount'].sum():,.2f}")
    col3.metric("Average",     f"${filtered['amount'].mean():,.2f}" if not filtered.empty else "$0.00")

    st.markdown("---")

    if filtered.empty:
        st.info("No records match your filters.")
        return

    # Add category icons to display
    display_df = filtered[["id","date","category","amount","description"]].copy()
    display_df["category"] = display_df["category"].apply(
        lambda c: f"{CATEGORY_ICONS.get(c,'📦')} {c}"
    )
    display_df.columns = ["ID","Date","Category","Amount ($)","Description"]
    display_df["Amount ($)"] = display_df["Amount ($)"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ── Delete ────────────────────────────────────────────────────────────────
    with st.expander("🗑️ Delete a Record"):
        del_id = st.number_input("Enter Record ID to delete", min_value=1, step=1, key="del_exp_id")
        if st.button("Delete", key="del_exp_btn"):
            if int(del_id) in filtered["id"].values:
                if delete_expense(int(del_id)):
                    st.success(f"Record #{int(del_id)} deleted.")
                    st.rerun()
                else:
                    st.error("Could not delete record.")
            else:
                st.warning("ID not found in current filtered view.")

    csv = filtered.to_csv(index=False)
    st.download_button(
        "📥 Export as CSV", csv,
        file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


def _render_charts(dark: bool):
    df = get_all_expenses()
    if df.empty:
        st.markdown(
            '<div class="empty-state"><div class="emoji">📊</div>'
            '<h3>No expense data yet</h3>'
            '<p>Add some expenses to see your spending breakdown.</p></div>',
            unsafe_allow_html=True,
        )
        return

    cat_totals = df.groupby("category")["amount"].sum().reset_index()
    cat_totals.columns = ["category","total"]

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(expense_pie_chart(cat_totals, dark), use_container_width=True)
    with col2:
        st.plotly_chart(category_spending_bar(cat_totals, dark), use_container_width=True)

    # Category breakdown table
    st.markdown("### Spending by Category")
    total_spend = cat_totals["total"].sum()
    cat_totals["% of Total"] = (cat_totals["total"] / total_spend * 100).round(1).astype(str) + "%"
    cat_totals["total"] = cat_totals["total"].apply(lambda x: f"${x:,.2f}")
    cat_totals.columns = ["Category","Total ($)","% of Total"]
    cat_totals["Category"] = cat_totals["Category"].apply(
        lambda c: f"{CATEGORY_ICONS.get(c,'📦')} {c}"
    )
    st.dataframe(cat_totals, use_container_width=True, hide_index=True)
