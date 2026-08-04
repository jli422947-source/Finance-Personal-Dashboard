"""
Database module for Personal Finance Dashboard.
Handles SQLite operations for income, expenses, and budgets.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Income table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            source TEXT NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(month, category)
        )
    """)

    conn.commit()
    conn.close()


# ── Income CRUD ──────────────────────────────────────────────────────────────

def add_income(date: str, amount: float, source: str, notes: str = "") -> bool:
    """Insert a new income record."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO income (date, amount, source, notes) VALUES (?, ?, ?, ?)",
            (date, amount, source, notes),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding income: {e}")
        return False


def get_all_income() -> pd.DataFrame:
    """Retrieve all income records as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM income ORDER BY date DESC", conn
    )
    conn.close()
    return df


def get_income_by_date_range(start: str, end: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM income WHERE date BETWEEN ? AND ? ORDER BY date DESC",
        conn, params=(start, end),
    )
    conn.close()
    return df


def delete_income(record_id: int) -> bool:
    try:
        conn = get_connection()
        conn.execute("DELETE FROM income WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ── Expense CRUD ─────────────────────────────────────────────────────────────

def add_expense(date: str, amount: float, category: str, description: str = "") -> bool:
    """Insert a new expense record."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO expenses (date, amount, category, description) VALUES (?, ?, ?, ?)",
            (date, amount, category, description),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding expense: {e}")
        return False


def get_all_expenses() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM expenses ORDER BY date DESC", conn
    )
    conn.close()
    return df


def get_expenses_by_date_range(start: str, end: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC",
        conn, params=(start, end),
    )
    conn.close()
    return df


def get_expenses_by_category(category: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC",
        conn, params=(category,),
    )
    conn.close()
    return df


def delete_expense(record_id: int) -> bool:
    try:
        conn = get_connection()
        conn.execute("DELETE FROM expenses WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ── Budget CRUD ───────────────────────────────────────────────────────────────

def set_budget(month: str, category: str, amount: float) -> bool:
    """Upsert a budget for a given month + category."""
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO budgets (month, category, amount)
               VALUES (?, ?, ?)
               ON CONFLICT(month, category) DO UPDATE SET amount = excluded.amount""",
            (month, category, amount),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error setting budget: {e}")
        return False


def get_budgets_for_month(month: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM budgets WHERE month = ? ORDER BY category",
        conn, params=(month,),
    )
    conn.close()
    return df


def get_all_budgets() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM budgets ORDER BY month DESC, category", conn
    )
    conn.close()
    return df


def delete_budget(record_id: int) -> bool:
    try:
        conn = get_connection()
        conn.execute("DELETE FROM budgets WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ── Aggregate helpers ─────────────────────────────────────────────────────────

def get_monthly_summary(month: str) -> dict:
    """Return income, expenses, savings for a given month (YYYY-MM)."""
    conn = get_connection()

    income_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE strftime('%Y-%m', date) = ?",
        (month,),
    ).fetchone()

    expense_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE strftime('%Y-%m', date) = ?",
        (month,),
    ).fetchone()

    conn.close()

    total_income = income_row["total"]
    total_expense = expense_row["total"]
    savings = total_income - total_expense
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0

    return {
        "income": total_income,
        "expenses": total_expense,
        "savings": savings,
        "savings_rate": savings_rate,
    }


def get_monthly_category_expenses(month: str) -> pd.DataFrame:
    """Return expenses grouped by category for a given month."""
    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT category, SUM(amount) AS total
           FROM expenses
           WHERE strftime('%Y-%m', date) = ?
           GROUP BY category
           ORDER BY total DESC""",
        conn, params=(month,),
    )
    conn.close()
    return df


def get_monthly_trends(months: int = 6) -> pd.DataFrame:
    """Return income, expenses, savings for the last N months."""
    conn = get_connection()
    df = pd.read_sql_query(
        """
        WITH months AS (
            SELECT strftime('%Y-%m', date) AS month FROM income
            UNION
            SELECT strftime('%Y-%m', date) FROM expenses
        ),
        income_agg AS (
            SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS income
            FROM income GROUP BY month
        ),
        expense_agg AS (
            SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS expenses
            FROM expenses GROUP BY month
        )
        SELECT
            m.month,
            COALESCE(i.income, 0) AS income,
            COALESCE(e.expenses, 0) AS expenses,
            COALESCE(i.income, 0) - COALESCE(e.expenses, 0) AS savings
        FROM months m
        LEFT JOIN income_agg i ON m.month = i.month
        LEFT JOIN expense_agg e ON m.month = e.month
        ORDER BY m.month DESC
        LIMIT ?
        """,
        conn, params=(months,),
    )
    conn.close()
    return df.sort_values("month")
