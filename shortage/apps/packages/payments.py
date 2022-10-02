import stripe
import logging
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_ENDPOINT_SECRET


def deserialize_stripe_event(payload, signature):
    try:
        return stripe.Webhook.construct_event(payload, signature, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        logging.error("Failed to construct Stripe event. Invalid payload %s", e)
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logging.error("Failed to construct Stripe event. Invalid signature: %s", e)
        raise e


def generate_package_checkout_url(
    organization_slug, package_uuid, items, customer_email
):
    package_status_url = "%s/organizations/%s/packages/%s" % (
        settings.FRONTEND_BASE_URL,
        organization_slug,
        package_uuid,
    )
    cart_url = "%s/donation/details/cart" % settings.FRONTEND_BASE_URL

    session = stripe.checkout.Session.create(
        customer_email=customer_email,
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Donation: %s" % item.product.name,
                        "metadata": {"product_slug": item.product.slug},
                    },
                    "unit_amount": item.product.price * 100,
                },
                "quantity": item.quantity,
            }
            for item in items
        ],
        mode="payment",
        success_url=package_status_url + "?paymentStatus=succeeded",
        cancel_url=cart_url + "?paymentStatus=cancelled",
        metadata={
            "organization_slug": organization_slug,
            "package_uuid": package_uuid,
        },
    )

    return session.url
