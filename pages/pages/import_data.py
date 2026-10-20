
"""CSV bulk import for FinanceFlow."""
import pandas as pd
import streamlit as st
from database.db import get_all_income, get_all_expenses, add_income, add_expense

def render(dark=True):
    st.markdown("## 📥 批量导入 CSV")
    st.write("上传交易明细 CSV，检查预览后再导入。请勿上传月度汇总文件。")
    st.info("需要的列：date、type、category、amount_usd、description")

    uploaded = st.file_uploader("选择交易明细 CSV 文件", type=["csv"])

    if uploaded is None:
        st.caption("示例列名：date,type,category,amount_usd,description")
        return

    try:
        df = pd.read_csv(uploaded)
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.rename(columns={
            "amount_usd": "amount",
            "transaction_type": "type",
            "notes": "description",
        })

        required = {"date", "type", "category", "amount"}
        missing = required - set(df.columns)
        if missing:
            st.error("缺少必要列：" + ", ".join(sorted(missing)))
            return

        if "description" not in df.columns:
            df["description"] = ""

        df["date"] = pd.to_datetime(
            df["date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df["type"] = df["type"].astype(str).str.strip().str.lower()
        df["category"] = df["category"].fillna("").astype(str).str.strip()
        df["description"] = df["description"].fillna("").astype(str).str.strip()

        df["type"] = df["type"].replace({
            "收入": "income",
            "支出": "expense",
        })

        invalid = (
            df["date"].isna()
            | df["amount"].isna()
            | (df["amount"] <= 0)
            | (~df["type"].isin(["income", "expense"]))
            | (df["category"] == "")
        )

        if invalid.any():
            st.error(f"发现 {int(invalid.sum())} 条无效记录，请修正 CSV 后重试。")
            st.dataframe(df[invalid], use_container_width=True, hide_index=True)
            return

        df = df.drop_duplicates(
            subset=["date", "type", "category", "amount", "description"]
        ).reset_index(drop=True)

    except Exception as e:
        st.error(f"读取 CSV 失败：{e}")
        return

    st.success(f"预览完成，共 {len(df)} 条不重复记录。")
    st.dataframe(df, use_container_width=True, hide_index=True)

    old_income = get_all_income()
    old_expenses = get_all_expenses()

    income_keys = set()
    expense_keys = set()

    if not old_income.empty:
        income_keys = {
            (str(r["date"]), str(r["source"]), round(float(r["amount"]), 2),
             str(r.get("notes", "") or ""))
            for _, r in old_income.iterrows()
        }

    if not old_expenses.empty:
        expense_keys = {
            (str(r["date"]), str(r["category"]), round(float(r["amount"]), 2),
             str(r.get("description", "") or ""))
            for _, r in old_expenses.iterrows()
        }

    new_rows = []
    skipped = 0

    for _, r in df.iterrows():
        key = (
            r["date"], r["category"], round(float(r["amount"]), 2),
            r["description"]
        )
        existing = income_keys if r["type"] == "income" else expense_keys
        if key in existing:
            skipped += 1
        else:
            new_rows.append(r)

    st.write(f"待导入：{len(new_rows)} 条；匹配到已有记录：{skipped} 条。")

    confirmed = st.checkbox("我已检查预览，确认导入这些记录。")

    if st.button("开始导入", type="primary", disabled=not confirmed or not new_rows):
        success = 0
        failed = 0

        for r in new_rows:
            if r["type"] == "income":
                ok = add_income(
                    r["date"], round(float(r["amount"]), 2),
                    r["category"], r["description"]
                )
            else:
                ok = add_expense(
                    r["date"], round(float(r["amount"]), 2),
                    r["category"], r["description"]
                )

            if ok:
                success += 1
            else:
                failed += 1

        if failed:
            st.warning(f"成功导入 {success} 条，失败 {failed} 条。请检查后再处理失败记录。")
        else:
            st.success(f"导入完成！成功导入 {success} 条，跳过已有记录 {skipped} 条。")

        st.info("请进入 Income 和 Expenses 页面，检查交易历史是否正确。")
