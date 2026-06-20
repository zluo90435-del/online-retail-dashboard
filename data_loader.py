from pathlib import Path

import pandas as pd
import pyodbc
import streamlit as st

SQL_SERVER = r"localhost"
SQL_DATABASE = "OnlineRetailDB"
SQL_DRIVER = "ODBC Driver 17 for SQL Server"
BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_FILE = BASE_DIR / "OnlineRetail.xlsx"


def get_sql_connection() -> pyodbc.Connection:
    conn_str = (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)


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
        return df_raw, df_valid, f"MS SQL Server ({SQL_DATABASE})"
    except Exception:
        if not EXCEL_FILE.exists():
            raise
        df_raw, df_valid = load_from_excel()
        return df_raw, df_valid, "Excel 檔案 (備援模式)"
