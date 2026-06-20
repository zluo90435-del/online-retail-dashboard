Online Retail Analytics Platform

跨國電商商業智慧（BI）分析平台 — 結合 MS SQL Server、ETL、Stored Procedure 與 Streamlit 互動儀表板，對 54 萬筆交易資料進行清洗、分析與視覺化。

🔗 線上展示：https://online-retail-dashboard-kkcqmfkdidngaze34tjjhk.streamlit.app



專案簡介

本專案以英國電商 Online Retail 資料集（541,909 筆）為基礎，模擬企業 BI 工作流程：





以 ETL 將原始 Excel 匯入 MS SQL Server



以 Stored Procedure 完成資料清洗



以 Streamlit 建立互動式分析儀表板



部署至 Streamlit Cloud 供線上展示

適用於電商營運 KPI 監控、RFM 客群分群、營收趨勢預測與跨國市場策略分析。



系統架構

OnlineRetail.xlsx（原始資料）
        │
        ▼  ETL 匯入（etl_import.py）
┌───────────────────────────────┐
│   MS SQL Server (OnlineRetailDB) │
│   ├── SalesRaw（原始表）          │
│   ├── vw_SalesClean（清洗 View）  │
│   └── sp_GetCleanSales（SP）     │
└───────────────────────────────┘
        │
        ├─► Streamlit 本機版（讀取 SQL Server）
        └─► Streamlit Cloud 線上版（Excel 備援模式）



儀表板功能







分頁



功能





主管營運總覽



一頁式 KPI、月營收趨勢、策略洞察、熱銷 Top 5





資料品質監控



缺失值/異常值檢核、清洗成效、覆蓋期間





資料基本狀況



原始/清洗筆數、髒資料比例、資料預覽





核心營運 KPI



營收、會員數、訂單數、AOV、熱銷商品 Top 10





RFM 會員分類



Champions / Loyal / At Risk / Lost 等客群分級





購物籃分析



商品共現組合、支持度、信心度、搭售建議





同期群留存



Cohort 熱力圖、各月留存率、获客品質洞察





流失預警



邏輯迴歸模型、AUC、高風險挽留名單





全球市場地區分析



各國營收排行、海外市場貢獻比較





迴歸分析與預測



月營收線性迴歸、RFM 多元迴歸

側邊欄支援跨國市場 + 日期區間動態篩選，所有分析可聯動切換。



資料統計







項目



筆數





原始交易資料



541,909





清洗後有效資料



397,884





涵蓋國家



37+





資料期間



2010–2011



技術棧







類別



技術





資料庫



MS SQL Server、T-SQL、Stored Procedure、View





ETL



Python（pandas、pyodbc）





分析



RFM 模型、購物籃分析、同期群留存、邏輯迴歸流失預警、線性迴歸（scikit-learn）





視覺化



Streamlit、Power BI、matplotlib、seaborn





部署



GitHub、Streamlit Community Cloud



Power BI 儀表板

本專案提供 Power BI 專用 SQL Views 與完整設定指南，可建立企業級 BI 報表：





設定指南：[powerbi/POWERBI_SETUP.md](powerbi/POWERBI_SETUP.md)



資料來源 Views：sql/03_powerbi_views.sql

Power BI Desktop → localhost / OnlineRetailDB → Import Views → 建立 KPI / RFM / 市場分析報表



專案結構

MyRetailDatas/
├── app.py                          # Streamlit 儀表板主程式
├── modules/                        # 分析模組
│   ├── data_loader.py
│   ├── filters.py
│   ├── kpi.py
│   ├── executive_summary.py
│   ├── market_basket.py
│   ├── cohort.py
│   ├── churn.py
│   └── data_quality.py
├── etl_import.py                   # ETL：Excel → MS SQL 匯入腳本
├── requirements.txt                # Python 套件
├── packages.txt                    # Streamlit Cloud 字型套件
├── OnlineRetail.xlsx               # 原始資料（線上展示用）
├── NotoSansCJKtc-Regular.otf       # 繁體中文字型
├── sql/
│   ├── 01_create_database.sql      # 建庫建表
│   ├── 02_stored_procedures.sql    # View + Stored Procedure
│   └── 03_powerbi_views.sql        # Power BI 專用 Views
└── powerbi/
    └── POWERBI_SETUP.md            # Power BI 逐步設定指南



本機執行

前置需求





Python 3.10+



MS SQL Server（本機已安裝 SSMS）



ODBC Driver 17 for SQL Server

Step 1：匯入資料到 SQL Server

pip install -r requirements.txt
python etl_import.py

Step 2：啟動儀表板

python -m streamlit run app.py

瀏覽器開啟 http://localhost:8501，側邊欄應顯示 MS SQL Server (OnlineRetailDB)。

SSMS 驗證

USE OnlineRetailDB;
SELECT COUNT(*) FROM dbo.SalesRaw;           -- 541,909
SELECT COUNT(*) FROM dbo.vw_SalesClean;      -- 397,884
EXEC dbo.sp_GetCleanSales @Country = N'United Kingdom';



線上部署說明





Streamlit Cloud 無法連線至本機 SQL Server，線上版自動切換為 Excel 備援模式



側邊欄顯示 Excel 檔案 (備援模式) 屬正常現象



本機版與線上版分析結果一致



對應 BI 工程師職能







職缺要求



本專案實作





ETL 資料清理



etl_import.py 匯入與型別轉換





SQL 撈取與建立



建表、索引、查詢





Stored Procedure



sp_GetCleanSales、sp_GetDataSummary





BI 報表工具



Streamlit 互動儀表板





資料探勘



RFM 分群、線性迴歸預測



作者

羅真蘊 — BI / 資料分析作品集
