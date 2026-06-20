import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st


@st.cache_data
def build_cohort_retention(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """建立同期群留存人數表與留存率表。"""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    work = df[["CustomerID", "InvoiceDate"]].drop_duplicates().copy()
    work["OrderMonth"] = work["InvoiceDate"].dt.to_period("M")
    work["CohortMonth"] = work.groupby("CustomerID")["InvoiceDate"].transform("min").dt.to_period("M")
    work["CohortIndex"] = work.apply(
        lambda row: (row["OrderMonth"] - row["CohortMonth"]).n, axis=1
    )

    cohort_counts = (
        work.groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
        .nunique()
        .reset_index()
        .pivot(index="CohortMonth", columns="CohortIndex", values="CustomerID")
        .fillna(0)
    )

    cohort_pct = cohort_counts.div(cohort_counts[0].replace(0, np.nan), axis=0) * 100
    return cohort_counts, cohort_pct


def render_cohort_analysis(df_filtered: pd.DataFrame, filter_label: str) -> None:
    """渲染同期群留存分析分頁。"""
    st.header(f"📊 同期群留存分析 (Cohort) — {filter_label}")
    st.caption(
        "以顧客「首次消費月份」為同期群，追蹤後續各月的回購留存率，評估获客品質與客戶黏着度。"
    )

    if df_filtered.empty:
        st.warning("當前篩選條件下無數據，無法進行同期群分析。")
        return

    cohort_counts, cohort_pct = build_cohort_retention(df_filtered)

    if cohort_pct.empty:
        st.warning("資料不足以建立同期群矩陣。")
        return

    max_periods = min(6, cohort_pct.shape[1])
    cohort_pct_view = cohort_pct.iloc[:, :max_periods]
    cohort_counts_view = cohort_counts.iloc[:, :max_periods]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("同期群數", f"{len(cohort_pct):,} 組")
    with col2:
        month1_retention = cohort_pct[1].mean() if 1 in cohort_pct.columns else 0
        st.metric("平均第 1 月留存率", f"{month1_retention:.1f}%")
    with col3:
        if cohort_pct.shape[1] >= 3:
            month3_retention = cohort_pct[2].mean()
            st.metric("平均第 3 月留存率", f"{month3_retention:.1f}%")
        else:
            st.metric("平均第 3 月留存率", "N/A")

    st.subheader("🔥 同期群留存率熱力圖 (%)")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(
        cohort_pct_view,
        annot=True,
        fmt=".0f",
        cmap="YlGnBu",
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "留存率 (%)"},
    )
    ax.set_xlabel("同期群經過月數")
    ax.set_ylabel("首次消費月份 (Cohort)")
    ax.set_yticklabels([str(idx) for idx in cohort_pct_view.index], rotation=0)
    st.pyplot(fig)

    st.subheader("📋 同期群留存人數明細")
    st.dataframe(cohort_counts_view.astype(int), use_container_width=True)

    best_cohort = cohort_pct[1].idxmax() if 1 in cohort_pct.columns else None
    if best_cohort is not None:
        st.info(
            f"""
            **洞察**：同期群 **{best_cohort}** 的第 1 月留存率最高（**{cohort_pct.loc[best_cohort, 1]:.1f}%**），
            代表該月獲取的客戶品質較佳，可回顧當時行銷活動作為複製策略。
            """
        )
