#!/bin/bash

# Resets the local Django database, adding an admin login and migrations
# Author: https://mattsegal.dev/reset-django-local-database.html

set -e
echo -e "\n>>> Resetting the database"
docker-compose exec django python manage.py reset_db --close-sessions --noinput

echo -e "\n>>> Running migrations"
docker-compose exec django python manage.py migrate

echo -e "\n>>> Creating new superuser 'admin'"
docker-compose exec django python manage.py createsuperuser \
   --username admin \
   --email admin@example.com \
   --noinput

echo -e "\n>>> Setting superuser 'admin' password to 12345"
docker-compose exec django python manage.py shell_plus --quiet-load -c "
u=User.objects.get(username='admin')
u.set_password('123456')
u.save()
"

echo -e "\n>>> Database restore finished."
