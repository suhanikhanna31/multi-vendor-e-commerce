from flask import Blueprint, jsonify

from app.auth.decorators import roles_required
from app.models import Order, Vendor

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/vendors")
@roles_required("admin")
def list_vendors():
    vendors = Vendor.query.all()
    return jsonify([
        {"id": v.id, "name": v.name, "slug": v.slug, "is_active": v.is_active}
        for v in vendors
    ])


@admin_bp.get("/platform-summary")
@roles_required("admin")
def platform_summary():
    total_orders = Order.query.count()
    total_vendors = Vendor.query.filter_by(is_active=True).count()
    return jsonify(total_orders=total_orders, active_vendors=total_vendors)

