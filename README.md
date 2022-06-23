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