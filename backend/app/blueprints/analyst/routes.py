from flask import Blueprint, jsonify, send_file

from app.auth.decorators import roles_required
from app.etl.vendors_etl import run_weekly_aggregation
from app.reports.pptx_generator import build_vendor_report_deck

analyst_bp = Blueprint("analyst", __name__, url_prefix="/api/analyst")


@analyst_bp.post("/etl/run")
@roles_required("analyst", "admin")
def trigger_etl():
    summary_df = run_weekly_aggregation()
    return jsonify(
        rows=len(summary_df),
        vendors=int(summary_df["vendor_id"].nunique()) if not summary_df.empty else 0,
    )


@analyst_bp.get("/reports/<int:vendor_id>/deck")
@roles_required("analyst", "admin")
def generate_deck(vendor_id):
    summary_df = run_weekly_aggregation(vendor_id=vendor_id)
    path = build_vendor_report_deck(vendor_id, summary_df)
    return send_file(path, as_attachment=True)

