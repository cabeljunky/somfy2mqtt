# The first lines of your Dockerfile should always be:
FROM python:3-slim-bullseye AS builder

ENV version 79

RUN apt-get update && \ 
    apt-get install --no-install-recommends -y wget unzip && \
    apt-get install --no-install-recommends -y build-essential && \ 
    wget https://github.com/joan2937/pigpio/archive/refs/tags/v${version}.zip -O pigipo.zip && \
    unzip pigipo.zip && \
    cd pigpio-${version} && \
    make && \
    make install

FROM python:3-slim-bullseye
RUN mkdir -p /opt/somfy && \
    mkdir -p /opt/somfy/log  && \
    mkdir -p /opt/somfy/config && \
    apt-get update && \ 
    apt-get install --no-install-recommends -y python3-pigpio pigpio-tools python3-paho-mqtt python3-requests python3-ephem python3-flask python3-iniparse && \
    apt-get install --no-install-recommends -y build-essential && \
    apt-get clean

WORKDIR /opt/somfy
VOLUME /opt/somfy/config /opt/somfy/log
EXPOSE 80 
EXPOSE 443

COPY ./*.py /opt/somfy/
COPY ./html /opt/somfy/html/
COPY ./defaultConfig.conf /opt/somfy/config/operateShutters.conf
COPY --from=builder /usr/local/bin/pigpiod /usr/local/bin/pig2vcd /usr/local/bin/pigpiod /usr/local/bin/pigs /bin/
COPY --from=builder /usr/local/lib/libpigpio.so* /usr/local/lib/libpigpio_if.so* /usr/local/lib/libpigpio_if2.so* /lib/

RUN cd /opt/somfy && \
    python -m pip install --upgrade pip && \
    pip install ephem pigpio requests configparser Flask paho-mqtt

COPY entrypoint.sh /opt/somfy

ENTRYPOINT [ "sh", "entrypoint.sh" ]