"""Order-level anomaly / fraud-risk scoring.

Uses ``IsolationForest`` — an unsupervised anomaly detector — rather than
a supervised fraud classifier, because a new marketplace has little or no
labelled fraud data to train a classifier against. Isolation Forest
instead flags orders that look statistically unlike a vendor's normal
pattern (amount relative to that vendor's mean/std, time of day, day of
week), which is a reasonable first-pass triage signal even with zero
labelled cases. It should be treated as "worth a human look", not a
fraud verdict.

``CONTAMINATION`` is the assumed fraction of orders that are anomalous;
it's a rough prior (3%) that should be tuned once real order volume and
any confirmed fraud/chargeback data are available.
"""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from app.ml.features import build_order_features
from app.ml.registry import load_latest_model, save_model
from app.models import MLModelVersion

MODEL_NAME = "fraud_detector"
MIN_TRAINING_ORDERS = 20
CONTAMINATION = 0.03

FEATURE_COLUMNS = ["amount_inr", "amount_zscore", "hour", "day_of_week"]


def train_fraud_model(orders_df: pd.DataFrame) -> MLModelVersion:
    df = build_order_features(orders_df)
    if len(df) < MIN_TRAINING_ORDERS:
        raise ValueError(
            f"Only {len(df)} orders available; need at least "
            f"{MIN_TRAINING_ORDERS} to train an anomaly detector."
        )

    X = df[FEATURE_COLUMNS]
    model = IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=42)
    model.fit(X)

    return save_model(
        MODEL_NAME,
        model,
        metrics={"training_rows": len(df), "contamination": CONTAMINATION},
        feature_columns=FEATURE_COLUMNS,
    )


def score_orders(orders_df: pd.DataFrame) -> tuple[pd.DataFrame, MLModelVersion]:
    model, record = load_latest_model(MODEL_NAME)
    if model is None:
        record = train_fraud_model(orders_df)
        model, _ = load_latest_model(MODEL_NAME)

    df = build_order_features(orders_df)
    X = df[FEATURE_COLUMNS]

    # decision_function: higher = more "normal". Invert + min-max scale to
    # a 0-1 "risk_score" so the frontend doesn't need to know sklearn's
    # sign convention.
    raw_scores = model.decision_function(X)
    score_range = raw_scores.max() - raw_scores.min()
    df["risk_score"] = (
        1 - (raw_scores - raw_scores.min()) / (score_range if score_range else 1)
    ).round(4)
    df["is_anomalous"] = model.predict(X) == -1

    return df[["vendor_id", "amount_inr", "created_at", "risk_score", "is_anomalous"]], record
