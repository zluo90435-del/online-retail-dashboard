import datetime as dt

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from app_imports import (
    load_and_clean_data,
    render_churn_prediction,
    render_cohort_analysis,
    render_data_quality,
    render_executive_summary,
    render_export_sidebar,
    render_market_basket,
    render_sidebar_filters,
)


def setup_chinese_font():
    """載入專案內建字型，確保本機與 Streamlit Cloud 都能顯示繁體中文。"""
    from pathlib import Path

    base_dir = Path(__file__).parent
    font_candidates = [
        base_dir / "fonts" / "NotoSansCJKtc-Regular.otf",
        base_dir / "NotoSansCJKtc-Regular.otf",
    ]
    for font_path in font_candidates:
        if font_path.exists():
            fm.fontManager.addfont(str(font_path))
            font_name = fm.FontProperties(fname=str(font_path)).get_name()
            matplotlib.rcParams["font.family"] = font_name
            matplotlib.rcParams["axes.unicode_minus"] = False
            return

    preferred_fonts = [
        "Microsoft JhengHei",
        "Microsoft YaHei",
        "Noto Sans CJK TC",
        "Noto Sans TC",
        "WenQuanYi Micro Hei",
    ]
    matplotlib.rcParams["font.sans-serif"] = preferred_fonts
    matplotlib.rcParams["axes.unicode_minus"] = False


setup_chinese_font()

st.set_page_config(
    page_title="Online Retail Analytics Platform",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Online Retail Analytics & Market Strategy Dashboard")
st.markdown(
    """
這個專案展示了如何利用 **Python Streamlit** 結合 **MS SQL Server** 與 AI 輔助工具（Cursor），將 **54 萬筆原始跨國電商交易數據**，
經由 **ETL 匯入、Stored Procedure 清洗** 後，建立核心營運 KPI 儀表板，並透過 **RFM 模型**、**購物籃分析**、**同期群留存**、**流失預警**、**線性迴歸預測** 與 **地理區域資料** 進行跨國市場分析與增長策略擬定。
"""
)

try:
    df_raw, df_valid, data_source = load_and_clean_data()
except Exception as e:
    st.error(f"找不到資料來源，請確認 SQL Server 已啟動或 Excel 檔案存在。錯誤訊息: {e}")
    st.stop()

df_filtered, filter_label, start_date, end_date, selected_country = render_sidebar_filters(
    df_valid, data_source
)

tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
    [
        "📋 主管營運總覽",
        "🔍 資料品質監控",
        "🧹 資料基本狀況",
        "📈 核心營運 KPI",
        "💎 RFM 會員分類",
        "🛒 購物籃分析",
        "📊 同期群留存",
        "⚠️ 流失預警",
        "🌍 全球市場地區分析",
        "📉 迴歸分析與預測",
    ]
)

with tab0:
    render_executive_summary(df_filtered, df_valid, filter_label, selected_country)

with tab1:
    render_data_quality(df_raw, df_valid)

with tab2:
    st.header("數據清洗與預處理報告")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("原始數據總筆數", f"{len(df_raw):,}")
    with col2:
        st.metric("剔除匿名客/異常後筆數", f"{len(df_valid):,}")
    with col3:
        st.metric("過濾髒資料比例", f"{(1 - len(df_valid) / len(df_raw)) * 100:.1f}%")

    st.subheader("💡 資料清洗決策說明")
    st.info(
        """
    - **缺失值處理**：過濾掉 25% 缺乏 `CustomerID` 的散客交易，以利精準追蹤會員個人行為。
    - **異常值處理**：識別並分離退貨（數量 <= 0）與 0 元促銷贈品，確保營收分析之準確性。
    """
    )
    st.subheader("乾淨數據預覽 (前 100 筆)")
    st.dataframe(df_valid.head(100), use_container_width=True)

