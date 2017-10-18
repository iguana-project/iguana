#!/bin/sh
su -m iguana -c 'cd src/ && python -m celery -A common beat --pidfile= -l debug'
