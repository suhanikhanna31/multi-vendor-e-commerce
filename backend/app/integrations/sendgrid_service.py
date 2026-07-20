"""SendGrid transactional email helper with templated sends."""

from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


TEMPLATE_IDS = {
    "order_confirmation": "d-order-confirmation-template-id",
    "shipment_update": "d-shipment-update-template-id",
    "weekly_vendor_digest": "d-weekly-digest-template-id",
}


def send_templated_email(to_email: str, template_key: str, dynamic_data: dict):
    template_id = TEMPLATE_IDS.get(template_key)
    if not template_id:
        raise ValueError(f"Unknown email template key: {template_key}")

    message = Mail(
        from_email=current_app.config["SENDGRID_FROM_EMAIL"],
        to_emails=to_email,
    )
    message.template_id = template_id
    message.dynamic_template_data = dynamic_data

    client = SendGridAPIClient(current_app.config["SENDGRID_API_KEY"])
    response = client.send(message)
    return response.status_code
