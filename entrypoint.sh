#!/bin/sh

set -e

: "${PIGPIOD_ARGS:-}"
: "${PIGPIOD_HOST:-}"
: "${PIGPIOD_PORT:-}"

#while true; do
#  sleep 100
#done

/usr/bin/python3 /opt/somfy/operateShutters.py -c "/opt/somfy/config/operateShutters.conf"
