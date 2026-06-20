from io import BytesIO

import pandas as pd
import streamlit as st

try:
    from modules.kpi import compute_kpis, compute_period_comparison, monthly_revenue_trend
    from modules.market_basket import compute_product_pairs
    from modules.cohort import build_cohort_retention
except ModuleNotFoundError:
    from kpi import compute_kpis, compute_period_comparison, monthly_revenue_trend
    from market_basket import compute_product_pairs
    from cohort import build_cohort_retention


def _to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return buffer.getvalue()


@st.cache_data
def build_executive_report(df_filtered: pd.DataFrame, filter_label: str) -> bytes:
    """產生主管營運總覽 Excel 報表。"""
    kpis = compute_kpis(df_filtered)
    comparison = compute_period_comparison(df_filtered)
    monthly = monthly_revenue_trend(df_filtered)
    top5 = (
        df_filtered.groupby(["StockCode", "Description"])["TotalAmount"]
        .sum()
        .reset_index()
        .sort_values("TotalAmount", ascending=False)
        .head(5)
    )

    summary = pd.DataFrame(
        [
            {"指標": "篩選條件", "數值": filter_label},
            {"指標": "總營業額 (£)", "數值": kpis["total_revenue"]},
            {"指標": "消費會員數", "數值": kpis["unique_customers"]},
            {"指標": "訂單數", "數值": kpis["total_orders"]},
            {"指標": "平均客單價 (£)", "數值": kpis["average_order_value"]},
            {"指標": "營收變化 (%)", "數值": comparison["revenue_delta_pct"]},
            {"指標": "趨勢", "數值": comparison["trend_label"]},
        ]
    )

    monthly_out = monthly.copy()
    monthly_out["YearMonth"] = monthly_out["YearMonth"].astype(str)

    return _to_excel_bytes(
        {
            "KPI摘要": summary,
            "月營收趨勢": monthly_out,
            "熱銷Top5": top5,
            "交易明細樣本": df_filtered.head(3000),
        }
    )


@st.cache_data
def build_market_report(df_filtered: pd.DataFrame, filter_label: str) -> bytes:
    """產生市場分析綜合 Excel 報表。"""
    _, cohort_pct = build_cohort_retention(df_filtered)
    pairs = compute_product_pairs(df_filtered)
    country_stats = (
        df_filtered.groupby("Country")
        .agg(TotalAmount=("TotalAmount", "sum"), Customers=("CustomerID", "nunique"))
        .reset_index()
        .sort_values("TotalAmount", ascending=False)
    )

    cohort_out = cohort_pct.reset_index()
    cohort_out["CohortMonth"] = cohort_out["CohortMonth"].astype(str)

    return _to_excel_bytes(
        {
            "報表條件": pd.DataFrame([{"篩選條件": filter_label}]),
            "各國營收": country_stats,
            "購物籃組合": pairs,
            "同期群留存率": cohort_out,
        }
    )


@st.cache_data
def build_detail_report(df_filtered: pd.DataFrame) -> bytes:
    """產生交易明細 Excel（限制筆數避免卡頓）。"""
    return _to_excel_bytes({"交易明細": df_filtered.head(5000)})


def render_export_sidebar(
    df_filtered: pd.DataFrame,
    filter_label: str,
) -> None:
    """在側邊欄渲染報表匯出（按需產生，不阻塞主畫面）。"""
    st.sidebar.markdown("---")
    st.sidebar.header("📥 報表匯出")

    if df_filtered.empty:
        st.sidebar.warning("目前無資料可匯出。")
        return

    safe_label = filter_label.replace("|", "-").replace(" ", "")
    report_type = st.sidebar.selectbox(
        "選擇報表類型",
        ["主管營運報表", "市場分析報表", "交易明細 (前 5000 筆)"],
    )

    if st.sidebar.button("產生報表", use_container_width=True):
        with st.spinner("報表產生中，請稍候..."):
            if report_type == "主管營運報表":
                st.session_state.export_bytes = build_executive_report(df_filtered, filter_label)
                st.session_state.export_fname = f"executive_summary_{safe_label}.xlsx"
            elif report_type == "市場分析報表":
                st.session_state.export_bytes = build_market_report(df_filtered, filter_label)
                st.session_state.export_fname = f"market_analysis_{safe_label}.xlsx"
            else:
                st.session_state.export_bytes = build_detail_report(df_filtered)
                st.session_state.export_fname = f"transactions_{safe_label}.xlsx"

    if st.session_state.get("export_bytes"):
        st.sidebar.download_button(
            label="⬇️ 下載 Excel 報表",
            data=st.session_state.export_bytes,
            file_name=st.session_state.get("export_fname", "report.xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
