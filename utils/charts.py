"""
Chart utilities for Personal Finance Dashboard.
All Plotly chart factory functions live here.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots

# ── Shared theme ──────────────────────────────────────────────────────────────

PURPLE = "#8B5CF6"
PINK   = "#EC4899"
CYAN   = "#06B6D4"
GREEN  = "#10B981"
AMBER  = "#F59E0B"
RED    = "#EF4444"

GRADIENT_COLORS = [PURPLE, PINK, CYAN, GREEN, AMBER, RED,
                   "#6366F1", "#F97316", "#14B8A6", "#A855F7"]

def _base_layout(dark: bool = True) -> dict:
    bg     = "#1E1B4B" if dark else "#FFFFFF"
    paper  = "#16133A" if dark else "#F8F7FF"
    text   = "#E2E8F0" if dark else "#1E1B4B"
    grid   = "rgba(255,255,255,0.07)" if dark else "rgba(0,0,0,0.06)"
    return dict(
        paper_bgcolor=paper,
        plot_bgcolor=bg,
        font=dict(color=text, family="Inter, sans-serif", size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor="rgba(0,0,0,0)" if dark else "rgba(255,255,255,0)",
            bordercolor="rgba(255,255,255,0.1)" if dark else "rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
        xaxis=dict(gridcolor=grid, zeroline=False),
        yaxis=dict(gridcolor=grid, zeroline=False),
    )


# ── Pie Chart ─────────────────────────────────────────────────────────────────

def expense_pie_chart(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    """Donut chart showing expense distribution by category."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**_base_layout(dark), title="No expense data available")
        return fig

    fig = go.Figure(go.Pie(
        labels=df["category"],
        values=df["total"],
        hole=0.55,
        marker=dict(colors=GRADIENT_COLORS[:len(df)],
                    line=dict(color="#1E1B4B" if dark else "#fff", width=2)),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
    ))

    layout = _base_layout(dark)
    layout["legend"] = dict(
        orientation="v",
        x=1.0,
        y=0.5,
    )

    fig.update_layout(
        **layout,
        title=dict(text="Expense Distribution", font=dict(size=16)),
        showlegend=True,
    )
    # Add center annotation
    total = df["total"].sum()
    fig.add_annotation(
        text=f"<b>${total:,.0f}</b><br>Total",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color=PURPLE),
    )
    return fig


# ── Bar Chart ─────────────────────────────────────────────────────────────────

def income_vs_expense_bar(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    """Grouped bar chart of monthly income vs expenses."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**_base_layout(dark), title="No data available")
        return fig

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Income", x=df["month"], y=df["income"],
        marker_color=GREEN,
        hovertemplate="<b>%{x}</b><br>Income: $%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Expenses", x=df["month"], y=df["expenses"],
        marker_color=PINK,
        hovertemplate="<b>%{x}</b><br>Expenses: $%{y:,.2f}<extra></extra>",
    ))

    layout = _base_layout(dark)
    layout["xaxis"]["title"] = "Month"
    layout["yaxis"]["title"] = "Amount ($)"
    fig.update_layout(
        **layout,
        title=dict(text="Monthly Income vs Expenses", font=dict(size=16)),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
    )
    return fig


# ── Savings Trend Line ────────────────────────────────────────────────────────

def savings_trend_line(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    """Area line chart showing savings over time."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**_base_layout(dark), title="No data available")
        return fig

    fill_color = "rgba(139,92,246,0.15)"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["savings"],
        mode="lines+markers",
        name="Savings",
        line=dict(color=PURPLE, width=3),
        marker=dict(size=8, color=PURPLE, line=dict(color="#fff", width=2)),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate="<b>%{x}</b><br>Savings: $%{y:,.2f}<extra></extra>",
    ))

    # Zero line
    fig.add_hline(y=0, line_dash="dash",
                  line_color="rgba(255,255,255,0.3)" if dark else "rgba(0,0,0,0.2)",
                  annotation_text="Break-even")

    layout = _base_layout(dark)
    layout["xaxis"]["title"] = "Month"
    layout["yaxis"]["title"] = "Savings ($)"
    fig.update_layout(
        **layout,
        title=dict(text="Savings Trend", font=dict(size=16)),
    )
    return fig


