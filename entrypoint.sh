#!/bin/sh

set -e

: "${PIGPIO_ARGS:-}"
: "${PIGPIO_ADDR:-}"
: "${PIGPIO_PORT:-}"

#while true; do
#  sleep 100
#done

/usr/bin/python3 /opt/somfy/operateShutters.py -c /opt/somfy/config/operateShutters.conf
