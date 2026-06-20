from pathlib import Path

import pandas as pd
import pyodbc
import streamlit as st

SQL_SERVER = r"localhost"
SQL_DATABASE = "OnlineRetailDB"
SQL_DRIVER = "ODBC Driver 17 for SQL Server"


def _resolve_base_dir() -> Path:
    path = Path(__file__).resolve().parent
    if path.name == "modules":
        return path.parent
    return path


BASE_DIR = _resolve_base_dir()
EXCEL_FILE = BASE_DIR / "OnlineRetail.xlsx"


def _get_sql_settings() -> dict:
    """讀取 Streamlit Secrets 或回退本機 SQL Server 設定。"""
    try:
        if "sql" in st.secrets:
            sql = st.secrets["sql"]
            return {
                "server": sql.get("server", SQL_SERVER),
                "database": sql.get("database", SQL_DATABASE),
                "driver": sql.get("driver", SQL_DRIVER),
                "username": sql.get("username"),
                "password": sql.get("password"),
            }
    except Exception:
        pass

    return {
        "server": SQL_SERVER,
        "database": SQL_DATABASE,
        "driver": SQL_DRIVER,
        "username": None,
        "password": None,
    }


def get_sql_connection() -> pyodbc.Connection:
    cfg = _get_sql_settings()
    if cfg.get("username") and cfg.get("password"):
        conn_str = (
            f"DRIVER={{{cfg['driver']}}};"
            f"SERVER={cfg['server']};"
            f"DATABASE={cfg['database']};"
            f"UID={cfg['username']};"
            f"PWD={cfg['password']};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
    else:
        conn_str = (
            f"DRIVER={{{cfg['driver']}}};"
            f"SERVER={cfg['server']};"
            f"DATABASE={cfg['database']};"
            "Trusted_Connection=yes;"
        )
    return pyodbc.connect(conn_str)


def get_data_source_label() -> str:
    cfg = _get_sql_settings()
    if cfg.get("username"):
        return f"Cloud SQL Server ({cfg['database']})"
    return f"MS SQL Server ({cfg['database']})"


def normalize_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    return df


@st.cache_data
def load_from_sql() -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = get_sql_connection()
    df_raw = pd.read_sql(
        """
        SELECT InvoiceNo, StockCode, Description, Quantity,
               InvoiceDate, UnitPrice, CustomerID, Country
        FROM dbo.SalesRaw
        """,
        conn,
    )
    df_valid = pd.read_sql("EXEC dbo.sp_GetCleanSales", conn)
    conn.close()

    df_raw = normalize_dataframe_types(df_raw)
    df_valid = normalize_dataframe_types(df_valid)
    return df_raw, df_valid


@st.cache_data
def load_from_excel() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_excel(EXCEL_FILE, dtype={"InvoiceNo": str, "StockCode": str})
    df_clean = df.dropna(subset=["CustomerID"]).copy()
    df_valid = df_clean[(df_clean["Quantity"] > 0) & (df_clean["UnitPrice"] > 0)].copy()
    df_valid["TotalAmount"] = df_valid["Quantity"] * df_valid["UnitPrice"]
    return normalize_dataframe_types(df), normalize_dataframe_types(df_valid)


@st.cache_data
def load_and_clean_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    try:
        df_raw, df_valid = load_from_sql()
        return df_raw, df_valid, get_data_source_label()
    except Exception:
        if not EXCEL_FILE.exists():
            raise
        df_raw, df_valid = load_from_excel()
        return df_raw, df_valid, "Excel 檔案 (備援模式)"
