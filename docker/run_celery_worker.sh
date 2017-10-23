#!/bin/sh
bash -c 'cd src/ && python -m celery -A common worker -l debug'
