'''
run this file to clean this host and be ready
'''

import setting

import sys
import time
import shutil
import subprocess,shlex
from xml.dom import minidom

import MySQLdb
import json

from dhcp import dhcpController
from storage import nfsController

from util import connection,cacheFile,network,general

from service import caService,dbService,nfsService,globalService

myIP=network.getMyIPAddr()
if myIP==None:
	try:
		shutil.copy2('/etc/sysconfig/network-scripts/_ifcfg-br0','/etc/sysconfig/network-scripts/ifcfg-br0')		
	except:
		print "do not have file _ifcfg-br0"
		sys.exit()

	network.kill_dhclient()
	result = subprocess.Popen(shlex.split("ifup br0"))
	result.wait()

	myIP=network.getMyIPAddr()

	if myIP==None:
		print "_ifcfg-br0 is wrong config"
		sys.exit()

#have ip now
result = subprocess.Popen(shlex.split("svn update /maekin/lib/middleware/"))
result.wait()

if 'distro' in sys.argv:
	result = subprocess.Popen(shlex.split("svn update /maekin/lib/distro/"))
	result.wait()