with tab3:
    st.header(f"📈 營運商務指標 - {filter_label}")

    total_revenue = df_filtered["TotalAmount"].sum()
    unique_customers = df_filtered["CustomerID"].nunique()
    total_orders = df_filtered["InvoiceNo"].nunique()
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 總營業額 (Revenue)", f"£{total_revenue:,.2f}")
    with col2:
        st.metric("👥 消費會員數", f"{unique_customers:,} 人")
    with col3:
        st.metric("📦 成立訂單數", f"{total_orders:,} 筆")
    with col4:
        st.metric("💵 平均客單價 (AOV)", f"£{average_order_value:,.2f}")

    st.markdown("---")
    st.subheader("🏆 當前市場熱銷商品 Top 10 (依銷售總數量)")

    if len(df_filtered) > 0:
        top_10 = df_filtered.groupby(["StockCode", "Description"])["Quantity"].sum().reset_index()
        top_10 = top_10.sort_values(by="Quantity", ascending=False).head(10)

        fig_top, ax_top = plt.subplots(figsize=(10, 4))
        sns.barplot(x="Quantity", y="Description", data=top_10, palette="Blues_r", ax=ax_top)
        ax_top.set_xlabel("Sales Quantity")
        ax_top.set_ylabel("Product Description")
        st.pyplot(fig_top)
    else:
        st.warning("當前篩選條件下無數據。")

with tab4:
    st.header(f"💎 RFM 客群價值分級 - {filter_label}")

    if len(df_filtered) > 0:
        snapshot_date = df_valid["InvoiceDate"].max() + dt.timedelta(days=1)
        rfm = (
            df_filtered.groupby("CustomerID")
            .agg(
                {
                    "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
                    "InvoiceNo": "nunique",
                    "TotalAmount": "sum",
                }
            )
            .reset_index()
        )
        rfm.columns = ["CustomerID", "Recency", "Frequency", "Monetary"]

        try:
            rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
            rfm["F_Score"] = pd.qcut(
                rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
            ).astype(int)
            rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
        except Exception:
            rfm["R_Score"] = 3
            rfm["F_Score"] = 3
            rfm["M_Score"] = 3

        def segment_customer(row):
            r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
            if r >= 4 and f >= 4 and m >= 4:
                return "重要價值客戶 (Champions)"
            if r >= 3 and f >= 3 and m >= 3:
                return "一般保持客戶 (Loyal)"
            if r >= 4 and f <= 2:
                return "潛力新客戶 (New)"
            if r <= 2 and m >= 4:
                return "重要挽留客戶 (At Risk)"
            if r <= 2 and f <= 2 and m <= 2:
                return "流失客戶 (Lost)"
            return "其他一般客群 (Others)"

        rfm["Segment"] = rfm.apply(segment_customer, axis=1)

        segment_stats = (
            rfm.groupby("Segment")
            .agg({"CustomerID": "count", "Monetary": "sum"})
            .reset_index()
        )
        segment_stats.columns = ["Segment", "客戶人數", "總貢獻金額"]
        segment_stats["人數佔比"] = segment_stats["客戶人數"] / segment_stats["客戶人數"].sum()
        segment_stats["金額佔比"] = segment_stats["總貢獻金額"] / segment_stats["總貢獻金額"].sum()

        st.dataframe(
            segment_stats.style.format(
                {"總貢獻金額": "£{:,.2f}", "人數佔比": "{:.2%}", "金額佔比": "{:.2%}"}
            ),
            use_container_width=True,
        )

        fig_rfm, ax1 = plt.subplots(figsize=(10, 4))
        ax1.set_xlabel("Customer Segments")
        ax1.set_ylabel("Percentage of Customers", color="#4C72B0")
        ax1.bar(segment_stats["Segment"], segment_stats["人數佔比"], color="#4C72B0", alpha=0.6)
        ax1.tick_params(axis="x", rotation=15)

        ax2 = ax1.twinx()
        ax2.set_ylabel("Percentage of Revenue", color="#C44E52")
        ax2.plot(
            segment_stats["Segment"],
            segment_stats["金額佔比"],
            color="#C44E52",
            marker="o",
            linewidth=2,
        )
        st.pyplot(fig_rfm)
    else:
        st.warning("無足夠客戶數據進行 RFM 分類。")

with tab5:
    render_market_basket(df_filtered, filter_label)

with tab6:
    render_cohort_analysis(df_filtered, filter_label)

with tab7:
    render_churn_prediction(df_filtered, df_valid, filter_label)

