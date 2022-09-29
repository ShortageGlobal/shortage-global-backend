from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def generate_package_checkout_url(organization_slug, package_uuid, product_name, price, customer_email):        
    package_status_url = "%s/organizations/%s/packages/%s" % (
        settings.FRONTEND_BASE_URL,
        organization_slug,
        package_uuid,
    )
    
    session = stripe.checkout.Session.create(
        customer_email=customer_email,
        line_items=[{
            'price_data': {
            'currency': 'usd',
            'product_data': {
                'name': product_name,
            },
            'unit_amount': price * 100,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=package_status_url + '?payment_status=succeed',
        cancel_url=package_status_url + '?payment_status=cancelled',
    )   

    return session.url