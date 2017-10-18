#!/bin/sh
su -m iguana -c 'cd src && gunicorn common.wsgi:application -w 2 -b :8000 --capture-output --enable-stdio-inheritance --log-level=debug --access-logfile=- --log-file=-'