with tab8:
    st.header("🌍 全球各國銷售貢獻與市場版圖")

    date_mask = (df_valid["InvoiceDate"].dt.date >= start_date) & (
        df_valid["InvoiceDate"].dt.date <= end_date
    )
    df_geo = df_valid[date_mask]

    country_stats = (
        df_geo.groupby("Country")
        .agg({"TotalAmount": "sum", "CustomerID": "nunique", "InvoiceNo": "nunique"})
        .reset_index()
        .rename(
            columns={
                "TotalAmount": "國家總營收",
                "CustomerID": "獨立客戶數",
                "InvoiceNo": "總訂單數",
            }
        )
    )

    country_stats = country_stats.sort_values(by="國家總營收", ascending=False)
    country_stats["營收全球佔比"] = country_stats["國家總營收"] / country_stats["國家總營收"].sum()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📊 跨國營收排行榜 (Top 10)")
        st.dataframe(
            country_stats.head(10).style.format(
                {"國家總營收": "£{:,.2f}", "營收全球佔比": "{:.2%}"}
            ),
            use_container_width=True,
        )

    with col2:
        st.subheader("💡 地區數據市場洞察")
        uk_rows = country_stats[country_stats["Country"] == "United Kingdom"]
        if len(uk_rows) > 0:
            uk_revenue = uk_rows["營收全球佔比"].values[0]
            st.warning(
                f"""
        - **核心母市場**：英國 (United Kingdom) 貢獻了全球高達 **{uk_revenue * 100:.1f}%** 的營收，為絕對主力市場。
        - **海外潛力市場**：除英國外，**Germany (德國)**、**France (法國)** 與 **EIRE (愛爾蘭)** 為前三大海外批發核心國家，具有高度增長潛力。
        """
            )
        else:
            st.info("此日期區間內無英國市場資料。")

    st.subheader("✈️ 核心海外市場營收規模對比 (不含英國)")
    overseas_top5 = country_stats[country_stats["Country"] != "United Kingdom"].head(5)

    if len(overseas_top5) > 0:
        fig_geo, ax_geo = plt.subplots(figsize=(10, 4))
        sns.barplot(x="國家總營收", y="Country", data=overseas_top5, palette="flare", ax=ax_geo)
        ax_geo.set_xlabel("Total Revenue (£)")
        ax_geo.set_ylabel("Country")
        st.pyplot(fig_geo)
    else:
        st.warning("此區間無海外市場資料。")

