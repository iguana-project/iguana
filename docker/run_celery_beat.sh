#!/bin/sh
bash -c 'cd src/ && python -m celery -A common beat --pidfile= -l debug'
