"""Pandas ETL: cleans and aggregates raw per-vendor order/inventory CSV exports
into a unified weekly analytics dataset.

Replaces a previously manual ~2 FTE-day weekly reporting process.
"""

import glob
import os

import pandas as pd

RAW_EXPORTS_DIR = os.environ.get("VENDOR_RAW_EXPORTS_DIR", "data/raw_exports")
OUTPUT_DIR = os.environ.get("VENDOR_ETL_OUTPUT_DIR", "data/processed")

EXPECTED_ORDER_COLUMNS = [
    "vendor_id", "order_id", "sku", "quantity", "unit_price_inr", "order_date", "status",
]


def _load_vendor_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    missing = set(EXPECTED_ORDER_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing expected columns: {missing}")
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["vendor_id", "order_id", "sku"])
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["unit_price_inr"] = pd.to_numeric(df["unit_price_inr"], errors="coerce").fillna(0)
    df["line_total_inr"] = df["quantity"] * df["unit_price_inr"]
    df["status"] = df["status"].str.strip().str.lower()
    return df


def run_weekly_aggregation(vendor_id: int | None = None) -> pd.DataFrame:
    """Loads all raw vendor CSVs, cleans them, and returns a per-vendor weekly summary.

    Also writes the aggregated dataset to OUTPUT_DIR as CSV for downstream reporting.
    """
    csv_paths = glob.glob(os.path.join(RAW_EXPORTS_DIR, "*.csv"))
    if not csv_paths:
        return pd.DataFrame(columns=["vendor_id", "week", "orders", "units_sold", "revenue_inr"])

    frames = [_clean(_load_vendor_csv(p)) for p in csv_paths]
    combined = pd.concat(frames, ignore_index=True)

    if vendor_id is not None:
        combined = combined[combined["vendor_id"] == vendor_id]

    combined["week"] = combined["order_date"].dt.to_period("W").astype(str)

    summary = (
        combined.groupby(["vendor_id", "week"])
        .agg(
            orders=("order_id", "nunique"),
            units_sold=("quantity", "sum"),
            revenue_inr=("line_total_inr", "sum"),
            failed_orders=("status", lambda s: (s == "failed").sum()),
        )
        .reset_index()
        .sort_values(["vendor_id", "week"])
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "weekly_vendor_summary.csv")
    summary.to_csv(out_path, index=False)

    return summary
