"""Per-vendor demand (next-week revenue) forecasting.

Uses gradient-boosted trees (``GradientBoostingRegressor``) trained
per-vendor on the weekly feature table, rather than a single global
sequence model. Reasoning:

- Vendor-week series here are short (tens of weeks, not thousands of
  timesteps), so an RNN/LSTM would be both overkill and undertrained.
- A per-vendor model lets each vendor's seasonality/scale be learned
  independently, rather than diluted into a single global model, while
  staying cheap enough to retrain on every "Run ETL" click.
- Boosted trees on lag/rolling features are a standard, well-understood
  baseline for short retail time series and are easy to explain to a
  non-ML stakeholder ("last week's revenue, and the trend").

Swap-in path: if per-vendor history grows large enough to justify it, a
global model with vendor_id as a categorical feature is a natural next
step and reuses the same feature table unchanged.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from app.ml.features import build_vendor_week_features
from app.ml.registry import load_latest_model, save_model
from app.models import MLModelVersion

MODEL_NAME = "demand_forecast"
MIN_TRAINING_WEEKS = 6

FEATURE_COLUMNS = [
    "week_index",
    "revenue_inr_lag1",
    "revenue_inr_rolling3",
    "units_sold_lag1",
    "units_sold_rolling3",
    "orders_lag1",
    "orders_rolling3",
    "failed_rate",
]
TARGET_COLUMN = "revenue_inr"


def train_demand_model(vendor_id: int) -> MLModelVersion:
    df = build_vendor_week_features(vendor_id=vendor_id)
    if len(df) < MIN_TRAINING_WEEKS:
        raise ValueError(
            f"Vendor {vendor_id} has only {len(df)} weeks of history; "
            f"need at least {MIN_TRAINING_WEEKS} to train a forecast model."
        )

    X, y = df[FEATURE_COLUMNS], df[TARGET_COLUMN]

    # Hold out the most recent 20% (no shuffling — this is a time series)
    # once there's enough data; otherwise evaluate in-sample and rely on
    # the "rows" count in metrics to flag how little data backed the score.
    if len(df) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = GradientBoostingRegressor(
        n_estimators=150, max_depth=3, learning_rate=0.05, random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    safe_y = np.where(y_test == 0, 1, y_test)
    mape = float(np.mean(np.abs((y_test - preds) / safe_y)) * 100)

    return save_model(
        MODEL_NAME,
        model,
        metrics={"mae_inr": round(mae, 2), "mape_pct": round(mape, 2), "training_rows": len(df)},
        feature_columns=FEATURE_COLUMNS,
        vendor_id=vendor_id,
    )


def predict_next_week_revenue(vendor_id: int) -> dict:
    model, record = load_latest_model(MODEL_NAME, vendor_id=vendor_id)
    if model is None:
        record = train_demand_model(vendor_id)
        model, _ = load_latest_model(MODEL_NAME, vendor_id=vendor_id)

    df = build_vendor_week_features(vendor_id=vendor_id)
    if df.empty:
        raise ValueError(f"No weekly history available for vendor {vendor_id}.")

    latest_row = df.iloc[[-1]][FEATURE_COLUMNS]
    prediction = float(model.predict(latest_row)[0])

    return {
        "vendor_id": vendor_id,
        "predicted_revenue_inr": round(max(prediction, 0), 2),
        "model_name": MODEL_NAME,
        "model_version": record.version,
        "model_metrics": record.metrics,
    }
