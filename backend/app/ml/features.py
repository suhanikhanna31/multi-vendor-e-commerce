"""Feature engineering for the ML pipeline.

Deliberately built as a thin layer on top of the existing ETL
(``app.etl.vendors_etl.run_weekly_aggregation``) rather than a parallel
data path — the weekly vendor summary is already cleaned/deduped, so
every model in ``app.ml`` reuses it instead of re-reading raw CSVs.

Two feature tables are produced:

- ``build_vendor_week_features`` — one row per (vendor, week), with lag
  and rolling-window features for demand forecasting and vendor scoring.
- ``build_order_features`` — one row per order, with per-vendor z-scores
  and time-of-day features for anomaly/fraud scoring.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.etl.vendors_etl import run_weekly_aggregation

LAG_COLUMNS = ["revenue_inr", "units_sold", "orders"]


def build_vendor_week_features(vendor_id: int | None = None) -> pd.DataFrame:
    """Weekly vendor features: lag-1 and trailing 3-week rolling averages.

    Lags are computed per-vendor so one vendor's history never leaks into
    another's features. The first 1-2 weeks per vendor will have lag/
    rolling values backfilled to 0 (handled via ``fillna``) since there's
    no prior history yet — acceptable for a model trained on many weeks.
    """
    df = run_weekly_aggregation(vendor_id=vendor_id)
    if df.empty:
        return df

    df = df.sort_values(["vendor_id", "week"]).reset_index(drop=True)
    df["week_index"] = df.groupby("vendor_id").cumcount()

    for col in LAG_COLUMNS:
        df[f"{col}_lag1"] = df.groupby("vendor_id")[col].shift(1)
        df[f"{col}_rolling3"] = df.groupby("vendor_id")[col].transform(
            lambda s: s.shift(1).rolling(3, min_periods=1).mean()
        )

    df["failed_rate"] = (
        df["failed_orders"] / df["orders"].replace(0, np.nan)
    ).fillna(0)

    return df.fillna(0)


def build_order_features(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Order-level features for anomaly detection.

    Expects columns: vendor_id, amount_inr, created_at, status.
    Adds a per-vendor amount z-score, since "unusual" only means
    something relative to a vendor's own typical order size — a ₹50,000
    order is routine for one vendor and wildly anomalous for another.
    """
    df = orders_df.copy()
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["hour"] = df["created_at"].dt.hour
    df["day_of_week"] = df["created_at"].dt.dayofweek

    vendor_stats = (
        df.groupby("vendor_id")["amount_inr"]
        .agg(["mean", "std"])
        .rename(columns={"mean": "vendor_mean_amount", "std": "vendor_std_amount"})
    )
    df = df.merge(vendor_stats, on="vendor_id", how="left")
    df["vendor_std_amount"] = df["vendor_std_amount"].fillna(0)

    denom = df["vendor_std_amount"].replace(0, np.nan)
    df["amount_zscore"] = ((df["amount_inr"] - df["vendor_mean_amount"]) / denom).fillna(0)

    return df
