import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

try:
    from modules.kpi import compute_kpis, compute_period_comparison, monthly_revenue_trend
except ModuleNotFoundError:
    from kpi import compute_kpis, compute_period_comparison, monthly_revenue_trend


def render_executive_summary(
    df_filtered: pd.DataFrame,
    df_valid: pd.DataFrame,
    filter_label: str,
    selected_country: str,
) -> None:
    """渲染主管營運總覽分頁。"""
    st.header(f"📋 主管營運總覽 — {filter_label}")

    if df_filtered.empty:
        st.warning("當前篩選條件下無數據，請調整國家或日期區間。")
        return

    kpis = compute_kpis(df_filtered)
    comparison = compute_period_comparison(df_filtered)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "💰 總營業額",
            f"£{kpis['total_revenue']:,.2f}",
            delta=f"{comparison['revenue_delta_pct']:+.1f}%",
        )
    with col2:
        st.metric("👥 消費會員數", f"{kpis['unique_customers']:,} 人")
    with col3:
        st.metric(
            "📦 成立訂單數",
            f"{kpis['total_orders']:,} 筆",
            delta=f"{comparison['orders_delta_pct']:+.1f}%",
        )
    with col4:
        st.metric("💵 平均客單價 (AOV)", f"£{kpis['average_order_value']:,.2f}")

    st.markdown("---")

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("📈 月營收趨勢")
        monthly = monthly_revenue_trend(df_filtered)
        if len(monthly) > 0:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.plot(
                monthly["YearMonth"].astype(str),
                monthly["Revenue"],
                marker="o",
                color="#4C72B0",
                linewidth=2,
            )
            ax.set_xlabel("月份")
            ax.set_ylabel("營收 (£)")
            ax.tick_params(axis="x", rotation=45)
            st.pyplot(fig)
        else:
            st.info("此區間無足夠月份資料。")

    with col_right:
        st.subheader("💡 策略洞察")
        top_product = (
            df_filtered.groupby("Description")["Quantity"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )
        top_product_name = top_product.index[0] if len(top_product) else "N/A"
        top_product_qty = int(top_product.iloc[0]) if len(top_product) else 0

        if selected_country == "全部國家 (All)":
            top_market = (
                df_valid.groupby("Country")["TotalAmount"]
                .sum()
                .sort_values(ascending=False)
                .head(1)
            )
            market_name = top_market.index[0]
            market_share = top_market.iloc[0] / df_valid["TotalAmount"].sum() * 100
            market_insight = (
                f"**核心市場**：{market_name} 貢獻 **{market_share:.1f}%** 全球營收，"
                "建議優先維護主力市場客戶體驗。"
            )
        else:
            market_insight = (
                f"**聚焦市場**：目前分析 **{selected_country}**，"
                f"區間營收 **£{kpis['total_revenue']:,.0f}**。"
            )

        alert = ""
        if comparison["trend_label"] == "下滑":
            alert = (
                "\n\n⚠️ **警示**：本期營收較上期下滑，"
                f"變化 **{comparison['revenue_delta_pct']:.1f}%**，建議檢視促銷與留存策略。"
            )

        st.success(
            f"""
            - {market_insight}
            - **熱銷商品**：{top_product_name}（銷量 {top_product_qty:,} 件）
            - **營收趨勢**：區間內呈現 **{comparison['trend_label']}** 態勢{alert}
            """
        )

    st.subheader("🏆 區間熱銷商品 Top 5")
    top5 = (
        df_filtered.groupby(["StockCode", "Description"])["TotalAmount"]
        .sum()
        .reset_index()
        .sort_values("TotalAmount", ascending=False)
        .head(5)
    )
    top5.columns = ["商品代碼", "商品名稱", "營收 (£)"]
    st.dataframe(
        top5.style.format({"營收 (£)": "£{:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )
