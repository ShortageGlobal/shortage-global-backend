# Local run
## Python
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run migrations
```
python manage.py migrate
```

## Create admin
```
python manage.py createsuperuser
```

## Run local server
```
python manage.py runserver
```

# Docker run
## Docker compose up
```
docker-compose -f docker-compose.yml -f docker-compose-local-infrastructure.yml up --build
```

## Create admin
```
docker-compose run shortage-global-web python manage.py createsuperuser
```