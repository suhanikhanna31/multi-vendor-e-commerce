"""Shiprocket integration with token caching and retry-on-failure shipment creation."""

import time

import requests
from flask import current_app

_BASE_URL = "https://apiv2.shiprocket.in/v1/external"
_token_cache = {"token": None, "expires_at": 0}


def _get_token():
    if _token_cache["token"] and _token_cache["expires_at"] > time.time():
        return _token_cache["token"]

    resp = requests.post(
        f"{_BASE_URL}/auth/login",
        json={
            "email": current_app.config["SHIPROCKET_EMAIL"],
            "password": current_app.config["SHIPROCKET_PASSWORD"],
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["token"]
    _token_cache["expires_at"] = time.time() + 9 * 24 * 3600  # tokens last ~10 days
    return _token_cache["token"]


def create_shipment(order_payload: dict, max_retries: int = 3):
    """Create a shipment, retrying transient failures with exponential backoff."""
    last_error = None
    for attempt in range(max_retries):
        try:
            token = _get_token()
            resp = requests.post(
                f"{_BASE_URL}/orders/create/adhoc",
                json=order_payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Shiprocket shipment creation failed after {max_retries} attempts: {last_error}")


def track_shipment(shipment_id: str):
    token = _get_token()
    resp = requests.get(
        f"{_BASE_URL}/courier/track/shipment/{shipment_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
