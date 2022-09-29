import stripe
import json
import logging
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def deserialize_stripe_event(payload):
    try:
        return stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        # Invalid payload
        logging.error("Failed to construct Stripe event. Invalid payload %s", e)
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logging.error("Failed to construct Stripe event. Invalid signature: %s", e)
        raise e


def generate_package_checkout_url(
    organization_slug, package_uuid, product_name, price, customer_email
):
    package_status_url = "%s/organizations/%s/packages/%s" % (
        settings.FRONTEND_BASE_URL,
        organization_slug,
        package_uuid,
    )

    session = stripe.checkout.Session.create(
        customer_email=customer_email,
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": product_name,
                    },
                    "unit_amount": price * 100,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=package_status_url + "?payment_status=succeeded",
        cancel_url=package_status_url + "?payment_status=cancelled",
        metadata={
            "package_uuid": package_uuid,
        },
    )

    return session.url
