from django.conf import settings
import stripe
import json
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY


def deserialize_stripe_event(payload):
    try:
        return stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        logging.error("Failed to construct Stripe even from payload: %s", e)
        return None


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
