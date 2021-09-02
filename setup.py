import os
import sys

from setuptools import setup, find_packages

VERSION = '1'

install_reqs = ['configparser', 'Flask',  'paho-mqtt', 'ephem', 'requests', 'ssl']

setup(name='somfy2mqtt', 
    version=VERSION,
    description='A server to control and log somfy  devices.',
    author='Edward Heuveling',
    author_email='author@red-software.nl',
    url='https://github.com/cabeljunky/somfyy2mqtt',
    license='GPL',
    packages=find_packages(),
    install_requires=install_reqs,
    scripts=['operateShutters.py', 'myconfig.py', 'mywebserver.py', 'myscheduler.py', 'mymqtt.py', 'mylog.py', 'myalexa.py', 'fauxmo.py'],
)

