from datetime import datetime
from enum import Enum

from app.extensions import db


class UserRole(str, Enum):
    ADMIN = "admin"
    VENDOR = "vendor"
    ANALYST = "analyst"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.VENDOR)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vendor = db.relationship("Vendor", back_populates="users")


class Vendor(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", back_populates="vendor")
    orders = db.relationship("Order", back_populates="vendor")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)
    external_order_id = db.Column(db.String(120), unique=True, nullable=False)
    amount_inr = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending/paid/shipped/failed
    payment_intent_id = db.Column(db.String(120), nullable=True)
    shipment_id = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vendor = db.relationship("Vendor", back_populates="orders")


class WebhookEvent(db.Model):
    """Stores processed webhook event IDs to guarantee idempotent processing."""

    __tablename__ = "webhook_events"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)  # stripe / shiprocket
    event_id = db.Column(db.String(150), unique=True, nullable=False, index=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)


class MLModelVersion(db.Model):
    """Registry entry for a trained ML pipeline artifact.

    See app/ml/registry.py. `file_path` points at the joblib-serialized
    sklearn pipeline on disk; `metrics` / `feature_columns` are stored so
    a prediction can be traced back to exactly what the model was
    trained on and how it performed, and so retraining always creates a
    new version rather than silently overwriting the previous one.
    """

    __tablename__ = "ml_model_versions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, index=True)  # demand_forecast / fraud_detector
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=True)
    version = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    metrics = db.Column(db.JSON, nullable=True)
    feature_columns = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
