#!/bin/bash
echo "from .global_conf import *" > src/common/settings/__init__.py
pip install -r requirements/production.req
cd /code/src
python manage.py migrate
python -m scss < common/scss/style.scss > common/static/css/style.css
python manage.py collectstatic --no-input --settings=common.settings
cd /code/
exec "$@"
