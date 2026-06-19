import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt

# 1. 網頁基本設定
st.set_page_config(
    page_title="Online Retail Analytics Platform",
    page_icon="📊",
    layout="wide"
)

# 2. 標題與專案簡介
st.title("📊 Online Retail Analytics & Market Strategy Dashboard")
st.markdown("""
這個專案展示了如何利用 **Python Streamlit** 結合 AI 輔助工具（Cursor），將 **54 萬筆原始跨國電商交易數據**，
經過資料清洗、特徵工程後，建立核心營運 KPI 儀表板，並透過 **RFM 模型** 與 **地理區域資料** 進行跨國市場分析與增長策略擬定。
""")

# 加載資料的快取機制 (加速網頁讀取)

@st.cache_data
def load_and_clean_data():
    df = pd.read_excel('OnlineRetail.xlsx')
    
    # 🌟 【新增這行】強制將 StockCode 轉換為字串格式，解決 pyarrow 報錯問題
    df['StockCode'] = df['StockCode'].astype(str)
    
    # 資料清洗流程
    df_clean = df.dropna(subset=['CustomerID']).copy()
    df_valid = df_clean[(df_clean['Quantity'] > 0) & (df_clean['UnitPrice'] > 0)].copy()
    
    # 特徵工程
    df_valid['TotalAmount'] = df_valid['Quantity'] * df_valid['UnitPrice']
    return df, df_valid

# 載入資料
try:
    df_raw, df_valid = load_and_clean_data()
except Exception as e:
    st.error(f"找不到資料檔案 'OnlineRetail.xlsx'，請確認檔案是否放在同一個資料夾。錯誤訊息: {e}")
    st.stop()

# ==========================================
# 全域側邊欄 (Sidebar)：跨國市場篩選器
# ==========================================
st.sidebar.header("🌍 跨國市場動態篩選")
country_list = ["全部國家 (All)"] + list(df_valid['Country'].unique())
selected_country = st.sidebar.selectbox("選擇要分析的國家/地區：", country_list)

# 根據選取的國家篩選資料
if selected_country == "全部國家 (All)":
    df_filtered = df_valid
else:
    df_filtered = df_valid[df_valid['Country'] == selected_country]


# 3. 建立分頁
tab1, tab2, tab3, tab4 = st.tabs(["🧹 資料基本狀況", "📈 核心營運 KPI", "💎 RFM 會員分類", "🌍 全球市場地區分析"])

# ==========================================
# 分頁一：資料基本狀況
# ==========================================
with tab1:
    st.header("數據清洗與預處理報告")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("原始數據總筆數", f"{len(df_raw):,}")
    with col2:
        st.metric("剔除匿名客/異常後筆數", f"{len(df_valid):,}")
    with col3:
        st.metric("過濾髒資料比例", f"{(1 - len(df_valid)/len(df_raw))*100:.1f}%")
        
    st.subheader("💡 資料清洗決策說明")
    st.info("""
    - **缺失值處理**：過濾掉 25% 缺乏 `CustomerID` 的散客交易，以利精準追蹤會員個人行為。
    - **異常值處理**：識別並分離退貨（數量 <= 0）與 0 元促銷贈品，確保營收分析之準確性。
    """)
    st.subheader("乾淨數據預覽 (前 100 筆)")
    st.dataframe(df_valid.head(100), use_container_width=True)

# ==========================================
# 分頁二：核心營運 KPI (會隨國家聯動)
# ==========================================
with tab2:
    st.header(f"📈 營運商務指標 - {selected_country}")
    
    # 計算 KPI
    total_revenue = df_filtered['TotalAmount'].sum()
    unique_customers = df_filtered['CustomerID'].nunique()
    total_orders = df_filtered['InvoiceNo'].nunique()
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
        top_10 = df_filtered.groupby(['StockCode', 'Description'])['Quantity'].sum().reset_index()
        top_10 = top_10.sort_values(by='Quantity', ascending=False).head(10)
        
        fig_top, ax_top = plt.subplots(figsize=(10, 4))
        sns.barplot(x='Quantity', y='Description', data=top_10, palette='Blues_r', ax=ax_top)
        ax_top.set_xlabel("Sales Quantity")
        ax_top.set_ylabel("Product Description")
        st.pyplot(fig_top)
    else:
        st.warning("當前篩選條件下無數據。")

