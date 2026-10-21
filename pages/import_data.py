"""Bulk import transaction records from a CSV file."""
import pandas as pd
import streamlit as st

from database.db import get_all_income, get_all_expenses, add_income, add_expense

COLUMN_ALIASES = {
    "amount_usd": "amount",
    "amount ($)": "amount",
    "transaction_type": "type",
    "notes": "description",
}

def render(dark=True):
    st.markdown('<div class="page-title">📥 批量导入 CSV</div>', unsafe_allow_html=True)
    st.write("上传交易明细 CSV，先预览并检查，再确认导入。请勿上传月度汇总文件。")
    st.info("必需列：date、type、category、amount_usd（或 amount）；description 可选。type 请使用 Income 或 Expense。")

    uploaded = st.file_uploader("选择交易明细 CSV 文件", type=["csv"], key="transaction_csv_upload")
    if uploaded is None:
        return

    try:
        df = pd.read_csv(uploaded)
        df.columns = [str(col).strip().lower() for col in df.columns]
        df = df.rename(columns={col: COLUMN_ALIASES[col] for col in df.columns if col in COLUMN_ALIASES})
        if "description" not in df.columns:
            df["description"] = ""

        required = {"date", "type", "category", "amount"}
        missing = required - set(df.columns)
        if missing:
            st.error("CSV 缺少必要列：" + "、".join(sorted(missing)))
            return

        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df["type"] = df["type"].astype(str).str.strip().str.lower().replace({
            "收入": "income", "支出": "expense"
        })
        df["category"] = df["category"].fillna("").astype(str).str.strip()
        df["description"] = df["description"].fillna("").astype(str).str.strip()

        invalid = (
            df["date"].isna()
            | df["amount"].isna()
            | (df["amount"] <= 0)
            | (~df["type"].isin(["income", "expense"]))
            | (df["category"] == "")
        )
        if invalid.any():
            st.error(f"发现 {int(invalid.sum())} 条无效记录。请修正日期、金额、类型或分类后重新上传。")
            st.dataframe(df[invalid], use_container_width=True, hide_index=True)
            return

        df["amount"] = df["amount"].round(2)
        df = df.drop_duplicates(subset=["date", "type", "category", "amount", "description"]).reset_index(drop=True)
    except Exception as exc:
        st.error(f"读取 CSV 失败：{exc}")
        return

    st.success(f"预览成功：共 {len(df)} 条不重复交易。")
    st.dataframe(df, use_container_width=True, hide_index=True)

    old_income = get_all_income()
    old_expenses = get_all_expenses()
    income_keys = set()
    expense_keys = set()
    income_core_keys = set()
    expense_core_keys = set()

    def normalized_date(value):
        parsed = pd.to_datetime(value, errors="coerce")
        return parsed.strftime("%Y-%m-%d") if not pd.isna(parsed) else str(value).strip()

    if not old_income.empty:
        income_keys = {
            (normalized_date(row["date"]), str(row["source"]).strip(),
             round(float(row["amount"]), 2), str(row.get("notes", "") or "").strip())
            for _, row in old_income.iterrows()
        }
        income_core_keys = {(key[0], key[1], key[2]) for key in income_keys}
    if not old_expenses.empty:
        expense_keys = {
            (normalized_date(row["date"]), str(row["category"]).strip(),
             round(float(row["amount"]), 2), str(row.get("description", "") or "").strip())
            for _, row in old_expenses.iterrows()
        }
        expense_core_keys = {(key[0], key[1], key[2]) for key in expense_keys}

    new_rows = []
    possible_duplicates = []
    skipped = 0
    for _, row in df.iterrows():
        key = (normalized_date(row["date"]), row["category"].strip(),
               round(float(row["amount"]), 2), row["description"].strip())
        existing = income_keys if row["type"] == "income" else expense_keys
        core_existing = income_core_keys if row["type"] == "income" else expense_core_keys
        core_key = key[:3]
        if key in existing:
            skipped += 1
        else:
            new_rows.append(row)
            if core_key in core_existing:
                possible_duplicates.append({
                    "date": key[0], "type": row["type"].title(),
                    "category/source": key[1], "amount": key[2],
                    "existing description differs": key[3] or "(empty)",
                })

    st.write(f"待导入：{len(new_rows)} 条；与现有记录完全匹配、将跳过：{skipped} 条。")
    if possible_duplicates:
        st.warning(
            f"发现 {len(possible_duplicates)} 条可能重复的交易：日期、类别/来源和金额与现有记录相同，"
            "但描述不同。系统不会自动跳过这些记录，请先检查后再确认导入。"
        )
        st.dataframe(pd.DataFrame(possible_duplicates), use_container_width=True, hide_index=True)
    confirmed = st.checkbox("我已检查预览，确认将这些记录写入当前 FinanceFlow 数据库。")

    if st.button("开始导入", type="primary", disabled=(not confirmed or not new_rows)):
        imported, failed = 0, 0
        for row in new_rows:
            amount = round(float(row["amount"]), 2)
            if row["type"] == "income":
                saved = add_income(row["date"], amount, row["category"], row["description"])
            else:
                saved = add_expense(row["date"], amount, row["category"], row["description"])
            if saved:
                imported += 1
            else:
                failed += 1

        if failed:
            st.warning(f"成功导入 {imported} 条，失败 {failed} 条。请检查交易历史，再决定如何处理失败记录。")
        else:
            st.success(f"导入完成！成功导入 {imported} 条，跳过 {skipped} 条已存在的匹配记录。")
        st.caption("请进入 Income 和 Expenses 的 Transaction History 检查导入结果。")
