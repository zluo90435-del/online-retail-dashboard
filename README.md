# Online Retail Analytics Platform

跨國電商商業智慧（BI）分析平台 — 結合 **MS SQL Server**、**ETL**、**Stored Procedure** 與 **Streamlit** 互動儀表板，對 54 萬筆交易資料進行清洗、分析與視覺化。

🔗 **線上展示**：[https://online-retail-dashboard-kkcqmfkdidngaze34tjjhk.streamlit.app](https://online-retail-dashboard-kkcqmfkdidngaze34tjjhk.streamlit.app)

---

## 專案簡介

本專案以英國電商 **Online Retail** 資料集（541,909 筆）為基礎，模擬企業 BI 工作流程：

1. 以 **ETL** 將原始 Excel 匯入 **MS SQL Server**
2. 以 **Stored Procedure** 完成資料清洗
3. 以 **Streamlit** 建立互動式分析儀表板
4. 部署至 **Streamlit Cloud** 供線上展示

適用於電商營運 KPI 監控、RFM 客群分群、營收趨勢預測與跨國市場策略分析。

---

## 系統架構

```
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
```

---

## 儀表板功能

| 分頁 | 功能 |
|------|------|
| 主管營運總覽 | 一頁式 KPI、月營收趨勢、策略洞察、熱銷 Top 5 |
| 資料品質監控 | 缺失值/異常值檢核、清洗成效、覆蓋期間 |
| 資料基本狀況 | 原始/清洗筆數、髒資料比例、資料預覽 |
| 核心營運 KPI | 營收、會員數、訂單數、AOV、熱銷商品 Top 10 |
| RFM 會員分類 | Champions / Loyal / At Risk / Lost 等客群分級 |
| 購物籃分析 | 商品共現組合、支持度、信心度、搭售建議 |
| 同期群留存 | Cohort 熱力圖、各月留存率、获客品質洞察 |
| 流失預警 | 邏輯迴歸模型、AUC、高風險挽留名單 |
| 全球市場地區分析 | 各國營收排行、海外市場貢獻比較 |
| 迴歸分析與預測 | 月營收線性迴歸、RFM 多元迴歸 |

側邊欄支援**跨國市場 + 日期區間動態篩選**，並提供 **Excel 報表一鍵匯出**。

---

## Phase 3 進階功能

| 功能 | 說明 |
|------|------|
| Excel 報表匯出 | 側邊欄下載主管營運、市場分析、交易明細 |
| 雲端資料庫支援 | 透過 Streamlit Secrets 連線 Azure SQL |
| ETL 排程腳本 | `run_etl.bat` 供 Windows 工作排程器使用 |

---

## 資料統計

| 項目 | 筆數 |
|------|------|
| 原始交易資料 | 541,909 |
| 清洗後有效資料 | 397,884 |
| 涵蓋國家 | 37+ |
| 資料期間 | 2010–2011 |

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 資料庫 | MS SQL Server、T-SQL、Stored Procedure、View |
| ETL | Python（pandas、pyodbc） |
| 分析 | RFM 模型、購物籃分析、同期群留存、邏輯迴歸流失預警、線性迴歸（scikit-learn） |
| 視覺化 | Streamlit、**Power BI**、matplotlib、seaborn |
| 部署 | GitHub、Streamlit Community Cloud |

---

## Power BI 儀表板

本專案提供 Power BI 專用 SQL Views 與完整設定指南，可建立企業級 BI 報表：

- 設定指南：[`powerbi/POWERBI_SETUP.md`](powerbi/POWERBI_SETUP.md)
- 資料來源 Views：`sql/03_powerbi_views.sql`

```
Power BI Desktop → localhost / OnlineRetailDB → Import Views → 建立 KPI / RFM / 市場分析報表
```

---

## 專案結構

```
MyRetailDatas/
├── app.py                          # Streamlit 儀表板主程式
├── app_imports.py                  # 相容本機 modules/ 與 GitHub 根目錄匯入
├── modules/                        # 分析模組（本機開發用）
│   ├── data_loader.py
│   ├── filters.py
│   ├── kpi.py
│   ├── executive_summary.py
│   ├── market_basket.py
│   ├── cohort.py
│   ├── churn.py
│   ├── data_quality.py
│   └── export_utils.py
├── data_loader.py                  # 同上模組（GitHub 根目錄部署用）
├── export_utils.py
├── executive_summary.py
├── filters.py
├── kpi.py
├── market_basket.py
├── cohort.py
├── run_etl.bat                     # ETL 排程腳本
├── .streamlit/
│   └── secrets.toml.example        # 雲端 DB 設定範例
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
```

---

## 本機執行

### 前置需求

- Python 3.10+
- MS SQL Server（本機已安裝 SSMS）
- ODBC Driver 17 for SQL Server

### Step 1：匯入資料到 SQL Server

```powershell
pip install -r requirements.txt
python etl_import.py
```

### Step 2：啟動儀表板

```powershell
python -m streamlit run app.py
```

瀏覽器開啟 `http://localhost:8501`，側邊欄應顯示 **MS SQL Server (OnlineRetailDB)**。

### SSMS 驗證

```sql
USE OnlineRetailDB;
SELECT COUNT(*) FROM dbo.SalesRaw;           -- 541,909
SELECT COUNT(*) FROM dbo.vw_SalesClean;      -- 397,884
EXEC dbo.sp_GetCleanSales @Country = N'United Kingdom';
```

---

## 線上部署說明

- **Streamlit Cloud** 預設無法連線至本機 SQL Server，線上版自動切換為 **Excel 備援模式**
- 側邊欄顯示 `Excel 檔案 (備援模式)` 屬正常現象
- 本機版與線上版分析結果一致

### 雲端資料庫（選用）

若已部署 **Azure SQL**，可在 Streamlit Cloud → **Settings → Secrets** 貼上：

```toml
[sql]
server = "your-server.database.windows.net"
database = "OnlineRetailDB"
username = "your_username"
password = "your_password"
driver = "ODBC Driver 17 for SQL Server"
```

範例檔：`.streamlit/secrets.toml.example`

設定成功後，側邊欄會顯示 **Cloud SQL Server (OnlineRetailDB)**。

### ETL 自動排程（本機）

以 Windows 工作排程器每日執行：

```powershell
# 動作程式：專案路徑\run_etl.bat
run_etl.bat
```

---

## 對應 BI 工程師職能

| 職缺要求 | 本專案實作 |
|----------|------------|
| ETL 資料清理 | `etl_import.py` 匯入與型別轉換 |
| SQL 撈取與建立 | 建表、索引、查詢 |
| Stored Procedure | `sp_GetCleanSales`、`sp_GetDataSummary` |
| BI 報表工具 | Streamlit 互動儀表板 + Excel 報表匯出 |
| 資料探勘 | RFM、購物籃、同期群、流失預警、線性迴歸 |
| 自動化 | ETL 排程腳本、Streamlit Secrets 雲端 DB |

---

## 作者

羅真蘊 — BI / 資料分析作品集
