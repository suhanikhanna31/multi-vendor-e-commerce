from unittest.mock import patch

from app.extensions import db
from app.models import WebhookEvent


@patch("app.webhooks.routes.stripe_service.verify_webhook_signature")
@patch("app.webhooks.routes.sendgrid_service.send_templated_email")
def test_stripe_webhook_is_idempotent(mock_send_email, mock_verify, client, app):
    fake_event = {
        "id": "evt_123",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_123", "metadata": {"order_id": "ord_1"}, "receipt_email": "a@b.com"}},
    }
    mock_verify.return_value = fake_event

    resp1 = client.post(
        "/api/webhooks/stripe",
        data=b"{}",
        headers={"Stripe-Signature": "test-sig"},
    )
    assert resp1.status_code == 200
    assert resp1.json["status"] == "ok"

    with app.app_context():
        assert WebhookEvent.query.filter_by(event_id="evt_123").count() == 1

    # Second delivery of the same event should be a no-op
    resp2 = client.post(
        "/api/webhooks/stripe",
        data=b"{}",
        headers={"Stripe-Signature": "test-sig"},
    )
    assert resp2.status_code == 200
    assert resp2.json["status"] == "already_processed"

    with app.app_context():
        assert WebhookEvent.query.filter_by(event_id="evt_123").count() == 1


def test_stripe_webhook_rejects_bad_signature(client):
    with patch("app.webhooks.routes.stripe_service.verify_webhook_signature", side_effect=Exception("bad sig")):
        resp = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            headers={"Stripe-Signature": "invalid"},
        )
    assert resp.status_code == 400
