# Shortage.Global backend

[![main](https://github.com/ShortageGlobal/shortage-global-backend/actions/workflows/main.yml/badge.svg)](https://github.com/ShortageGlobal/shortage-global-backend/actions/workflows/main.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

API: https://backend-wp66a.ondigitalocean.app/api/

Swagger: https://backend-wp66a.ondigitalocean.app/api/swagger

Admin: https://backend-wp66a.ondigitalocean.app/admin/

## Docker run for local development

### Docker compose up

```
docker-compose up
```

If you want to rebuild the container and run it:

```
docker-compose up --build
```

If you want to update dependencies in `django` container and keep `postgres` untouched:

```
docker-compose build --no-cache django
```

### Create migrations

Hereafter we use `exec` instead of `run`, which means the container must be running before executing the command.

```
docker-compose exec django python manage.py makemigrations
```

### Run migrations

```
docker-compose exec django python manage.py migrate
```

### Create admin

```
docker-compose exec django python manage.py createsuperuser
```

### Run shell

```
docker-compose exec django python manage.py shell
```

### Run tests

```
docker compose exec django python manage.py test
```


## Installing all dependencies when starting from scratch (on macOS)

### Install XCode tools

```
xcode-select --install
```

### Install libpq

```
brew install libpq
```

### Install openssl

```
brew install openssl
```

### Install and activate virtual env

```
python3.10 -m venv venv
source venv/bin/activate
```

### Install psycopg2

`psycopg2` requires `postgresql` to be installed, if you don't have one, run: 
```
brew install postgresql
```

At this point you have all dependencies to finally build psycopg2

```
export LDFLAGS="-L/opt/homebrew/opt/openssl@3/lib"
export CPPFLAGS="-I/opt/homebrew/opt/openssl@3/include"
pip install psycopg2
```

### Install dependencies

```
pip install -r requirements.txt
```

## Generate OpenAPI schema when changing any API elements
```
docker compose exec django python manage.py generateschema > schema.yaml
```
Schema file should be located in /static/openapi/schema.yaml

Make sure you don't overwrite the file located in /static/openapi/ folder but manually merge the old and new files

## MailCatcher 

[MailCatcher](https://mailcatcher.me/) is used locally to catch emails sent through SMTP. To access the UI of the catcher, 
open [http://127.0.0.1:1080/](http://127.0.0.1:1080/).

## Stripe 

To configure `/api/packages/payments/webhook/` endpoint in the Stripe Dashboard, go to the [webhook settings](https://dashboard.stripe.com/webhooks).

To test webhooks locally follow [the Stripe guide](https://stripe.com/docs/payments/handling-payment-events#use-cli). Or try to install with the next 2 commands: 

```
brew install stripe/stripe-cli/stripe

# Connect the CLI to your dashboard
stripe login
```

Run locally (**not in Docker**): 
```
stripe listen --forward-to http://localhost:8080/api/packages/payments/webhook/
```

It will give you a webhook signing secret:
```
> Ready! You are using Stripe API Version [2022-08-01]. Your webhook signing secret is {{YOUR_ENDPOINT_SECRET}}
```

Store it in `shortage/settings/local.py` to forward events from stripe to your local machine:
```py
# local.py
STRIPE_ENDPOINT_SECRET={{YOUR_ENDPOINT_SECRET}}
```

You can manually trigger events: 

- successful payment:

```
stripe trigger payment_intent.succeeded \
  --add "payment_intent:metadata[package_uuid]={{package_uuid}}" \
  --add "payment_intent:metadata[organization_slug]={{organization_slug}}" \
  --add "payment_intent:metadata[organization_name]={{organization_name}}" 
```

- failed payment: 

```
stripe trigger payment_intent.payment_failed \
  --add "payment_intent:metadata[package_uuid]={{package_uuid}}" \
  --add "payment_intent:metadata[organization_slug]={{organization_slug}}" \
  --add "payment_intent:metadata[organization_name]={{organization_name}}" 
```

The list of [Stripe test cards](https://stripe.com/docs/testing).
