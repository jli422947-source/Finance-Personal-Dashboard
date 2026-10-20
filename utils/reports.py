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

    income_df = get_all_income()
    expenses_df = get_all_expenses()
    budgets_df = get_all_budgets()
    trends_df = get_monthly_trends(12)

    total_income = income_df["amount"].sum() if not income_df.empty else 0
    total_expenses = expenses_df["amount"].sum() if not expenses_df.empty else 0
    savings = total_income - total_expenses
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0

    summary_df = pd.DataFrame({
        "Metric": ["Total Income", "Total Expenses", "Net Savings", "Savings Rate", "Report Generated"],
        "Value": [
            f"${total_income:,.2f}", f"${total_expenses:,.2f}",
            f"${savings:,.2f}", f"{savings_rate:.1f}%",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ],
    })

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        _auto_width(writer, "Summary", summary_df)

        if not income_df.empty:
            income_out = income_df[["date", "amount", "source", "notes"]].copy()
            income_out.columns = ["Date", "Amount ($)", "Source", "Notes"]
            income_out.to_excel(writer, sheet_name="Income", index=False)
            _auto_width(writer, "Income", income_out)

        if not expenses_df.empty:
            exp_out = expenses_df[["date", "amount", "category", "description"]].copy()
            exp_out.columns = ["Date", "Amount ($)", "Category", "Description"]
            exp_out.to_excel(writer, sheet_name="Expenses", index=False)
            _auto_width(writer, "Expenses", exp_out)

        if not budgets_df.empty:
            bud_out = budgets_df[["month", "category", "amount"]].copy()
            bud_out.columns = ["Month", "Category", "Budget ($)"]
            bud_out.to_excel(writer, sheet_name="Budgets", index=False)
            _auto_width(writer, "Budgets", bud_out)

        if not trends_df.empty:
            trend_out = trends_df.copy()
            trend_out.columns = ["Month", "Income ($)", "Expenses ($)", "Savings ($)"]
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
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(max_len + 4, 50)


def generate_monthly_summary_csv(month: str) -> str:
    """Export one month's income and expenses with a stable CSV schema.

    Dates are normalized before filtering, and the output always contains a
    header row—even when the selected month has no transactions.
    """
    columns = ["date", "type", "category_or_source", "amount", "description"]
    income_df = get_all_income()
    expenses_df = get_all_expenses()
    frames = []

    if not income_df.empty:
        income_df = income_df.copy()
        income_df["date"] = pd.to_datetime(income_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        income_df = income_df[income_df["date"].str.startswith(month, na=False)].copy()
        if not income_df.empty:
            frames.append(pd.DataFrame({
                "date": income_df["date"],
                "type": "Income",
                "category_or_source": income_df["source"],
                "amount": income_df["amount"],
                "description": income_df["notes"].fillna("") if "notes" in income_df else "",
            }))

    if not expenses_df.empty:
        expenses_df = expenses_df.copy()
        expenses_df["date"] = pd.to_datetime(expenses_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        expenses_df = expenses_df[expenses_df["date"].str.startswith(month, na=False)].copy()
        if not expenses_df.empty:
            frames.append(pd.DataFrame({
                "date": expenses_df["date"],
                "type": "Expense",
                "category_or_source": expenses_df["category"],
                "amount": expenses_df["amount"],
                "description": expenses_df["description"].fillna("") if "description" in expenses_df else "",
            }))

    if not frames:
        return pd.DataFrame(columns=columns).to_csv(index=False, lineterminator="\n")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[columns].sort_values(["date", "type", "category_or_source"], kind="stable")
    return combined.to_csv(index=False, lineterminator="\n")
