"""
Report generation utilities.
Handles Excel export and downloadable report creation.
"""

import io
import pandas as pd
from datetime import datetime
from database.db import get_all_income, get_all_expenses, get_all_budgets, get_monthly_trends


def generate_excel_report() -> bytes:
    """
    Generate a comprehensive Excel workbook with:
      - Summary sheet
      - Income sheet
      - Expenses sheet
      - Budgets sheet
      - Monthly Trends sheet
    Returns raw bytes for Streamlit download_button.
    """
    buffer = io.BytesIO()

    income_df   = get_all_income()
    expenses_df = get_all_expenses()
    budgets_df  = get_all_budgets()
    trends_df   = get_monthly_trends(12)

    # ── Summary ───────────────────────────────────────────────────────────────
    total_income   = income_df["amount"].sum()   if not income_df.empty   else 0
    total_expenses = expenses_df["amount"].sum() if not expenses_df.empty else 0
    savings        = total_income - total_expenses
    savings_rate   = (savings / total_income * 100) if total_income > 0 else 0

    summary_data = {
        "Metric":  ["Total Income",  "Total Expenses", "Net Savings", "Savings Rate",
                    "Report Generated"],
        "Value":   [f"${total_income:,.2f}", f"${total_expenses:,.2f}",
                    f"${savings:,.2f}", f"{savings_rate:.1f}%",
                    datetime.now().strftime("%Y-%m-%d %H:%M")],
    }
    summary_df = pd.DataFrame(summary_data)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Summary
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        _auto_width(writer, "Summary", summary_df)

        # Income
        if not income_df.empty:
            income_out = income_df[["date","amount","source","notes"]].copy()
            income_out.columns = ["Date","Amount ($)","Source","Notes"]
            income_out.to_excel(writer, sheet_name="Income", index=False)
            _auto_width(writer, "Income", income_out)

        # Expenses
        if not expenses_df.empty:
            exp_out = expenses_df[["date","amount","category","description"]].copy()
            exp_out.columns = ["Date","Amount ($)","Category","Description"]
            exp_out.to_excel(writer, sheet_name="Expenses", index=False)
            _auto_width(writer, "Expenses", exp_out)

        # Budgets
        if not budgets_df.empty:
            bud_out = budgets_df[["month","category","amount"]].copy()
            bud_out.columns = ["Month","Category","Budget ($)"]
            bud_out.to_excel(writer, sheet_name="Budgets", index=False)
            _auto_width(writer, "Budgets", bud_out)

        # Monthly Trends
        if not trends_df.empty:
            trend_out = trends_df.copy()
            trend_out.columns = ["Month","Income ($)","Expenses ($)","Savings ($)"]
            trend_out.to_excel(writer, sheet_name="Monthly Trends", index=False)
            _auto_width(writer, "Monthly Trends", trend_out)

    return buffer.getvalue()


def _auto_width(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame):
    """Auto-fit column widths in an Excel sheet."""
    ws = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns, 1):
        max_len = max(
            len(str(col)),
            df[col].astype(str).map(len).max() if not df.empty else 0,
        )
        ws.column_dimensions[
            ws.cell(row=1, column=idx).column_letter
        ].width = min(max_len + 4, 50)


def generate_monthly_summary_csv(month: str) -> str:
    """Export a month's income + expenses as CSV string."""
    income_df   = get_all_income()
    expenses_df = get_all_expenses()

    if not income_df.empty:
        income_df = income_df[
            income_df["date"].str.startswith(month)
        ].copy()
        income_df["type"] = "Income"
        income_df.rename(columns={"source": "category_or_source"}, inplace=True)

    if not expenses_df.empty:
        expenses_df = expenses_df[
            expenses_df["date"].str.startswith(month)
        ].copy()
        expenses_df["type"] = "Expense"
        expenses_df.rename(columns={"category": "category_or_source"}, inplace=True)

    combined = pd.concat(
        [
            income_df[["date","amount","type","category_or_source"]]
            if not income_df.empty else pd.DataFrame(),
            expenses_df[["date","amount","type","category_or_source"]]
            if not expenses_df.empty else pd.DataFrame(),
        ],
        ignore_index=True,
    )

    if combined.empty:
        return "No data for selected month."

    combined = combined.sort_values("date")
    return combined.to_csv(index=False)
