"""Stripe integration with idempotent payment intent creation and webhook verification."""

import stripe
from flask import current_app


def _client():
    stripe.api_key = current_app.config["STRIPE_API_KEY"]
    return stripe


def create_payment_intent(order_id: str, amount_inr: float, idempotency_key: str):
    """Create a Stripe PaymentIntent, safe to retry with the same idempotency_key."""
    client = _client()
    return client.PaymentIntent.create(
        amount=int(amount_inr * 100),  # paise
        currency="inr",
        metadata={"order_id": order_id},
        idempotency_key=idempotency_key,
    )


def verify_webhook_signature(payload: bytes, sig_header: str):
    client = _client()
    webhook_secret = current_app.config["STRIPE_WEBHOOK_SECRET"]
    return client.Webhook.construct_event(payload, sig_header, webhook_secret)


def refund_payment(payment_intent_id: str, idempotency_key: str):
    client = _client()
    return client.Refund.create(
        payment_intent=payment_intent_id,
        idempotency_key=idempotency_key,
    )
