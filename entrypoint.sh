#!/bin/sh

set -e

: "${PIGPIO_ARGS:-}"
: "${PIGPIO_ADDR:-}"
: "${PIGPIO_PORT:-}"

#while true; do
#  sleep 100
#done

/usr/bin/python3 /opt/somfy/operateShutters.py -config /opt/somfy/config/operateShutters.conf -auto -mqtt
