'''
run this file to clean this host and be ready
'''

import setting

import sys
import time
import subprocess,shlex
from xml.dom import minidom

import MySQLdb
import json

from dhcp import dhcpController
from storage import nfsController

from util import connection,cacheFile,network,general

from service import caService,dbService,nfsService,globalService

cacheFile.clearValue()

result = subprocess.Popen(shlex.split("service dhcpd stop"))
result.wait()
result = subprocess.Popen(shlex.split("service mysqld stop"))
result.wait()

result = subprocess.Popen(shlex.split("service mklocd clearlog"))
result.wait()
result = subprocess.Popen(shlex.split("service mklocm clearlog"))
result.wait()
result = subprocess.Popen(shlex.split("service mkplanner clearlog"))
result.wait()
result = subprocess.Popen(shlex.split("service mkapi clearlog"))
result.wait()

result = subprocess.Popen(shlex.split("service mkplanner stop"))
result.wait()
result = subprocess.Popen(shlex.split("service mklocd restart"))
result.wait()