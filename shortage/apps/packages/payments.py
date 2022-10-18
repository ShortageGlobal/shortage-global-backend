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
    organization_slug,
    organization_name,
    package_uuid,
    items,
    cart_item_uuids,
    customer_email,
):
    package_status_url = "%s/organizations/%s/packages/%s" % (
        settings.FRONTEND_BASE_URL,
        organization_slug,
        package_uuid,
    )

    cart_url = "%s/donation/details/cart" % settings.FRONTEND_BASE_URL

    # attach cart item ids to the url, so the frontend
    # could delete the cart items on page visit
    success_url = "%s?paymentStatus=succeeded&%s" % (
        package_status_url,
        "&".join(
            ["dci={}".format(cart_item_uuid) for cart_item_uuid in cart_item_uuids]
        ),
    )

    cancel_url = "%s?paymentStatus=cancelled" % cart_url

    metadata = {
        "organization_slug": organization_slug,
        "organization_name": organization_name,
        "package_uuid": package_uuid,
    }

    session = stripe.checkout.Session.create(
        customer_email=customer_email,
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.product.name,
                        "metadata": {
                            "product_slug": item.product.slug,
                            **metadata,
                        },
                    },
                    "unit_amount": item.product.price * 100,
                },
                "quantity": item.quantity,
            }
            for item in items
        ],
        mode="payment",
        submit_type="donate",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
        payment_intent_data={"metadata": metadata},
        payment_method_types=["card"],
    )

    return session.url
