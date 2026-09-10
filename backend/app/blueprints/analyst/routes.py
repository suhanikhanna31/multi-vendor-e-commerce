from flask import Blueprint, jsonify, send_file

from app.auth.decorators import roles_required
from app.etl.vendors_etl import run_weekly_aggregation
from app.reports.pptx_generator import build_vendor_report_deck
from app.integrations.s3_service import upload_report

analyst_bp = Blueprint("analyst", __name__, url_prefix="/api/analyst")


@analyst_bp.post("/etl/run")
@roles_required("analyst", "admin")
def trigger_etl():
    summary_df = run_weekly_aggregation()

    return jsonify(
        rows=len(summary_df),
        vendors=int(summary_df["vendor_id"].nunique())
        if not summary_df.empty
        else 0,
    )


@analyst_bp.get("/reports/<int:vendor_id>/deck")
@roles_required("analyst", "admin")
def generate_deck(vendor_id):
    summary_df = run_weekly_aggregation(vendor_id=vendor_id)
    path = build_vendor_report_deck(vendor_id, summary_df)

    # Store generated reports in S3 when AWS_S3_BUCKET is configured.
    # The local file is still returned so existing deployments keep working.
    s3_url = upload_report(
        path,
        f"reports/vendor_{vendor_id}_report.pptx",
    )

    response = send_file(
        path,
        as_attachment=True,
    )

    # Expose the temporary S3 download URL to the client while
    # preserving the existing file-download response.
    if s3_url:
        response.headers["X-S3-Report-URL"] = s3_url

    return response
