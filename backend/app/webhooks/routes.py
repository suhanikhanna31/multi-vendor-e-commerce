from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.integrations import sendgrid_service, stripe_service
from app.models import Order, WebhookEvent

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")


def _already_processed(source: str, event_id: str) -> bool:
    """Idempotency guard: skip work if we've already recorded this event_id."""
    return WebhookEvent.query.filter_by(source=source, event_id=event_id).first() is not None


def _mark_processed(source: str, event_id: str):
    db.session.add(WebhookEvent(source=source, event_id=event_id))
    db.session.commit()


@webhooks_bp.post("/stripe")
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe_service.verify_webhook_signature(payload, sig_header)
    except Exception as exc:  # signature/verification failure
        current_app.logger.warning("Stripe webhook verification failed: %s", exc)
        return jsonify(error="invalid signature"), 400

    if _already_processed("stripe", event["id"]):
        return jsonify(status="already_processed"), 200

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")
        order = Order.query.filter_by(external_order_id=order_id).first()
        if order:
            order.status = "paid"
            order.payment_intent_id = intent["id"]
            db.session.commit()
            sendgrid_service.send_templated_email(
                to_email=intent.get("receipt_email", ""),
                template_key="order_confirmation",
                dynamic_data={"order_id": order_id},
            )

    _mark_processed("stripe", event["id"])
    return jsonify(status="ok"), 200


@webhooks_bp.post("/shiprocket")
def shiprocket_webhook():
    data = request.get_json(silent=True) or {}
    event_id = data.get("event_id") or f"{data.get('shipment_id')}-{data.get('status')}"

    if _already_processed("shiprocket", event_id):
        return jsonify(status="already_processed"), 200

    shipment_id = data.get("shipment_id")
    order = Order.query.filter_by(shipment_id=shipment_id).first()
    if order:
        order.status = data.get("status", order.status)
        db.session.commit()
        sendgrid_service.send_templated_email(
            to_email=data.get("customer_email", ""),
            template_key="shipment_update",
            dynamic_data={"status": order.status, "shipment_id": shipment_id},
        )

    _mark_processed("shiprocket", event_id)
    return jsonify(status="ok"), 200
