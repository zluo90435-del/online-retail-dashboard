import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


def _pct(part: int, total: int) -> float:
    return (part / total * 100) if total > 0 else 0.0


def compute_quality_metrics(df_raw: pd.DataFrame, df_valid: pd.DataFrame) -> pd.DataFrame:
    """計算資料品質檢核指標。"""
    total = len(df_raw)
    missing_customer = df_raw["CustomerID"].isna().sum()
    negative_qty = (df_raw["Quantity"] <= 0).sum()
    zero_price = (df_raw["UnitPrice"] <= 0).sum()
    duplicate_rows = df_raw.duplicated().sum()
    valid_rows = len(df_valid)

    metrics = [
        ("總筆數", total, "100.0%", "基準"),
        ("缺少 CustomerID", missing_customer, f"{_pct(missing_customer, total):.1f}%", "過濾"),
        ("數量 ≤ 0（退貨/異常）", negative_qty, f"{_pct(negative_qty, total):.1f}%", "過濾"),
        ("單價 ≤ 0", zero_price, f"{_pct(zero_price, total):.1f}%", "過濾"),
        ("完全重複列", duplicate_rows, f"{_pct(duplicate_rows, total):.1f}%", "檢核"),
        ("清洗後有效筆數", valid_rows, f"{_pct(valid_rows, total):.1f}%", "保留"),
    ]

    return pd.DataFrame(metrics, columns=["檢核項目", "筆數", "佔比", "處理方式"])


def render_data_quality(df_raw: pd.DataFrame, df_valid: pd.DataFrame) -> None:
    """渲染資料品質監控分頁。"""
    st.header("🔍 資料品質監控")
    st.caption("監控原始資料的完整性、異常值與清洗成效，確保下游分析可信。")

    metrics_df = compute_quality_metrics(df_raw, df_valid)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("原始筆數", f"{len(df_raw):,}")
    with col2:
        st.metric("有效筆數", f"{len(df_valid):,}")
    with col3:
        st.metric("剔除比例", f"{(1 - len(df_valid) / len(df_raw)) * 100:.1f}%")
    with col4:
        st.metric("涵蓋國家數", f"{df_valid['Country'].nunique():,}")

    st.subheader("📋 品質檢核明細")
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    st.subheader("📊 異常類型分布")
    issue_df = metrics_df[metrics_df["處理方式"] == "過濾"].copy()
    if not issue_df.empty:
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.bar(issue_df["檢核項目"], issue_df["筆數"], color=["#C44E52", "#DD8452", "#55A868"])
        ax.set_ylabel("筆數")
        ax.tick_params(axis="x", rotation=15)
        st.pyplot(fig)

    st.subheader("🗓️ 資料覆蓋期間")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        st.write("**原始資料**")
        st.write(
            f"- 起始：{df_raw['InvoiceDate'].min().date()}\n"
            f"- 結束：{df_raw['InvoiceDate'].max().date()}\n"
            f"- 天數：{(df_raw['InvoiceDate'].max() - df_raw['InvoiceDate'].min()).days + 1} 天"
        )
    with date_col2:
        st.write("**清洗後資料**")
        st.write(
            f"- 起始：{df_valid['InvoiceDate'].min().date()}\n"
            f"- 結束：{df_valid['InvoiceDate'].max().date()}\n"
            f"- 天數：{(df_valid['InvoiceDate'].max() - df_valid['InvoiceDate'].min()).days + 1} 天"
        )

    missing_customer_pct = _pct(df_raw["CustomerID"].isna().sum(), len(df_raw))
    if missing_customer_pct > 20:
        st.warning(
            f"CustomerID 缺失率達 **{missing_customer_pct:.1f}%**，"
            "建議在 ETL 階段加入資料來源標記，區分會員與散客交易。"
        )
    else:
        st.success("資料品質檢核通過，異常值已在清洗流程中妥善處理。")
