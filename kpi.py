import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict:
    """計算核心營運 KPI。"""
    total_revenue = df["TotalAmount"].sum()
    unique_customers = df["CustomerID"].nunique()
    total_orders = df["InvoiceNo"].nunique()
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0

    return {
        "total_revenue": total_revenue,
        "unique_customers": unique_customers,
        "total_orders": total_orders,
        "average_order_value": average_order_value,
    }


def compute_period_comparison(df: pd.DataFrame) -> dict:
    """比較本期與上期營收、訂單變化（以資料中段為分界）。"""
    if df.empty:
        return {"revenue_delta_pct": 0.0, "orders_delta_pct": 0.0, "trend_label": "資料不足"}

    dates = df["InvoiceDate"].sort_values()
    midpoint = dates.iloc[len(dates) // 2]
    current = df[df["InvoiceDate"] >= midpoint]
    previous = df[df["InvoiceDate"] < midpoint]

    current_rev = current["TotalAmount"].sum()
    previous_rev = previous["TotalAmount"].sum()
    current_orders = current["InvoiceNo"].nunique()
    previous_orders = previous["InvoiceNo"].nunique()

    revenue_delta_pct = (
        ((current_rev - previous_rev) / previous_rev) * 100 if previous_rev > 0 else 0.0
    )
    orders_delta_pct = (
        ((current_orders - previous_orders) / previous_orders) * 100
        if previous_orders > 0
        else 0.0
    )

    if revenue_delta_pct > 5:
        trend_label = "成長"
    elif revenue_delta_pct < -5:
        trend_label = "下滑"
    else:
        trend_label = "持平"

    return {
        "revenue_delta_pct": revenue_delta_pct,
        "orders_delta_pct": orders_delta_pct,
        "trend_label": trend_label,
        "current_rev": current_rev,
        "previous_rev": previous_rev,
    }


def monthly_revenue_trend(df: pd.DataFrame) -> pd.DataFrame:
    """彙總每月營收趨勢。"""
    monthly = df.copy()
    monthly["YearMonth"] = monthly["InvoiceDate"].dt.to_period("M")
    return (
        monthly.groupby("YearMonth")["TotalAmount"]
        .sum()
        .reset_index()
        .rename(columns={"TotalAmount": "Revenue"})
    )
