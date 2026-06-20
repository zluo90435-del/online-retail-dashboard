import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


@st.cache_data
def build_churn_dataset(df: pd.DataFrame, snapshot_date: dt.datetime, churn_days: int) -> pd.DataFrame:
    """依 RFM 特徵建立流失標籤與風險分數資料集。"""
    if df.empty:
        return pd.DataFrame()

    rfm = (
        df.groupby("CustomerID")
        .agg(
            {
                "InvoiceDate": ["min", "max"],
                "InvoiceNo": "nunique",
                "TotalAmount": "sum",
            }
        )
        .reset_index()
    )
    rfm.columns = [
        "CustomerID",
        "FirstPurchase",
        "LastPurchase",
        "Frequency",
        "Monetary",
    ]
    rfm["Recency"] = (snapshot_date - rfm["LastPurchase"]).dt.days
    rfm["Tenure"] = (rfm["LastPurchase"] - rfm["FirstPurchase"]).dt.days
    rfm["Churned"] = (rfm["Recency"] >= churn_days).astype(int)
    return rfm


def render_churn_prediction(
    df_filtered: pd.DataFrame,
    df_valid: pd.DataFrame,
    filter_label: str,
) -> None:
    """渲染流失預警分頁。"""
    st.header(f"⚠️ 流失預警模型 — {filter_label}")
    st.caption(
        "以 Recency、Frequency、Monetary 等特徵訓練邏輯迴歸模型，"
        "辨識高流失風險客戶並提供挽留名單。"
    )

    if df_filtered.empty:
        st.warning("當前篩選條件下無數據，無法進行流失預測。")
        return

    churn_days = st.slider("流失定義：超過幾天未消費視為流失？", 30, 180, 90, step=15)
    snapshot_date = df_valid["InvoiceDate"].max() + dt.timedelta(days=1)
    rfm = build_churn_dataset(df_filtered, snapshot_date, churn_days)

    if len(rfm) < 30:
        st.warning("客戶數不足（至少需要 30 人），無法訓練流失模型。")
        return

    feature_cols = ["Recency", "Frequency", "Monetary", "Tenure"]
    X = rfm[feature_cols]
    y = rfm["Churned"]

    if y.nunique() < 2:
        st.warning("目前資料僅有一種客戶狀態，請調整流失天數或擴大日期區間。")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    auc = roc_auc_score(y_test, y_prob)
    accuracy = accuracy_score(y_test, y_pred)
    churn_rate = y.mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("分析客戶數", f"{len(rfm):,} 人")
    with col2:
        st.metric("流失率", f"{churn_rate:.1f}%")
    with col3:
        st.metric("模型 AUC", f"{auc:.3f}")
    with col4:
        st.metric("測試集準確率", f"{accuracy:.1%}")

    rfm["ChurnRisk"] = model.predict_proba(rfm[feature_cols])[:, 1]
    at_risk = rfm[rfm["ChurnRisk"] >= 0.7].sort_values("ChurnRisk", ascending=False)

    st.subheader("🎯 高風險挽留名單 (風險 ≥ 70%)")
    if at_risk.empty:
        st.success("目前無高風險客戶，客戶留存狀況良好。")
    else:
        display_cols = [
            "CustomerID",
            "Recency",
            "Frequency",
            "Monetary",
            "ChurnRisk",
            "Churned",
        ]
        st.dataframe(
            at_risk[display_cols]
            .head(50)
            .style.format({"Monetary": "£{:,.2f}", "ChurnRisk": "{:.1%}"}),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("📈 特徵係數（影響流失的關鍵因子）")
    coef_df = pd.DataFrame(
        {"特徵": feature_cols, "係數": model.coef_[0]}
    ).sort_values("係數", key=abs, ascending=False)

    fig, ax = plt.subplots(figsize=(8, 3))
    colors = ["#C44E52" if c > 0 else "#4C72B0" for c in coef_df["係數"]]
    ax.barh(coef_df["特徵"], coef_df["係數"], color=colors)
    ax.set_xlabel("邏輯迴歸係數")
    ax.axvline(0, color="gray", linewidth=0.8)
    st.pyplot(fig)

    top_factor = coef_df.iloc[0]
    direction = "提高" if top_factor["係數"] > 0 else "降低"
    st.info(
        f"""
        **解讀**：**{top_factor['特徵']}** 是影響流失的最重要因子（係數 {top_factor['係數']:.4f}）。
        此特徵上升會 **{direction}** 流失機率。建議針對高 Recency（久未消費）客戶
        啟動 EDM 召回或專屬優惠券活動。
        """
    )
