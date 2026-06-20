from collections import Counter
from itertools import combinations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


@st.cache_data
def compute_product_pairs(
    df: pd.DataFrame,
    top_n_products: int = 40,
    min_pair_count: int = 15,
) -> pd.DataFrame:
    """計算購物籃商品組合共現次數與關聯指標。"""
    if df.empty:
        return pd.DataFrame()

    product_order_count = (
        df.groupby("Description")["InvoiceNo"].nunique().sort_values(ascending=False)
    )
    top_products = set(product_order_count.head(top_n_products).index)
    df_subset = df[df["Description"].isin(top_products)]

    baskets = (
        df_subset.groupby("InvoiceNo")["Description"]
        .apply(lambda items: sorted(set(items)))
        .reset_index()
    )

    pair_counter: Counter = Counter()
    product_counter: Counter = Counter()

    for items in baskets["Description"]:
        for item in items:
            product_counter[item] += 1
        if len(items) >= 2:
            for pair in combinations(items, 2):
                pair_counter[pair] += 1

    total_baskets = len(baskets)
    rows = []
    for (product_a, product_b), pair_count in pair_counter.most_common():
        if pair_count < min_pair_count:
            continue
        rows.append(
            {
                "商品 A": product_a,
                "商品 B": product_b,
                "共現訂單數": pair_count,
                "支持度 (%)": pair_count / total_baskets * 100,
                "A→B 信心度 (%)": pair_count / product_counter[product_a] * 100,
            }
        )

    return pd.DataFrame(rows).head(20)


def render_market_basket(df_filtered: pd.DataFrame, filter_label: str) -> None:
    """渲染購物籃分析分頁。"""
    st.header(f"🛒 購物籃分析 (Market Basket) — {filter_label}")
    st.caption(
        "分析同一筆訂單中經常一起購買的商品組合，協助制定搭售與組合促銷策略。"
    )

    if df_filtered.empty:
        st.warning("當前篩選條件下無數據，無法進行購物籃分析。")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        top_n = st.slider("分析熱門商品數", 20, 60, 40, step=5)
    with col2:
        min_count = st.slider("最低共現訂單數", 5, 50, 15, step=5)
    with col3:
        st.metric("分析訂單數", f"{df_filtered['InvoiceNo'].nunique():,} 筆")

    pairs_df = compute_product_pairs(df_filtered, top_n_products=top_n, min_pair_count=min_count)

    if pairs_df.empty:
        st.warning("找不到足夠的商品組合，請放寬篩選條件或降低最低共現訂單數。")
        return

    st.subheader("🔗 高關聯商品組合 Top 20")
    st.dataframe(
        pairs_df.style.format(
            {
                "支持度 (%)": "{:.2f}%",
                "A→B 信心度 (%)": "{:.1f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("📊 共現次數視覺化 (Top 10)")
    top10 = pairs_df.head(10).copy()
    top10["組合標籤"] = top10.apply(
        lambda row: f"{row['商品 A'][:18]} + {row['商品 B'][:18]}", axis=1
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.barh(top10["組合標籤"], top10["共現訂單數"], color="#55A868")
    ax.set_xlabel("共現訂單數")
    ax.invert_yaxis()
    st.pyplot(fig)

    best = pairs_df.iloc[0]
    st.info(
        f"""
        **搭售建議**：當顧客購買「{best['商品 A']}」時，
        有 **{best['A→B 信心度 (%)']:.1f}%** 的機率也會購買「{best['商品 B']}」。
        可考慮建立組合包或結帳頁交叉銷售。
        """
    )
