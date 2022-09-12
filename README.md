# Shortage.Global backend

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

### Run migrations

Hereafter we use `exec` instead of `run`, which means the container must be running before executing the command.

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
