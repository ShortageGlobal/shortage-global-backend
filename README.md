# Shortage.Global backend

[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

If you want to update dependencies in `django` container and keep `postgres`  untouched:
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
