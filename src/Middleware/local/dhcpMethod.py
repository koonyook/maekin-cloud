import setting

from util import network,cacheFile,ping,general
from util import connection
from util import debugger
from info import dbController
from dhcp import dhcpController
from service import globalService

import os
import time
import threading
import subprocess,shlex
import libvirt
import MySQLdb
import json
import shutil

def wake_up_dhcp(argv):
	conn =argv[0][0]
	s    =argv[0][1]
	
	dhcpController.refreshConfig()
	dhcpController.start(conn,s)

	return "OK"

def dhcp_unbind_host(argv):
	'''
	must be called at main host only (globalController)
	'''
	macAddress=argv[0]
	ipAddress=argv[1]
	
	conn =argv[2][0]
	s    =argv[2][1]

	success=dhcpController.unbind([(macAddress,ipAddress)],conn,s)
	if not success:
		return "dhcp unbinding error"

	return 'OK'

	
def dhcp_bind_host(argv):
	'''
	must be called at main host only (globalController)
	'''
	macAddress=argv[0]
	ipAddress=argv[1]
	hostName=argv[2]

	conn =argv[3][0]
	s    =argv[3][1]

	success=dhcpController.bind([(macAddress,ipAddress,hostName)],conn,s)
	if not success:
		return "dhcp binding error"

	return 'OK'

def dhcp_update_from_database(argv):
	'''
	must be called at main host only (globalController)
	'''
	conn=argv[0][0]
	s=argv[0][1]

	success=dhcpController.updateFromDatabase(conn,s)
	if not success:
		return "dhcp_update_from_database error"

	return 'OK'