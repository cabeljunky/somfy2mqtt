#!/bin/sh

set -e

: "${PIGPIOD_ARGS:=}"

#while true; do
#  sleep 100
#done

/usr/bin/python3 /opt/somfy/operateShutters.py -c "/opt/somfy/config/operateShutters.conf" "${PIGPIOD_ARGS}"
