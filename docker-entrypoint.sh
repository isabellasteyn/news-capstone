#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py setup_groups
python manage.py collectstatic --noinput

exec "$@"
