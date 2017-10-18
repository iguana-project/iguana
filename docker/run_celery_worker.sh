#!/bin/sh
su -m iguana -c 'cd src/ && python -m celery -A common worker -l debug'