# ==========================================
# 分頁三：RFM 會員分類 (會隨國家聯動)
# ==========================================
with tab3:
    st.header(f"💎 RFM 客群價值分級 - {selected_country}")
    
    if len(df_filtered) > 0:
        # RFM 計算
        snapshot_date = df_valid['InvoiceDate'].max() + dt.timedelta(days=1)
        rfm = df_filtered.groupby('CustomerID').agg({
            'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
            'InvoiceNo': 'nunique',
            'TotalAmount': 'sum'
        }).reset_index()
        rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
        
        # 為了避免某些國家人數太少無法切分五等分，加入適當排錯
        try:
            rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
            rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
            rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
        except:
            # 人數過少時的保底設定
            rfm['R_Score'] = 3
            rfm['F_Score'] = 3
            rfm['M_Score'] = 3
        
        # 分類標籤
        def segment_customer(df):
            r, f, m = df['R_Score'], df['F_Score'], df['M_Score']
            if r >= 4 and f >= 4 and m >= 4: return '重要價值客戶 (Champions)'
            elif r >= 3 and f >= 3 and m >= 3: return '一般保持客戶 (Loyal)'
            elif r >= 4 and f <= 2: return '潛力新客戶 (New)'
            elif r <= 2 and m >= 4: return '重要挽留客戶 (At Risk)'
            elif r <= 2 and f <= 2 and m <= 2: return '流失客戶 (Lost)'
            else: return '其他一般客群 (Others)'
            
        rfm['Segment'] = rfm.apply(segment_customer, axis=1)
        
        # 統計
        segment_stats = rfm.groupby('Segment').agg({'CustomerID': 'count', 'Monetary': 'sum'}).reset_index()
        segment_stats.columns = ['Segment', '客戶人數', '總貢獻金額']
        segment_stats['人數佔比'] = segment_stats['客戶人數'] / segment_stats['客戶人數'].sum()
        segment_stats['金額佔比'] = segment_stats['總貢獻金額'] / segment_stats['總貢獻金額'].sum()
        
        st.dataframe(segment_stats.style.format({
            '總貢獻金額': '£{:,.2f}', '人數佔比': '{:.2%}', '金額佔比': '{:.2%}'
        }), use_container_width=True)
        
        # 繪圖
        fig_rfm, ax1 = plt.subplots(figsize=(10, 4))
        ax1.set_xlabel('Customer Segments')
        ax1.set_ylabel('Percentage of Customers', color='#4C72B0')
        ax1.bar(segment_stats['Segment'], segment_stats['人數佔比'], color='#4C72B0', alpha=0.6)
        ax1.tick_params(axis='x', rotation=15)
        
        ax2 = ax1.twinx()
        ax2.set_ylabel('Percentage of Revenue', color='#C44E52')
        ax2.plot(segment_stats['Segment'], segment_stats['金額佔比'], color='#C44E52', marker='o', linewidth=2)
        st.pyplot(fig_rfm)
    else:
        st.warning("無足夠客戶數據進行 RFM 分類。")

# ==========================================
# 分頁四：全球市場地區分析 (最核心的新增功能)
# ==========================================
with tab4:
    st.header("🌍 全球各國銷售貢獻與市場版圖")
    
    # 統計每個國家的總營收、客戶數、訂單數
    country_stats = df_valid.groupby('Country').agg({
        'TotalAmount': 'sum',
        'CustomerID': 'nunique',
        'InvoiceNo': 'nunique'
    }).reset_index().rename(columns={
        'TotalAmount': '國家總營收',
        'CustomerID': '獨立客戶數',
        'InvoiceNo': '總訂單數'
    })
    
    country_stats = country_stats.sort_values(by='國家總營收', ascending=False)
    country_stats['營收全球佔比'] = country_stats['國家總營收'] / country_stats['國家總營收'].sum()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 跨國營收排行榜 (Top 10)")
        st.dataframe(country_stats.head(10).style.format({
            '國家總營收': '£{:,.2f}',
            '營收全球佔比': '{:.2%}'
        }), use_container_width=True)
        
    with col2:
        st.subheader("💡 地區數據市場洞察")
        uk_revenue = country_stats[country_stats['Country'] == 'United Kingdom']['營收全球佔比'].values[0]
        st.warning(f"""
        - **核心母市場**：英國 (United Kingdom) 貢獻了全球高達 **{uk_revenue*100:.1f}%** 的營收，為絕對主力市場。
        - **海外潛力市場**：除英國外，**Germany (德國)**、**France (法國)** 與 **EIRE (愛爾蘭)** 為前三大海外批發核心國家，具有高度增長潛力。
        """)
        
    # 畫出前五大海外市場的營收對比（剔除英國，因為英國太高會壓扁圖表）
    st.subheader("✈️ 核心海外市場營收規模對比 (不含英國)")
    overseas_top5 = country_stats[country_stats['Country'] != 'United Kingdom'].head(5)
    
    fig_geo, ax_geo = plt.subplots(figsize=(10, 4))
    sns.barplot(x='國家總營收', y='Country', data=overseas_top5, palette='flare', ax=ax_geo)
    ax_geo.set_xlabel("Total Revenue (£)")
    ax_geo.set_ylabel("Country")
    st.pyplot(fig_geo)