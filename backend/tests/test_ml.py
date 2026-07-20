import os
from datetime import datetime, timedelta

import pandas as pd
import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import MLModelVersion, Order, User, UserRole
from app.ml.demand_forecast import predict_next_week_revenue, train_demand_model
from app.ml.fraud_detection import score_orders, train_fraud_model
from app.ml.vendor_scoring import score_vendors


@pytest.fixture(autouse=True)
def _isolated_etl_and_model_dirs(tmp_path, monkeypatch):
    """vendors_etl reads raw CSVs from disk (decoupled from the live Order
    table by design — see README). Point it and the model registry at a
    per-test tmp_path so tests don't touch real data/ dirs or leak state
    between tests.
    """
    raw_dir = tmp_path / "raw_exports"
    raw_dir.mkdir()
    monkeypatch.setattr("app.etl.vendors_etl.RAW_EXPORTS_DIR", str(raw_dir))
    monkeypatch.setattr("app.etl.vendors_etl.OUTPUT_DIR", str(tmp_path / "processed"))
    monkeypatch.setattr("app.ml.registry.MODEL_DIR", str(tmp_path / "models"))
    return raw_dir


def _write_vendor_csv(raw_dir, vendor_id, weeks=10, orders_per_week=6):
    """Writes a per-vendor CSV export matching vendors_etl's expected
    columns, with a mild upward revenue trend so the forecast model has
    a non-trivial pattern to learn instead of pure noise.
    """
    base = datetime.utcnow() - timedelta(weeks=weeks)
    rows = []
    for w in range(weeks):
        for i in range(orders_per_week):
            rows.append(
                {
                    "vendor_id": vendor_id,
                    "order_id": f"ML-{vendor_id}-{w}-{i}",
                    "sku": f"SKU-{i}",
                    "quantity": 1,
                    "unit_price_inr": 100 + w * 15 + i,
                    "order_date": (base + timedelta(weeks=w, days=i % 7)).isoformat(),
                    "status": "paid",
                }
            )
    pd.DataFrame(rows).to_csv(raw_dir / f"vendor_{vendor_id}.csv", index=False)


def _seed_orders(vendor_id, weeks=10, orders_per_week=6):
    """Seeds live Order rows (used by fraud detection, which scores the
    live table directly rather than going through the CSV-based ETL).
    """
    base = datetime.utcnow() - timedelta(weeks=weeks)
    for w in range(weeks):
        for i in range(orders_per_week):
            db.session.add(
                Order(
                    vendor_id=vendor_id,
                    external_order_id=f"ML-{vendor_id}-{w}-{i}",
                    amount_inr=100 + w * 15 + i,
                    status="paid",
                    created_at=base + timedelta(weeks=w, days=i % 7),
                )
            )
    db.session.commit()


@pytest.fixture
def analyst_token(client, app):
    user = User(
        email="analyst@example.com",
        password_hash=generate_password_hash("password123"),
        role=UserRole.ANALYST,
    )
    db.session.add(user)
    db.session.commit()
    login = client.post(
        "/api/auth/login",
        json={"email": "analyst@example.com", "password": "password123"},
    )
    return login.json["access_token"]


def test_train_demand_model_requires_minimum_history(app, vendor, _isolated_etl_and_model_dirs):
    _write_vendor_csv(_isolated_etl_and_model_dirs, vendor.id, weeks=2)
    with pytest.raises(ValueError):
        train_demand_model(vendor.id)


def test_train_and_predict_demand_model(app, vendor, _isolated_etl_and_model_dirs):
    _write_vendor_csv(_isolated_etl_and_model_dirs, vendor.id, weeks=10)
    record = train_demand_model(vendor.id)

    assert record.name == "demand_forecast"
    assert "mae_inr" in record.metrics
    assert MLModelVersion.query.filter_by(name="demand_forecast", vendor_id=vendor.id).count() == 1

    result = predict_next_week_revenue(vendor.id)
    assert result["predicted_revenue_inr"] >= 0
    assert result["model_version"] == record.version


def test_fraud_scoring_flags_outlier_order(app, vendor):
    _seed_orders(vendor.id, weeks=10)
    # inject one order far outside this vendor's normal amount range
    db.session.add(
        Order(
            vendor_id=vendor.id,
            external_order_id="ML-outlier",
            amount_inr=50000,
            status="paid",
            created_at=datetime.utcnow(),
        )
    )
    db.session.commit()

    orders_df = pd.DataFrame(
        [
            {
                "vendor_id": o.vendor_id,
                "amount_inr": float(o.amount_inr),
                "created_at": o.created_at,
                "status": o.status,
            }
            for o in Order.query.filter_by(vendor_id=vendor.id).all()
        ]
    )

    train_fraud_model(orders_df)
    scored, record = score_orders(orders_df)

    assert record.name == "fraud_detector"
    outlier_row = scored[scored["amount_inr"] == 50000].iloc[0]
    assert outlier_row["is_anomalous"]
    assert scored["risk_score"].between(0, 1).all()


def test_vendor_scoring_ranks_higher_revenue_vendor_first(app, vendor, _isolated_etl_and_model_dirs):
    from app.models import Vendor

    other = Vendor(name="Other Vendor", slug="other-vendor")
    db.session.add(other)
    db.session.commit()

    _write_vendor_csv(_isolated_etl_and_model_dirs, vendor.id, weeks=10, orders_per_week=2)
    _write_vendor_csv(_isolated_etl_and_model_dirs, other.id, weeks=10, orders_per_week=20)

    result = score_vendors(n_clusters=2)
    assert not result.empty
    assert "composite_score" in result.columns
    # higher-volume vendor should rank first (rows are sorted descending)
    assert result.iloc[0]["vendor_id"] == other.id


def test_forecast_endpoint_forbidden_for_wrong_vendor(client, vendor_user, vendor):
    login = client.post(
        "/api/auth/login",
        json={"email": "vendor@example.com", "password": "password123"},
    )
    token = login.json["access_token"]

    other_vendor_id = vendor.id + 999
    resp = client.get(
        f"/api/ml/forecast/{other_vendor_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_vendor_scores_endpoint_requires_analyst_or_admin(client, vendor_user):
    login = client.post(
        "/api/auth/login",
        json={"email": "vendor@example.com", "password": "password123"},
    )
    token = login.json["access_token"]

    resp = client.get("/api/ml/vendors/scores", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
