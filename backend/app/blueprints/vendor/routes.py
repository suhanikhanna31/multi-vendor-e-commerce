from flask import Blueprint, jsonify

from app.auth.decorators import roles_required, vendor_scoped
from app.models import Order

vendor_bp = Blueprint("vendor", __name__, url_prefix="/api/vendor")


@vendor_bp.get("/<int:vendor_id>/orders")
@roles_required("vendor", "admin")
@vendor_scoped
def get_orders(vendor_id):
    orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(100).all()
    return jsonify([
        {
            "id": o.id,
            "external_order_id": o.external_order_id,
            "amount_inr": str(o.amount_inr),
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ])
