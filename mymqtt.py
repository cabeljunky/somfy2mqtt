#!/usr/bin/python3
# -*- coding: utf-8 -*-
#

import sys, re, argparse
import fcntl
import os
import re
import time
import locale
import pigpio
import socket
import signal, atexit, subprocess, traceback
import ssl
import threading
import json
from copy import deepcopy

try:
    # pip3 install paho-mqtt
    from mylog import MyLog
    import paho.mqtt.client as paho
except Exception as e1:
    print("\n\nThis program requires the modules located from the same github repository that are not present.\n")
    print("Error: " + str(e1))
    sys.exit(2)


class DiscoveryMsg:
    DISCOVERY_MSG = {"name": "",
                     "command_topic": "%s/%s/level/cmd",
                     "position_topic": "%s/%s/level/set_state",
                     "set_position_topic": "%s/%s/level/cmd",
                     "payload_open": "100",
                     "payload_close": "0",
                     "state_open": "100",
                     "state_closed": "0",
                     "unique_id": "",
                     "device": {"name": "",
                                "model": "somfy2mqtt controlled shutter",
                                "manufacturer": "Nickduino",
                                "identifiers": ""
                                }
                     }

    def __init__(self, shutter, shutter_id, topic):
        self.discovery_msg = deepcopy(DiscoveryMsg.DISCOVERY_MSG)
        self.discovery_msg["name"] = shutter
        self.discovery_msg["command_topic"] = DiscoveryMsg.DISCOVERY_MSG["command_topic"] % topic % shutter_id
        self.discovery_msg["position_topic"] = DiscoveryMsg.DISCOVERY_MSG["position_topic"] % topic % shutter_id
        self.discovery_msg["set_position_topic"] = DiscoveryMsg.DISCOVERY_MSG["set_position_topic"] % topic % shutter_id
        self.discovery_msg["unique_id"] = shutter_id
        self.discovery_msg["device"]["name"] = shutter
        self.discovery_msg["device"]["identifiers"] = shutter_id

    def __str__(self):
        return json.dumps(self.discovery_msg)


class MQTT(threading.Thread, MyLog):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        threading.Thread.__init__(self, group=group, target=target, name="MQTT")
        self.shutdown_flag = threading.Event()

        self.client = ()
        self.args = args
        self.kwargs = kwargs
        if kwargs["log"] != None:
            self.log = kwargs["log"]
        if kwargs["shutter"] != None:
            self.shutter = kwargs["shutter"]
        if kwargs["config"] != None:
            self.config = kwargs["config"]

        return

    def receiveMessageFromMQTT(self, client, userdata, message):
        self.LogInfo("starting receiveMessageFromMQTT")
        try:
            msg = str(message.payload.decode("utf-8"))
            topic = message.topic
            self.LogInfo("message received from MQTT: " + topic + " = " + msg)

            data = topic.split("/")
            if data[0] == self.config.MQTT_Discover_Topic and data[1] == "status":
                if msg == "online":
                    self.sendStartupInfo()
                return

            [prefix, shutterId, property, command] = topic.split("/")
            if (command == "cmd"):
                self.LogInfo("sending message: " + str(msg))
                if msg == "STOP":
                    self.shutter.stop(shutterId)
                elif int(msg) == 0:
                    self.shutter.lower(shutterId)
                elif int(msg) == 100:
                    self.shutter.rise(shutterId)
                elif (int(msg) > 0) and (int(msg) < 100):
                    currentPosition = self.shutter.getPosition(shutterId)
                    if int(msg) > currentPosition:
                        self.shutter.risePartial(shutterId, int(msg))
                    elif int(msg) < currentPosition:
                        self.shutter.lowerPartial(shutterId, int(msg))
            else:
                self.LogError("received unkown message: " + topic + ", message: " + msg)

        except Exception as e1:
            self.LogError("Exception Occured: " + str(e1))

        self.LogInfo("finishing receiveMessageFromMQTT")

    def sendMQTT(self, topic, msg):
        self.LogInfo("sending message to MQTT: " + topic + " = " + msg)
        self.client.publish(topic, msg, retain=True)

    def sendStartupInfo(self):
        for shutter, shutterId in sorted(self.config.ShuttersByName.items(), key=lambda kv: kv[1]):
            self.sendMQTT(self.config.MQTT_Discover_Topic + "/cover/" + shutterId + "/config",
                          str(DiscoveryMsg(shutter, shutterId, self.config.MQTT_Discover_Topic)))

    def on_connect(self, client, userdata, flags, rc):
        self.LogInfo("Connected to MQTT with result code " + str(rc))
        for shutter, shutterId in sorted(self.config.ShuttersByName.items(), key=lambda kv: kv[1]):
            self.LogInfo("Subscribe to shutter: " + shutter)
            self.client.subscribe(self.config.MQTT_Topic + "/" + shutterId + "/level/cmd")
        if self.config.EnableDiscovery:
            self.LogInfo("Sending Home Assistant MQTT Discovery messages")
            self.sendStartupInfo()

    def set_state(self, shutterId, level):
        self.LogInfo("Received request to set Shutter " + shutterId + " to " + str(level))
        self.sendMQTT(self.config.MQTT_Topic + "/" + shutterId + "/level/set_state", str(level))

    def run(self):
        self.LogInfo("Entering MQTT polling loop")

        # Setup the mqtt client
        self.client = paho.Client(client_id=self.config.MQTT_ClientID)
        # set username and password
        if not (self.config.MQTT_Password.strip() == ""):
            self.client.username_pw_set(username=self.config.MQTT_User, password=self.config.MQTT_Password)
        # set the ssl options

        if not ((self.config.MQTT_Cert.strip() == "") and not (self.config.MQTT_Key.strip() == "")):
            self.client.tls_set(ca_certs=self.config.MQTT_CA, certfile=self.config.MQTT_Cert, keyfile=self.config.MQTT_Key, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=self.config.MQTT_AllowedCiphers)
            self.client.tls_insecure_set(self.config.MQTT_VerifyCertificate)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.receiveMessageFromMQTT
        self.shutter.registerCallBack(self.set_state)

        # Startup the mqtt listener
        error = 0
        while not self.shutdown_flag.is_set():
            # Loop until the server is available
            try:
                self.LogInfo("Connecting to MQTT server")
                self.client.connect(self.config.MQTT_Server, self.config.MQTT_Port)
                if self.config.EnableDiscovery:
                    self.sendStartupInfo()
                break
            except Exception as e:
                error += 1
                self.LogInfo("Exception in MQTT connect " + str(error) + ": " + str(e.args))
                time.sleep(10 + error * 5)  # Wait some time before re-connecting

        error = 0
        while not self.shutdown_flag.is_set():
            # Loop and poll for incoming requests
            try:
                # NOTE: Timeout value must be smaller than MQTT keep_alive (which is 60s by default)
                self.client.loop(timeout=30)
            except Exception as e:
                error += 1
                self.LogInfo("Critical exception " + str(error) + ": " + str(e.args))
                time.sleep(0.5)  # Wait half a second when an exception occurs

        self.LogError("Received Signal to shut down MQTT thread")
        return