# ── Category Bar ──────────────────────────────────────────────────────────────

def category_spending_bar(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    """Horizontal bar chart for category-wise spending."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**_base_layout(dark), title="No expense data available")
        return fig

    df_sorted = df.sort_values("total", ascending=True)
    fig = go.Figure(go.Bar(
        x=df_sorted["total"],
        y=df_sorted["category"],
        orientation="h",
        marker=dict(
            color=df_sorted["total"],
            colorscale=[[0, CYAN], [0.5, PURPLE], [1, PINK]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>",
    ))

    layout = _base_layout(dark)
    layout["yaxis"]["title"] = ""
    layout["xaxis"]["title"] = "Amount ($)"
    fig.update_layout(
        **layout,
        title=dict(text="Category-wise Spending", font=dict(size=16)),
        height=max(300, len(df_sorted) * 50),
    )
    return fig


# ── Top Spending ──────────────────────────────────────────────────────────────

def top_spending_categories(df: pd.DataFrame, top_n: int = 5, dark: bool = True) -> go.Figure:
    """Funnel chart showing top N spending categories."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**_base_layout(dark), title="No expense data available")
        return fig

    top = df.nlargest(top_n, "total")
    fig = go.Figure(go.Funnel(
        y=top["category"],
        x=top["total"],
        marker=dict(color=GRADIENT_COLORS[:len(top)]),
        textinfo="value+percent initial",
        hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(dark),
        title=dict(text=f"Top {top_n} Spending Categories", font=dict(size=16)),
    )
    return fig


# ── Budget Progress ───────────────────────────────────────────────────────────

def budget_vs_actual_bar(
    budgets_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    dark: bool = True,
) -> go.Figure:
    """Grouped bar comparing budgeted vs actual spend per category."""

    if budgets_df.empty:
        fig = go.Figure()
        fig.update_layout(
            **_base_layout(dark),
            title="No budget data set",
        )
        return fig

    # Prepare actual expenses by category.
    if (
        expenses_df.empty
        or "category" not in expenses_df.columns
    ):
        actual = pd.DataFrame(
            columns=["category", "actual"]
        )
    elif "total" in expenses_df.columns:
        actual = expenses_df[
            ["category", "total"]
        ].copy()
        actual = actual.rename(
            columns={"total": "actual"}
        )
        actual = actual.groupby(
            "category", as_index=False
        )["actual"].sum()
    elif "amount" in expenses_df.columns:
        actual = (
            expenses_df.groupby("category")["amount"]
            .sum()
            .reset_index()
            .rename(columns={"amount": "actual"})
        )
    else:
        actual = pd.DataFrame(
            columns=["category", "actual"]
        )

    merged = budgets_df.merge(
        actual,
        on="category",
        how="left",
    ).fillna({"actual": 0})

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Budget",
        x=merged["category"],
        y=merged["amount"],
        marker_color=CYAN,
        hovertemplate="Budget: $%{y:,.2f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Actual",
        x=merged["category"],
        y=merged["actual"],
        marker_color=PINK,
        hovertemplate="Actual: $%{y:,.2f}<extra></extra>",
    ))

    layout = _base_layout(dark)
    layout["xaxis"]["title"] = "Category"
    layout["yaxis"]["title"] = "Amount ($)"

    fig.update_layout(
        **layout,
        title=dict(
            text="Budget vs Actual Spending",
            font=dict(size=16),
        ),
        barmode="group",
    )

    return fig

# ── Income Sources Pie ────────────────────────────────────────────────────────

def income_sources_pie(df: pd.DataFrame, dark: bool = True) -> go.Figure:
    """Donut chart of income by source."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**_base_layout(dark), title="No income data available")
        return fig

    grouped = df.groupby("source")["amount"].sum().reset_index()
    fig = go.Figure(go.Pie(
        labels=grouped["source"],
        values=grouped["amount"],
        hole=0.55,
        marker=dict(colors=[GREEN, CYAN, AMBER, PURPLE, PINK][:len(grouped)],
                    line=dict(color="#1E1B4B" if dark else "#fff", width=2)),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(dark),
        title=dict(text="Income by Source", font=dict(size=16)),
    )
    return fig
