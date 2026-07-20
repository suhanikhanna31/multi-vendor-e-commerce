"""Lightweight model registry.

Trained sklearn pipelines are serialized to disk with joblib; a matching
row in ``ml_model_versions`` (see app/models.py) records the file path,
metrics, and feature list, so a prediction can always be traced back to
the exact model version that produced it — and so retraining never
silently overwrites a previous version's artifact.

Deliberately simple (filesystem + one DB table) rather than a dedicated
model-store service: the training data here is small (weekly vendor
aggregates, not millions of rows), so a heavier MLOps stack would add
operational cost without a corresponding benefit at this scale.
"""

from __future__ import annotations

import os
from datetime import datetime

import joblib

from app.extensions import db
from app.models import MLModelVersion

MODEL_DIR = os.environ.get("ML_MODEL_DIR", "data/models")


def save_model(
    name: str,
    model,
    metrics: dict,
    feature_columns: list[str],
    vendor_id: int | None = None,
) -> MLModelVersion:
    os.makedirs(MODEL_DIR, exist_ok=True)
    version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{name}_{vendor_id or 'global'}_{version}.joblib"
    path = os.path.join(MODEL_DIR, filename)
    joblib.dump(model, path)

    record = MLModelVersion(
        name=name,
        vendor_id=vendor_id,
        version=version,
        file_path=path,
        metrics=metrics,
        feature_columns=",".join(feature_columns),
    )
    db.session.add(record)
    db.session.commit()
    return record


def load_latest_model(name: str, vendor_id: int | None = None):
    """Returns (model, record) for the newest version of `name`, or (None, None)."""
    record = (
        MLModelVersion.query.filter_by(name=name, vendor_id=vendor_id)
        .order_by(MLModelVersion.created_at.desc())
        .first()
    )
    if record is None:
        return None, None
    model = joblib.load(record.file_path)
    return model, record
