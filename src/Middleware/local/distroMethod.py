#distroMethod for distro asking

import setting

from util import network,cacheFile,ping,general
from util import connection
from util import debugger
from info import dbController
from storage import nfsController

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import shutil
import string

def have_this_mac(argv):
	'''
	this will reply weather that mac address is in cloud system or not
	'''
	mac=argv[0]
	infoHost=cacheFile.getDatabaseIP()
	
	if infoHost==None:
		return 'no'
	
	try:
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute('''SELECT * FROM
			(SELECT `MACAddress` FROM `hosts` 
			UNION 
			SELECT `MACAddress` FROM `guests`) as `tmp` WHERE `MACAddress`='%s'
		'''%string.upper(mac))
		if cursor.fetchone()==None:
			db.close()
			return 'no'
		else:
			db.close()
			return 'yes'
	except MySQLdb.Error, e:
		return 'no'

def are_you_running_dhcpd(argv):
	'''
	if i am running dhcpd, i will reply "yes"
	'''
	myIP=network.getMyIPAddr()
	globalControllerIP=cacheFile.getGlobalControllerIP()
	
	if globalControllerIP==None:
		return 'no'
	
	if str(myIP)!=str(globalControllerIP):
		return 'no'
	else:
		
		try:
			infoHost=cacheFile.getDatabaseIP()
			db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
			cursor = db.cursor()
			cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isGlobalController`=1")
			result=cursor.fetchone()
			db.close()
			if result==None or result[0]!=str(myIP):
				return 'no'
			else:
				return 'yes'

		except MySQLdb.Error, e:
			return 'no'
