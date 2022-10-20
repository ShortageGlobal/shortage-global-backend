#!/bin/bash

python manage.py dumpdata catalog.Organization > organization_fixture.json
python manage.py dumpdata catalog.Product > product_fixture.json
python manage.py dumpdata catalog.Instruction > instruction_fixture.json
