import pandas as pd
import streamlit as st

try:
    from modules.kpi import compute_period_comparison
except ModuleNotFoundError:
    from kpi import compute_period_comparison


def render_insight_box(title: str, bullets: list[str], style: str = "info") -> None:
    """以統一格式顯示洞察分析說明。"""
    st.subheader(title)
    content = "\n".join(f"- {item}" for item in bullets)
    if style == "success":
        st.success(content)
    elif style == "warning":
        st.warning(content)
    else:
        st.info(content)


def render_kpi_insights(df_filtered: pd.DataFrame) -> None:
    """核心營運 KPI 分頁的洞察分析。"""
    if df_filtered.empty:
        return

    total_revenue = df_filtered["TotalAmount"].sum()
    unique_customers = df_filtered["CustomerID"].nunique()
    total_orders = df_filtered["InvoiceNo"].nunique()
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    revenue_per_customer = total_revenue / unique_customers if unique_customers > 0 else 0
    orders_per_customer = total_orders / unique_customers if unique_customers > 0 else 0

    top_product = (
        df_filtered.groupby("Description")["Quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(1)
    )
    top_name = top_product.index[0] if len(top_product) else "N/A"
    top_qty = int(top_product.iloc[0]) if len(top_product) else 0
    total_qty = df_filtered["Quantity"].sum()
    top_share = (top_qty / total_qty * 100) if total_qty > 0 else 0

    comparison = compute_period_comparison(df_filtered)
    trend_note = (
        f"區間後半段營收較前半段 **{comparison['revenue_delta_pct']:+.1f}%**（{comparison['trend_label']}）"
    )

    bullets = [
        f"**客均貢獻**：每位會員平均貢獻 **£{revenue_per_customer:,.2f}**，人均訂單 **{orders_per_customer:.1f}** 筆。",
        f"**客單價**：平均客單價 **£{average_order_value:,.2f}**，可作為促銷門檻與免運門檻設定參考。",
        f"**商品集中度**：熱銷品「{top_name}」占區間銷量 **{top_share:.1f}%**。",
        f"**趨勢觀察**：{trend_note}。",
    ]

    render_insight_box("💡 洞察分析說明", bullets)


def render_rfm_insights(segment_stats: pd.DataFrame) -> None:
    """RFM 會員分類分頁的洞察分析。"""
    if segment_stats.empty:
        return

    total_customers = segment_stats["客戶人數"].sum()
    champions = segment_stats[segment_stats["Segment"].str.contains("Champions", na=False)]
    at_risk = segment_stats[segment_stats["Segment"].str.contains("At Risk", na=False)]
    lost = segment_stats[segment_stats["Segment"].str.contains("Lost", na=False)]

    champ_count = int(champions["客戶人數"].sum()) if not champions.empty else 0
    champ_rev_share = float(champions["金額佔比"].sum()) if not champions.empty else 0
    at_risk_count = int(at_risk["客戶人數"].sum()) if not at_risk.empty else 0
    at_risk_rev = float(at_risk["總貢獻金額"].sum()) if not at_risk.empty else 0
    lost_pct = float(lost["客戶人數"].sum() / total_customers) if not lost.empty and total_customers else 0

    bullets = [
        f"**核心客群**：Champions 共 **{champ_count:,}** 人，貢獻 **{champ_rev_share:.1%}** 營收，應優先維護 VIP 權益。",
        f"**挽留優先**：At Risk 客群 **{at_risk_count:,}** 人，合計價值 **£{at_risk_rev:,.0f}**，建議啟動召回優惠。",
        f"**流失規模**：Lost 客群占 **{lost_pct:.1%}**，可評估是否值得再激活或降低投入。",
        "**行動建議**：人數占比與金額占比差距大的客群（如 Loyal）適合交叉銷售，提升客單與回購頻次。",
    ]

    style = "warning" if at_risk_count > 0 and champ_rev_share < 0.3 else "info"
    render_insight_box("💡 洞察分析說明", bullets, style=style)


def render_data_quality_insights(df_raw: pd.DataFrame, df_valid: pd.DataFrame) -> None:
    """資料品質監控分頁的洞察分析。"""
    total = len(df_raw)
    missing_customer = df_raw["CustomerID"].isna().sum()
    negative_qty = (df_raw["Quantity"] <= 0).sum()
    zero_price = (df_raw["UnitPrice"] <= 0).sum()
    valid_pct = len(df_valid) / total * 100 if total > 0 else 0
    missing_pct = missing_customer / total * 100 if total > 0 else 0

    bullets = [
        f"**可用率**：清洗後保留 **{valid_pct:.1f}%** 原始交易，下游 KPI 與 RFM 分析基於此有效集。",
        f"**會員覆蓋**：CustomerID 缺失 **{missing_pct:.1f}%**（**{missing_customer:,}** 筆），多為散客，不納入會員行為分析。",
        f"**異常交易**：退貨/異常數量 **{negative_qty:,}** 筆、零單價 **{zero_price:,}** 筆，已排除以免扭曲營收。",
        f"**地理覆蓋**：有效資料涵蓋 **{df_valid['Country'].nunique()}** 個國家，"
        f"期間 **{df_valid['InvoiceDate'].min().date()}** 至 **{df_valid['InvoiceDate'].max().date()}**。",
    ]

    style = "warning" if missing_pct > 20 else "success"
    render_insight_box("💡 洞察分析說明", bullets, style=style)
