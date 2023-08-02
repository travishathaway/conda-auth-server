#!/bin/bash
#
# Tips:
#   `--error-logfile -` means write logs to stdout

set -e

sleep 3

exec gunicorn app:app \
    --name trkr-web \
    --workers 3 \
    --log-level info \
    --pythonpath '/opt' \
    --bind 0.0.0.0:9000 \
    --error-logfile - \
    --access-logfile -