with tab9:
    st.header(f"📉 迴歸分析與預測 - {filter_label}")

    if len(df_filtered) == 0:
        st.warning("當前篩選條件下無數據，無法進行迴歸分析。")
    else:
        st.subheader("📅 月營收趨勢預測（線性迴歸）")
        st.caption("將每月營收對時間進行線性迴歸，觀察營收成長趨勢並外推未來預測值。")

        monthly = df_filtered.copy()
        monthly["YearMonth"] = monthly["InvoiceDate"].dt.to_period("M")
        monthly_rev = monthly.groupby("YearMonth")["TotalAmount"].sum().reset_index()
        monthly_rev.columns = ["YearMonth", "Revenue"]
        monthly_rev["MonthIndex"] = np.arange(len(monthly_rev))

        if len(monthly_rev) < 3:
            st.warning("月份數據不足（至少需要 3 個月），無法進行月營收迴歸分析。")
        else:
            X_month = monthly_rev[["MonthIndex"]]
            y_month = monthly_rev["Revenue"]

            model_month = LinearRegression()
            model_month.fit(X_month, y_month)
            monthly_rev["Predicted"] = model_month.predict(X_month)

            r2_month = r2_score(y_month, monthly_rev["Predicted"])
            mae_month = mean_absolute_error(y_month, monthly_rev["Predicted"])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("R² 決定係數", f"{r2_month:.3f}")
            with col2:
                st.metric("每月營收變化（斜率）", f"£{model_month.coef_[0]:,.2f}")
            with col3:
                st.metric("平均預測誤差 (MAE)", f"£{mae_month:,.2f}")

            trend = "成長" if model_month.coef_[0] > 0 else "下滑"
            st.info(
                f"""
            **解讀**：在 **{selected_country}** 市場，月營收呈現 **{trend}** 趨勢。
            每經過一個月，營收平均變化 **£{model_month.coef_[0]:,.2f}**（R² = {r2_month:.3f}）。
            R² 越接近 1 代表趨勢線越能解釋實際營收變化。
            """
            )

            fig_month, ax_month = plt.subplots(figsize=(10, 4))
            x_labels = monthly_rev["YearMonth"].astype(str)
            ax_month.plot(x_labels, y_month, label="實際營收", marker="o", color="#4C72B0")
            ax_month.plot(
                x_labels,
                monthly_rev["Predicted"],
                label="迴歸預測",
                linestyle="--",
                color="#C44E52",
                linewidth=2,
            )
            ax_month.set_xlabel("月份")
            ax_month.set_ylabel("營收 (£)")
            ax_month.legend()
            ax_month.tick_params(axis="x", rotation=45)
            st.pyplot(fig_month)

            future_steps = 3
            last_index = monthly_rev["MonthIndex"].max()
            future_index = np.arange(last_index + 1, last_index + 1 + future_steps).reshape(-1, 1)
            future_pred = model_month.predict(future_index)
            last_period = monthly_rev["YearMonth"].iloc[-1]
            future_periods = [str(last_period + i) for i in range(1, future_steps + 1)]

            st.subheader("🔮 未來 3 個月營收預測（外推）")
            future_df = pd.DataFrame({"預測月份": future_periods, "預測營收 (£)": future_pred})
            st.dataframe(
                future_df.style.format({"預測營收 (£)": "£{:,.2f}"}),
                use_container_width=True,
            )

        st.markdown("---")

        st.subheader("💎 RFM 多元迴歸分析")
        st.caption("以 Frequency（消費次數）與 Recency（距上次消費天數）預測 Monetary（消費總金額）。")

        snapshot_date = df_valid["InvoiceDate"].max() + dt.timedelta(days=1)
        rfm_reg = (
            df_filtered.groupby("CustomerID")
            .agg(
                {
                    "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
                    "InvoiceNo": "nunique",
                    "TotalAmount": "sum",
                }
            )
            .reset_index()
        )
        rfm_reg.columns = ["CustomerID", "Recency", "Frequency", "Monetary"]

        if len(rfm_reg) < 10:
            st.warning("客戶數不足（至少需要 10 人），無法進行 RFM 多元迴歸分析。")
        else:
            X_rfm = rfm_reg[["Frequency", "Recency"]]
            y_rfm = rfm_reg["Monetary"]

            model_rfm = LinearRegression()
            model_rfm.fit(X_rfm, y_rfm)
            rfm_reg["Predicted"] = model_rfm.predict(X_rfm)

            r2_rfm = r2_score(y_rfm, rfm_reg["Predicted"])
            mae_rfm = mean_absolute_error(y_rfm, rfm_reg["Predicted"])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("R² 決定係數", f"{r2_rfm:.3f}")
            with col2:
                st.metric("Frequency 係數", f"{model_rfm.coef_[0]:,.2f}")
            with col3:
                st.metric("Recency 係數", f"{model_rfm.coef_[1]:,.2f}")
            with col4:
                st.metric("平均預測誤差 (MAE)", f"£{mae_rfm:,.2f}")

            st.info(
                f"""
            **解讀**：
            - **Frequency 係數 {model_rfm.coef_[0]:,.2f}**：消費次數每增加 1 次，預期消費金額變化 **£{model_rfm.coef_[0]:,.2f}**
            - **Recency 係數 {model_rfm.coef_[1]:,.2f}**：距上次消費每多 1 天，預期消費金額變化 **£{model_rfm.coef_[1]:,.2f}**
            - **截距**：£{model_rfm.intercept_:,.2f}
            """
            )

            col1, col2 = st.columns(2)

            with col1:
                fig_freq, ax_freq = plt.subplots(figsize=(8, 4))
                ax_freq.scatter(
                    rfm_reg["Frequency"],
                    rfm_reg["Monetary"],
                    alpha=0.3,
                    color="#4C72B0",
                    label="實際值",
                )
                freq_range = np.linspace(rfm_reg["Frequency"].min(), rfm_reg["Frequency"].max(), 50)
                recency_mean = rfm_reg["Recency"].mean()
                pred_line = model_rfm.predict(
                    pd.DataFrame({"Frequency": freq_range, "Recency": recency_mean})
                )
                ax_freq.plot(
                    freq_range,
                    pred_line,
                    color="#C44E52",
                    linewidth=2,
                    label=f"迴歸線 (Recency={recency_mean:.0f})",
                )
                ax_freq.set_xlabel("Frequency（消費次數）")
                ax_freq.set_ylabel("Monetary（消費金額 £）")
                ax_freq.legend()
                st.pyplot(fig_freq)

            with col2:
                fig_pred, ax_pred = plt.subplots(figsize=(8, 4))
                ax_pred.scatter(y_rfm, rfm_reg["Predicted"], alpha=0.3, color="#4C72B0")
                max_val = max(y_rfm.max(), rfm_reg["Predicted"].max())
                ax_pred.plot([0, max_val], [0, max_val], "--", color="#C44E52", label="完美預測線")
                ax_pred.set_xlabel("實際消費金額 (£)")
                ax_pred.set_ylabel("預測消費金額 (£)")
                ax_pred.legend()
                st.pyplot(fig_pred)

render_export_sidebar(df_filtered, filter_label)
