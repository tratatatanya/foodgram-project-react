#!/bin/bash
python manage.py migrate &&
python manage.py collectstatic --no-input &&
python manage.py load_data
cp redoc.yaml ./static/
exec "$@"