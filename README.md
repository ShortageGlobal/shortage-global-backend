# Shortage.Global backend

API: https://backend-wp66a.ondigitalocean.app/api/

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