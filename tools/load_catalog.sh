#!/bin/bash

python manage.py loaddata organization_fixture.json
python manage.py loaddata product_fixture.json
python manage.py loaddata instruction_fixture.json
