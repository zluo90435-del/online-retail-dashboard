import datetime as dt

import pandas as pd
import streamlit as st


def render_sidebar_filters(df_valid: pd.DataFrame, data_source: str) -> tuple[pd.DataFrame, str, dt.date, dt.date, str]:
    """渲染側邊欄篩選器，回傳篩選後資料與篩選條件摘要。"""
    st.sidebar.header("🌍 跨國市場動態篩選")
    st.sidebar.caption(f"資料來源：{data_source}")

    country_list = ["全部國家 (All)"] + sorted(df_valid["Country"].dropna().unique().tolist())
    selected_country = st.sidebar.selectbox("選擇要分析的國家/地區：", country_list)

    min_date = df_valid["InvoiceDate"].min().date()
    max_date = df_valid["InvoiceDate"].max().date()
    date_range = st.sidebar.date_input(
        "選擇日期區間：",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]

    df_filtered = df_valid.copy()
    if selected_country != "全部國家 (All)":
        df_filtered = df_filtered[df_filtered["Country"] == selected_country]

    df_filtered = df_filtered[
        (df_filtered["InvoiceDate"].dt.date >= start_date)
        & (df_filtered["InvoiceDate"].dt.date <= end_date)
    ]

    filter_label = f"{selected_country} | {start_date} ~ {end_date}"
    return df_filtered, filter_label, start_date, end_date, selected_country
