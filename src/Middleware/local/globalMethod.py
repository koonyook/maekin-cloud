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
"""
class globalServiceMigrateCaller(threading.Thread):

	def setArguments(self,targetHostIP,taskID):
		self.targetHostIP = targetHostIP
		self.taskID = taskID

	def run(self):
		success=globalService.migrate(self.targetHostIP)
		queue.finishSpecialTask(self.taskID)

def call_globalService_migrate(argv):
	targetHostIP=argv[1]
	taskID=argv[2]
	global closeSocketEvent
	closeSocketEvent=argv[0][2]
	aThread=globalServiceMigrateCaller()
	aThread.setArguments(targetHostIP,taskID)
	aThread.start()

	return 'OK'
"""
def you_are_next_global_controller(argv):
	'''
	promote myself to be global_controller and DHCP server
	'''
	conn = argv[0][0]
	s = argv[0][1]

	mode = argv[1]
	
	whitelistString = argv[2]

	#config and start dhcp server
	dhcpInfo=dhcpController.getDHCPInfoFromDatabase()
	dhcpController.configAll(dhcpInfo['networkID'],dhcpInfo['subnetMask'],dhcpInfo['defaultRoute'],dhcpInfo['dns'],dhcpInfo['hostBindings'],conn,s)
	
	#network.configToStaticFromCacheFile() #(conn,s)	#new system no need to do this
	
	#generate whitelist file
	aFile=open(setting.API_WHITELIST_FILE,'w')
	aFile.write(whitelistString)
	aFile.close()
	#start global controller (mkapi and mkworker and [scheduler])
	general.runDaemonCommand(command="service mkapi start",conn=conn,sock=s,pipe=True)	#can be True in log system
	#general.runDaemonCommand("service mkworker start debug",conn,s)	

	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()	
	
	if mode=='migrate':
		#must tell old GlobalController to stop service
		cursor.execute("SELECT `IPAddress` FROM `hosts` WHERE `isGlobalController`=1;")
		hostData=cursor.fetchone()
		if hostData!=None:
			result=connection.socketCall(hostData[0],setting.LOCAL_PORT,"close_global_controller_and_dhcp_server",['{socket_connection}'])
			if result!='OK':
				print 'close_global_controller_and_dhcp_server was not complete.(can leave it, no problem)'

	cursor.execute("UPDATE `hosts` SET `isGlobalController`=1 WHERE `IPAddress`='%s';"%(str(network.getMyIPAddr())))
	db.close()

	return "OK"
"""
class closeGlobalServices( threading.Thread ):
	def run ( self ):
		closeSocketEvent.wait()
		dhcpController.stop()
		time.sleep(3)
		result = subprocess.Popen(shlex.split("service mkapi stop"), stdout=subprocess.PIPE)
		result.wait()

		#update database
		infoHost=cacheFile.getDatabaseIP()
		db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
		cursor = db.cursor()
		cursor.execute("UPDATE `hosts` SET `isGlobalController`=0 WHERE `IPAddress`='%s';"%(str(network.getMyIPAddr())))
		db.close()

		network.configToAuto()

def close_global_controller_and_dhcp_server(argv):
	'''
	close and update database
	** dhcp server can be closed immediately
	*** but mkapi cannot (it should be delay to make sure that all socket of socketCall was closed)
	'''
	global closeSocketEvent
	closeSocketEvent=argv[0][2]
	aThread=closeGlobalServices()
	aThread.start()

	return 'OK'
"""
def close_global_controller_and_dhcp_server(argv):
	'''
	close and update database for move to other place
	'''
	dhcpController.stop()
	dhcpController.clearConfigFile()
	time.sleep(1)
	result = subprocess.Popen(shlex.split("service mkapi stop"), stdout=subprocess.PIPE)
	result.wait()

	#update database
	infoHost=cacheFile.getDatabaseIP()
	db = MySQLdb.connect(infoHost, setting.DB_USERNAME, setting.DB_PASSWORD, setting.DB_NAME )
	cursor = db.cursor()
	cursor.execute("UPDATE `hosts` SET `isGlobalController`=0 WHERE `IPAddress`='%s';"%(str(network.getMyIPAddr())))
	db.close()

	#network.configToAuto()		#no need to do like this

	return 'OK'

def suspend_global_controller_and_dhcp_server(argv):
	'''
	stop service to stop cloud
	'''
	dhcpController.stop()
	dhcpController.clearConfigFile()
	time.sleep(1)
	result = subprocess.Popen(shlex.split("service mkapi stop"), stdout=subprocess.PIPE)
	result.wait()

	return 'OK'

def wake_up_global_controller(argv):
	'''
	start mkapi
	'''
	conn =argv[0][0]
	s    =argv[0][1]

	general.runDaemonCommand("service mkapi start",conn,s,pipe=True)

	return "OK"