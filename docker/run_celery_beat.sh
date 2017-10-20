#!/bin/sh
su -c 'touch src/celerybeat-schedule && chown -R iguana:iguana src/celerybeat-schedule'
su -m iguana -c 'cd src/ && python -m celery -A common beat --pidfile= -l debug'
