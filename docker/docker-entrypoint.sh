#!/bin/bash
cd /code/src
python manage.py migrate
python -m scss < common/scss/style.scss > common/static/css/style.css
python manage.py collectstatic --no-input --settings=common.settings
cd /code/
exec "$@"
