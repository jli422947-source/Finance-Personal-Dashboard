# 💜 FinanceFlow — Personal Finance Dashboard

A modern, professional personal finance management dashboard built with **Python** and **Streamlit**, featuring a stunning fintech-style UI with dark/light mode.

---

## 🚀 Features

### 🏠 Dashboard
- Real-time KPI cards: Total Income, Expenses, Savings, Savings Rate, Remaining Budget
- Monthly Income vs Expenses bar chart
- Expense Distribution pie chart
- Savings Trend line chart
- Financial insights & recommendations
- Recent transactions table

### 💰 Income Management
- Add income records (Date, Amount, Source, Notes)
- Search and filter by source, date range
- Income analytics charts (donut chart by source, monthly trend)
- Export to CSV

### 💸 Expense Management
- Add expenses with category quick-select buttons
- 8 categories: Food, Transport, Shopping, Entertainment, Bills, Education, Health, Other
- Search, filter by date range and category
- Category breakdown charts
- Export to CSV

### 🎯 Budget Management
- Set monthly budgets per category
- Real-time progress bars with color coding
- Over-budget warnings
- Budget vs Actual comparison chart
- Historical budget tracking

### 📈 Analytics
- Expense distribution pie chart
- Monthly income vs expenses bar chart
- Savings trend line chart
- Category-wise spending horizontal bar chart
- Top N spending categories funnel chart
- Income sources breakdown
- Monthly performance summary table
- Financial health score (0–100) with grade

### 📄 Reports
- Full Excel export (5 sheets: Summary, Income, Expenses, Budgets, Trends)
- Monthly CSV export
- Combined transaction history with filtering
- 12-month summary table

---

## 🛠️ Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Frontend    | Streamlit 1.28+         |
| Charts      | Plotly 5.x              |
| Data        | Pandas 2.x              |
| Database    | SQLite3 (built-in)      |
| Export      | OpenPyXL                |
| Language    | Python 3.11             |

---

## 📁 Project Structure

```
PersonalFinanceDashboard/
├── app.py                  # Main entry point & routing
├── database.db             # SQLite database (auto-created)
├── requirements.txt        # Python dependencies
├── README.md
│
├── .streamlit/
│   └── config.toml         # Server & theme config
│
├── database/
│   └── db.py               # All SQLite CRUD operations
│
├── pages/
│   ├── dashboard.py        # Dashboard page
│   ├── income.py           # Income management
│   ├── expenses.py         # Expense management
│   ├── budgets.py          # Budget management
│   ├── analytics.py        # Analytics & charts
│   └── reports.py          # Reports & exports
│
├── utils/
│   ├── charts.py           # Plotly chart factory functions
│   └── reports.py          # Excel/CSV export utilities
│
└── assets/
    └── styles.css          # Custom fintech CSS styling
```

---

## 🏃 Running the App

```bash
cd PersonalFinanceDashboard
streamlit run app.py --server.port 5000
```

The app will be available at `http://localhost:5000`.

---

## 🗄️ Database Schema

### `income`
| Column     | Type    | Description          |
|------------|---------|----------------------|
| id         | INTEGER | Primary key          |
| date       | TEXT    | Date (YYYY-MM-DD)    |
| amount     | REAL    | Income amount        |
| source     | TEXT    | Income source        |
| notes      | TEXT    | Optional notes       |
| created_at | TEXT    | Record timestamp     |

### `expenses`
| Column      | Type    | Description          |
|-------------|---------|----------------------|
| id          | INTEGER | Primary key          |
| date        | TEXT    | Date (YYYY-MM-DD)    |
| amount      | REAL    | Expense amount       |
| category    | TEXT    | Expense category     |
| description | TEXT    | Optional description |
| created_at  | TEXT    | Record timestamp     |

### `budgets`
| Column     | Type    | Description              |
|------------|---------|--------------------------|
| id         | INTEGER | Primary key              |
| month      | TEXT    | Month (YYYY-MM)          |
| category   | TEXT    | Budget category          |
| amount     | REAL    | Budget limit             |
| created_at | TEXT    | Record timestamp         |

---

## 🎨 Design

- **Color palette:** Purple (#8B5CF6) and Pink (#EC4899) gradient accents
- **Dark mode:** Deep navy background (#0F0C29 → #1E1B4B)
- **Light mode:** Soft lavender background
- **Font:** Inter (Google Fonts)
- Inspired by modern fintech dashboards

---

## 📊 Financial Health Score

The app calculates a 0–100 financial health score based on:
- **Savings rate** (0–40 pts) — target 20%+
- **Expense diversity** (0–20 pts) — tracking multiple categories
- **Data consistency** (0–20 pts) — 3+ months of records
- **Income diversity** (0–20 pts) — multiple income sources

---

*Built as a portfolio project — showcasing Python, Streamlit, SQLite, Plotly, and Pandas.*
