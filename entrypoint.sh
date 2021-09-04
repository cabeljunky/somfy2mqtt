#!/bin/sh

set -e

: "${PIGPIOD_ARGS:-}"
: "${PIGPIO_HOST:-}"
: "${PIGPIO_PORT:-}"
: "${CONFIG:-"/opt/somfy/config/operateShutters.conf"}"

#while true; do
#  sleep 100
#done

/usr/bin/python3 /opt/somfy/operateShutters.py -auto -mqtt -config "${CONFIG}"
