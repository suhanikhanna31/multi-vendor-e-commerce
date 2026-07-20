"""ML API blueprint.

Sits alongside the existing admin/vendor/analyst blueprints and reuses
the same RBAC decorators (``roles_required`` / ``vendor_scoped``) rather
than inventing separate ML-specific auth. Training and inference are
split into separate endpoints deliberately: training is a heavier,
explicit action (triggered by an analyst/admin, mirroring the existing
"Run ETL" button) while inference stays cheap and can be called more
often, including by vendors viewing their own forecast.

Routes
------
POST /api/ml/forecast/<vendor_id>/train   analyst/admin  - train demand model
GET  /api/ml/forecast/<vendor_id>         analyst/admin/vendor (own only)
POST /api/ml/fraud/train                  analyst/admin  - train anomaly model
GET  /api/ml/fraud/orders                 analyst/admin  - score all orders
GET  /api/ml/vendors/scores               admin/analyst  - vendor segmentation
"""

from __future__ import annotations

import pandas as pd
from flask import Blueprint, jsonify, request

from app.auth.decorators import roles_required, vendor_scoped
from app.models import Order
from app.ml.demand_forecast import predict_next_week_revenue, train_demand_model
from app.ml.fraud_detection import score_orders, train_fraud_model
from app.ml.vendor_scoring import score_vendors

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")


def _orders_dataframe(vendor_id: int | None = None) -> pd.DataFrame:
    query = Order.query
    if vendor_id is not None:
        query = query.filter_by(vendor_id=vendor_id)
    rows = query.all()
    return pd.DataFrame(
        [
            {
                "vendor_id": o.vendor_id,
                "amount_inr": float(o.amount_inr),
                "created_at": o.created_at,
                "status": o.status,
            }
            for o in rows
        ]
    )


@ml_bp.post("/forecast/<int:vendor_id>/train")
@roles_required("analyst", "admin")
def train_forecast(vendor_id):
    try:
        record = train_demand_model(vendor_id)
    except ValueError as exc:
        return jsonify(error=str(exc)), 422
    return jsonify(model_name=record.name, model_version=record.version, metrics=record.metrics)


@ml_bp.get("/forecast/<int:vendor_id>")
@roles_required("analyst", "admin", "vendor")
@vendor_scoped
def forecast(vendor_id):
    try:
        result = predict_next_week_revenue(vendor_id)
    except ValueError as exc:
        return jsonify(error=str(exc)), 422
    return jsonify(result)


@ml_bp.post("/fraud/train")
@roles_required("analyst", "admin")
def train_fraud():
    df = _orders_dataframe()
    try:
        record = train_fraud_model(df)
    except ValueError as exc:
        return jsonify(error=str(exc)), 422
    return jsonify(model_name=record.name, model_version=record.version, metrics=record.metrics)


@ml_bp.get("/fraud/orders")
@roles_required("analyst", "admin")
def fraud_scores():
    df = _orders_dataframe()
    if df.empty:
        return jsonify(error="No orders to score."), 422
    try:
        scored, record = score_orders(df)
    except ValueError as exc:
        return jsonify(error=str(exc)), 422
    return jsonify(
        model_version=record.version,
        flagged_count=int(scored["is_anomalous"].sum()),
        results=scored.to_dict(orient="records"),
    )


@ml_bp.get("/vendors/scores")
@roles_required("admin", "analyst")
def vendor_scores():
    n_clusters = int(request.args.get("clusters", 3))
    result = score_vendors(n_clusters=n_clusters)
    if result.empty:
        return jsonify(error="Not enough weekly data to score vendors yet."), 422
    return jsonify(vendors=result.to_dict(orient="records"))
