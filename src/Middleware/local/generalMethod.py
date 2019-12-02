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
################################################
### this zone is called by global controller ###
################################################

def hello(argv):
	'''
	this is the first method to be call by startup.py to check that local controller is ready on this host.
	'''
	if len(argv)==0:
		return 'OK'
	else:
		return str(argv)

def update_cloud_info(argv):
	'''
	get info and update
	'''
	conn=argv[0][0]
	s=argv[0][1]
	dataDict=json.loads(argv[1])
	
	if 'masterDB' not in dataDict.keys():
		dataDict['masterDB']=None
	if 'masterDB_MAC' not in dataDict.keys():
		dataDict['masterDB_MAC']=None
	if 'slaveDB' not in dataDict.keys():
		dataDict['slaveDB']=None
	if 'globalController' not in dataDict.keys():
		dataDict['globalController']=None
	if 'network' not in dataDict.keys():
		dataDict['network']=None

	newDataDict=cacheFile.setValue(masterDB=dataDict['masterDB'],masterDB_MAC=dataDict['masterDB_MAC'],slaveDB=dataDict['slaveDB'],globalController=dataDict['globalController'],network=dataDict['network'])
	
	infoHost=newDataDict['masterDB']
	
	myIP=network.getMyIPAddr()
	
	#if INFO_HOST is not me and i am not slave , i should stop mysqld service
	#if infoHost!=str(myIP):
	#	dbController.stop()
	
	if 'nfs' in argv:
		#connect to database to get data of NFS Server to mount (may call updateLocal() to make everything)
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute('''SELECT `IPAddress` FROM `hosts` WHERE `isStorageHolder`=1;''')
		storageHost=str(cursor.fetchone()[0])
		db.close()

		#debugger.countdown(10,"before local unmount and mount")

		print "Umount:",nfsController.umount()
		print "Mount :",nfsController.mount(storageHost)
	
	if 'planner' in argv:
		general.runDaemonCommand("service mkplanner restart",conn,s,True)	#can be True in log system
	
	if 'dynamic' in argv:
		network.configToAuto() #(conn,s)

	return 'OK'

def stop_mkplanner(argv):
	'''
	just stop mkplanner (should do when remove host from system)
	'''
	general.runDaemonCommand("service mkplanner stop")
	return 'OK'